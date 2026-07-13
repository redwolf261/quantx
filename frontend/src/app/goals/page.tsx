"use client";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import AppLayout from "@/components/layout/AppLayout";
import { goalsApi, getApiError } from "@/lib/api";
import { useAuth, useGoals } from "@/lib/store";
import { formatINR, yearsUntil, probabilityColor } from "@/lib/utils";
import type { GoalCreate, Goal } from "@/types";
import GoalCard from "@/components/goals/GoalCard";

const GOAL_ICONS: Record<string, string> = {
  retirement: "🏖️",
  home_purchase: "🏠",
  education: "🎓",
  emergency_fund: "🛡️",
  other: "🎯",
};

const DEFAULT_GOAL: GoalCreate = {
  goal_name: "",
  goal_type: "retirement",
  target_amount: 10000000,
  target_year: new Date().getFullYear() + 25,
  priority: 1,
  importance_score: 8.0,
  notes: "",
};

export default function GoalsPage() {
  const { user } = useAuth();
  const { goals, setGoals, addGoal, removeGoal } = useGoals();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<GoalCreate>(DEFAULT_GOAL);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user?.id) return;
    goalsApi.list(user.id).then(setGoals).catch(() => {});
  }, [user?.id]);

  const update = (key: keyof GoalCreate, value: unknown) => {
    setForm(prev => ({ ...prev, [key]: value }));
  };

  const handleCreate = async () => {
    setLoading(true);
    setError("");
    try {
      const goal = await goalsApi.create(form);
      addGoal(goal);
      setShowForm(false);
      setForm(DEFAULT_GOAL);
    } catch (e) {
      setError(getApiError(e));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (goalId: string) => {
    try {
      await goalsApi.delete(goalId);
      removeGoal(goalId);
    } catch (e) {
      console.error(getApiError(e));
    }
  };

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
            <h1 className="text-2xl font-bold text-white">🎯 Goal Planner</h1>
            <p className="text-slate-400 text-sm">Set and track your financial goals</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="btn-primary"
          >
            {showForm ? "✕ Cancel" : "+ Add Goal"}
          </button>
        </motion.div>

        {/* Add Goal Form */}
        {showForm && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6"
          >
            <h3 className="text-white font-semibold mb-4">New Goal</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Goal Name</label>
                <input type="text" className="form-input" placeholder="My Retirement Goal"
                  value={form.goal_name} onChange={e => update("goal_name", e.target.value)} />
              </div>
              <div>
                <label className="form-label">Goal Type</label>
                <select className="form-select" value={form.goal_type}
                  onChange={e => update("goal_type", e.target.value)}>
                  {Object.entries(GOAL_ICONS).map(([k, v]) => (
                    <option key={k} value={k}>{v} {k.replace("_", " ")}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="form-label">Target Amount (₹)</label>
                <input type="number" className="form-input"
                  value={form.target_amount} onChange={e => update("target_amount", Number(e.target.value))} />
              </div>
              <div>
                <label className="form-label">Target Year</label>
                <input type="number" className="form-input" min={new Date().getFullYear() + 1} max={2100}
                  value={form.target_year} onChange={e => update("target_year", Number(e.target.value))} />
              </div>
              <div>
                <label className="form-label">Priority (1=highest, 5=lowest)</label>
                <select className="form-select" value={form.priority}
                  onChange={e => update("priority", Number(e.target.value))}>
                  {[1,2,3,4,5].map(p => <option key={p} value={p}>Priority {p}</option>)}
                </select>
              </div>
              <div>
                <label className="form-label">Importance Score (1-10)</label>
                <input type="number" className="form-input" min={1} max={10} step={0.5}
                  value={form.importance_score} onChange={e => update("importance_score", Number(e.target.value))} />
              </div>
            </div>

            <div className="mt-4">
              <label className="form-label">Notes (optional)</label>
              <textarea className="form-input resize-none" rows={2} placeholder="Additional context..."
                value={form.notes ?? ""} onChange={e => update("notes", e.target.value)} />
            </div>

            {/* Quick preview */}
            {form.target_amount > 0 && form.target_year > new Date().getFullYear() && (
              <div className="mt-4 px-4 py-3 rounded-xl text-sm"
                style={{ background: "rgba(139,92,246,0.08)", border: "1px solid rgba(139,92,246,0.2)" }}>
                <span className="text-teal-400 font-semibold">Quick Estimate: </span>
                <span className="text-slate-300">
                  {yearsUntil(form.target_year)} years to reach {formatINR(form.target_amount, true)}.
                  Estimated SIP at 10% return: ₹{Math.round(
                    form.target_amount * (0.10/12) / ((1 + 0.10/12)**(yearsUntil(form.target_year)*12) - 1)
                  ).toLocaleString("en-IN")}/month
                </span>
              </div>
            )}

            {error && (
              <div className="mt-3 px-4 py-3 rounded-xl text-sm text-red-400 border border-red-500/20"
                style={{ background: "rgba(239,68,68,0.08)" }}>
                {error}
              </div>
            )}

            <div className="flex gap-3 mt-4">
              <button onClick={handleCreate} disabled={loading} className="btn-success">
                {loading ? "Creating..." : "✓ Create Goal"}
              </button>
              <button onClick={() => setShowForm(false)} className="btn-secondary">
                Cancel
              </button>
            </div>
          </motion.div>
        )}

        {/* Goals list */}
        {goals.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <p className="text-5xl mb-4">🎯</p>
            <h3 className="text-white font-semibold text-lg mb-2">No goals yet</h3>
            <p className="text-slate-400 mb-6 max-w-sm mx-auto">
              Define your financial goals and FutureLens will simulate your probability of achieving each one.
            </p>
            <button onClick={() => setShowForm(true)} className="btn-primary">
              Create Your First Goal
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {goals.map((goal) => (
                <div key={goal.id} className="relative group">
                  <GoalCard goal={goal} />
                  <button
                    onClick={() => handleDelete(goal.id)}
                    className="absolute top-3 right-3 w-6 h-6 rounded-full flex items-center justify-center text-slate-600 hover:text-red-400 hover:bg-red-400/10 transition-all opacity-0 group-hover:opacity-100"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
