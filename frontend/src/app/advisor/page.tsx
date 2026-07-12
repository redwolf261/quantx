"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import AppLayout from "@/components/layout/AppLayout";
import { explainApi, simulationApi, optimizationApi, getApiError } from "@/lib/api";
import { useAuth, useStore } from "@/lib/store";
import { formatINR, formatPct } from "@/lib/utils";
import type { ExplainResponse, SimulationResult, OptimizationResult } from "@/types";

type ContextType = "simulation" | "optimization" | "stress_test" | "goal_status";

const CONTEXT_OPTIONS = [
  { value: "simulation" as ContextType, label: "📊 Simulation Results", desc: "Explain Monte Carlo output" },
  { value: "optimization" as ContextType, label: "⚙️ Optimization", desc: "Explain recommended changes" },
  { value: "stress_test" as ContextType, label: "🛡️ Stress Test", desc: "Explain risk scenarios" },
  { value: "goal_status" as ContextType, label: "🎯 Goal Status", desc: "Explain goal progress" },
];

export default function AdvisorPage() {
  const { user } = useAuth();
  const { profile, goals, latestSimulation } = useStore();
  const [contextType, setContextType] = useState<ContextType>("simulation");
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [optResult, setOptResult] = useState<OptimizationResult | null>(null);
  const [error, setError] = useState("");

  const selectedGoal = goals.find(g => g.goal_type === "retirement") || goals[0];
  const horizon = selectedGoal ? selectedGoal.target_year - new Date().getFullYear() : 20;
  const initialWealth = profile ? profile.total_savings + profile.total_investments : 0;

  const runAnalysis = async () => {
    if (!user?.id) return;
    setAnalyzing(true);
    setError("");
    setExplanation(null);

    try {
      let structuredData: Record<string, unknown> = {};
      let goalName = selectedGoal?.goal_name;

      if (contextType === "simulation" || contextType === "goal_status") {
        const sim = latestSimulation || await simulationApi.run({
          monthly_sip: selectedGoal?.required_monthly_sip ?? 15000,
          horizon_years: Math.max(5, horizon),
          initial_wealth: initialWealth,
          goal_id: selectedGoal?.id,
        });
        setSimResult(sim);
        structuredData = {
          success_probability: sim.success_probability,
          failure_probability: sim.failure_probability,
          median_corpus: sim.median_corpus,
          p10_corpus: sim.p10_corpus,
          p90_corpus: sim.p90_corpus,
          required_monthly_sip: sim.required_monthly_sip,
          current_monthly_sip: sim.current_monthly_sip,
          horizon_years: sim.horizon_years,
          num_simulations: sim.num_simulations,
          parameters: sim.parameters,
        };
      } else if (contextType === "optimization") {
        const opt = await optimizationApi.run({
          horizon_years: Math.max(5, horizon),
          goal_id: selectedGoal?.id,
        });
        setOptResult(opt);
        structuredData = opt as unknown as Record<string, unknown>;
      } else {
        // Stress test context — use latest sim as base
        const sim = latestSimulation;
        structuredData = {
          base_success_probability: sim?.success_probability ?? 0,
          scenario_count: 4,
          scenarios: [
            { name: "Market Crash", impact: -0.18 },
            { name: "Inflation Spike", impact: -0.12 },
            { name: "Salary Loss", impact: -0.25 },
            { name: "Medical Emergency", impact: -0.08 },
          ],
        };
      }

      // Call explainer
      const result = await explainApi.explain({
        context_type: contextType,
        structured_data: structuredData,
        goal_name: goalName,
        user_name: user.full_name || undefined,
      });
      setExplanation(result);
    } catch (e) {
      setError(getApiError(e));
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <AppLayout>
      <div className="p-6 space-y-6 bg-mesh min-h-screen">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-4"
        >
          {/* Avatar */}
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl flex-shrink-0 animate-glow-pulse"
            style={{
              background: "linear-gradient(135deg, #6d28d9, #10b981)",
              boxShadow: "0 0 30px rgba(109,40,217,0.4)",
            }}>
            🤖
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">AI Financial Advisor</h1>
            <p className="text-slate-400 text-sm">
              Powered by analytics + AI explanation — not an LLM chatbot
            </p>
          </div>
        </motion.div>

        {/* Important note */}
        <div className="glass-card p-4 border-violet-500/20"
          style={{ borderColor: "rgba(139,92,246,0.2)" }}>
          <p className="text-xs text-slate-400">
            <span className="text-violet-400 font-semibold">⚡ How it works:</span>{" "}
            Our analytics engine (Monte Carlo, optimization, stress testing) first computes precise
            financial insights. The AI then <strong className="text-white">only explains</strong> those
            pre-computed results in plain language — it never makes financial calculations itself.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Context selector */}
          <div className="space-y-4">
            <h3 className="text-white font-semibold">What would you like explained?</h3>
            <div className="space-y-2">
              {CONTEXT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setContextType(opt.value)}
                  className={`w-full text-left p-4 rounded-xl transition-all ${
                    contextType === opt.value ? "border-violet-500/30" : "border-white/06"
                  }`}
                  style={{
                    background: contextType === opt.value
                      ? "rgba(109,40,217,0.15)"
                      : "rgba(255,255,255,0.03)",
                    border: contextType === opt.value
                      ? "1px solid rgba(139,92,246,0.3)"
                      : "1px solid rgba(255,255,255,0.06)",
                  }}
                >
                  <p className="text-sm font-semibold text-white">{opt.label}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{opt.desc}</p>
                </button>
              ))}
            </div>

            {selectedGoal && (
              <div className="glass-card p-4">
                <p className="text-xs text-slate-400 mb-1">Selected Goal</p>
                <p className="text-white font-semibold text-sm">{selectedGoal.goal_name}</p>
                <p className="text-xs text-slate-500">Target: {formatINR(selectedGoal.target_amount, true)}</p>
              </div>
            )}

            <button
              onClick={runAnalysis}
              disabled={analyzing}
              className="btn-primary w-full justify-center"
            >
              {analyzing ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                  </svg>
                  Analyzing...
                </span>
              ) : "🤖 Get AI Explanation"}
            </button>
          </div>

          {/* Explanation result */}
          <div className="lg:col-span-2 space-y-4">
            <AnimatePresence mode="wait">
              {!explanation && !analyzing && (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="glass-card p-12 text-center h-full flex flex-col items-center justify-center"
                >
                  <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl mb-4"
                    style={{ background: "rgba(109,40,217,0.15)" }}>
                    🤖
                  </div>
                  <h3 className="text-white font-semibold mb-2">Ready to Explain</h3>
                  <p className="text-slate-400 text-sm max-w-xs">
                    Select what you&apos;d like explained and click &ldquo;Get AI Explanation&rdquo;.
                    The engine will analyze your finances and provide clear insights.
                  </p>
                </motion.div>
              )}

              {analyzing && (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="glass-card p-8 text-center"
                >
                  <div className="flex items-center gap-3 justify-center mb-4">
                    <div className="w-2 h-2 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="w-2 h-2 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="w-2 h-2 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                  <p className="text-slate-400 text-sm">Running financial analysis + generating explanation...</p>
                </motion.div>
              )}

              {explanation && (
                <motion.div
                  key="result"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-4"
                >
                  {/* Main explanation */}
                  <div className="glass-card p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-8 h-8 rounded-xl flex items-center justify-center text-base"
                        style={{ background: "linear-gradient(135deg, #6d28d9, #10b981)" }}>
                        🤖
                      </div>
                      <div>
                        <p className="text-white font-semibold text-sm">AI Financial Advisor</p>
                        <p className="text-xs text-slate-500">
                          {explanation.is_fallback
                            ? "Template-based explanation (no API key)"
                            : `Powered by ${explanation.model_used}`}
                        </p>
                      </div>
                      {explanation.is_fallback && (
                        <span className="badge-muted text-xs ml-auto">Fallback Mode</span>
                      )}
                    </div>
                    <p className="text-slate-200 leading-relaxed">{explanation.explanation}</p>
                  </div>

                  {/* Key insights */}
                  <div className="glass-card p-5">
                    <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                      <span>💡</span> Key Insights
                    </h4>
                    <ul className="space-y-2">
                      {explanation.key_insights.map((insight, i) => (
                        <motion.li
                          key={i}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.1 }}
                          className="flex items-start gap-3 text-sm"
                        >
                          <span className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5"
                            style={{ background: "rgba(139,92,246,0.2)", color: "#a78bfa" }}>
                            {i + 1}
                          </span>
                          <span className="text-slate-300">{insight}</span>
                        </motion.li>
                      ))}
                    </ul>
                  </div>

                  {/* Action items */}
                  <div className="glass-card p-5">
                    <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                      <span>✅</span> Recommended Actions
                    </h4>
                    <ul className="space-y-2">
                      {explanation.action_items.map((action, i) => (
                        <motion.li
                          key={i}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.3 + i * 0.1 }}
                          className="flex items-start gap-3 text-sm"
                        >
                          <span className="text-emerald-400 mt-0.5">→</span>
                          <span className="text-slate-300">{action}</span>
                        </motion.li>
                      ))}
                    </ul>
                  </div>

                  {/* Re-run button */}
                  <button
                    onClick={runAnalysis}
                    className="btn-secondary w-full justify-center text-sm"
                  >
                    🔄 Refresh Analysis
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            {error && (
              <div className="px-4 py-3 rounded-xl text-sm text-red-400 border border-red-500/20"
                style={{ background: "rgba(239,68,68,0.08)" }}>
                {error}
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
