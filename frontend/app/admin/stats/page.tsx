"use client";

import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAdminStore } from "@/lib/stores/adminStore";
import { formatCurrency } from "@/lib/utils";

export default function AdminStatsPage() {
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

  const planColors: Record<string, string> = {
    free: "bg-gray-200",
    starter: "bg-blue-400",
    pro: "bg-primary",
    enterprise: "bg-purple-600",
  };

  const totalSubs = Object.values(s.plans_distribution).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Statistiques</h1>
        <p className="text-muted-foreground">Analyse détaillée de la plateforme</p>
      </div>

      {/* Revenue cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Revenu mensuel récurrent</p>
            <p className="text-3xl font-bold text-primary mt-1">{formatCurrency(s.total_revenue_monthly)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Revenu annuel projeté</p>
            <p className="text-3xl font-bold mt-1">{formatCurrency(s.total_revenue_annual)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Churn Rate</p>
            <p className="text-3xl font-bold mt-1">{s.churn_rate}%</p>
            <p className="text-xs text-muted-foreground mt-1">30 derniers jours</p>
          </CardContent>
        </Card>
      </div>

      {/* Users & Activity */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Utilisateurs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total</span>
              <span className="font-bold">{s.total_users}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Actifs</span>
              <span className="font-bold text-green-600">{s.active_users}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Nouveaux ce mois</span>
              <span className="font-bold text-blue-600">+{s.new_users_this_month}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Inactifs</span>
              <span className="font-bold text-red-600">{s.total_users - s.active_users}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Plateforme</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Organisations</span>
              <span className="font-bold">{s.total_organizations}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Sites</span>
              <span className="font-bold">{s.total_sites}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Appareils</span>
              <span className="font-bold">{s.total_devices}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Actions Autopilot (ce mois)</span>
              <span className="font-bold">{s.autopilot_actions_this_month}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Plan distribution chart */}
      <Card>
        <CardHeader>
          <CardTitle>Distribution des plans</CardTitle>
        </CardHeader>
        <CardContent>
          {Object.keys(s.plans_distribution).length > 0 ? (
            <>
              <div className="flex h-8 w-full overflow-hidden rounded-full">
                {Object.entries(s.plans_distribution).map(([plan, count]) => (
                  <div
                    key={plan}
                    className={cn(planColors[plan] || "bg-gray-300")}
                    style={{ width: `${(count / totalSubs) * 100}%` }}
                    title={`${plan}: ${count}`}
                  />
                ))}
              </div>
              <div className="flex flex-wrap gap-4 mt-4">
                {Object.entries(s.plans_distribution).map(([plan, count]) => (
                  <div key={plan} className="flex items-center gap-2">
                    <div className={`h-3 w-3 rounded-full ${planColors[plan] || "bg-gray-300"}`} />
                    <span className="text-sm capitalize">{plan}</span>
                    <span className="text-sm font-bold">{count}</span>
                    <span className="text-xs text-muted-foreground">({Math.round((count / totalSubs) * 100)}%)</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-muted-foreground">Aucun abonnement</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function cn(...classes: (string | undefined | false)[]) {
  return classes.filter(Boolean).join(" ");
}
