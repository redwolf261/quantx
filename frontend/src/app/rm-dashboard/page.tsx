"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import AppLayout from "@/components/layout/AppLayout";
import { dashboardApi, getApiError } from "@/lib/api";
import { useAuth } from "@/lib/store";
import { formatINR, formatPct, riskLevelClass, healthScoreColor } from "@/lib/utils";
import type { CustomerSummary } from "@/types";

export default function RMDashboardPage() {
  const { user } = useAuth();
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filterRisk, setFilterRisk] = useState<string>("all");

  useEffect(() => {
    dashboardApi.getRmCustomers()
      .then(setCustomers)
      .catch(e => setError(getApiError(e)))
      .finally(() => setLoading(false));
  }, []);

  const filtered = customers.filter(c => {
    const matchSearch = c.user.full_name.toLowerCase().includes(search.toLowerCase()) ||
      c.user.email.toLowerCase().includes(search.toLowerCase());
    const matchRisk = filterRisk === "all" || c.risk_level === filterRisk;
    return matchSearch && matchRisk;
  });

  const stats = {
    total: customers.length,
    atRisk: customers.filter(c => c.risk_level === "high" || c.risk_level === "critical").length,
    highHealth: customers.filter(c => c.health_score >= 70).length,
    avgProbability: customers.reduce((s, c) => s + c.avg_success_probability, 0) / (customers.length || 1),
  };

  return (
    <AppLayout>
      <div className="p-6 space-y-6 bg-mesh min-h-screen">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold text-white">📋 Relationship Manager Dashboard</h1>
          <p className="text-slate-400 text-sm">Customer portfolio overview and discussion intelligence</p>
        </motion.div>

        {/* Stats row */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Total Customers", value: stats.total, icon: "👥", color: "text-violet-400" },
            { label: "At Risk", value: stats.atRisk, icon: "⚠️", color: "text-red-400" },
            { label: "Healthy Portfolios", value: stats.highHealth, icon: "✅", color: "text-emerald-400" },
            { label: "Avg Success Prob.", value: formatPct(stats.avgProbability), icon: "📊", color: "text-amber-400" },
          ].map((s) => (
            <div key={s.label} className="stat-card">
              <div className="flex items-center gap-2">
                <span>{s.icon}</span>
                <p className="stat-label">{s.label}</p>
              </div>
              <p className={`stat-value mt-1 ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="flex gap-3">
          <input
            type="text"
            placeholder="Search customers..."
            className="form-input max-w-xs"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <div className="tab-group">
            {["all", "low", "medium", "high", "critical"].map(r => (
              <button
                key={r}
                onClick={() => setFilterRisk(r)}
                className={`tab-item capitalize text-xs ${filterRisk === r ? "active" : ""}`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        {loading && (
          <div className="grid grid-cols-1 gap-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="shimmer h-28 rounded-2xl" />
            ))}
          </div>
        )}

        {error && (
          <div className="px-4 py-3 rounded-xl text-sm text-red-400 border border-red-500/20"
            style={{ background: "rgba(239,68,68,0.08)" }}>
            {error}
          </div>
        )}

        {/* Customer table */}
        {!loading && (
          <div className="space-y-3">
            {filtered.length === 0 ? (
              <div className="glass-card p-8 text-center">
                <p className="text-slate-400">No customers found</p>
              </div>
            ) : (
              filtered.map((customer, idx) => (
                <motion.div
                  key={customer.user.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.04 }}
                  className="glass-card p-5"
                >
                  <div className="flex items-start gap-4">
                    {/* Avatar */}
                    <div className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
                      style={{ background: "linear-gradient(135deg, #7c3aed, #10b981)" }}>
                      {customer.user.full_name[0]}
                    </div>

                    {/* Info */}
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <p className="text-white font-semibold">{customer.user.full_name}</p>
                          <p className="text-slate-500 text-xs">{customer.user.email}</p>
                          {customer.profile && (
                            <p className="text-slate-500 text-xs mt-0.5">
                              {customer.profile.occupation} · {customer.profile.city}
                            </p>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={riskLevelClass(customer.risk_level)}>
                            {customer.risk_level.toUpperCase()} RISK
                          </span>
                        </div>
                      </div>

                      {/* Metrics */}
                      <div className="grid grid-cols-4 gap-4 mb-3">
                        <div>
                          <p className="text-slate-500 text-xs">Net Worth</p>
                          <p className="font-mono text-sm text-white font-medium">{formatINR(customer.net_worth, true)}</p>
                        </div>
                        <div>
                          <p className="text-slate-500 text-xs">Health Score</p>
                          <p className={`font-mono text-sm font-semibold ${healthScoreColor(customer.health_score)}`}>
                            {customer.health_score.toFixed(0)}/100
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-500 text-xs">Avg Success</p>
                          <p className={`font-mono text-sm font-semibold ${customer.avg_success_probability >= 0.7 ? "text-emerald-400" : "text-amber-400"}`}>
                            {formatPct(customer.avg_success_probability)}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-500 text-xs">Goals</p>
                          <p className="font-mono text-sm text-white">{customer.goals_count}</p>
                        </div>
                      </div>

                      {/* Discussion points */}
                      {customer.discussion_points.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          <span className="text-xs text-slate-500 mr-1">💬 Discuss:</span>
                          {customer.discussion_points.map((point, i) => (
                            <span
                              key={i}
                              className="badge-muted text-xs px-2 py-1 rounded-full"
                            >
                              {point}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
