"use client";
import { useState, useEffect } from "react";
import AppLayout from "@/components/layout/AppLayout";
import { twinApi, getApiError } from "@/lib/api";
import { TimelineEvent, TimelineResult } from "@/types";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/store";

export default function TimelinePage() {
  const { user } = useAuth();
  const [timeline, setTimeline] = useState<TimelineResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user?.id) return;
    setLoading(true);
    twinApi.getTimeline()
      .then(setTimeline)
      .catch(e => setError(getApiError(e)))
      .finally(() => setLoading(false));
  }, [user]);

  return (
    <AppLayout>
      <div className="p-6 min-h-screen" style={{ background: "rgba(7,13,26,0.98)" }}>
        <div className="max-w-4xl mx-auto">
          
          {/* Header */}
          <div className="mb-10 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl mb-4 text-2xl"
              style={{ background: "linear-gradient(135deg,#6d28d9,#10b981)" }}>⏳</div>
            <h1 className="text-2xl font-black text-white mb-2">Financial Timeline</h1>
            <p className="text-sm text-slate-400">Your projected financial life milestones, year by year.</p>
          </div>

          {error && (
            <div className="rounded-xl p-3 mb-6 text-xs text-red-400"
              style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)" }}>
              {error}
            </div>
          )}

          {loading ? (
            <div className="space-y-6">
              {[0, 1, 2, 3].map(i => (
                <div key={i} className="animate-pulse flex gap-6">
                  <div className="w-16 flex-shrink-0 text-right">
                    <div className="h-4 bg-white/10 rounded w-10 ml-auto" />
                  </div>
                  <div className="flex-1">
                    <div className="h-20 bg-white/10 rounded-2xl" />
                  </div>
                </div>
              ))}
            </div>
          ) : timeline?.events?.length ? (
            <div className="relative">
              {/* Vertical line */}
              <div className="absolute top-0 bottom-0 left-[4.5rem] w-px"
                style={{ background: "linear-gradient(to bottom, #7c3aed, rgba(255,255,255,0.06))" }} />
              
              <div className="space-y-8">
                {timeline.events.map((event, i) => {
                  const isPast = event.year <= timeline.current_year;
                  const isCurrent = event.year === timeline.current_year;
                  return (
                    <motion.div
                      key={`${event.year}-${event.title}-${i}`}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="flex gap-6 relative"
                    >
                      {/* Year column */}
                      <div className="w-16 flex-shrink-0 text-right pt-4">
                        <span className={`text-lg font-black ${isPast ? "text-violet-400" : "text-slate-500"}`}>
                          {event.year}
                        </span>
                        {isCurrent && <div className="text-[10px] uppercase font-bold text-emerald-400 mt-1">This Year</div>}
                      </div>

                      {/* Node */}
                      <div className="absolute left-[4.5rem] -translate-x-1/2 top-5 w-4 h-4 rounded-full border-4 border-[#070d1a]"
                        style={{ background: isPast ? "#10b981" : "#6d28d9" }} />

                      {/* Content Card */}
                      <div className="flex-1">
                        <div className="rounded-2xl p-5 transition-all"
                          style={{
                            background: "rgba(255,255,255,0.03)",
                            border: `1px solid ${isPast ? "rgba(16,185,129,0.3)" : "rgba(255,255,255,0.06)"}`,
                          }}>
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3 mb-2">
                              <span className="text-2xl">{event.icon}</span>
                              <div>
                                <h3 className="text-base font-bold text-white">{event.title}</h3>
                                {event.achieved && (
                                  <span className="inline-flex items-center gap-1 text-[10px] uppercase font-bold text-emerald-400 mt-0.5">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                                      <polyline points="20 6 9 17 4 12" />
                                    </svg>
                                    Achieved
                                  </span>
                                )}
                              </div>
                            </div>
                            {event.probability !== null && (
                              <div className="text-right">
                                <div className="text-xl font-black"
                                  style={{ color: event.probability >= 0.8 ? "#10b981" : event.probability >= 0.6 ? "#f59e0b" : "#ef4444" }}>
                                  {(event.probability * 100).toFixed(0)}%
                                </div>
                                <div className="text-[10px] text-slate-500 font-semibold uppercase">Prob</div>
                              </div>
                            )}
                          </div>
                          
                          <p className="text-sm text-slate-400 mt-2">{event.description}</p>
                          
                          {event.amount && (
                            <div className="mt-4 inline-block px-3 py-1.5 rounded-lg text-xs font-semibold"
                              style={{ background: "rgba(255,255,255,0.06)", color: "#94a3b8" }}>
                              Target: INR {(event.amount).toLocaleString("en-IN")}
                            </div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500">
              No milestones found. Set up your profile and goals to generate your timeline.
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
