import { create } from "zustand";
import api from "../api";
import { isDemoMode, getDemoDashboardOverview } from "../demo";

export interface DailyAnalytics {
  date: string;
  total_kwh: number;
  total_cost_eur: number;
  avg_power_kw: number;
  peak_power_kw: number;
  co2_kg: number;
}

export interface Forecast {
  forecast_date: string;
  horizon_hours: number;
  predicted_kwh: number;
  predicted_cost_eur: number;
  confidence_lower: number;
  confidence_upper: number;
}

export interface Anomaly {
  time: string;
  device_id: string;
  actual_kw: number;
  expected_kw: number;
  deviation_pct: number;
  estimated_waste_eur: number;
}

export interface AutopilotAction {
  id: string;
  site_id: string;
  device_id: string;
  action_type: string;
  action_params: Record<string, unknown>;
  reasoning: string | null;
  predicted_savings_eur: number | null;
  confidence_score: number | null;
  status: string;
  executed_at: string | null;
  created_at: string;
}

export interface DashboardOverview {
  total_savings_eur: number;
  total_savings_pct: number;
  total_kwh_saved: number;
  co2_avoided_kg: number;
  actions_count: number;
  active_sites: number;
  active_devices: number;
  daily_consumption: DailyAnalytics[];
  recent_actions: AutopilotAction[];
}

interface EnergyState {
  dailyAnalytics: DailyAnalytics[];
  forecasts: Forecast[];
  anomalies: Anomaly[];
  dashboardOverview: DashboardOverview | null;
  isLoading: boolean;
  error: string | null;
  fetchDailyAnalytics: (siteId: string, startDate?: string, endDate?: string) => Promise<void>;
  fetchForecasts: (siteId: string) => Promise<void>;
  fetchAnomalies: (siteId: string) => Promise<void>;
  fetchDashboardOverview: () => Promise<void>;
}

export const useEnergyStore = create<EnergyState>((set) => ({
  dailyAnalytics: [],
  forecasts: [],
  anomalies: [],
  dashboardOverview: null,
  isLoading: false,
  error: null,

  fetchDailyAnalytics: async (siteId, startDate, endDate) => {
    if (isDemoMode()) {
      const overview = getDemoDashboardOverview();
      set({ dailyAnalytics: overview.daily_consumption, isLoading: false, error: null });
      return;
    }
    set({ isLoading: true, error: null });
    try {
      const params: Record<string, string> = { site_id: siteId };
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      const response = await api.get("/energy/analytics/daily", { params });
      set({ dailyAnalytics: response.data, isLoading: false });
    } catch {
      set({ error: "Erreur de chargement des analytics", isLoading: false });
    }
  },

  fetchForecasts: async (siteId) => {
    if (isDemoMode()) {
      set({ forecasts: [], isLoading: false, error: null });
      return;
    }
    set({ isLoading: true, error: null });
    try {
      const response = await api.get("/energy/forecast", { params: { site_id: siteId } });
      set({ forecasts: response.data, isLoading: false });
    } catch {
      set({ error: "Erreur de chargement des prévisions", isLoading: false });
    }
  },

  fetchAnomalies: async (siteId) => {
    if (isDemoMode()) {
      set({ anomalies: [], isLoading: false, error: null });
      return;
    }
    set({ isLoading: true, error: null });
    try {
      const response = await api.get("/energy/anomalies", { params: { site_id: siteId } });
      set({ anomalies: response.data, isLoading: false });
    } catch {
      set({ error: "Erreur de chargement des anomalies", isLoading: false });
    }
  },

  fetchDashboardOverview: async () => {
    if (isDemoMode()) {
      set({ dashboardOverview: getDemoDashboardOverview(), isLoading: false, error: null });
      return;
    }
    set({ isLoading: true, error: null });
    try {
      const response = await api.get("/dashboard/overview");
      set({ dashboardOverview: response.data, isLoading: false });
    } catch {
      set({ error: "Erreur de chargement du dashboard", isLoading: false });
    }
  },
}));
