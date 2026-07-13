"use client";
import { useState, useCallback, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import AppLayout from "@/components/layout/AppLayout";
import NetWorthChart from "@/components/charts/NetWorthChart";
import { simulationApi, getApiError } from "@/lib/api";
import { useAuth, useStore } from "@/lib/store";
import { formatINR, formatPct, probabilityRingColor, debounce } from "@/lib/utils";
import type { SimulationResult } from "@/types";

const HORIZONS = [5, 10, 20, 30];

export default function PlaygroundPage() {
  const { user } = useAuth();
  const { profile } = useStore();

  const [sip, setSip] = useState(15000);
  const [horizon, setHorizon] = useState(20);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const maxSip = profile ? Math.max(50000, profile.monthly_income * 0.5) : 100000;
  const initialWealth = profile
    ? profile.total_savings + profile.total_investments
    : 500000;

  const runSimulation = useCallback(
    async (sipAmount: number, horizonYears: number) => {
      if (!user?.id) return;
      setLoading(true);
      setError("");
      try {
        const res = await simulationApi.run({
          monthly_sip: sipAmount,
          horizon_years: horizonYears,
          initial_wealth: initialWealth,
          num_simulations: 10000,
        });
        setResult(res);
      } catch (e) {
        setError(getApiError(e));
      } finally {
        setLoading(false);
      }
    },
    [user?.id, initialWealth]
  );

  // Debounced simulation trigger on slider change
  const debouncedRun = useRef(debounce((s: unknown, h: unknown) => runSimulation(s as number, h as number), 600));

  useEffect(() => {
    debouncedRun.current(sip, horizon);
  }, [sip, horizon]);

  const prob = result?.success_probability ?? 0;
  const ringColor = probabilityRingColor(prob);
  const circumference = 2 * Math.PI * 55;

  return (
    <AppLayout>
      <div className="p-6 space-y-6 bg-mesh min-h-screen">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold text-white mb-1">⚡ Financial Decision Playground</h1>
          <p className="text-slate-400 text-sm">
            Adjust sliders to simulate different financial decisions. Results update in real-time.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls Panel */}
          <div className="space-y-6">
            {/* SIP Slider */}
            <div className="glass-card p-5 space-y-4">
              <h3 className="text-white font-semibold flex items-center gap-2">
                <span className="text-teal-400">₹</span> Monthly SIP
              </h3>

              <div className="text-3xl font-bold font-mono text-teal-400">
                {formatINR(sip)}
              </div>

              <input
                type="range"
                min={500}
                max={maxSip}
                step={500}
                value={sip}
                onChange={(e) => setSip(Number(e.target.value))}
                className="fl-slider w-full"
                style={{ "--pct": `${((sip - 500) / (maxSip - 500)) * 100}%` } as React.CSSProperties}
              />

              <div className="flex justify-between text-xs text-slate-500">
                <span>₹500/mo</span>
                <span>{formatINR(maxSip, true)}/mo</span>
              </div>

              {/* SIP quick picks */}
              <div className="flex gap-2 flex-wrap">
                {[5000, 10000, 20000, 50000].filter(v => v <= maxSip).map((v) => (
                  <button
                    key={v}
                    onClick={() => setSip(v)}
                    className={`text-xs px-3 py-1 rounded-full border transition-all ${
                      sip === v
                        ? "border-teal-500 bg-teal-500/20 text-teal-300"
                        : "border-white/10 text-slate-400 hover:border-teal-500/40"
                    }`}
                  >
                    {formatINR(v, true)}
                  </button>
                ))}
              </div>
            </div>

            {/* Horizon Selector */}
            <div className="glass-card p-5">
              <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                <span>📅</span> Time Horizon
              </h3>
              <div className="grid grid-cols-4 gap-2">
                {HORIZONS.map((h) => (
                  <button
                    key={h}
                    onClick={() => setHorizon(h)}
                    className={`py-3 rounded-xl text-sm font-semibold transition-all ${
                      horizon === h
                        ? "text-white"
                        : "text-slate-400 hover:text-white"
                    }`}
                    style={{
                      background: horizon === h
                        ? "linear-gradient(135deg, rgba(109,40,217,0.4), rgba(139,92,246,0.25))"
                        : "rgba(255,255,255,0.04)",
                      border: horizon === h
                        ? "1px solid rgba(139,92,246,0.4)"
                        : "1px solid rgba(255,255,255,0.06)",
                    }}
                  >
                    {h}Y
                  </button>
                ))}
              </div>
            </div>

            {/* Current Wealth (read-only) */}
            <div className="glass-card p-5 space-y-3">
              <h3 className="text-white font-semibold">Starting Wealth</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Savings</span>
                  <span className="font-mono text-white">
                    {formatINR(profile?.total_savings ?? 0, true)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Investments</span>
                  <span className="font-mono text-white">
                    {formatINR(profile?.total_investments ?? 0, true)}
                  </span>
                </div>
                <div className="fl-divider" />
                <div className="flex justify-between">
                  <span className="text-slate-400">Total</span>
                  <span className="font-mono text-emerald-400 font-bold">
                    {formatINR(initialWealth, true)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2 space-y-6">
            {/* Probability Gauge */}
            <div className="glass-card p-6">
              <div className="flex items-start gap-8">
                {/* Large probability ring */}
                <div className="relative w-36 h-36 flex-shrink-0">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 144 144">
                    <circle cx="72" cy="72" r="55" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
                    <motion.circle
                      cx="72" cy="72" r="55"
                      fill="none"
                      stroke={ringColor}
                      strokeWidth="10"
                      strokeLinecap="round"
                      strokeDasharray={circumference}
                      animate={{ strokeDashoffset: circumference - prob * circumference }}
                      transition={{ duration: 0.8, ease: "easeOut" }}
                      style={{ filter: `drop-shadow(0 0 12px ${ringColor}80)` }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <AnimatePresence mode="wait">
                      <motion.span
                        key={Math.round(prob * 100)}
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 5 }}
                        className="text-3xl font-bold font-mono"
                        style={{ color: ringColor }}
                      >
                        {loading ? "..." : `${Math.round(prob * 100)}%`}
                      </motion.span>
                    </AnimatePresence>
                    <span className="text-xs text-slate-500">Success</span>
                  </div>
                </div>

                {/* Key metrics */}
                <div className="flex-1 grid grid-cols-2 gap-4">
                  {[
                    {
                      label: "Median Corpus",
                      value: result ? formatINR(result.median_corpus, true) : "—",
                      color: "text-emerald-400",
                    },
                    {
                      label: "Best Case (P90)",
                      value: result ? formatINR(result.p90_corpus, true) : "—",
                      color: "text-teal-400",
                    },
                    {
                      label: "Worst Case (P10)",
                      value: result ? formatINR(result.p10_corpus, true) : "—",
                      color: "text-red-400",
                    },
                    {
                      label: "Required SIP",
                      value: result ? `${formatINR(result.required_monthly_sip, true)}/mo` : "—",
                      color: "text-amber-400",
                    },
                  ].map((m) => (
                    <div key={m.label} className="metric-pill flex-col items-start p-3 rounded-xl"
                      style={{ background: "rgba(255,255,255,0.03)" }}>
                      <span className="text-slate-500 text-xs">{m.label}</span>
                      <AnimatePresence mode="wait">
                        <motion.span
                          key={m.value}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className={`font-mono font-bold text-sm mt-1 ${m.color}`}
                        >
                          {m.value}
                        </motion.span>
                      </AnimatePresence>
                    </div>
                  ))}
                </div>
              </div>

              {/* Status banner */}
              {result && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mt-4 px-4 py-3 rounded-xl text-sm"
                  style={{
                    background: prob >= 0.8
                      ? "rgba(16,185,129,0.1)"
                      : prob >= 0.6
                      ? "rgba(245,158,11,0.1)"
                      : "rgba(239,68,68,0.1)",
                    border: `1px solid ${prob >= 0.8 ? "rgba(16,185,129,0.2)" : prob >= 0.6 ? "rgba(245,158,11,0.2)" : "rgba(239,68,68,0.2)"}`,
                  }}
                >
                  <span style={{ color: ringColor }} className="font-semibold">
                    {prob >= 0.8
                      ? "✅ Great! This plan has a high probability of success."
                      : prob >= 0.6
                      ? "⚠️ Moderate confidence. Consider increasing SIP for better odds."
                      : "🚨 Low probability. Significant adjustments recommended."}
                  </span>
                  {result.required_monthly_sip > sip && (
                    <span className="text-slate-400 ml-2">
                      Increase SIP by {formatINR(result.required_monthly_sip - sip, true)} for 80% confidence.
                    </span>
                  )}
                </motion.div>
              )}
            </div>

            {/* Fan Chart */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-semibold">Wealth Projection Fan</h3>
                <div className="flex gap-3 text-xs">
                  <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-teal-400 inline-block rounded dashed" />Best</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-emerald-400 inline-block rounded" />Median</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-red-400 inline-block rounded dashed" />Worst</span>
                </div>
              </div>
              {result?.percentile_bands ? (
                <NetWorthChart bands={result.percentile_bands} />
              ) : (
                <div className="h-52 flex items-center justify-center">
                  {loading ? (
                    <div className="flex items-center gap-2 text-slate-400 text-sm">
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
                      Running 10,000 simulations...
                    </div>
                  ) : (
                    <p className="text-slate-500 text-sm">Move the sliders to run a simulation</p>
                  )}
                </div>
              )}
            </div>

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
