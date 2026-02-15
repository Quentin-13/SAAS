import { create } from "zustand";
import { User, login as authLogin, register as authRegister, getUser, logout as authLogout } from "../auth";
import { isDemoMode, enableDemoMode, disableDemoMode, DEMO_USER } from "../demo";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  loginDemo: () => void;
  /** Try a real backend login with demo admin creds; falls back to demo mode on failure. */
  loginAsAdmin: () => Promise<void>;
  register: (data: { email: string; password: string; full_name: string; organization_name: string }) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  isAuthenticated: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      await authLogin(email, password);
      const user = await getUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Echec de la connexion";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  loginDemo: () => {
    enableDemoMode();
    set({ user: DEMO_USER, isAuthenticated: true, isLoading: false });
  },

  loginAsAdmin: async () => {
    // Try real backend login first, then fall back to demo mode
    set({ isLoading: true, error: null });
    try {
      await authLogin("demo@energy-autopilot.fr", "demo1234");
      const user = await getUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      // Backend unavailable — fall back to demo mode
      enableDemoMode();
      set({ user: DEMO_USER, isAuthenticated: true, isLoading: false });
    }
  },

  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      await authRegister(data);
      const user = await getUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Echec de l'inscription";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  logout: () => {
    disableDemoMode();
    authLogout();
    set({ user: null, isAuthenticated: false });
  },

  fetchUser: async () => {
    if (isDemoMode()) {
      set({ user: DEMO_USER, isAuthenticated: true, isLoading: false });
      return;
    }
    set({ isLoading: true });
    try {
      const user = await getUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  initialize: async () => {
    if (typeof window === "undefined") return;
    if (isDemoMode()) {
      set({ user: DEMO_USER, isAuthenticated: true });
      return;
    }
    const token = localStorage.getItem("access_token");
    if (token) {
      try {
        const user = await getUser();
        set({ user, isAuthenticated: true });
      } catch {
        set({ user: null, isAuthenticated: false });
      }
    }
  },
}));
