"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/store";
import LoginForm from "@/components/auth/LoginForm";
import { motion } from "framer-motion";

export default function Home() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  return (
    <main className="min-h-screen bg-navy-950 bg-mesh flex">
      {/* Left: Branding */}
      <div className="hidden lg:flex flex-col justify-center px-16 flex-1 relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-teal-700/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-emerald-500/08 rounded-full blur-3xl" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="relative z-10 max-w-lg"
        >
          {/* Logo */}
          <div className="flex items-center gap-3 mb-10">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, #0f766e, #f97316)" }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v3m0 14v3M2 12h3m14 0h3M4.93 4.93l2.12 2.12m9.9 9.9 2.12 2.12M4.93 19.07l2.12-2.12m9.9-9.9 2.12-2.12" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">FutureLens</h1>
              <p className="text-xs text-slate-400 font-medium">AI Financial Intelligence</p>
            </div>
          </div>

          <h2 className="text-5xl font-bold text-white leading-tight mb-6">
            See Your
            <span className="block text-gradient-teal">Financial Future</span>
            Clearly
          </h2>

          <p className="text-lg text-slate-300 mb-10 leading-relaxed">
            FutureLens creates your <strong className="text-white">Financial Digital Twin</strong> and simulates
            10,000 possible futures using Monte Carlo analytics — helping you make better money decisions today.
          </p>

          {/* Feature cards */}
          <div className="space-y-3">
            {[
              { title: "Goal-Based Planning", desc: "Retirement, home, education — all in one view" },
              { title: "Monte Carlo Simulation", desc: "10,000 simulations → your success probability" },
              { title: "Stress Testing", desc: "Know how market crashes affect your goals" },
              { title: "AI Explanations", desc: "Plain-language insights from complex analytics" },
            ].map((f) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                className="flex items-center gap-3 glass-card px-4 py-3"
              >
                <div>
                  <p className="text-sm font-semibold text-white">{f.title}</p>
                  <p className="text-xs text-slate-400">{f.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>

        </motion.div>
      </div>

      {/* Right: Login Form */}
      <div className="flex-1 lg:max-w-md flex items-center justify-center p-8 relative">
        <div className="absolute inset-0 lg:border-l border-white/05" />
        <LoginForm />
      </div>
    </main>
  );
}
