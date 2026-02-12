"use client";

import { useEffect, useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import EnergyChart from "@/components/dashboard/EnergyChart";
import { useEnergyStore } from "@/lib/stores/energyStore";
import { useSitesStore } from "@/lib/stores/sitesStore";
import { formatCurrency, formatKWh } from "@/lib/utils";

export default function EnergyPage() {
  const { sites } = useSitesStore();
  const { dailyAnalytics, forecasts, anomalies } = useEnergyStore();
  const [selectedSite, setSelectedSite] = useState<string>("");
  const loaded = useRef(false);

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;
    useSitesStore.getState().fetchSites();
  }, []);

  useEffect(() => {
    if (sites.length > 0 && !selectedSite) {
      setSelectedSite(sites[0].id);
    }
  }, [sites, selectedSite]);

  useEffect(() => {
    if (selectedSite) {
      const store = useEnergyStore.getState();
      store.fetchDailyAnalytics(selectedSite);
      store.fetchForecasts(selectedSite);
      store.fetchAnomalies(selectedSite);
    }
  }, [selectedSite]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Analyse Énergie</h1>
        <p className="text-muted-foreground">Consommation, prévisions et anomalies</p>
      </div>

      {sites.length > 0 && (
        <select
          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={selectedSite}
          onChange={(e) => setSelectedSite(e.target.value)}
        >
          {sites.map((site) => (
            <option key={site.id} value={site.id}>{site.name}</option>
          ))}
        </select>
      )}

      <Tabs defaultValue="consumption">
        <TabsList>
          <TabsTrigger value="consumption">Consommation</TabsTrigger>
          <TabsTrigger value="forecast">Prévisions</TabsTrigger>
          <TabsTrigger value="anomalies">Anomalies</TabsTrigger>
        </TabsList>

        <TabsContent value="consumption" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Consommation journalière</CardTitle>
            </CardHeader>
            <CardContent>
              <EnergyChart data={dailyAnalytics} />
            </CardContent>
          </Card>
          {dailyAnalytics.length > 0 && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <Card>
                <CardContent className="p-6">
                  <p className="text-sm text-muted-foreground">Total période</p>
                  <p className="text-2xl font-bold">
                    {formatKWh(dailyAnalytics.reduce((s, d) => s + d.total_kwh, 0))}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-6">
                  <p className="text-sm text-muted-foreground">Coût total</p>
                  <p className="text-2xl font-bold">
                    {formatCurrency(dailyAnalytics.reduce((s, d) => s + d.total_cost_eur, 0))}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-6">
                  <p className="text-sm text-muted-foreground">Pic de puissance</p>
                  <p className="text-2xl font-bold">
                    {Math.max(...dailyAnalytics.map((d) => d.peak_power_kw)).toFixed(1)} kW
                  </p>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="forecast" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Prévisions 48h</CardTitle>
            </CardHeader>
            <CardContent>
              {forecasts.length === 0 ? (
                <p className="py-8 text-center text-muted-foreground">
                  Aucune prévision disponible. Le modèle sera entraîné prochainement.
                </p>
              ) : (
                <div className="space-y-3">
                  {forecasts.map((f, i) => (
                    <div key={i} className="flex items-center justify-between rounded-lg border border-border p-3">
                      <span className="text-sm">{new Date(f.forecast_date).toLocaleString("fr-FR")}</span>
                      <span className="font-medium">{f.predicted_kwh.toFixed(1)} kWh</span>
                      <span className="text-muted-foreground">{formatCurrency(f.predicted_cost_eur)}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="anomalies" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Anomalies détectées</CardTitle>
            </CardHeader>
            <CardContent>
              {anomalies.length === 0 ? (
                <p className="py-8 text-center text-muted-foreground">
                  Aucune anomalie détectée récemment
                </p>
              ) : (
                <div className="space-y-3">
                  {anomalies.map((a, i) => (
                    <div key={i} className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-destructive">
                          +{a.deviation_pct.toFixed(0)}% au-dessus de la normale
                        </span>
                        <span className="text-sm text-muted-foreground">
                          {new Date(a.time).toLocaleString("fr-FR")}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        Consommation: {a.actual_kw.toFixed(1)} kW (attendu: {a.expected_kw.toFixed(1)} kW)
                      </p>
                      <p className="text-sm text-destructive">
                        Gaspillage estimé: {formatCurrency(a.estimated_waste_eur)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
