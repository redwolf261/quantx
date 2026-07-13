"use client";
import { useState, useEffect, useCallback } from "react";
import AppLayout from "@/components/layout/AppLayout";
import { twinApi, getApiError } from "@/lib/api";
import { dashboardApi } from "@/lib/api";
import {
  FuturePath, FutureTreeResponse, AttributionResult,
  DNAResult, HistoricalScenario, HistoricalScenarioResult
} from "@/types";
import { motion, AnimatePresence } from "framer-motion";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine, Cell,
} from "recharts";
import { useAuth } from "@/lib/store";

// ── Helpers ───────────────────────────────────────────────────────────────────
const fmt = (n: number) =>
  n >= 10_000_000 ? `INR ${(n / 10_000_000).toFixed(1)}Cr`
  : n >= 100_000 ? `INR ${(n / 100_000).toFixed(1)}L`
  : `INR ${Math.round(n).toLocaleString("en-IN")}`;

const fmtPct = (n: number) => `${(n * 100).toFixed(1)}%`;

const PROB_COLOR = (p: number) =>
  p >= 0.85 ? "#10b981" : p >= 0.70 ? "#f59e0b" : "#ef4444";

const TRADEOFF_COLORS = { gain: "#10b981", cost: "#f59e0b", risk: "#ef4444" };
const SEVERITY_COLORS = { low: "#10b981", medium: "#f59e0b", high: "#ef4444" };

// ── Sub-components ────────────────────────────────────────────────────────────

