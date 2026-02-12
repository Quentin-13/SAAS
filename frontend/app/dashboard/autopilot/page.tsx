"use client";

import { useEffect, useState, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import ActionsFeed from "@/components/dashboard/ActionsFeed";
import { useSitesStore } from "@/lib/stores/sitesStore";
import { type AutopilotAction } from "@/lib/stores/energyStore";
import { isDemoMode, getDemoDashboardOverview } from "@/lib/demo";
import api from "@/lib/api";

interface SiteAutopilotConfig {
  siteId: string;
  temp_min: number;
  temp_max: number;
  eco_temp: number;
  frost_protection_temp: number;
  priority: "comfort" | "savings" | "balanced";
  schedule_enabled: boolean;
  schedule_eco_start: string;
  schedule_eco_end: string;
  weekend_mode: boolean;
  max_actions_per_hour: number;
  humidity_control: boolean;
  humidity_min: number;
  humidity_max: number;
}

const defaultConfig: Omit<SiteAutopilotConfig, "siteId"> = {
  temp_min: 19,
  temp_max: 22,
  eco_temp: 17,
  frost_protection_temp: 7,
  priority: "balanced",
  schedule_enabled: true,
  schedule_eco_start: "22:00",
  schedule_eco_end: "06:00",
  weekend_mode: false,
  max_actions_per_hour: 4,
  humidity_control: false,
  humidity_min: 30,
  humidity_max: 60,
};

export default function AutopilotPage() {
  const { sites, fetchSites } = useSitesStore();
  const [actions, setActions] = useState<AutopilotAction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const loaded = useRef(false);
  const [selectedSite, setSelectedSite] = useState<string | null>(null);
  const [configs, setConfigs] = useState<Record<string, SiteAutopilotConfig>>({});
  const [savedFeedback, setSavedFeedback] = useState<string | null>(null);

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;

    fetchSites();
    loadActions();
  }, [fetchSites]);

  useEffect(() => {
    if (sites.length > 0 && !selectedSite) {
      setSelectedSite(sites[0].id);
    }
    // Initialize configs for all sites
    const newConfigs: Record<string, SiteAutopilotConfig> = {};
    for (const site of sites) {
      if (!configs[site.id]) {
        newConfigs[site.id] = { siteId: site.id, ...defaultConfig };
      }
    }
    if (Object.keys(newConfigs).length > 0) {
      setConfigs((prev) => ({ ...prev, ...newConfigs }));
    }
  }, [sites, selectedSite, configs]);

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

  const currentConfig = selectedSite ? configs[selectedSite] : null;

  const updateConfig = (field: keyof SiteAutopilotConfig, value: unknown) => {
    if (!selectedSite) return;
    setConfigs((prev) => ({
      ...prev,
      [selectedSite]: { ...prev[selectedSite], [field]: value },
    }));
  };

  const handleSaveConfig = () => {
    setSavedFeedback(selectedSite);
    setTimeout(() => setSavedFeedback(null), 2000);
  };

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
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Site list */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-base">Vos sites</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {sites.map((site) => (
                  <button
                    key={site.id}
                    onClick={() => setSelectedSite(site.id)}
                    className={`w-full flex items-center justify-between rounded-lg border p-3 text-left transition ${
                      selectedSite === site.id
                        ? "border-primary bg-primary/5"
                        : "border-border hover:bg-accent"
                    }`}
                  >
                    <div>
                      <p className="font-medium text-sm">{site.name}</p>
                      <p className="text-xs text-muted-foreground">{site.city}</p>
                    </div>
                    <Badge variant={site.autopilot_enabled ? "default" : "outline"} className="text-xs">
                      {site.autopilot_enabled ? "Actif" : "Inactif"}
                    </Badge>
                  </button>
                ))}
                {sites.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    Aucun site configuré
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Advanced config form */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Configuration avancée</CardTitle>
                <CardDescription>
                  {selectedSite
                    ? `Paramètres de l'autopilot pour ${sites.find((s) => s.id === selectedSite)?.name || "ce site"}`
                    : "Sélectionnez un site pour configurer l'autopilot"}
                </CardDescription>
              </CardHeader>
              {currentConfig && (
                <CardContent className="space-y-6">
                  {/* Priority mode */}
                  <div>
                    <Label className="text-sm font-semibold mb-3 block">Mode de priorité</Label>
                    <div className="grid grid-cols-3 gap-3">
                      {(["comfort", "balanced", "savings"] as const).map((mode) => (
                        <button
                          key={mode}
                          onClick={() => updateConfig("priority", mode)}
                          className={`rounded-lg border p-3 text-center transition ${
                            currentConfig.priority === mode
                              ? "border-primary bg-primary/10 text-primary"
                              : "border-border hover:bg-accent"
                          }`}
                        >
                          <p className="text-2xl mb-1">
                            {mode === "comfort" ? "🏠" : mode === "balanced" ? "⚖️" : "💰"}
                          </p>
                          <p className="text-xs font-medium">
                            {mode === "comfort" ? "Confort" : mode === "balanced" ? "Équilibré" : "Économies max"}
                          </p>
                        </button>
                      ))}
                    </div>
                  </div>

                  <Separator />

                  {/* Temperature constraints */}
                  <div>
                    <Label className="text-sm font-semibold mb-3 block">Contraintes de température</Label>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-xs text-muted-foreground">Température min. confort</Label>
                        <div className="flex items-center gap-2">
                          <Input
                            type="number"
                            step="0.5"
                            min="10"
                            max="30"
                            value={currentConfig.temp_min}
                            onChange={(e) => updateConfig("temp_min", parseFloat(e.target.value))}
                          />
                          <span className="text-sm text-muted-foreground">°C</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs text-muted-foreground">Température max. confort</Label>
                        <div className="flex items-center gap-2">
                          <Input
                            type="number"
                            step="0.5"
                            min="10"
                            max="35"
                            value={currentConfig.temp_max}
                            onChange={(e) => updateConfig("temp_max", parseFloat(e.target.value))}
                          />
                          <span className="text-sm text-muted-foreground">°C</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs text-muted-foreground">Température mode éco</Label>
                        <div className="flex items-center gap-2">
                          <Input
                            type="number"
                            step="0.5"
                            min="5"
                            max="25"
                            value={currentConfig.eco_temp}
                            onChange={(e) => updateConfig("eco_temp", parseFloat(e.target.value))}
                          />
                          <span className="text-sm text-muted-foreground">°C</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs text-muted-foreground">Protection antigel</Label>
                        <div className="flex items-center gap-2">
                          <Input
                            type="number"
                            step="0.5"
                            min="0"
                            max="15"
                            value={currentConfig.frost_protection_temp}
                            onChange={(e) => updateConfig("frost_protection_temp", parseFloat(e.target.value))}
                          />
                          <span className="text-sm text-muted-foreground">°C</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* Schedule */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <Label className="text-sm font-semibold">Plages horaires éco</Label>
                      <Switch
                        checked={currentConfig.schedule_enabled}
                        onCheckedChange={(v) => updateConfig("schedule_enabled", v)}
                      />
                    </div>
                    {currentConfig.schedule_enabled && (
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label className="text-xs text-muted-foreground">Début mode éco</Label>
                            <Input
                              type="time"
                              value={currentConfig.schedule_eco_start}
                              onChange={(e) => updateConfig("schedule_eco_start", e.target.value)}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label className="text-xs text-muted-foreground">Fin mode éco</Label>
                            <Input
                              type="time"
                              value={currentConfig.schedule_eco_end}
                              onChange={(e) => updateConfig("schedule_eco_end", e.target.value)}
                            />
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium">Mode week-end</p>
                            <p className="text-xs text-muted-foreground">
                              Appliquer le mode éco toute la journée le week-end
                            </p>
                          </div>
                          <Switch
                            checked={currentConfig.weekend_mode}
                            onCheckedChange={(v) => updateConfig("weekend_mode", v)}
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  <Separator />

                  {/* Humidity control */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <Label className="text-sm font-semibold">Contrôle d&apos;humidité</Label>
                      <Switch
                        checked={currentConfig.humidity_control}
                        onCheckedChange={(v) => updateConfig("humidity_control", v)}
                      />
                    </div>
                    {currentConfig.humidity_control && (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label className="text-xs text-muted-foreground">Humidité minimale</Label>
                          <div className="flex items-center gap-2">
                            <Input
                              type="number"
                              min="0"
                              max="100"
                              value={currentConfig.humidity_min}
                              onChange={(e) => updateConfig("humidity_min", parseInt(e.target.value))}
                            />
                            <span className="text-sm text-muted-foreground">%</span>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label className="text-xs text-muted-foreground">Humidité maximale</Label>
                          <div className="flex items-center gap-2">
                            <Input
                              type="number"
                              min="0"
                              max="100"
                              value={currentConfig.humidity_max}
                              onChange={(e) => updateConfig("humidity_max", parseInt(e.target.value))}
                            />
                            <span className="text-sm text-muted-foreground">%</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  <Separator />

                  {/* Actions limit */}
                  <div className="space-y-2">
                    <Label className="text-sm font-semibold">Actions max par heure</Label>
                    <p className="text-xs text-muted-foreground mb-2">
                      Limite le nombre d&apos;ajustements que l&apos;autopilot peut faire par heure
                    </p>
                    <Input
                      type="number"
                      min="1"
                      max="12"
                      value={currentConfig.max_actions_per_hour}
                      onChange={(e) => updateConfig("max_actions_per_hour", parseInt(e.target.value))}
                      className="w-24"
                    />
                  </div>

                  <div className="flex items-center gap-3 pt-2">
                    <Button onClick={handleSaveConfig}>
                      Sauvegarder la configuration
                    </Button>
                    {savedFeedback === selectedSite && (
                      <span className="text-sm text-green-600 font-medium">
                        Configuration sauvegardée
                      </span>
                    )}
                  </div>
                </CardContent>
              )}
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
