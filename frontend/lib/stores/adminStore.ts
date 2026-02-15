import { create } from "zustand";
import api from "../api";
import { isDemoMode } from "../demo";

export interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  phone: string | null;
  is_active: boolean;
  is_superuser: boolean;
  role: string;
  organization_id: string | null;
  organization_name: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface AdminOrg {
  id: string;
  name: string;
  subscription_tier: string;
  subscription_status: string;
  created_at: string;
  user_count: number;
  site_count: number;
}

export interface AdminSubscription {
  id: string;
  organization_id: string;
  organization_name: string | null;
  plan: string;
  status: string;
  monthly_price_eur: number | null;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  start_date: string;
  end_date: string | null;
  created_at: string;
}

export interface PlatformStats {
  total_users: number;
  active_users: number;
  total_organizations: number;
  total_sites: number;
  total_devices: number;
  autopilot_actions_this_month: number;
  total_revenue_monthly: number;
  total_revenue_annual: number;
  plans_distribution: Record<string, number>;
  churn_rate: number;
  new_users_this_month: number;
}

export interface ActivityLog {
  id: string;
  user_id: string | null;
  user_email: string | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  details: string | null;
  ip_address: string | null;
  created_at: string;
}

interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// ── Demo data ──────────────────────────────────────────────────────────

const DEMO_STATS: PlatformStats = {
  total_users: 156,
  active_users: 134,
  total_organizations: 42,
  total_sites: 87,
  total_devices: 312,
  autopilot_actions_this_month: 1847,
  total_revenue_monthly: 8400,
  total_revenue_annual: 100800,
  plans_distribution: { free: 12, starter: 18, pro: 9, enterprise: 3 },
  churn_rate: 2.4,
  new_users_this_month: 23,
};

const DEMO_USERS: PaginatedResult<AdminUser> = {
  items: [
    { id: "1", email: "admin@energy-autopilot.fr", full_name: "Admin Principal", phone: null, is_active: true, is_superuser: true, role: "admin", organization_id: "org-1", organization_name: "Energy Autopilot", created_at: "2024-01-10T10:00:00Z", updated_at: null },
    { id: "2", email: "jean.dupont@acme.fr", full_name: "Jean Dupont", phone: "+33612345678", is_active: true, is_superuser: false, role: "user", organization_id: "org-2", organization_name: "ACME Corp", created_at: "2024-02-15T10:00:00Z", updated_at: null },
    { id: "3", email: "marie.martin@techco.fr", full_name: "Marie Martin", phone: null, is_active: true, is_superuser: false, role: "user", organization_id: "org-3", organization_name: "TechCo", created_at: "2024-03-01T10:00:00Z", updated_at: null },
    { id: "4", email: "pierre.bernard@greenergy.fr", full_name: "Pierre Bernard", phone: "+33698765432", is_active: false, is_superuser: false, role: "user", organization_id: "org-4", organization_name: "GreenErgy", created_at: "2024-03-20T10:00:00Z", updated_at: null },
  ],
  total: 4, page: 1, per_page: 20, pages: 1,
};

const DEMO_ORGS: PaginatedResult<AdminOrg> = {
  items: [
    { id: "org-1", name: "Energy Autopilot", subscription_tier: "enterprise", subscription_status: "active", created_at: "2024-01-10T10:00:00Z", user_count: 5, site_count: 3 },
    { id: "org-2", name: "ACME Corp", subscription_tier: "pro", subscription_status: "active", created_at: "2024-02-15T10:00:00Z", user_count: 12, site_count: 8 },
    { id: "org-3", name: "TechCo", subscription_tier: "starter", subscription_status: "active", created_at: "2024-03-01T10:00:00Z", user_count: 3, site_count: 2 },
    { id: "org-4", name: "GreenErgy", subscription_tier: "free", subscription_status: "trialing", created_at: "2024-03-20T10:00:00Z", user_count: 1, site_count: 1 },
  ],
  total: 4, page: 1, per_page: 20, pages: 1,
};

const DEMO_SUBS: PaginatedResult<AdminSubscription> = {
  items: [
    { id: "sub-1", organization_id: "org-1", organization_name: "Energy Autopilot", plan: "enterprise", status: "active", monthly_price_eur: 500, stripe_customer_id: null, stripe_subscription_id: null, start_date: "2024-01-10", end_date: null, created_at: "2024-01-10T10:00:00Z" },
    { id: "sub-2", organization_id: "org-2", organization_name: "ACME Corp", plan: "pro", status: "active", monthly_price_eur: 200, stripe_customer_id: null, stripe_subscription_id: null, start_date: "2024-02-15", end_date: null, created_at: "2024-02-15T10:00:00Z" },
    { id: "sub-3", organization_id: "org-3", organization_name: "TechCo", plan: "starter", status: "active", monthly_price_eur: 100, stripe_customer_id: null, stripe_subscription_id: null, start_date: "2024-03-01", end_date: null, created_at: "2024-03-01T10:00:00Z" },
  ],
  total: 3, page: 1, per_page: 20, pages: 1,
};

