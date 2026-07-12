"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import AppLayout from "@/components/layout/AppLayout";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
  ReferenceLine,
} from "recharts";
import { stressTestApi, optimizationApi, simulationApi, getApiError } from "@/lib/api";
import { useAuth, useStore } from "@/lib/store";
import { formatINR, formatPct, riskLevelClass } from "@/lib/utils";
import type { StressTestResult, OptimizationResult, ScenarioResult } from "@/types";
import NetWorthChart from "@/components/charts/NetWorthChart";

type ViewMode = "comparison" | "stress" | "optimization";

export default function FuturesPage() {
  const { user } = useAuth();
  const { profile, goals } = useStore();
  const [view, setView] = useState<ViewMode>("comparison");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [stressResult, setStressResult] = useState<StressTestResult | null>(null);
  const [optResult, setOptResult] = useState<OptimizationResult | null>(null);
  const [baseResult, setBaseResult] = useState<any>(null);

  const selectedGoal = goals.find(g => g.goal_type === "retirement") || goals[0];
  const horizon = selectedGoal ? selectedGoal.target_year - new Date().getFullYear() : 20;
  const sip = selectedGoal?.required_monthly_sip ?? 15000;
  const initialWealth = profile
    ? profile.total_savings + profile.total_investments
    : 0;

  const runAll = async () => {
    if (!user?.id) return;
    setLoading(true);
    setError("");
    try {
      const [base, stress, opt] = await Promise.all([
        simulationApi.run({
          monthly_sip: sip,
          horizon_years: Math.max(5, horizon),
          initial_wealth: initialWealth,
          goal_id: selectedGoal?.id,
        }),
        stressTestApi.run({
          monthly_sip: sip,
          horizon_years: Math.max(5, horizon),
          goal_id: selectedGoal?.id,
        }),
        optimizationApi.run({
          horizon_years: Math.max(5, horizon),
          goal_id: selectedGoal?.id,
        }),
      ]);
      setBaseResult(base);
      setStressResult(stress);
      setOptResult(opt);
    } catch (e) {
      setError(getApiError(e));
    } finally {
      setLoading(false);
    }
  };

  const hasData = stressResult && optResult && baseResult;

  // Build comparison chart data
  const comparisonData = hasData
    ? [
        {
          name: "Current Plan",
          probability: Math.round((baseResult.success_probability ?? 0) * 100),
          corpus: Math.round(baseResult.median_corpus / 1e5),
          fill: "#8b5cf6",
        },
        {
          name: "Optimized",
          probability: Math.round((optResult.optimized_probability) * 100),
          corpus: Math.round(baseResult.median_corpus * (1 + optResult.improvement) / 1e5),
          fill: "#10b981",
        },
        ...stressResult.scenarios.slice(0, 3).map(s => ({
          name: s.scenario_label.split(" ")[0] + " Shock",
          probability: Math.round(s.stressed_success_probability * 100),
          corpus: Math.round(s.stressed_median_corpus / 1e5),
          fill: "#ef4444",
        })),
      ]
    : [];

  return (
    <AppLayout>
      <div className="p-6 space-y-6 bg-mesh min-h-screen">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="text-2xl font-bold text-white">⑂ Future Forks</h1>
            <p className="text-slate-400 text-sm">
              Compare your current plan against optimized and stress-tested scenarios
            </p>
          </div>
          <button
            onClick={runAll}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Analyzing...
              </span>
            ) : "⑂ Compare Futures"}
          </button>
        </motion.div>

        {error && (
          <div className="px-4 py-3 rounded-xl text-sm text-red-400 border border-red-500/20"
            style={{ background: "rgba(239,68,68,0.08)" }}>
            {error}
          </div>
        )}

        {!hasData && !loading && (
          <div className="glass-card p-12 text-center">
            <p className="text-5xl mb-4">⑂</p>
            <h3 className="text-xl font-bold text-white mb-2">Compare Your Financial Futures</h3>
            <p className="text-slate-400 mb-6 max-w-md mx-auto">
              Click &ldquo;Compare Futures&rdquo; to run Monte Carlo simulation, stress tests, and optimization
              simultaneously and compare results side by side.
            </p>
            <button onClick={runAll} className="btn-primary">
              Run Full Analysis
            </button>
          </div>
        )}

        {hasData && (
          <>
            {/* View tabs */}
            <div className="tab-group">
              {(["comparison", "stress", "optimization"] as ViewMode[]).map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  className={`tab-item flex-1 capitalize ${view === v ? "active" : ""}`}
                >
                  {v === "comparison" ? "📊 Overview" : v === "stress" ? "🛡️ Stress Test" : "⚙️ Optimization"}
                </button>
              ))}
            </div>

            {/* Overview */}
            {view === "comparison" && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                {/* 3 cards */}
                <div className="grid grid-cols-3 gap-4">
                  <PlanCard
                    title="Current Plan"
                    emoji="📋"
                    probability={baseResult.success_probability}
                    corpus={baseResult.median_corpus}
                    sip={sip}
                    color="#8b5cf6"
                    highlight={false}
                  />
                  <PlanCard
                    title="Optimized Plan"
                    emoji="⚙️"
                    probability={optResult.optimized_probability}
                    corpus={baseResult.median_corpus * (1 + optResult.improvement)}
                    sip={optResult.recommended_sip}
                    color="#10b981"
                    highlight
                  />
                  <PlanCard
                    title="Worst Stress"
                    emoji="🚨"
                    probability={stressResult.scenarios.reduce((min, s) =>
                      s.stressed_success_probability < min ? s.stressed_success_probability : min, 1)}
                    corpus={stressResult.scenarios.reduce((min, s) =>
                      s.stressed_median_corpus < min ? s.stressed_median_corpus : min, Infinity)}
                    sip={sip}
                    color="#ef4444"
                    highlight={false}
                  />
                </div>

                {/* Comparison bar chart */}
                <div className="glass-card p-6">
                  <h3 className="text-white font-semibold mb-4">Success Probability Comparison</h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={comparisonData} barCategoryGap="30%">
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                        <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} />
                        <YAxis tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} domain={[0, 100]} />
                        <Tooltip
                          contentStyle={{ background: "rgba(7,13,26,0.95)", border: "1px solid rgba(139,92,246,0.25)", borderRadius: "12px" }}
                          formatter={(v: any) => [`${v}%`, "Probability"]}
                        />
                        <ReferenceLine y={80} stroke="#10b981" strokeDasharray="4 4" label={{ value: "80% Target", fill: "#10b981", fontSize: 11 }} />
                        <Bar dataKey="probability" radius={[6, 6, 0, 0]}>
                          {comparisonData.map((entry, i) => (
                            <rect key={i} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Stress Test View */}
            {view === "stress" && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                <div className="glass-card p-5 mb-4">
                  <div className="flex items-center gap-3 mb-2">
                    <p className="text-white font-semibold">Baseline Success Probability</p>
                    <span className="badge-success">
                      {formatPct(stressResult.base_result.success_probability ?? 0)}
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm">
                    Impact of each stress scenario on your {selectedGoal?.goal_name || "goal"}
                  </p>
                </div>

                {stressResult.scenarios.map((scenario) => (
                  <ScenarioRow key={scenario.scenario} scenario={scenario} />
                ))}
              </motion.div>
            )}

            {/* Optimization View */}
            {view === "optimization" && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div className="glass-card p-6">
                    <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-4">Before Optimization</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-slate-400 text-sm">Success Probability</span>
                        <span className="font-mono font-bold text-amber-400">{formatPct(optResult.current_probability)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400 text-sm">Monthly SIP</span>
                        <span className="font-mono text-white">{formatINR(optResult.current_sip, true)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="glass-card p-6 border-emerald-500/20"
                    style={{ borderColor: "rgba(16,185,129,0.2)" }}>
                    <h3 className="text-emerald-400 text-sm font-medium uppercase tracking-wider mb-4">After Optimization ✨</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-slate-400 text-sm">Success Probability</span>
                        <span className="font-mono font-bold text-emerald-400">{formatPct(optResult.optimized_probability)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400 text-sm">Recommended SIP</span>
                        <span className="font-mono text-white">{formatINR(optResult.recommended_sip, true)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400 text-sm">SIP Increase</span>
                        <span className="font-mono text-amber-400">+{formatINR(optResult.sip_increase, true)}/mo</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400 text-sm">Improvement</span>
                        <span className="font-mono text-emerald-400">
                          +{(optResult.improvement * 100).toFixed(1)} percentage points
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Optimization convergence path */}
                {optResult.optimization_path.length > 0 && (
                  <div className="glass-card p-6">
                    <h3 className="text-white font-semibold mb-4">Optimization Convergence</h3>
                    <div className="h-48">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={optResult.optimization_path}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                          <XAxis dataKey="sip" tickFormatter={(v) => formatINR(v, true)} tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                          <YAxis tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                          <Tooltip
                            contentStyle={{ background: "rgba(7,13,26,0.95)", border: "1px solid rgba(139,92,246,0.25)", borderRadius: "12px" }}
                            formatter={(v: any) => [formatPct(v), "Probability"]}
                            labelFormatter={(v) => `SIP: ${formatINR(Number(v), true)}`}
                          />
                          <Bar dataKey="probability" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </>
        )}
      </div>
    </AppLayout>
  );
}

function PlanCard({ title, emoji, probability, corpus, sip, color, highlight }: {
  title: string; emoji: string; probability: number; corpus: number;
  sip: number; color: string; highlight: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass-card p-5 ${highlight ? "border-emerald-500/25" : ""}`}
      style={highlight ? { borderColor: "rgba(16,185,129,0.25)", boxShadow: "0 0 30px rgba(16,185,129,0.08)" } : {}}
    >
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">{emoji}</span>
        <h3 className="text-white font-semibold text-sm">{title}</h3>
        {highlight && <span className="badge-success text-xs">Best</span>}
      </div>
      <div className="space-y-3">
        <div>
          <p className="text-slate-500 text-xs mb-1">Success Probability</p>
          <p className="text-2xl font-bold font-mono" style={{ color }}>
            {formatPct(probability)}
          </p>
        </div>
        <div>
          <p className="text-slate-500 text-xs mb-1">Median Corpus</p>
          <p className="font-mono font-semibold text-white">{formatINR(corpus, true)}</p>
        </div>
        <div>
          <p className="text-slate-500 text-xs mb-1">Monthly SIP</p>
          <p className="font-mono text-slate-300">{formatINR(sip, true)}/mo</p>
        </div>
      </div>
    </motion.div>
  );
}

function ScenarioRow({ scenario }: { scenario: ScenarioResult }) {
  const impact = scenario.probability_impact * 100;
  const barWidth = Math.abs(impact) / 30 * 100; // normalize to 30% max impact

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="glass-card p-5"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="text-white font-semibold">{scenario.scenario_label}</h4>
          <p className="text-xs text-slate-400 mt-0.5">
            Corpus impact: {scenario.corpus_impact_pct.toFixed(1)}%
          </p>
        </div>
        <span className={riskLevelClass(scenario.risk_level)}>
          {scenario.risk_level.toUpperCase()}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4 text-sm mb-3">
        <div>
          <p className="text-slate-500 text-xs">Baseline</p>
          <p className="font-mono font-semibold text-white">{formatPct(scenario.base_success_probability)}</p>
        </div>
        <div>
          <p className="text-slate-500 text-xs">Stressed</p>
          <p className="font-mono font-semibold text-red-400">{formatPct(scenario.stressed_success_probability)}</p>
        </div>
        <div>
          <p className="text-slate-500 text-xs">Impact</p>
          <p className="font-mono font-semibold text-red-400">{impact.toFixed(1)} pts</p>
        </div>
      </div>

      {/* Impact bar */}
      <div className="progress-bar">
        <motion.div
          className="progress-fill"
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, barWidth)}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          style={{
            background: scenario.risk_level === "critical"
              ? "linear-gradient(90deg, #dc2626, #ef4444)"
              : scenario.risk_level === "high"
              ? "linear-gradient(90deg, #ea580c, #f97316)"
              : "linear-gradient(90deg, #d97706, #f59e0b)",
          }}
        />
      </div>
    </motion.div>
  );
}
