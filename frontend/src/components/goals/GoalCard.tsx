"use client";
import { motion } from "framer-motion";
import type { Goal } from "@/types";
import { formatINR, probabilityRingColor, yearsUntil } from "@/lib/utils";

const GOAL_ICONS: Record<string, string> = {
  retirement: "🏖️",
  home_purchase: "🏠",
  education: "🎓",
  emergency_fund: "🛡️",
  other: "🎯",
};

interface GoalCardProps {
  goal: Goal;
}

export default function GoalCard({ goal }: GoalCardProps) {
  const prob = goal.current_success_probability ?? 0;
  const color = probabilityRingColor(prob);
  const years = yearsUntil(goal.target_year);

  const circumference = 2 * Math.PI * 22;
  const strokeDashoffset = circumference - prob * circumference;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glow-card p-5 flex gap-4"
    >
      {/* Probability ring */}
      <div className="flex-shrink-0">
        <div className="relative w-14 h-14">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 56 56">
            <circle cx="28" cy="28" r="22" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="5" />
            <motion.circle
              cx="28" cy="28" r="22"
              fill="none"
              stroke={color}
              strokeWidth="5"
              strokeLinecap="round"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-bold font-mono" style={{ color }}>
              {Math.round(prob * 100)}%
            </span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between mb-1">
          <p className="text-sm font-semibold text-white truncate flex items-center gap-1">
            {GOAL_ICONS[goal.goal_type]} {goal.goal_name}
          </p>
          <span className={`badge text-xs ml-2 flex-shrink-0 ${
            prob >= 0.8 ? "badge-success" : prob >= 0.6 ? "badge-warning" : "badge-danger"
          }`}>
            {prob >= 0.8 ? "On Track" : prob >= 0.6 ? "Moderate" : "At Risk"}
          </span>
        </div>

        <div className="space-y-1 text-xs text-slate-400">
          <div className="flex justify-between">
            <span>Target</span>
            <span className="font-mono text-white">{formatINR(goal.target_amount, true)}</span>
          </div>
          <div className="flex justify-between">
            <span>Timeline</span>
            <span className="text-amber-400 font-medium">{years}y ({goal.target_year})</span>
          </div>
          {goal.required_monthly_sip && (
            <div className="flex justify-between">
              <span>Required SIP</span>
              <span className="font-mono text-teal-400">{formatINR(goal.required_monthly_sip, true)}/mo</span>
            </div>
          )}
        </div>

        {/* Priority indicator */}
        <div className="flex gap-1 mt-2">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="w-4 h-1 rounded-full"
              style={{
                background: i < goal.priority
                  ? "linear-gradient(90deg, #f97316, #0f766e)"
                  : "rgba(255,255,255,0.08)",
              }}
            />
          ))}
          <span className="text-xs text-slate-500 ml-1">Priority</span>
        </div>
      </div>
    </motion.div>
  );
}