const DEMO_LOGS: PaginatedResult<ActivityLog> = {
  items: [
    { id: "log-1", user_id: "1", user_email: "admin@energy-autopilot.fr", action: "user.login", target_type: null, target_id: null, details: "Admin login", ip_address: "127.0.0.1", created_at: new Date().toISOString() },
    { id: "log-2", user_id: "1", user_email: "admin@energy-autopilot.fr", action: "user.update", target_type: "user", target_id: "4", details: "is_active=false", ip_address: "127.0.0.1", created_at: new Date(Date.now() - 3600000).toISOString() },
    { id: "log-3", user_id: "1", user_email: "admin@energy-autopilot.fr", action: "subscription.update", target_type: "subscription", target_id: "sub-2", details: "plan=pro", ip_address: "127.0.0.1", created_at: new Date(Date.now() - 7200000).toISOString() },
  ],
  total: 3, page: 1, per_page: 30, pages: 1,
};

// ── Store ──────────────────────────────────────────────────────────────

interface AdminState {
  users: PaginatedResult<AdminUser> | null;
  organizations: PaginatedResult<AdminOrg> | null;
  subscriptions: PaginatedResult<AdminSubscription> | null;
  stats: PlatformStats | null;
  logs: PaginatedResult<ActivityLog> | null;
  isLoading: boolean;

  fetchUsers: (page?: number, search?: string, role?: string) => Promise<void>;
  updateUser: (userId: string, data: { is_active?: boolean; role?: string; reset_password?: string }) => Promise<void>;
  fetchOrganizations: (page?: number, search?: string) => Promise<void>;
  fetchSubscriptions: (page?: number, status?: string) => Promise<void>;
  updateSubscription: (subId: string, data: { plan?: string; status?: string }) => Promise<void>;
  fetchStats: () => Promise<void>;
  fetchLogs: (page?: number, action?: string) => Promise<void>;
}

export const useAdminStore = create<AdminState>((set) => ({
  users: null,
  organizations: null,
  subscriptions: null,
  stats: null,
  logs: null,
  isLoading: false,

  fetchUsers: async (page = 1, search = "", role = "") => {
    if (isDemoMode()) {
      set({ users: DEMO_USERS, isLoading: false });
      return;
    }
    set({ isLoading: true });
    try {
      const params = new URLSearchParams({ page: String(page), per_page: "20" });
      if (search) params.set("search", search);
      if (role) params.set("role", role);
      const res = await api.get(`/admin/users?${params}`);
      set({ users: res.data, isLoading: false });
    } catch {
      set({ users: DEMO_USERS, isLoading: false });
    }
  },

  updateUser: async (userId, data) => {
    if (isDemoMode()) return;
    await api.patch(`/admin/users/${userId}`, data);
  },

  fetchOrganizations: async (page = 1, search = "") => {
    if (isDemoMode()) {
      set({ organizations: DEMO_ORGS, isLoading: false });
      return;
    }
    set({ isLoading: true });
    try {
      const params = new URLSearchParams({ page: String(page), per_page: "20" });
      if (search) params.set("search", search);
      const res = await api.get(`/admin/organizations?${params}`);
      set({ organizations: res.data, isLoading: false });
    } catch {
      set({ organizations: DEMO_ORGS, isLoading: false });
    }
  },

  fetchSubscriptions: async (page = 1, status = "") => {
    if (isDemoMode()) {
      set({ subscriptions: DEMO_SUBS, isLoading: false });
      return;
    }
    set({ isLoading: true });
    try {
      const params = new URLSearchParams({ page: String(page), per_page: "20" });
      if (status) params.set("status", status);
      const res = await api.get(`/admin/subscriptions?${params}`);
      set({ subscriptions: res.data, isLoading: false });
    } catch {
      set({ subscriptions: DEMO_SUBS, isLoading: false });
    }
  },

  updateSubscription: async (subId, data) => {
    if (isDemoMode()) return;
    await api.patch(`/admin/subscriptions/${subId}`, data);
  },

  fetchStats: async () => {
    if (isDemoMode()) {
      set({ stats: DEMO_STATS, isLoading: false });
      return;
    }
    set({ isLoading: true });
    try {
      const res = await api.get("/admin/stats");
      set({ stats: res.data, isLoading: false });
    } catch {
      set({ stats: DEMO_STATS, isLoading: false });
    }
  },

  fetchLogs: async (page = 1, action = "") => {
    if (isDemoMode()) {
      set({ logs: DEMO_LOGS, isLoading: false });
      return;
    }
    set({ isLoading: true });
    try {
      const params = new URLSearchParams({ page: String(page), per_page: "30" });
      if (action) params.set("action", action);
      const res = await api.get(`/admin/logs?${params}`);
      set({ logs: res.data, isLoading: false });
    } catch {
      set({ logs: DEMO_LOGS, isLoading: false });
    }
  },
}));
