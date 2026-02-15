import { create } from "zustand";
import api from "../api";

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
    set({ isLoading: true });
    try {
      const params = new URLSearchParams({ page: String(page), per_page: "20" });
      if (search) params.set("search", search);
      if (role) params.set("role", role);
      const res = await api.get(`/admin/users?${params}`);
      set({ users: res.data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  updateUser: async (userId, data) => {
    await api.patch(`/admin/users/${userId}`, data);
  },

  fetchOrganizations: async (page = 1, search = "") => {
    set({ isLoading: true });
    try {
      const params = new URLSearchParams({ page: String(page), per_page: "20" });
      if (search) params.set("search", search);
      const res = await api.get(`/admin/organizations?${params}`);
      set({ organizations: res.data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchSubscriptions: async (page = 1, status = "") => {
    set({ isLoading: true });
    try {
      const params = new URLSearchParams({ page: String(page), per_page: "20" });
      if (status) params.set("status", status);
      const res = await api.get(`/admin/subscriptions?${params}`);
      set({ subscriptions: res.data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  updateSubscription: async (subId, data) => {
    await api.patch(`/admin/subscriptions/${subId}`, data);
  },

  fetchStats: async () => {
    set({ isLoading: true });
    try {
      const res = await api.get("/admin/stats");
      set({ stats: res.data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchLogs: async (page = 1, action = "") => {
    set({ isLoading: true });
    try {
      const params = new URLSearchParams({ page: String(page), per_page: "30" });
      if (action) params.set("action", action);
      const res = await api.get(`/admin/logs?${params}`);
      set({ logs: res.data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },
}));
