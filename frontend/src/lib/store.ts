/**
 * Zustand global store for FutureLens
 */
"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type {
  User,
  FinancialProfile,
  Goal,
  SimulationResult,
  DashboardData,
} from "@/types";

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: User) => void;
  clearAuth: () => void;
}

interface ProfileState {
  profile: FinancialProfile | null;
  setProfile: (profile: FinancialProfile | null) => void;
}

interface GoalsState {
  goals: Goal[];
  setGoals: (goals: Goal[]) => void;
  addGoal: (goal: Goal) => void;
  removeGoal: (goalId: string) => void;
}

interface SimulationState {
  latestSimulation: SimulationResult | null;
  setLatestSimulation: (result: SimulationResult | null) => void;
}

interface DashboardState {
  dashboard: DashboardData | null;
  setDashboard: (data: DashboardData | null) => void;
}

type FutureLensStore = AuthState &
  ProfileState &
  GoalsState &
  SimulationState &
  DashboardState;

export const useStore = create<FutureLensStore>()(
  persist(
    (set) => ({
      // Auth
      token: null,
      user: null,
      isAuthenticated: false,
      setAuth: (token, user) => set({ token, user, isAuthenticated: true }),
      clearAuth: () => set({ token: null, user: null, isAuthenticated: false }),

      // Profile
      profile: null,
      setProfile: (profile) => set({ profile }),

      // Goals
      goals: [],
      setGoals: (goals) => set({ goals }),
      addGoal: (goal) => set((state) => ({ goals: [...state.goals, goal] })),
      removeGoal: (goalId) =>
        set((state) => ({ goals: state.goals.filter((g) => g.id !== goalId) })),

      // Simulation
      latestSimulation: null,
      setLatestSimulation: (result) => set({ latestSimulation: result }),

      // Dashboard
      dashboard: null,
      setDashboard: (data) => set({ dashboard: data }),
    }),
    {
      name: "futurelens-store",
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Convenience selectors
export const useAuth = () => useStore((s) => ({ token: s.token, user: s.user, isAuthenticated: s.isAuthenticated, setAuth: s.setAuth, clearAuth: s.clearAuth }));
export const useProfile = () => useStore((s) => ({ profile: s.profile, setProfile: s.setProfile }));
export const useGoals = () => useStore((s) => ({ goals: s.goals, setGoals: s.setGoals, addGoal: s.addGoal, removeGoal: s.removeGoal }));
export const useSimulation = () => useStore((s) => ({ latestSimulation: s.latestSimulation, setLatestSimulation: s.setLatestSimulation }));
