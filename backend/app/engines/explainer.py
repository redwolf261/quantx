"""
Explainable AI Module
======================
IMPORTANT: The LLM never calculates financial recommendations.

Flow:
  Analytics Engine → Structured JSON → LLM → Natural Language

The LLM receives pre-computed structured data and is ONLY asked
to explain it in plain language. If no API key is configured,
falls back to template-based explanations.
"""
from __future__ import annotations
import json
from typing import Dict, List, Any, Optional
import structlog

from app.core.config import settings

log = structlog.get_logger()


SYSTEM_PROMPT = """You are FutureLens Financial Advisor — an AI that explains financial analysis results to Indian customers.

CRITICAL RULES:
- You do NOT calculate anything. All numbers are pre-computed by the analytics engine.
- You only explain the provided structured data in clear, empathetic language.
- Use Indian financial context (INR currency, SIP, EMI, lakh/crore notation).
- Be specific: always reference the exact numbers from the data.
- Keep explanations under 200 words.
- Format: One paragraph summary, then 2-3 key insights, then 2-3 action items.
"""

EXPLANATION_TEMPLATES = {
    "simulation": """Based on our Monte Carlo analysis with {num_simulations:,} simulations of your financial future:

Your {goal_name} goal has a **{success_probability:.0%} probability** of success over {horizon_years} years.

With your current monthly SIP of INR {monthly_sip:,.0f}, your portfolio is projected to reach INR {median_corpus:,.0f} (median scenario). In the best case (P90), it could reach INR {p90_corpus:,.0f}; in the worst case (P10), INR {p10_corpus:,.0f}.

To achieve an 80% success probability, a monthly SIP of INR {required_monthly_sip:,.0f} is recommended.""",

    "optimization": """Our optimization engine analyzed {optimization_iters} scenarios to maximize your goal probability.

**Current plan**: {current_probability:.0%} success probability with INR {current_sip:,.0f}/month SIP.

**Optimized plan**: {optimized_probability:.0%} success probability — an improvement of {improvement_pct:.0f} percentage points.

The recommended SIP increase is INR {sip_increase:,.0f}/month, bringing your total to INR {recommended_sip:,.0f}/month. This represents {savings_rate:.1%} of your monthly income.""",

    "stress_test": """We tested your financial plan against {scenario_count} stress scenarios.

**Baseline**: {base_success_probability:.0%} success probability.

Most impactful risk: **{worst_scenario}** reduces your success probability by {worst_impact:.0f} percentage points, resulting in {stressed_probability:.0%} success probability.

Your plan shows {resilience_level} resilience to financial shocks.""",

    "goal_status": """Your {goal_name} goal (target: INR {target_amount:,.0f} by {target_year}) currently has a **{success_probability:.0%}** probability of success.

You are currently investing INR {monthly_sip:,.0f}/month. The required SIP for this goal is INR {required_sip:,.0f}/month.

{status_message}""",
}

STATUS_MESSAGES = {
    "on_track": "🟢 You are on track! Keep up the consistent SIP contributions.",
    "slightly_off": "🟡 Minor adjustment needed. Consider increasing your SIP by INR {gap:,.0f}/month.",
    "at_risk": "🔴 This goal is at risk. Immediate action recommended — increase SIP or extend timeline.",
}


