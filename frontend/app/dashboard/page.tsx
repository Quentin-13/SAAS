"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import MetricCard from "@/components/dashboard/MetricCard";
import EnergyChart from "@/components/dashboard/EnergyChart";
import ActionsFeed from "@/components/dashboard/ActionsFeed";
import { useEnergyStore } from "@/lib/stores/energyStore";
import { formatCurrency, formatKWh, formatCO2 } from "@/lib/utils";

export default function DashboardPage() {
  const { dashboardOverview, isLoading } = useEnergyStore();
  const loaded = useRef(false);
  const [showGuide, setShowGuide] = useState(false);

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;
    useEnergyStore.getState().fetchDashboardOverview();
  }, []);

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Vue d&apos;ensemble de votre consommation énergétique</p>
        </div>
        <button
          onClick={() => setShowGuide(!showGuide)}
          className="flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-accent transition"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" />
          </svg>
          Comment ça marche
        </button>
      </div>

      {showGuide && (
        <Card className="border-primary/20 bg-primary/5">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Comment utiliser votre dashboard</CardTitle>
              <button onClick={() => setShowGuide(false)} className="text-muted-foreground hover:text-foreground">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">1</span>
                  <h4 className="font-semibold text-sm">Ajoutez vos sites</h4>
                </div>
                <p className="text-xs text-muted-foreground">
                  Allez dans &quot;Sites&quot; pour ajouter vos bâtiments avec leur adresse et surface. Connectez ensuite vos équipements (Linky, Nest, Netatmo).
                </p>
              </div>
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">2</span>
                  <h4 className="font-semibold text-sm">Activez l&apos;Autopilot</h4>
                </div>
                <p className="text-xs text-muted-foreground">
                  Sur chaque site, activez l&apos;autopilot. Configurez vos contraintes de confort (températures min/max, plages horaires, priorités).
                </p>
              </div>
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">3</span>
                  <h4 className="font-semibold text-sm">Suivez l&apos;énergie</h4>
                </div>
                <p className="text-xs text-muted-foreground">
                  L&apos;onglet &quot;Énergie&quot; affiche votre consommation, les prévisions IA et les anomalies détectées. Analysez par site ou globalement.
                </p>
              </div>
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">4</span>
                  <h4 className="font-semibold text-sm">Économisez</h4>
                </div>
                <p className="text-xs text-muted-foreground">
                  Les cartes ci-dessous résument vos économies. L&apos;autopilot agit automatiquement et vous pouvez suivre chaque action en temps réel.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

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
