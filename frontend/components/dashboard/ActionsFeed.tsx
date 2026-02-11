"use client";

import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import type { AutopilotAction } from "@/lib/stores/energyStore";

interface ActionsFeedProps {
  actions: AutopilotAction[];
}

const actionTypeLabels: Record<string, string> = {
  temperature_adjustment: "Ajustement température",
  mode_change: "Changement de mode",
  schedule_override: "Override planning",
  equipment_shutdown: "Arrêt équipement",
  load_shedding: "Délestage",
};

const statusColors: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  executed: "default",
  pending: "secondary",
  failed: "destructive",
  rolled_back: "outline",
};

export default function ActionsFeed({ actions }: ActionsFeedProps) {
  if (!actions || actions.length === 0) {
    return (
      <div className="py-8 text-center text-muted-foreground">
        Aucune action récente
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {actions.map((action) => (
        <div key={action.id} className="flex items-start gap-4 rounded-lg border border-border p-4">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="font-medium">
                {actionTypeLabels[action.action_type] || action.action_type}
              </span>
              <Badge variant={statusColors[action.status] || "secondary"}>
                {action.status}
              </Badge>
            </div>
            {action.reasoning && (
              <p className="mt-1 text-sm text-muted-foreground">{action.reasoning}</p>
            )}
            <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
              <span>{formatDate(action.created_at)}</span>
              {action.predicted_savings_eur && (
                <span className="text-green-500">
                  +{action.predicted_savings_eur.toFixed(2)} EUR estimés
                </span>
              )}
              {action.confidence_score && (
                <span>Confiance: {(action.confidence_score * 100).toFixed(0)}%</span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
