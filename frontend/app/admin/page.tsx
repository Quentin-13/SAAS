"use client";

import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAdminStore } from "@/lib/stores/adminStore";
import { formatCurrency } from "@/lib/utils";

export default function AdminDashboard() {
  const { stats, fetchStats, isLoading } = useAdminStore();
  const loaded = useRef(false);

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;
    fetchStats();
  }, [fetchStats]);

  if (isLoading && !stats) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  const s = stats || {
    total_users: 0,
    active_users: 0,
    total_organizations: 0,
    total_sites: 0,
    total_devices: 0,
    autopilot_actions_this_month: 0,
    total_revenue_monthly: 0,
    total_revenue_annual: 0,
    plans_distribution: {},
    churn_rate: 0,
    new_users_this_month: 0,
  };

  const kpis = [
    { label: "Utilisateurs", value: s.total_users, sub: `${s.active_users} actifs` },
    { label: "Organisations", value: s.total_organizations },
    { label: "Sites", value: s.total_sites },
    { label: "Appareils", value: s.total_devices },
    { label: "Revenu mensuel", value: formatCurrency(s.total_revenue_monthly) },
    { label: "Revenu annuel", value: formatCurrency(s.total_revenue_annual) },
    { label: "Actions Autopilot", value: s.autopilot_actions_this_month, sub: "ce mois" },
    { label: "Churn Rate", value: `${s.churn_rate}%` },
    { label: "Nouveaux users", value: s.new_users_this_month, sub: "ce mois" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <p className="text-muted-foreground">Vue d&apos;ensemble de la plateforme</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {kpis.map((kpi) => (
          <Card key={kpi.label}>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground">{kpi.label}</p>
              <p className="text-2xl font-bold mt-1">{kpi.value}</p>
              {kpi.sub && <p className="text-xs text-muted-foreground mt-1">{kpi.sub}</p>}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Plans distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Distribution des plans</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-6">
            {Object.entries(s.plans_distribution).map(([plan, count]) => (
              <div key={plan} className="text-center">
                <p className="text-2xl font-bold">{count}</p>
                <p className="text-sm text-muted-foreground capitalize">{plan}</p>
              </div>
            ))}
            {Object.keys(s.plans_distribution).length === 0 && (
              <p className="text-sm text-muted-foreground">Aucun abonnement</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
