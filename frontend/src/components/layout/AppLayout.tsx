"use client";
import { ReactNode, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/store";

const NAV_ITEMS = [
  { href: "/twin",         label: "Financial Twin", desc: "Command Center",  icon: "🧬" },
  { href: "/roadmap",      label: "Financial GPS",  desc: "Live navigation", icon: "📍" },
  { href: "/timeline",     label: "Timeline",       desc: "Life milestones", icon: "⏳" },
  { href: "/futures",      label: "Future Forks",   desc: "Compare paths",   icon: "⑂" },
  { href: "/advisor",      label: "Fin Intelligence",desc: "AI insights",    icon: "🤖" },
  { href: "/profile",      label: "My Profile",     desc: "Financial data",  icon: "◉" },
  { href: "/playground",   label: "Playground",     desc: "Scenarios",       icon: "⚡" },
];

const RM_NAV = [
  { href: "/rm-dashboard", label: "RM Dashboard",  icon: "📋", desc: "Customer overview" },
];

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { isAuthenticated, user, clearAuth } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) return null;

  const navItems = user?.role === "rm" || user?.role === "admin"
    ? [...RM_NAV, ...NAV_ITEMS]
    : NAV_ITEMS;

  const handleLogout = () => {
    clearAuth();
    localStorage.removeItem("fl_token");
    router.push("/");
  };

  return (
    <div className="flex h-screen bg-navy-950 overflow-hidden">
      {/* Sidebar */}
      <motion.aside
        initial={{ x: -60, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="w-64 flex flex-col border-r"
        style={{
          background: "rgba(7, 13, 26, 0.9)",
          borderColor: "rgba(255,255,255,0.06)",
          backdropFilter: "blur(20px)",
        }}
      >
        {/* Logo */}
        <div className="p-5 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, #6d28d9, #8b5cf6)" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v3m0 14v3M2 12h3m14 0h3" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-bold text-white">FutureLens</p>
              <p className="text-xs text-slate-500">Wealth Intelligence</p>
            </div>
          </div>
        </div>

        {/* User info */}
        <div className="p-4 border-b" style={{ borderColor: "rgba(255,255,255,0.04)" }}>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white"
              style={{ background: "linear-gradient(135deg, #7c3aed, #10b981)" }}>
              {user?.full_name?.[0] || "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white truncate">{user?.full_name}</p>
              <span className={`badge text-xs ${user?.role === "rm" ? "badge-violet" : "badge-muted"}`}>
                {user?.role?.toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href}>
                <div className={`nav-item ${isActive ? "active" : ""}`}>
                  <span className="text-lg">{item.icon}</span>
                  <div>
                    <p className="text-xs font-semibold leading-none">{item.label}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{item.desc}</p>
                  </div>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
          <button
            onClick={handleLogout}
            className="nav-item w-full text-left"
          >
            <span>↩</span>
            <span className="text-xs font-medium">Sign Out</span>
          </button>
        </div>
      </motion.aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <motion.div
          key={pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="min-h-full"
        >
          {children}
        </motion.div>
      </main>
    </div>
  );
}
