"use client";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import type { PercentileBand } from "@/types";
import { formatINR } from "@/lib/utils";

interface NetWorthChartProps {
  bands: PercentileBand[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="fl-tooltip">
      <p className="font-semibold text-white mb-2">Year {label}</p>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex justify-between gap-4 text-xs">
          <span style={{ color: p.color }}>{p.name}</span>
          <span className="font-mono text-white">{formatINR(p.value, true)}</span>
        </div>
      ))}
    </div>
  );
};

export default function NetWorthChart({ bands }: NetWorthChartProps) {
  return (
    <div className="h-52">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={bands} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="p90" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f97316" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="p50" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="p10" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.1} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis
            dataKey="year"
            tick={{ fill: "#64748b", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `Yr ${v}`}
          />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => formatINR(v, true)}
            width={55}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* P90 band */}
          <Area
            type="monotone"
            dataKey="p90"
            name="Best (P90)"
            stroke="#f97316"
            strokeWidth={1.5}
            strokeDasharray="4 4"
            fill="url(#p90)"
            dot={false}
          />
          {/* P50 (median) */}
          <Area
            type="monotone"
            dataKey="p50"
            name="Median"
            stroke="#10b981"
            strokeWidth={2.5}
            fill="url(#p50)"
            dot={false}
          />
          {/* P10 band */}
          <Area
            type="monotone"
            dataKey="p10"
            name="Worst (P10)"
            stroke="#ef4444"
            strokeWidth={1.5}
            strokeDasharray="4 4"
            fill="url(#p10)"
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
