"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import AppLayout from "@/components/layout/AppLayout";
import NetWorthChart from "@/components/charts/NetWorthChart";
import GoalCard from "@/components/goals/GoalCard";
import HealthScoreRing from "@/components/dashboard/HealthScoreRing";
import { dashboardApi, getApiError } from "@/lib/api";
import { useAuth, useStore } from "@/lib/store";
import { formatINR, formatPct, probabilityColor } from "@/lib/utils";
import type { DashboardData } from "@/types";
import Link from "next/link";

export default function DashboardPage() {
  const { user } = useAuth();
  const { setDashboard } = useStore();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user?.id) return;
    dashboardApi
      .get(user.id)
      .then((d) => {
        setData(d);
        setDashboard(d);
      })
      .catch((e) => setError(getApiError(e)))
      .finally(() => setLoading(false));
  }, [user?.id]);

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
            <h1 className="text-2xl font-bold text-white">
              {loading ? "Loading..." : `Welcome back, ${data?.user.full_name?.split(" ")[0] || "there"}!`}
            </h1>
            <p className="text-slate-400 text-sm mt-0.5">
              Here&apos;s your financial picture for today
            </p>
          </div>
          <Link href="/playground">
            <button className="btn-primary text-sm">
              ⚡ Run Simulation
            </button>
          </Link>
        </motion.div>

        {loading && <DashboardSkeleton />}
        {error && (
          <div className="glass-card p-8 text-center">
            <p className="text-red-400 mb-2">Failed to load dashboard</p>
            <p className="text-slate-500 text-sm">{error}</p>
            {!data?.profile && (
              <Link href="/profile">
                <button className="btn-primary mt-4">
                  Complete Your Profile First
                </button>
              </Link>
            )}
          </div>
        )}

        {data && !loading && (
          <>
            {/* KPI Row */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <KpiCard
                label="Net Worth"
                value={formatINR(data.net_worth, true)}
                icon="💰"
                color="violet"
              />
              <KpiCard
                label="Monthly Surplus"
                value={formatINR(data.monthly_surplus, true)}
                icon="📈"
                color={data.monthly_surplus > 0 ? "emerald" : "crimson"}
              />
              <KpiCard
                label="Goals On Track"
                value={`${data.goals_summary.on_track} / ${data.goals_summary.total}`}
                icon="🎯"
                color="gold"
              />
              <KpiCard
                label="Avg Success Prob."
                value={formatPct(data.goals_summary.avg_success_probability)}
                icon="📊"
                color={data.goals_summary.avg_success_probability >= 0.7 ? "emerald" : "crimson"}
              />
            </div>

            {/* Main grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Health Score */}
              <div className="glass-card p-6 flex flex-col items-center justify-center gap-4">
                <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">
                  Financial Health Score
                </h3>
                <HealthScoreRing score={data.health_score} />
                <div className="text-center">
                  <p className="text-xs text-slate-500 max-w-[200px] text-center">
                    Based on savings rate, debt ratio, emergency fund, and investment health
                  </p>
                </div>
                <Link href="/profile" className="btn-secondary text-xs py-2 px-4">
                  Update Profile
                </Link>
              </div>

              {/* Net Worth Projection */}
              <div className="lg:col-span-2 glass-card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-white font-semibold">Wealth Projection</h3>
                  <span className="badge-violet text-xs">Monte Carlo P50</span>
                </div>
                {data.latest_simulation?.percentile_bands ? (
                  <NetWorthChart bands={data.latest_simulation.percentile_bands} />
                ) : (
                  <div className="h-48 flex flex-col items-center justify-center gap-3">
                    <p className="text-slate-500 text-sm">No simulation data yet</p>
                    <Link href="/playground">
                      <button className="btn-primary text-xs py-2">Run Your First Simulation</button>
                    </Link>
                  </div>
                )}
              </div>
            </div>

            {/* Goals */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-white font-semibold text-lg">Your Goals</h2>
                <Link href="/goals">
                  <button className="btn-secondary text-xs py-2">+ Add Goal</button>
                </Link>
              </div>
              {data.goals.length === 0 ? (
                <div className="glass-card p-8 text-center">
                  <p className="text-4xl mb-3">🎯</p>
                  <h3 className="text-white font-semibold mb-1">No goals yet</h3>
                  <p className="text-slate-400 text-sm mb-4">
                    Set your financial goals to see success probability and SIP recommendations
                  </p>
                  <Link href="/goals">
                    <button className="btn-primary text-sm">Create Your First Goal</button>
                  </Link>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {data.goals.map((goal) => (
                    <GoalCard key={goal.id} goal={goal} />
                  ))}
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { href: "/playground", icon: "⚡", label: "Decision Playground", desc: "Adjust SIP & see impact" },
                { href: "/futures", icon: "⑂", label: "Future Forks", desc: "Compare scenarios" },
                { href: "/advisor", icon: "🤖", label: "AI Advisor", desc: "Get AI insights" },
                { href: "/goals", icon: "🎯", label: "Manage Goals", desc: "Update targets" },
              ].map((action) => (
                <Link key={action.href} href={action.href}>
                  <motion.div
                    whileHover={{ scale: 1.02, y: -2 }}
                    className="glass-card p-4 cursor-pointer text-center"
                  >
                    <p className="text-2xl mb-2">{action.icon}</p>
                    <p className="text-white text-xs font-semibold">{action.label}</p>
                    <p className="text-slate-500 text-xs mt-0.5">{action.desc}</p>
                  </motion.div>
                </Link>
              ))}
            </div>
          </>
        )}
      </div>
    </AppLayout>
  );
}

function KpiCard({ label, value, icon, color }: { label: string; value: string; icon: string; color: string }) {
  const colorMap: Record<string, string> = {
    violet: "rgba(139,92,246,0.15)",
    emerald: "rgba(16,185,129,0.15)",
    crimson: "rgba(239,68,68,0.15)",
    gold: "rgba(245,158,11,0.15)",
  };
  const textMap: Record<string, string> = {
    violet: "text-violet-400",
    emerald: "text-emerald-400",
    crimson: "text-red-400",
    gold: "text-amber-400",
  };
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="stat-card"
      style={{ background: colorMap[color] || "rgba(255,255,255,0.04)" }}
    >
      <div className="flex items-center gap-2">
        <span className="text-xl">{icon}</span>
        <p className="stat-label">{label}</p>
      </div>
      <p className={`stat-value mt-1 ${textMap[color]}`}>{value}</p>
    </motion.div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="shimmer h-24 rounded-2xl" />
        ))}
      </div>
      <div className="grid grid-cols-3 gap-6">
        <div className="shimmer h-64 rounded-2xl" />
        <div className="col-span-2 shimmer h-64 rounded-2xl" />
      </div>
    </div>
  );
}
