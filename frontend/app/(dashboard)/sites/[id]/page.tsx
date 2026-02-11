"use client";

import { useEffect } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { useSitesStore } from "@/lib/stores/sitesStore";

export default function SiteDetailPage() {
  const params = useParams();
  const siteId = params.id as string;
  const { currentSite, isLoading, fetchSite, toggleAutopilot } = useSitesStore();

  useEffect(() => {
    fetchSite(siteId);
  }, [siteId, fetchSite]);

  if (isLoading || !currentSite) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">{currentSite.name}</h1>
          <p className="text-muted-foreground">
            {currentSite.address && `${currentSite.address}, `}
            {currentSite.city}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Autopilot</span>
            <Switch
              checked={currentSite.autopilot_enabled}
              onCheckedChange={(checked) => toggleAutopilot(siteId, checked)}
            />
          </div>
          <Badge variant={currentSite.autopilot_enabled ? "default" : "outline"}>
            {currentSite.autopilot_enabled ? "Actif" : "Inactif"}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Surface</p>
            <p className="text-2xl font-bold">{currentSite.surface_area || "-"} m²</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Type</p>
            <p className="text-2xl font-bold capitalize">{currentSite.building_type || "-"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Pays</p>
            <p className="text-2xl font-bold">{currentSite.country}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Équipements</CardTitle>
          <Button size="sm">Ajouter un équipement</Button>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Les équipements connectés à ce site apparaîtront ici.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
