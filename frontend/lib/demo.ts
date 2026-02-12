/**
 * Demo mode: provides mock data and auth so the app works without a backend.
 * Activated when a user clicks "Voir la démo" or the "Compte démo" button.
 */

import type { User } from "./auth";
import type { DashboardOverview } from "./stores/energyStore";

const DEMO_TOKEN = "demo-mode-token";

export const DEMO_USER: User = {
  id: "demo-user-001",
  email: "demo@energy-autopilot.fr",
  full_name: "Jean Dupont",
  phone: "+33 6 12 34 56 78",
  is_active: true,
  organization_id: "demo-org-001",
  created_at: "2024-01-15T10:00:00Z",
};

export function isDemoMode(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem("demo_mode") === "true";
}

export function enableDemoMode() {
  localStorage.setItem("demo_mode", "true");
  localStorage.setItem("access_token", DEMO_TOKEN);
  localStorage.setItem("refresh_token", DEMO_TOKEN);
}

export function disableDemoMode() {
  localStorage.removeItem("demo_mode");
}

function generateDailyConsumption() {
  const data = [];
  const now = new Date();
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const isWeekend = date.getDay() === 0 || date.getDay() === 6;
    const baseKwh = isWeekend ? 180 : 320;
    const variation = (Math.random() - 0.5) * 80;
    const total_kwh = Math.round(baseKwh + variation);
    data.push({
      date: date.toISOString().split("T")[0],
      total_kwh,
      total_cost_eur: Math.round(total_kwh * 0.22 * 100) / 100,
      avg_power_kw: Math.round((total_kwh / 24) * 10) / 10,
      peak_power_kw: Math.round((total_kwh / 24) * 1.8 * 10) / 10,
      co2_kg: Math.round(total_kwh * 0.057 * 10) / 10,
    });
  }
  return data;
}

function generateRecentActions() {
  const actions = [
    {
      action_type: "set_temperature",
      action_params: { target_temp: 19, previous_temp: 21 },
      reasoning: "Tarif heures pleines détecté, réduction de 2°C pour optimiser les coûts.",
      predicted_savings_eur: 1.85,
      confidence_score: 0.92,
    },
    {
      action_type: "set_temperature",
      action_params: { target_temp: 20, previous_temp: 22 },
      reasoning: "Bâtiment inoccupé détecté via capteur de présence, passage en mode éco.",
      predicted_savings_eur: 2.10,
      confidence_score: 0.88,
    },
    {
      action_type: "set_temperature",
      action_params: { target_temp: 21, previous_temp: 19 },
      reasoning: "Pré-chauffage avant arrivée des occupants (prévision météo : 3°C).",
      predicted_savings_eur: 0.50,
      confidence_score: 0.95,
    },
    {
      action_type: "set_temperature",
      action_params: { target_temp: 18, previous_temp: 21 },
      reasoning: "Passage en tarif heures super creuses, réduction nocturne activée.",
      predicted_savings_eur: 2.40,
      confidence_score: 0.91,
    },
    {
      action_type: "set_temperature",
      action_params: { target_temp: 20, previous_temp: 22 },
      reasoning: "Optimisation basée sur prévision météo favorable (15°C extérieur).",
      predicted_savings_eur: 1.20,
      confidence_score: 0.87,
    },
  ];

  const now = new Date();
  return actions.map((action, i) => {
    const executed = new Date(now);
    executed.setHours(executed.getHours() - i * 4);
    return {
      id: `demo-action-${i + 1}`,
      site_id: "demo-site-001",
      device_id: `demo-device-${(i % 3) + 1}`,
      ...action,
      status: "executed",
      executed_at: executed.toISOString(),
      created_at: executed.toISOString(),
    };
  });
}

export function getDemoDashboardOverview(): DashboardOverview {
  return {
    total_savings_eur: 847.5,
    total_savings_pct: 27.3,
    total_kwh_saved: 3852,
    co2_avoided_kg: 219.6,
    actions_count: 142,
    active_sites: 3,
    active_devices: 5,
    daily_consumption: generateDailyConsumption(),
    recent_actions: generateRecentActions(),
  };
}

export function getDemoSites(): import("./stores/sitesStore").Site[] {
  return [
    {
      id: "demo-site-001",
      name: "Bureau Paris 11e",
      address: "42 rue de la Roquette",
      postal_code: "75011",
      city: "Paris",
      country: "FR",
      latitude: 48.8566,
      longitude: 2.3783,
      surface_area: 850,
      building_type: "office",
      autopilot_enabled: true,
      created_at: "2024-01-15T10:00:00Z",
    },
    {
      id: "demo-site-002",
      name: "Agence Lyon Part-Dieu",
      address: "15 boulevard Vivier Merle",
      postal_code: "69003",
      city: "Lyon",
      country: "FR",
      latitude: 45.7602,
      longitude: 4.8596,
      surface_area: 420,
      building_type: "office",
      autopilot_enabled: true,
      created_at: "2024-02-01T10:00:00Z",
    },
    {
      id: "demo-site-003",
      name: "Boutique Bordeaux",
      address: "8 cours de l'Intendance",
      postal_code: "33000",
      city: "Bordeaux",
      country: "FR",
      latitude: 44.8378,
      longitude: -0.5792,
      surface_area: 180,
      building_type: "retail",
      autopilot_enabled: false,
      created_at: "2024-03-10T10:00:00Z",
    },
  ];
}
