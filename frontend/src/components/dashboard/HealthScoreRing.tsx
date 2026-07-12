"use client";
import { motion } from "framer-motion";
import { probabilityRingColor } from "@/lib/utils";

interface HealthScoreRingProps {
  score: number;
}

export default function HealthScoreRing({ score }: HealthScoreRingProps) {
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const color = score >= 70 ? "#10b981" : score >= 45 ? "#f59e0b" : "#ef4444";
  const label = score >= 70 ? "Excellent" : score >= 55 ? "Good" : score >= 40 ? "Fair" : "At Risk";

  return (
    <div className="relative flex flex-col items-center gap-3">
      <div className="relative w-40 h-40">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 160 160">
          {/* Track */}
          <circle
            cx="80" cy="80" r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="12"
          />
          {/* Progress */}
          <motion.circle
            cx="80" cy="80" r={radius}
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            style={{ filter: `drop-shadow(0 0 8px ${color}80)` }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="text-3xl font-bold font-mono"
            style={{ color }}
          >
            {Math.round(score)}
          </motion.span>
          <span className="text-xs text-slate-400 font-medium">/ 100</span>
        </div>
      </div>
      <div className="text-center">
        <p className="font-semibold text-sm" style={{ color }}>{label}</p>
      </div>
    </div>
  );
}
