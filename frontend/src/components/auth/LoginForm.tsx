"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { authApi, getApiError } from "@/lib/api";
import { useAuth } from "@/lib/store";

export default function LoginForm() {
  const router = useRouter();
  const { setAuth } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    role: "customer",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let result;
      if (mode === "login") {
        result = await authApi.login(form.email, form.password);
      } else {
        result = await authApi.register({
          email: form.email,
          password: form.password,
          full_name: form.full_name,
          role: form.role,
        });
      }

      // Persist token
      localStorage.setItem("fl_token", result.access_token);

      // Update store
      setAuth(result.access_token, {
        id: result.user_id,
        email: form.email,
        full_name: result.full_name,
        role: result.role as "customer" | "rm" | "admin",
        is_active: true,
        created_at: new Date().toISOString(),
      });

      // Redirect
      if (result.role === "rm" || result.role === "admin") {
        router.push("/rm-dashboard");
      } else {
        router.push("/dashboard");
      }
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-sm relative z-10"
    >
      {/* Mobile logo */}
      <div className="flex items-center gap-3 mb-8 lg:hidden">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: "linear-gradient(135deg, #0f766e, #f97316)" }}>
          <span className="text-white text-lg">🔭</span>
        </div>
        <div>
          <h1 className="text-xl font-bold text-white">FutureLens</h1>
          <p className="text-xs text-slate-400">AI Financial Intelligence</p>
        </div>
      </div>

      <div className="glass-card p-8">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white mb-1">
            {mode === "login" ? "Welcome back" : "Create account"}
          </h2>
          <p className="text-sm text-slate-400">
            {mode === "login"
              ? "Sign in to your financial dashboard"
              : "Start your wealth management journey"}
          </p>
        </div>

        {/* Tab switcher */}
        <div className="tab-group mb-6">
          <button
            onClick={() => setMode("login")}
            className={`tab-item flex-1 ${mode === "login" ? "active" : ""}`}
          >
            Sign In
          </button>
          <button
            onClick={() => setMode("register")}
            className={`tab-item flex-1 ${mode === "register" ? "active" : ""}`}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Full name (register only) */}
          {mode === "register" && (
            <div>
              <label className="form-label">Full Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="Arjun Sharma"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                required
              />
            </div>
          )}

          {/* Role (register only) */}
          {mode === "register" && (
            <div>
              <label className="form-label">Role</label>
              <select
                className="form-select"
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
              >
                <option value="customer">Customer</option>
                <option value="rm">Relationship Manager</option>
              </select>
            </div>
          )}

          <div>
            <label className="form-label">Email</label>
            <input
              type="email"
              className="form-input"
              placeholder="you@example.com"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
              minLength={8}
            />
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="px-4 py-3 rounded-xl text-sm text-red-400 border border-red-500/20"
              style={{ background: "rgba(239,68,68,0.08)" }}
            >
              {error}
            </motion.div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center"
            style={{ opacity: loading ? 0.7 : 1 }}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                {mode === "login" ? "Signing in..." : "Creating account..."}
              </span>
            ) : (
              mode === "login" ? "Sign In" : "Create Account"
            )}
          </button>
        </form>

        {/* Demo credentials hint */}
        {mode === "login" && (
          <div className="mt-4 px-3 py-2 rounded-lg text-xs text-slate-500 border border-white/05"
            style={{ background: "rgba(255,255,255,0.02)" }}>
            <strong className="text-slate-400">Demo:</strong> Use any synthetic customer email
            from the seeded data. Password: <code className="text-teal-400">FutureLens@2026</code>
          </div>
        )}
      </div>

      <p className="text-center text-xs text-slate-500 mt-4">
        IDBI Innovate 2026 · Digital Wealth Management Track
      </p>
    </motion.div>
  );
}