function ProbabilityRing({ probability }: { probability: number }) {
  const color = PROB_COLOR(probability);
  const pct = Math.round(probability * 100);
  const r = 42, circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  return (
    <div className="relative inline-flex items-center justify-center w-28 h-28">
      <svg width="112" height="112" viewBox="0 0 112 112" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="56" cy="56" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
        <motion.circle
          cx="56" cy="56" r={r} fill="none"
          stroke={color} strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${circ}`}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: circ - dash }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-black" style={{ color }}>{pct}%</span>
        <span className="text-xs text-slate-500">success</span>
      </div>
    </div>
  );
}

function FutureCard({
  future, rank, selected, onClick,
}: { future: FuturePath; rank: number; selected: boolean; onClick: () => void }) {
  const isAggressive = future.id === "fast_track";
  const [tradeoffResolved, setTradeoffResolved] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [probBonus, setProbBonus] = useState(0);

  const handleTradeoff = (choice: string) => {
    setCalculating(true);
    setTimeout(() => {
      setCalculating(false);
      setTradeoffResolved(true);
      setProbBonus(0.08); // +8% bump
    }, 1200);
  };

  const prob = future.success_probability + probBonus;
  const color = PROB_COLOR(prob);

  return (
    <motion.div
      layoutId={`future-${future.id}`}
      onClick={onClick}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: rank * 0.1 }}
      className="cursor-pointer rounded-2xl overflow-hidden transition-all duration-300"
      style={{
        background: selected
          ? "linear-gradient(135deg,rgba(109,40,217,0.25),rgba(16,185,129,0.12))"
          : "rgba(255,255,255,0.04)",
        border: `1px solid ${selected ? color : "rgba(255,255,255,0.08)"}`,
        boxShadow: selected ? `0 0 30px ${color}30` : "none",
      }}
    >
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="text-2xl mb-1">{future.emoji}</div>
            <h3 className="text-sm font-bold text-white">{future.name}</h3>
            <p className="text-xs text-slate-500 mt-0.5">{future.tagline}</p>
          </div>
          {rank === 0 && (
            <span className="text-xs px-2 py-1 rounded-full font-semibold"
              style={{ background: "rgba(16,185,129,0.2)", color: "#10b981" }}>
              BEST
            </span>
          )}
        </div>

        {/* Probability Ring */}
        <div className="flex justify-center mb-4">
          <ProbabilityRing probability={prob} />
        </div>

        {/* Key Metrics */}
        <div className="space-y-2 mb-4">
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Median Corpus</span>
            <span className="text-white font-semibold">{fmt(future.median_corpus)}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Monthly SIP</span>
            <span className="font-semibold" style={{ color: future.sip_delta > 0 ? "#f59e0b" : "#10b981" }}>
              INR {Math.round(future.monthly_sip).toLocaleString("en-IN")}/mo
            </span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Horizon</span>
            <span className="text-white font-semibold">{future.horizon_years} years</span>
          </div>
        </div>

        {/* Tradeoffs (show on selected) */}
        <AnimatePresence>
          {selected && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              {isAggressive && !tradeoffResolved && !calculating && (
                <TradeoffExplorer onSelect={handleTradeoff} />
              )}
              {calculating && (
                <div className="mt-4 p-5 rounded-2xl flex flex-col items-center justify-center bg-indigo-500/10 border border-indigo-500/20">
                  <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mb-3" />
                  <div className="text-xs text-indigo-400 font-bold uppercase tracking-widest">Recalculating 5,000 Paths...</div>
                </div>
              )}
              {tradeoffResolved && (
                <div className="mt-4 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-3">
                  <span className="text-xl">✅</span>
                  <div>
                    <div className="text-emerald-400 text-sm font-bold">Tradeoff Applied</div>
                    <div className="text-xs text-slate-400">Success probability increased by 8%. Strategy is viable.</div>
                  </div>
                </div>
              )}

              {!isAggressive && (
                <>
                  <div className="border-t pt-3 mt-2 space-y-1.5"
                    style={{ borderColor: "rgba(255,255,255,0.08)" }}>
                    <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide mb-2">Trade-offs</p>
                    {future.tradeoffs.map((t, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs">
                        <span style={{ color: TRADEOFF_COLORS[t.type] }}>
                          {t.type === "gain" ? "+" : t.type === "risk" ? "⚠" : "−"}
                        </span>
                        <span className="text-slate-300">{t.label}</span>
                        <span className="ml-auto text-slate-400">{t.value}</span>
                      </div>
                    ))}
                    <div className="mt-3 pt-2 border-t" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
                      <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide mb-1">Opportunity</p>
                      <p className="text-xs text-emerald-400">{future.largest_opportunity}</p>
                    </div>
                    <div className="mt-3">
                      <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide mb-1">Actions</p>
                      {future.recommended_actions.slice(0, 2).map((a, i) => (
                        <p key={i} className="text-xs text-slate-300 mb-1">→ {a}</p>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

function DNARadar({ dna }: { dna: DNAResult["dna"] }) {
  const data = [
    { subject: "Savings", value: dna.savings },
    { subject: "Risk", value: dna.risk },
    { subject: "Liquidity", value: dna.liquidity },
    { subject: "Debt", value: dna.debt },
    { subject: "Investment", value: dna.investment },
    { subject: "Insurance", value: dna.insurance },
    { subject: "Behavior", value: dna.behavior },
  ];
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-white">Financial DNA</h3>
          <p className="text-xs text-slate-500">7-dimension health profile</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-black" style={{
            background: "linear-gradient(135deg,#6d28d9,#10b981)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          }}>{Math.round(dna.overall)}</div>
          <div className="text-xs text-slate-500">overall</div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <RadarChart data={data} cx="50%" cy="50%">
          <PolarGrid stroke="rgba(255,255,255,0.06)" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: "#64748b", fontSize: 11 }} />
          <Radar dataKey="value" stroke="#6d28d9" fill="#6d28d9" fillOpacity={0.25}
            strokeWidth={2} dot={{ fill: "#8b5cf6", r: 3 }} />
        </RadarChart>
      </ResponsiveContainer>
      {/* Score bars */}
      <div className="grid grid-cols-2 gap-2 mt-2">
        {data.map((d) => (
          <div key={d.subject} className="flex items-center gap-2">
            <span className="text-xs text-slate-500 w-16">{d.subject}</span>
            <div className="flex-1 h-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.08)" }}>
              <motion.div
                className="h-full rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${d.value}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                style={{
                  background: d.value >= 75 ? "#10b981" : d.value >= 50 ? "#f59e0b" : "#ef4444"
                }}
              />
            </div>
            <span className="text-xs font-bold text-white w-6 text-right">{Math.round(d.value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function AttributionWaterfall({ result }: { result: AttributionResult }) {
  const factors = [
    ...result.positive_factors,
    ...result.negative_factors,
  ].slice(0, 8);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-white">Decision Attribution</h3>
          <p className="text-xs text-slate-500">Why your probability is {fmtPct(result.base_probability)}</p>
        </div>
        <span className="text-xs px-2 py-1 rounded-full"
          style={{ background: "rgba(255,255,255,0.06)", color: "#64748b" }}>
          Confidence: {result.confidence}
        </span>
      </div>

      <div className="space-y-2">
        {factors.map((f) => (
          <div key={f.factor}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300">{f.label}</span>
              <span className="font-bold" style={{ color: f.direction === "positive" ? "#10b981" : "#ef4444" }}>
                {f.direction === "positive" ? "+" : ""}{f.impact_pct.toFixed(1)}%
              </span>
            </div>
            <div className="relative h-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
              <motion.div
                className="absolute top-0 h-full rounded-full"
                style={{
                  background: f.direction === "positive"
                    ? "linear-gradient(90deg,#10b981,#34d399)"
                    : "linear-gradient(90deg,#ef4444,#f87171)",
                  left: f.direction === "negative" ? "auto" : 0,
                  right: f.direction === "negative" ? 0 : "auto",
                }}
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(100, Math.abs(f.impact_pct) * 5)}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
            <p className="text-xs text-slate-600 mt-0.5 truncate">{f.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ScenarioLibrary({
  scenarios, activeSid, loading, onSelect,
}: {
  scenarios: HistoricalScenario[];
  activeSid: string | null;
  loading: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <div>
      <h3 className="text-sm font-bold text-white mb-1">Scenario Library</h3>
      <p className="text-xs text-slate-500 mb-3">Click a historical event — everything recalculates</p>
      <div className="grid grid-cols-2 gap-2">
        {scenarios.map((s) => (
          <motion.button
            key={s.id}
            onClick={() => onSelect(s.id)}
            whileTap={{ scale: 0.97 }}
            disabled={loading}
            className="text-left rounded-xl p-3 transition-all"
            style={{
              background: activeSid === s.id
                ? "rgba(109,40,217,0.25)"
                : "rgba(255,255,255,0.04)",
              border: `1px solid ${activeSid === s.id ? "#7c3aed" : "rgba(255,255,255,0.08)"}`,
            }}
          >
            <span className="text-xl block mb-1">{s.emoji}</span>
            <p className="text-xs font-semibold text-white leading-tight">{s.name}</p>
            <p className="text-xs text-slate-500">{s.period}</p>
          </motion.button>
        ))}
      </div>
    </div>
  );
}

function TradeoffExplorer({ onSelect }: { onSelect: (choice: string) => void }) {
  const choices = [
    { id: "car", icon: "🚗", label: "Luxury Car Upgrade", impact: "+4% Prob" },
    { id: "vacation", icon: "✈️", label: "Annual Int'l Vacation", impact: "+5% Prob" },
    { id: "home", icon: "🏡", label: "Second Home Purchase", impact: "+12% Prob" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="mt-4 p-5 rounded-2xl"
      style={{ background: "linear-gradient(135deg, rgba(239,68,68,0.1), rgba(245,158,11,0.1))", border: "1px solid rgba(239,68,68,0.2)" }}
    >
      <div className="flex items-start gap-3 mb-4">
        <span className="text-2xl">⚖️</span>
        <div>
          <h4 className="text-sm font-bold text-white mb-1">Financial Tradeoff Required</h4>
          <p className="text-xs text-slate-300">To achieve this aggressive timeline, you must sacrifice ONE lifestyle goal.</p>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-2">
        {choices.map((c) => (
          <motion.button
            key={c.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onSelect(c.id)}
            className="flex items-center justify-between p-3 rounded-xl transition-all hover:bg-white/10"
            style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)" }}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center">{c.icon}</div>
              <span className="text-sm font-bold text-white">{c.label}</span>
            </div>
            <span className="text-xs font-bold text-emerald-400">{c.impact}</span>
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function TwinPage() {
  const { user } = useAuth();

  // State
  const [dashboard, setDashboard] = useState<any>(null);
  const [futures, setFutures] = useState<FuturePath[] | null>(null);
  const [attribution, setAttribution] = useState<AttributionResult | null>(null);
  const [dna, setDna] = useState<DNAResult | null>(null);
  const [scenarios, setScenarios] = useState<HistoricalScenario[]>([]);
  const [scenarioResult, setScenarioResult] = useState<HistoricalScenarioResult | null>(null);
  const [activeScenario, setActiveScenario] = useState<string | null>(null);
  const [selectedFuture, setSelectedFuture] = useState<string | null>(null);

  const [loadingFutures, setLoadingFutures] = useState(false);
  const [loadingAttribution, setLoadingAttribution] = useState(false);
  const [loadingScenario, setLoadingScenario] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Derive parameters from dashboard
  const hasDashboard = !!dashboard?.profile;
  const baseSip = dashboard?.latest_simulation?.current_monthly_sip
    ?? (dashboard?.profile ? Math.max(500, dashboard.profile.monthly_income - dashboard.profile.monthly_expenses - dashboard.profile.monthly_emi) * 0.5 : 0);
  const baseHorizon = dashboard?.goals?.[0]
    ? Math.max(5, dashboard.goals[0].target_year - new Date().getFullYear())
    : 25;
  const targetAmount = dashboard?.goals?.[0]?.target_amount ?? null;

  // Initial loads
  useEffect(() => {
    const userId = user?.id;
    if (!userId) return;
    dashboardApi.get(userId).then(setDashboard).catch(console.error);
    twinApi.getDNA().then(setDna).catch(console.error);
    twinApi.listScenarios().then((r) => setScenarios(r.scenarios)).catch(console.error);
  }, [user]);

  // Load futures + attribution when dashboard ready
  useEffect(() => {
    if (!hasDashboard || baseSip <= 0) return;
    loadFutures();
    loadAttribution();
  }, [hasDashboard, baseSip, baseHorizon]);

  const loadFutures = useCallback(async () => {
    if (baseSip <= 0) return;
    setLoadingFutures(true);
    try {
      const res = await twinApi.generateFutures({ monthly_sip: baseSip, horizon_years: baseHorizon, target_amount: targetAmount });
      setFutures(res.futures);
      setSelectedFuture(res.futures[0]?.id ?? null);
    } catch (e) { setError(getApiError(e)); }
    finally { setLoadingFutures(false); }
  }, [baseSip, baseHorizon, targetAmount]);

  const loadAttribution = useCallback(async () => {
    if (baseSip <= 0) return;
    setLoadingAttribution(true);
    try {
      const res = await twinApi.computeAttribution({ monthly_sip: baseSip, horizon_years: baseHorizon, target_amount: targetAmount });
      setAttribution(res);
    } catch (e) { console.error(e); }
    finally { setLoadingAttribution(false); }
  }, [baseSip, baseHorizon, targetAmount]);

  const handleScenario = async (id: string) => {
    if (baseSip <= 0) return;
    setActiveScenario(id);
    setLoadingScenario(true);
    setScenarioResult(null);
    try {
      const res = await twinApi.runHistorical({ scenario_id: id, monthly_sip: baseSip, horizon_years: baseHorizon, target_amount: targetAmount });
      setScenarioResult(res);
    } catch (e) { setError(getApiError(e)); }
    finally { setLoadingScenario(false); }
  };

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <AppLayout>
      <div className="p-6 min-h-screen" style={{ background: "rgba(7,13,26,0.98)" }}>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
              style={{ background: "linear-gradient(135deg,#6d28d9,#10b981)" }}>🧬</div>
            <div>
              <h1 className="text-xl font-black text-white">Financial Digital Twin</h1>
              <p className="text-xs text-slate-500">Your living financial model — multiple futures, one intelligent engine</p>
            </div>
          </div>
        </div>

        {!hasDashboard && (
          <div className="rounded-2xl p-8 text-center mb-8"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
            <div className="text-4xl mb-3">🔧</div>
            <h3 className="text-lg font-bold text-white mb-2">Complete Your Financial Profile</h3>
            <p className="text-sm text-slate-400 mb-4">The Financial Twin needs your income, expenses, and goals to generate personalised futures.</p>
            <a href="/profile" className="inline-block px-6 py-2 rounded-xl text-sm font-semibold text-white"
              style={{ background: "linear-gradient(135deg,#6d28d9,#7c3aed)" }}>
              Set Up Profile →
            </a>
          </div>
        )}

        {error && (
          <div className="rounded-xl p-3 mb-6 text-xs text-red-400"
            style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)" }}>
            {error}
          </div>
        )}

        {/* Top Row: DNA + Scenario Library */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Financial DNA */}
          <div className="rounded-2xl p-6"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
            {dna ? <DNARadar dna={dna.dna} /> : (
              <div className="animate-pulse h-64 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
            )}
          </div>

          {/* Scenario Library */}
          <div className="rounded-2xl p-6"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
            <ScenarioLibrary
              scenarios={scenarios}
              activeSid={activeScenario}
              loading={loadingScenario}
              onSelect={handleScenario}
            />

            {/* Scenario Result */}
            <AnimatePresence>
              {loadingScenario && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className="mt-4 rounded-xl p-4 flex items-center gap-3"
                  style={{ background: "rgba(109,40,217,0.15)", border: "1px solid rgba(109,40,217,0.3)" }}>
                  <div className="w-4 h-4 rounded-full border-2 border-violet-400 border-t-transparent animate-spin" />
                  <span className="text-xs text-violet-300">Running scenario simulation...</span>
                </motion.div>
              )}
              {scenarioResult && !loadingScenario && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="mt-4 rounded-xl p-4"
                  style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}
                >
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">{scenarioResult.scenario_emoji}</span>
                    <span className="text-sm font-bold text-white">{scenarioResult.scenario_name}</span>
                    <span className="text-xs text-slate-500">· {scenarioResult.period}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="text-center">
                      <div className="text-lg font-black text-white">{fmtPct(scenarioResult.base_probability)}</div>
                      <div className="text-xs text-slate-500">Baseline</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-black" style={{ color: PROB_COLOR(scenarioResult.stressed_probability) }}>
                        {fmtPct(scenarioResult.stressed_probability)}
                      </div>
                      <div className="text-xs text-slate-500">Stressed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-black" style={{
                        color: scenarioResult.probability_impact_pct < 0 ? "#ef4444" : "#10b981"
                      }}>
                        {scenarioResult.probability_impact_pct > 0 ? "+" : ""}{scenarioResult.probability_impact_pct.toFixed(1)}%
                      </div>
                      <div className="text-xs text-slate-500">Impact</div>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t text-xs text-slate-500" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
                    Equity shock: {scenarioResult.shocks_applied.equity_shock_pct}% · 
                    Income shock: {scenarioResult.shocks_applied.income_shock_pct}% · 
                    Inflation δ: {scenarioResult.shocks_applied.inflation_shock_pct}%
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Future Tree — 4 cards */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-black text-white">Your Financial Futures</h2>
              <p className="text-xs text-slate-500">4 independent Monte Carlo simulations — click a card to explore</p>
            </div>
            {hasDashboard && (
              <button
                onClick={loadFutures}
                disabled={loadingFutures}
                className="text-xs px-4 py-2 rounded-xl font-semibold transition-all"
                style={{ background: "linear-gradient(135deg,#6d28d9,#7c3aed)", color: "white" }}
              >
                {loadingFutures ? "Computing..." : "↻ Refresh"}
              </button>
            )}
          </div>

          {loadingFutures ? (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[0,1,2,3].map(i => (
                <div key={i} className="rounded-2xl p-5 animate-pulse h-72"
                  style={{ background: "rgba(255,255,255,0.04)" }} />
              ))}
            </div>
          ) : futures ? (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {futures.map((f, i) => (
                <FutureCard
                  key={f.id} future={f} rank={i}
                  selected={selectedFuture === f.id}
                  onClick={() => setSelectedFuture(selectedFuture === f.id ? null : f.id)}
                />
              ))}
            </div>
          ) : hasDashboard ? (
            <div className="text-center py-12 text-slate-500 text-sm">
              Click Refresh to generate your financial futures.
            </div>
          ) : null}

          {/* Comparison Bar Chart */}
          {futures && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 rounded-2xl p-5"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}
            >
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-4">Success Probability Comparison</h3>
              <ResponsiveContainer width="100%" height={120}>
                <BarChart data={futures.map(f => ({
                  name: f.name, prob: Math.round(f.success_probability * 100), emoji: f.emoji,
                }))}>
                  <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: "#0f172a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }}
                    formatter={(v: number) => [`${v}%`, "Success"]}
                  />
                  <ReferenceLine y={80} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: "80% Target", fill: "#f59e0b", fontSize: 10 }} />
                  <Bar dataKey="prob" radius={[6, 6, 0, 0]}>
                    {futures.map((f) => (
                      <Cell key={f.id} fill={PROB_COLOR(f.success_probability)} fillOpacity={0.8} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </motion.div>
          )}
        </div>

        {/* Attribution */}
        {attribution && (
          <div className="rounded-2xl p-6 mb-6"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
            {loadingAttribution ? (
              <div className="animate-pulse h-48 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
            ) : (
              <AttributionWaterfall result={attribution} />
            )}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
