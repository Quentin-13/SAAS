"use client";

import { useEffect, useState, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import ActionsFeed from "@/components/dashboard/ActionsFeed";
import { useSitesStore } from "@/lib/stores/sitesStore";
import { type AutopilotAction } from "@/lib/stores/energyStore";
import { isDemoMode, getDemoDashboardOverview } from "@/lib/demo";
import api from "@/lib/api";

export default function AutopilotPage() {
  const { sites, fetchSites } = useSitesStore();
  const [actions, setActions] = useState<AutopilotAction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const loaded = useRef(false);

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;

    fetchSites();
    loadActions();
  }, [fetchSites]);

  const loadActions = async () => {
    if (isDemoMode()) {
      const overview = getDemoDashboardOverview();
      setActions(overview.recent_actions);
      setIsLoading(false);
      return;
    }
    try {
      const response = await api.get("/autopilot/actions");
      setActions(response.data);
    } catch {
      // API not available
    } finally {
      setIsLoading(false);
    }
  };

  const activeSites = sites.filter((s) => s.autopilot_enabled);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Autopilot</h1>
        <p className="text-muted-foreground">
          Configuration et historique des actions automatiques
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Sites avec Autopilot</p>
            <p className="text-2xl font-bold">{activeSites.length} / {sites.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Actions cette semaine</p>
            <p className="text-2xl font-bold">{actions.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Taux de succès</p>
            <p className="text-2xl font-bold">
              {actions.length > 0
                ? `${((actions.filter((a) => a.status === "executed").length / actions.length) * 100).toFixed(0)}%`
                : "-"}
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="history">
        <TabsList>
          <TabsTrigger value="history">Historique</TabsTrigger>
          <TabsTrigger value="config">Configuration</TabsTrigger>
        </TabsList>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Actions récentes</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex justify-center py-8">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                </div>
              ) : (
                <ActionsFeed actions={actions} />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="config">
          <Card>
            <CardHeader>
              <CardTitle>Contraintes de confort</CardTitle>
              <CardDescription>
                Définissez les limites que l&apos;autopilot doit respecter
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {sites.map((site) => (
                <div key={site.id} className="flex items-center justify-between rounded-lg border border-border p-4">
                  <div>
                    <p className="font-medium">{site.name}</p>
                    <p className="text-sm text-muted-foreground">{site.city}</p>
                  </div>
                  <Badge variant={site.autopilot_enabled ? "default" : "outline"}>
                    {site.autopilot_enabled ? "Actif" : "Inactif"}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
