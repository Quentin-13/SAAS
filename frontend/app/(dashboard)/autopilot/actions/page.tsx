"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDate, formatCurrency } from "@/lib/utils";
import type { AutopilotAction } from "@/lib/stores/energyStore";
import api from "@/lib/api";

export default function ActionsDetailPage() {
  const [actions, setActions] = useState<AutopilotAction[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.get("/autopilot/actions?limit=50")
      .then((res) => setActions(res.data))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Historique des actions</h1>
        <p className="text-muted-foreground">Détail complet des actions autopilot</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : (
        <div className="space-y-4">
          {actions.map((action) => (
            <Card key={action.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{action.action_type.replace(/_/g, " ")}</span>
                      <Badge variant={action.status === "executed" ? "default" : "destructive"}>
                        {action.status}
                      </Badge>
                    </div>
                    {action.reasoning && (
                      <p className="mt-2 text-sm text-muted-foreground">{action.reasoning}</p>
                    )}
                  </div>
                  <div className="text-right text-sm">
                    <p>{formatDate(action.created_at)}</p>
                    {action.predicted_savings_eur && (
                      <p className="text-green-500">
                        {formatCurrency(action.predicted_savings_eur)} estimés
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
