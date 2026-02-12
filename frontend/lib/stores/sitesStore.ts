import { create } from "zustand";
import api from "../api";
import { isDemoMode, getDemoSites } from "../demo";

export interface Site {
  id: string;
  name: string;
  address: string | null;
  postal_code: string | null;
  city: string | null;
  country: string;
  latitude: number | null;
  longitude: number | null;
  surface_area: number | null;
  building_type: string | null;
  autopilot_enabled: boolean;
  created_at: string;
  zones_count?: number;
  devices_count?: number;
}

interface SitesState {
  sites: Site[];
  currentSite: Site | null;
  isLoading: boolean;
  error: string | null;
  fetchSites: () => Promise<void>;
  fetchSite: (id: string) => Promise<void>;
  createSite: (data: Partial<Site>) => Promise<Site>;
  updateSite: (id: string, data: Partial<Site>) => Promise<void>;
  deleteSite: (id: string) => Promise<void>;
  toggleAutopilot: (id: string, enabled: boolean) => Promise<void>;
}

export const useSitesStore = create<SitesState>((set, get) => ({
  sites: [],
  currentSite: null,
  isLoading: false,
  error: null,

  fetchSites: async () => {
    if (isDemoMode()) {
      set({ sites: getDemoSites() as Site[], isLoading: false });
      return;
    }
    set({ isLoading: true });
    try {
      const response = await api.get("/sites/");
      set({ sites: response.data, isLoading: false });
    } catch {
      set({ error: "Erreur de chargement des sites", isLoading: false });
    }
  },

  fetchSite: async (id) => {
    set({ isLoading: true });
    try {
      const response = await api.get(`/sites/${id}`);
      set({ currentSite: response.data, isLoading: false });
    } catch {
      set({ error: "Site non trouvé", isLoading: false });
    }
  },

  createSite: async (data) => {
    const response = await api.post("/sites/", data);
    const newSite = response.data;
    set((state) => ({ sites: [...state.sites, newSite] }));
    return newSite;
  },

  updateSite: async (id, data) => {
    const response = await api.patch(`/sites/${id}`, data);
    const updated = response.data;
    set((state) => ({
      sites: state.sites.map((s) => (s.id === id ? updated : s)),
      currentSite: state.currentSite?.id === id ? updated : state.currentSite,
    }));
  },

  deleteSite: async (id) => {
    await api.delete(`/sites/${id}`);
    set((state) => ({
      sites: state.sites.filter((s) => s.id !== id),
      currentSite: state.currentSite?.id === id ? null : state.currentSite,
    }));
  },

  toggleAutopilot: async (id, enabled) => {
    const endpoint = enabled ? "enable" : "disable";
    await api.post(`/sites/${id}/autopilot/${endpoint}`);
    set((state) => ({
      sites: state.sites.map((s) => (s.id === id ? { ...s, autopilot_enabled: enabled } : s)),
      currentSite:
        state.currentSite?.id === id
          ? { ...state.currentSite, autopilot_enabled: enabled }
          : state.currentSite,
    }));
  },
}));
