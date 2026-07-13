"use client";
import { useState, useEffect } from "react";
import AppLayout from "@/components/layout/AppLayout";
import { twinApi, dashboardApi, getApiError } from "@/lib/api";
import { FuturePath, AttributionResult } from "@/types";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/lib/store";

export default function RoadmapPage() {
  const { user } = useAuth();
  
  const [dashboard, setDashboard] = useState<any>(null);
  const [attribution, setAttribution] = useState<AttributionResult | null>(null);
  const [smartBalance, setSmartBalance] = useState<FuturePath | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Simulated GPS state for "Wow" factor
  const [recalculating, setRecalculating] = useState(false);
  const [routeAccepted, setRouteAccepted] = useState(false);

  useEffect(() => {
    if (!user?.id) return;
    setLoading(true);
    dashboardApi.get(user.id)
      .then(d => {
        setDashboard(d);
        const baseSip = d.latest_simulation?.current_monthly_sip || 10000;
        const horizon = d.goals?.[0] ? Math.max(5, d.goals[0].target_year - new Date().getFullYear()) : 25;
        const targetAmount = d.goals?.[0]?.target_amount;
        
        return Promise.all([
          twinApi.computeAttribution({ monthly_sip: baseSip, horizon_years: horizon, target_amount: targetAmount }),
          twinApi.generateFutures({ monthly_sip: baseSip, horizon_years: horizon, target_amount: targetAmount })
        ]);
      })
      .then(([attr, futs]) => {
        setAttribution(attr);
        setSmartBalance(futs.futures.find(f => f.id === "smart_balance") || futs.futures[0]);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [user]);

  const handleAcceptRoute = () => {
    setRecalculating(true);
    setTimeout(() => {
      setRecalculating(false);
      setRouteAccepted(true);
    }, 1200);
  };

  const currentYear = new Date().getFullYear();
  const goalYear = dashboard?.goals?.[0]?.target_year || currentYear + 25;
  const goalName = dashboard?.goals?.[0]?.goal_name || "Retirement";

  const obstacle = attribution?.negative_factors?.[0] || { label: "Unknown Risk", description: "Market volatility detected on path." };
  
  const altSipDelta = smartBalance?.sip_delta || 0;
  const currentProb = attribution?.base_probability || 0;
  const altProb = smartBalance?.success_probability || 0;

  return (
    <AppLayout>
      <div className="p-6 min-h-screen flex flex-col" style={{ background: "rgba(7,13,26,0.98)" }}>
        
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
              style={{ background: "linear-gradient(135deg,#0ea5e9,#3b82f6)" }}>📍</div>
            <div>
              <h1 className="text-xl font-black text-white">Financial GPS</h1>
              <p className="text-xs text-slate-500">Live navigation to your financial destination</p>
            </div>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold"
            style={{ background: "rgba(16,185,129,0.1)", color: "#10b981", border: "1px solid rgba(16,185,129,0.2)" }}>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            GPS ACTIVE
          </div>
        </div>

        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="animate-pulse flex flex-col items-center">
              <div className="w-12 h-12 rounded-full border-4 border-blue-500 border-t-transparent animate-spin mb-4" />
              <div className="text-slate-400 text-sm font-semibold">Calculating Optimal Route...</div>
            </div>
          </div>
        ) : (
          <div className="max-w-2xl mx-auto w-full">
            <div className="relative p-8 rounded-3xl overflow-hidden"
              style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}>
              
              {/* Background gradient */}
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-teal-500 to-emerald-500" />

              {/* Destination */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex justify-between items-center mb-8">
                <div>
                  <div className="text-xs uppercase font-bold tracking-widest text-slate-500 mb-1">Destination</div>
                  <div className="text-2xl font-black text-white">{goalName}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs uppercase font-bold tracking-widest text-slate-500 mb-1">ETA</div>
                  <div className="text-2xl font-black text-blue-400">{goalYear}</div>
                </div>
              </motion.div>

              <div className="h-px w-full bg-white/5 mb-8" />

              {/* Current Route & Obstacle */}
              <AnimatePresence mode="wait">
                {recalculating ? (
                  <motion.div
                    key="recalc"
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="py-12 flex flex-col items-center justify-center"
                  >
                    <div className="w-8 h-8 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin mb-4" />
                    <div className="text-emerald-400 font-bold uppercase tracking-widest">Rerouting...</div>
                  </motion.div>
                ) : routeAccepted ? (
                  <motion.div
                    key="accepted"
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    className="py-8"
                  >
                    <div className="flex items-center gap-4 mb-6">
                      <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 text-xl border border-emerald-500/30">
                        ✓
                      </div>
                      <div>
                        <div className="text-emerald-400 font-bold text-lg mb-1">New Route Locked In</div>
                        <div className="text-slate-400 text-sm">Path updated to Smart Balance strategy.</div>
                      </div>
                    </div>
                    
                    <div className="bg-white/5 rounded-xl p-4 flex justify-between items-center">
                      <div>
                        <div className="text-xs text-slate-500 uppercase font-bold mb-1">Updated ETA</div>
                        <div className="text-emerald-400 font-bold text-2xl">{(altProb * 100).toFixed(0)}% <span className="text-sm font-normal text-slate-400">Success</span></div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-slate-500 uppercase font-bold mb-1">Action Required</div>
                        <div className="text-white font-bold">Increase SIP by INR {altSipDelta.toLocaleString("en-IN")}</div>
                      </div>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div key="current" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    <div className="flex gap-6 relative">
                      {/* Route Line */}
                      <div className="w-4 flex flex-col items-center">
                        <div className="w-4 h-4 rounded-full bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.6)]" />
                        <div className="w-1 flex-1 bg-gradient-to-b from-blue-500 to-red-500 my-1" />
                        <div className="w-4 h-4 rounded-full bg-red-500 animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.6)]" />
                      </div>

                      <div className="flex-1 space-y-8 pb-4">
                        {/* Current Status */}
                        <div>
                          <div className="text-sm font-bold text-blue-400 mb-1">Current Route</div>
                          <div className="text-2xl font-black text-white mb-2">{(currentProb * 100).toFixed(0)}% <span className="text-sm font-normal text-slate-400">Success Prob</span></div>
                        </div>

                        {/* Obstacle Alert */}
                        <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-5 relative overflow-hidden">
                          <div className="absolute top-0 left-0 w-1 h-full bg-red-500" />
                          <div className="flex items-start gap-3">
                            <span className="text-2xl">⚠️</span>
                            <div>
                              <div className="text-red-400 font-bold mb-1">Obstacle Ahead: {obstacle.label}</div>
                              <div className="text-slate-300 text-sm">{obstacle.description}</div>
                              <div className="mt-2 text-xs font-bold text-red-500">Reduces success by {Math.abs(obstacle.impact_pct).toFixed(1)}%</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="h-px w-full bg-white/5 my-8" />

                    {/* Alternative Route Suggestion */}
                    <div className="bg-teal-500/10 border border-teal-500/20 rounded-2xl p-5">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-full bg-teal-500/20 flex items-center justify-center text-teal-400 text-xs">⑂</div>
                          <div className="text-teal-400 font-bold">Alternative Route Found</div>
                        </div>
                        <div className="text-right">
                          <div className="text-emerald-400 font-bold text-xl">{(altProb * 100).toFixed(0)}%</div>
                          <div className="text-[10px] uppercase font-bold text-slate-500">New ETA</div>
                        </div>
                      </div>
                      
                      <div className="text-slate-300 text-sm mb-5">
                        <span className="font-semibold text-white">Smart Balance:</span> Increase your monthly SIP by <span className="text-emerald-400 font-bold">INR {altSipDelta.toLocaleString("en-IN")}</span> to bypass the obstacle.
                      </div>

                      <button
                        onClick={handleAcceptRoute}
                        className="w-full py-3 rounded-xl font-bold text-white transition-all transform hover:scale-[1.02] active:scale-95"
                        style={{ background: "linear-gradient(135deg,#14b8a6,#f97316)", boxShadow: "0 10px 25px -5px rgba(99,102,241,0.4)" }}
                      >
                        Accept New Route
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