class ExplainerEngine:
    """
    Converts structured financial analytics output into natural language explanations.
    Uses OpenAI-compatible LLM API if configured, else falls back to templates.
    """

    def __init__(self):
        self._client = None
        self._use_llm = bool(settings.OPENAI_API_KEY)
        if self._use_llm:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL,
                )
                log.info("ExplainerEngine initialized with LLM", model=settings.OPENAI_MODEL)
            except Exception as e:
                log.warning("Failed to initialize OpenAI client, using templates", error=str(e))
                self._use_llm = False

    async def explain(
        self,
        context_type: str,
        structured_data: Dict[str, Any],
        goal_name: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate natural language explanation for financial analytics output.

        Args:
            context_type: Type of analysis (simulation, stress_test, optimization, goal_status)
            structured_data: Pre-computed analytics result
            goal_name: Name of the goal being explained
            user_name: Customer name for personalization

        Returns:
            Dict with explanation, key_insights, action_items, model_used
        """
        if self._use_llm:
            try:
                return await self._explain_with_llm(
                    context_type, structured_data, goal_name, user_name
                )
            except Exception as e:
                log.warning("LLM explanation failed, falling back to template", error=str(e))

        return self._explain_with_template(context_type, structured_data, goal_name)

    def _get_safe_value(self, data: Dict, *keys: str, default: Any = 0) -> Any:
        """Safely extract nested dictionary values."""
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, {})
            else:
                return default
        return current if current != {} else default

    async def _explain_with_llm(
        self,
        context_type: str,
        structured_data: Dict[str, Any],
        goal_name: Optional[str],
        user_name: Optional[str],
    ) -> Dict[str, Any]:
        """Call LLM with structured data, request explanation only."""
        data_json = json.dumps(structured_data, indent=2, default=str)
        user_prompt = f"""Context type: {context_type}
Goal name: {goal_name or 'General'}
Customer name: {user_name or 'Customer'}

Pre-computed financial analytics data:
{data_json}

Please explain these results to the customer. Provide:
1. A clear paragraph summary (2-3 sentences)
2. Three key insights (bullet points)
3. Three specific action items

Remember: You are ONLY explaining these pre-computed numbers. Do not perform any calculations."""

        response = await self._client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=500,
            temperature=0.3,
        )

        content = response.choices[0].message.content or ""

        # Parse structured response
        lines = content.split("\n")
        explanation = " ".join(lines[:3]) if lines else content
        key_insights = self._extract_bullets(content, "insights", 3)
        action_items = self._extract_bullets(content, "action", 3)

        return {
            "explanation": explanation.strip(),
            "key_insights": key_insights,
            "action_items": action_items,
            "model_used": settings.OPENAI_MODEL,
            "is_fallback": False,
        }

    def _explain_with_template(
        self,
        context_type: str,
        data: Dict[str, Any],
        goal_name: Optional[str],
    ) -> Dict[str, Any]:
        """Generate explanation from pre-defined templates without LLM."""
        try:
            if context_type == "simulation":
                explanation = EXPLANATION_TEMPLATES["simulation"].format(
                    num_simulations=data.get("num_simulations", 10000),
                    goal_name=goal_name or "financial",
                    success_probability=data.get("success_probability", 0),
                    horizon_years=data.get("parameters", {}).get("horizon_years", "N"),
                    monthly_sip=data.get("parameters", {}).get("monthly_sip", 0),
                    median_corpus=data.get("median_corpus", 0),
                    p90_corpus=data.get("p90_corpus", 0),
                    p10_corpus=data.get("p10_corpus", 0),
                    required_monthly_sip=data.get("required_monthly_sip", 0),
                )
                prob = data.get("success_probability", 0)
                insights = [
                    f"Your success probability is {prob:.0%} — {'strong' if prob >= 0.75 else 'moderate' if prob >= 0.5 else 'needs improvement'}",
                    f"Median portfolio value: INR {data.get('median_corpus', 0):,.0f}",
                    f"Range: INR {data.get('p10_corpus', 0):,.0f} (worst) to INR {data.get('p90_corpus', 0):,.0f} (best)",
                ]
                actions = [
                    f"Maintain consistent SIP of INR {data.get('parameters', {}).get('monthly_sip', 0):,.0f}/month",
                    f"Consider increasing SIP to INR {data.get('required_monthly_sip', 0):,.0f} for 80% confidence",
                    "Review asset allocation annually to stay aligned with risk profile",
                ]

            elif context_type == "optimization":
                curr_prob = data.get("current_probability", 0)
                opt_prob = data.get("optimized_probability", 0)
                improvement = (opt_prob - curr_prob) * 100
                explanation = EXPLANATION_TEMPLATES["optimization"].format(
                    optimization_iters=len(data.get("optimization_path", [])),
                    current_probability=curr_prob,
                    current_sip=data.get("current_sip", 0),
                    optimized_probability=opt_prob,
                    improvement_pct=improvement,
                    sip_increase=data.get("sip_increase", 0),
                    recommended_sip=data.get("recommended_sip", 0),
                    savings_rate=data.get("recommended_savings_rate", 0),
                )
                insights = [
                    f"Increasing SIP by INR {data.get('sip_increase', 0):,.0f}/month lifts success by {improvement:.0f}%",
                    f"Optimized probability: {opt_prob:.0%} vs current {curr_prob:.0%}",
                    f"Recommended savings rate: {data.get('recommended_savings_rate', 0):.1%} of income",
                ]
                actions = [
                    f"Increase monthly SIP to INR {data.get('recommended_sip', 0):,.0f}",
                    "Set up automatic SIP step-up of 10% annually",
                    "Review and eliminate unnecessary recurring expenses",
                ]

            elif context_type == "stress_test":
                scenarios = data.get("scenarios", [])
                worst = min(scenarios, key=lambda s: s.get("probability_impact", 0)) if scenarios else {}
                base_prob = data.get("base", {}).get("success_probability", 0)
                worst_impact = abs(worst.get("probability_impact", 0)) * 100

                resilience = "strong" if worst_impact < 10 else "moderate" if worst_impact < 20 else "low"
                explanation = EXPLANATION_TEMPLATES["stress_test"].format(
                    scenario_count=len(scenarios),
                    base_success_probability=base_prob,
                    worst_scenario=worst.get("scenario_label", "unknown scenario"),
                    worst_impact=worst_impact,
                    stressed_probability=worst.get("stressed_success_probability", 0),
                    resilience_level=resilience,
                )
                insights = [
                    f"Most vulnerable to: {worst.get('scenario_label', 'N/A')} (-{worst_impact:.0f}% probability)",
                    f"Baseline success: {base_prob:.0%}",
                    f"Plan resilience: {resilience.upper()}",
                ]
                actions = [
                    "Build emergency fund to cover 6 months expenses",
                    "Consider term life insurance if not already in place",
                    "Review portfolio diversification across asset classes",
                ]

            else:
                explanation = f"Analysis complete. Success probability: {data.get('success_probability', 'N/A')}"
                insights = ["Review your financial goals regularly", "Maintain consistent investments"]
                actions = ["Consult with your relationship manager for personalized advice"]

        except Exception as e:
            log.warning("Template explanation failed", error=str(e))
            explanation = "Your financial analysis has been completed. Please review the detailed metrics above."
            insights = ["Maintain consistent SIP contributions", "Review goals annually"]
            actions = ["Contact your relationship manager for detailed guidance"]

        return {
            "explanation": explanation.strip(),
            "key_insights": insights,
            "action_items": actions,
            "model_used": "template-fallback",
            "is_fallback": True,
        }

    def _extract_bullets(self, text: str, section: str, count: int) -> List[str]:
        """Extract bullet points from LLM response."""
        lines = text.split("\n")
        bullets = [
            line.lstrip("•-*123456789. ").strip()
            for line in lines
            if line.strip().startswith(("•", "-", "*", "1", "2", "3"))
        ]
        return bullets[:count] if bullets else [text[:100]]
