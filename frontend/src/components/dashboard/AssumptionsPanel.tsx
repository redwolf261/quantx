"use client";
import { motion } from "framer-motion";

export default function AssumptionsPanel() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6 mt-6 border border-teal-500/20"
      style={{ background: "rgba(139, 92, 246, 0.05)" }}
    >
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">🔍</span>
        <h3 className="text-white font-semibold text-lg">Financial Assumptions</h3>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <AssumptionItem label="Expected Equity Return" value="12.0% p.a." />
        <AssumptionItem label="Expected Debt Return" value="7.0% p.a." />
        <AssumptionItem label="Inflation Rate" value="6.0% p.a." />
        <AssumptionItem label="Salary Growth" value="8.0% p.a." />
        
        <AssumptionItem label="Tax Model" value="New Regime (Appx 30%)" />
        <AssumptionItem label="Simulation Engine" value="Vectorized Monte Carlo" />
        <AssumptionItem label="Simulation Count" value="10,000 Paths" />
        <AssumptionItem label="Data Source" value="Synthetic Profiles" />
      </div>

      <p className="text-xs text-slate-500 mt-4 text-center">
        * Assumptions are static for the MVP demonstration purposes to ensure consistent evaluation.
      </p>
    </motion.div>
  );
}

function AssumptionItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white/5 p-3 rounded-xl border border-white/5">
      <p className="text-xs text-slate-400 font-medium mb-1 uppercase tracking-wider">{label}</p>
      <p className="text-sm text-teal-300 font-semibold">{value}</p>
    </div>
  );
}
