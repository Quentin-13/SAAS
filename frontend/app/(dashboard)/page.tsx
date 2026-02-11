"use client";

import { useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import MetricCard from "@/components/dashboard/MetricCard";
import EnergyChart from "@/components/dashboard/EnergyChart";
import ActionsFeed from "@/components/dashboard/ActionsFeed";
import { useEnergyStore } from "@/lib/stores/energyStore";
import { formatCurrency, formatKWh, formatCO2 } from "@/lib/utils";

export default function DashboardPage() {
  const { dashboardOverview, isLoading, fetchDashboardOverview } = useEnergyStore();

  useEffect(() => {
    fetchDashboardOverview();
  }, [fetchDashboardOverview]);

  if (isLoading && !dashboardOverview) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  const overview = dashboardOverview || {
    total_savings_eur: 0,
    total_savings_pct: 0,
    total_kwh_saved: 0,
    co2_avoided_kg: 0,
    actions_count: 0,
    active_sites: 0,
    active_devices: 0,
    daily_consumption: [],
    recent_actions: [],
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Vue d&apos;ensemble de votre consommation énergétique</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Économies ce mois"
          value={formatCurrency(overview.total_savings_eur)}
          change={`${overview.total_savings_pct.toFixed(1)}%`}
          trend="up"
        />
        <MetricCard
          title="kWh économisés"
          value={formatKWh(overview.total_kwh_saved)}
          trend="down"
          subtitle="vs baseline"
        />
        <MetricCard
          title="CO2 évité"
          value={formatCO2(overview.co2_avoided_kg)}
          trend="up"
        />
        <MetricCard
          title="Actions Autopilot"
          value={String(overview.actions_count)}
          subtitle="cette semaine"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Consommation énergétique</CardTitle>
        </CardHeader>
        <CardContent>
          <EnergyChart data={overview.daily_consumption} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Actions Autopilot récentes</CardTitle>
        </CardHeader>
        <CardContent>
          <ActionsFeed actions={overview.recent_actions} />
        </CardContent>
      </Card>
    </div>
  );
}
