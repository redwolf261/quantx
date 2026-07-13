"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import AppLayout from "@/components/layout/AppLayout";
import { profileApi, getApiError } from "@/lib/api";
import { useAuth, useStore } from "@/lib/store";
import type { ProfileCreate } from "@/types";

const STEPS = ["Personal", "Income", "Assets", "Goals & Risk"];

const DEFAULT_FORM: ProfileCreate = {
  age: 30,
  occupation: "",
  city: "",
  city_tier: 1,
  monthly_income: 80000,
  salary_growth_rate: 0.08,
  monthly_expenses: 40000,
  inflation_rate: 0.06,
  total_savings: 500000,
  total_investments: 1000000,
  equity_allocation: 0.60,
  debt_allocation: 0.40,
  total_loans: 0,
  monthly_emi: 0,
  risk_profile: "moderate",
};

export default function ProfilePage() {
  const { user } = useAuth();
  const { profile, setProfile } = useStore();
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<ProfileCreate>(profile || DEFAULT_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const update = (key: keyof ProfileCreate, value: unknown) => {
    setForm(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    try {
      const result = profile
        ? await profileApi.update(form)
        : await profileApi.create(form);
      setProfile(result);
      setSuccess(true);
      setTimeout(() => router.push("/dashboard"), 1500);
    } catch (e) {
      setError(getApiError(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <div className="p-6 max-w-2xl mx-auto space-y-6 bg-mesh min-h-screen">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold text-white">◉ Financial Profile</h1>
          <p className="text-slate-400 text-sm">Your Digital Twin configuration — used for all simulations</p>
        </motion.div>

        {/* Step indicator */}
        <div className="flex items-center gap-2">
          {STEPS.map((s, i) => (
            <div key={s} className="flex items-center gap-2 flex-1">
              <button
                onClick={() => setStep(i)}
                className="flex items-center gap-2"
              >
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                    i <= step
                      ? "text-white"
                      : "text-slate-500"
                  }`}
                  style={{
                    background: i <= step
                      ? "linear-gradient(135deg, #0f766e, #f97316)"
                      : "rgba(255,255,255,0.08)",
                  }}
                >
                  {i < step ? "✓" : i + 1}
                </div>
                <span className={`text-xs font-medium hidden sm:block ${
                  i === step ? "text-white" : "text-slate-500"
                }`}>
                  {s}
                </span>
              </button>
              {i < STEPS.length - 1 && (
                <div className="flex-1 h-0.5 mx-1" style={{
                  background: i < step ? "rgba(139,92,246,0.5)" : "rgba(255,255,255,0.06)"
                }} />
              )}
            </div>
          ))}
        </div>

        {/* Form steps */}
        <motion.div
          key={step}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass-card p-6 space-y-5"
        >
          {step === 0 && (
            <>
              <h3 className="text-white font-semibold">Personal Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="form-label">Age</label>
                  <input type="number" className="form-input" min={18} max={100}
                    value={form.age} onChange={e => update("age", Number(e.target.value))} />
                </div>
                <div>
                  <label className="form-label">City Tier</label>
                  <select className="form-select" value={form.city_tier}
                    onChange={e => update("city_tier", Number(e.target.value))}>
                    <option value={1}>Metro (Tier 1)</option>
                    <option value={2}>Tier 2 City</option>
                    <option value={3}>Tier 3 City</option>
                  </select>
                </div>
                <div>
                  <label className="form-label">Occupation</label>
                  <input type="text" className="form-input" placeholder="Software Engineer"
                    value={form.occupation} onChange={e => update("occupation", e.target.value)} />
                </div>
                <div>
                  <label className="form-label">City</label>
                  <input type="text" className="form-input" placeholder="Mumbai"
                    value={form.city} onChange={e => update("city", e.target.value)} />
                </div>
              </div>
            </>
          )}

          {step === 1 && (
            <>
              <h3 className="text-white font-semibold">Income & Expenses</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="form-label">Monthly Income (₹)</label>
                  <input type="number" className="form-input"
                    value={form.monthly_income} onChange={e => update("monthly_income", Number(e.target.value))} />
                </div>
                <div>
                  <label className="form-label">Monthly Expenses (₹)</label>
                  <input type="number" className="form-input"
                    value={form.monthly_expenses} onChange={e => update("monthly_expenses", Number(e.target.value))} />
                </div>
                <div>
                  <label className="form-label">Salary Growth Rate (%)</label>
                  <input type="number" className="form-input" step={0.5} min={0} max={30}
                    value={(form.salary_growth_rate * 100).toFixed(1)}
                    onChange={e => update("salary_growth_rate", Number(e.target.value) / 100)} />
                </div>
                <div>
                  <label className="form-label">Inflation Rate (%)</label>
                  <input type="number" className="form-input" step={0.5} min={0} max={20}
                    value={(form.inflation_rate * 100).toFixed(1)}
                    onChange={e => update("inflation_rate", Number(e.target.value) / 100)} />
                </div>
                <div>
                  <label className="form-label">Monthly EMI (₹)</label>
                  <input type="number" className="form-input"
                    value={form.monthly_emi} onChange={e => update("monthly_emi", Number(e.target.value))} />
                </div>
                <div>
                  <label className="form-label">Total Loans (₹)</label>
                  <input type="number" className="form-input"
                    value={form.total_loans} onChange={e => update("total_loans", Number(e.target.value))} />
                </div>
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <h3 className="text-white font-semibold">Assets & Investments</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="form-label">Total Savings (₹)</label>
                  <input type="number" className="form-input"
                    value={form.total_savings} onChange={e => update("total_savings", Number(e.target.value))} />
                </div>
                <div>
                  <label className="form-label">Total Investments (₹)</label>
                  <input type="number" className="form-input"
                    value={form.total_investments} onChange={e => update("total_investments", Number(e.target.value))} />
                </div>
                <div>
                  <label className="form-label">Equity Allocation (%)</label>
                  <input type="number" className="form-input" step={5} min={0} max={100}
                    value={(form.equity_allocation * 100).toFixed(0)}
                    onChange={e => {
                      const eq = Number(e.target.value) / 100;
                      update("equity_allocation", eq);
                      update("debt_allocation", 1 - eq);
                    }} />
                </div>
                <div>
                  <label className="form-label">Debt Allocation (%)</label>
                  <input type="number" className="form-input" readOnly
                    value={(form.debt_allocation * 100).toFixed(0)} />
                </div>
              </div>
              <div className="h-3 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                <motion.div
                  className="h-full rounded-full"
                  style={{
                    width: `${form.equity_allocation * 100}%`,
                    background: "linear-gradient(90deg, #f97316, #10b981)",
                  }}
                  animate={{ width: `${form.equity_allocation * 100}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
              <div className="flex justify-between text-xs text-slate-500">
                <span>🟣 Equity {(form.equity_allocation * 100).toFixed(0)}%</span>
                <span>🟢 Debt {(form.debt_allocation * 100).toFixed(0)}%</span>
              </div>
            </>
          )}

          {step === 3 && (
            <>
              <h3 className="text-white font-semibold">Risk Profile</h3>
              <div className="grid grid-cols-3 gap-3">
                {(["conservative", "moderate", "aggressive"] as const).map((r) => (
                  <button
                    key={r}
                    onClick={() => update("risk_profile", r)}
                    className={`p-4 rounded-xl text-sm font-semibold transition-all capitalize border ${
                      form.risk_profile === r
                        ? "text-white"
                        : "text-slate-400"
                    }`}
                    style={{
                      background: form.risk_profile === r
                        ? r === "conservative"
                          ? "rgba(16,185,129,0.15)"
                          : r === "moderate"
                          ? "rgba(139,92,246,0.15)"
                          : "rgba(239,68,68,0.15)"
                        : "rgba(255,255,255,0.04)",
                      borderColor: form.risk_profile === r
                        ? r === "conservative"
                          ? "rgba(16,185,129,0.3)"
                          : r === "moderate"
                          ? "rgba(139,92,246,0.3)"
                          : "rgba(239,68,68,0.3)"
                        : "rgba(255,255,255,0.06)",
                    }}
                  >
                    {r === "conservative" ? "🛡️" : r === "moderate" ? "⚖️" : "🚀"}
                    <p className="mt-2">{r}</p>
                    <p className="text-xs font-normal mt-1 text-slate-400">
                      {r === "conservative" ? "Capital preservation" : r === "moderate" ? "Balanced growth" : "High growth"}
                    </p>
                  </button>
                ))}
              </div>

              {/* Summary preview */}
              <div className="glass-card p-4 mt-4 space-y-2 text-sm">
                <h4 className="text-white font-medium mb-2">Profile Summary</h4>
                {[
                  ["Monthly Income", `₹${form.monthly_income.toLocaleString("en-IN")}`],
                  ["Monthly Expenses", `₹${form.monthly_expenses.toLocaleString("en-IN")}`],
                  ["Net Worth", `₹${(form.total_savings + form.total_investments - form.total_loans).toLocaleString("en-IN")}`],
                  ["Risk Profile", form.risk_profile.toUpperCase()],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <span className="text-slate-400">{k}</span>
                    <span className="font-mono text-white">{v}</span>
                  </div>
                ))}
              </div>
            </>
          )}

          {error && (
            <div className="px-4 py-3 rounded-xl text-sm text-red-400 border border-red-500/20"
              style={{ background: "rgba(239,68,68,0.08)" }}>
              {error}
            </div>
          )}

          {success && (
            <div className="px-4 py-3 rounded-xl text-sm text-emerald-400 border border-emerald-500/20"
              style={{ background: "rgba(16,185,129,0.08)" }}>
              ✅ Profile saved! Redirecting to dashboard...
            </div>
          )}
        </motion.div>

        {/* Navigation */}
        <div className="flex gap-3 justify-between">
          <button
            onClick={() => setStep(s => Math.max(0, s - 1))}
            disabled={step === 0}
            className="btn-secondary"
          >
            ← Back
          </button>
          {step < STEPS.length - 1 ? (
            <button onClick={() => setStep(s => s + 1)} className="btn-primary">
              Next →
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="btn-success"
            >
              {loading ? "Saving..." : profile ? "Update Profile" : "Create Profile ✓"}
            </button>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
