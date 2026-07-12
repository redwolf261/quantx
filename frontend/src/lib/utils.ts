/**
 * Utility helpers
 */

/** Format number as Indian currency (₹ with lakh/crore notation) */
export function formatINR(amount: number, compact = false): string {
  if (compact) {
    if (amount >= 1_00_00_000) return `₹${(amount / 1_00_00_000).toFixed(2)}Cr`;
    if (amount >= 1_00_000) return `₹${(amount / 1_00_000).toFixed(2)}L`;
    if (amount >= 1_000) return `₹${(amount / 1_000).toFixed(1)}K`;
    return `₹${amount.toFixed(0)}`;
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

/** Format percentage */
export function formatPct(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/** Format percentage as color class */
export function probabilityColor(prob: number): string {
  if (prob >= 0.80) return "text-emerald-400";
  if (prob >= 0.65) return "text-amber-400";
  return "text-red-400";
}

/** Format percentage ring color */
export function probabilityRingColor(prob: number): string {
  if (prob >= 0.80) return "#10b981";  // emerald
  if (prob >= 0.65) return "#f59e0b";  // amber
  return "#ef4444";  // red
}

/** Health score color */
export function healthScoreColor(score: number): string {
  if (score >= 70) return "text-emerald-400";
  if (score >= 45) return "text-amber-400";
  return "text-red-400";
}

/** Risk level badge class */
export function riskLevelClass(level: string): string {
  switch (level) {
    case "low":      return "risk-low";
    case "medium":   return "risk-medium";
    case "high":     return "risk-high";
    case "critical": return "risk-critical";
    default:         return "badge-muted";
  }
}

/** Calculate years until a target year */
export function yearsUntil(targetYear: number): number {
  return targetYear - new Date().getFullYear();
}

/** Format compact number */
export function formatNumber(n: number): string {
  if (n >= 1e7) return `${(n / 1e7).toFixed(1)}Cr`;
  if (n >= 1e5) return `${(n / 1e5).toFixed(1)}L`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return n.toFixed(0);
}

/** Clamp value between min and max */
export function clamp(val: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, val));
}

/** Debounce function */
export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}
