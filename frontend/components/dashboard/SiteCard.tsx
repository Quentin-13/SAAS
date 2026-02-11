"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Site } from "@/lib/stores/sitesStore";

interface SiteCardProps {
  site: Site;
}

const buildingTypeLabels: Record<string, string> = {
  office: "Bureau",
  retail: "Commerce",
  warehouse: "Entrepôt",
  hotel: "Hôtel",
  restaurant: "Restaurant",
};

export default function SiteCard({ site }: SiteCardProps) {
  return (
    <Link href={`/sites/${site.id}`}>
      <Card className="hover:border-primary/50 transition-colors cursor-pointer">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold">{site.name}</h3>
              <p className="text-sm text-muted-foreground">
                {site.address ? `${site.address}, ` : ""}
                {site.city || ""}
              </p>
            </div>
            <Badge variant={site.autopilot_enabled ? "default" : "outline"}>
              {site.autopilot_enabled ? "Autopilot ON" : "Autopilot OFF"}
            </Badge>
          </div>
          <div className="mt-4 flex items-center gap-4 text-sm text-muted-foreground">
            {site.building_type && (
              <span>{buildingTypeLabels[site.building_type] || site.building_type}</span>
            )}
            {site.surface_area && <span>{site.surface_area} m²</span>}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
