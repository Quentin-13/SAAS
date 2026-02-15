"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAdminStore } from "@/lib/stores/adminStore";

const actionColors: Record<string, string> = {
  "user.update": "default",
  "subscription.update": "outline",
  "organization.create": "default",
  "organization.delete": "destructive",
};

export default function AdminLogsPage() {
  const { logs, fetchLogs } = useAdminStore();
  const loaded = useRef(false);
  const [actionFilter, setActionFilter] = useState("");

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;
    fetchLogs();
  }, [fetchLogs]);

  const handleSearch = () => {
    fetchLogs(1, actionFilter);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Logs d&apos;activité</h1>
        <p className="text-muted-foreground">Historique des actions admin</p>
      </div>

      <div className="flex gap-3">
        <Input
          placeholder="Filtrer par action (ex: user.update)..."
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="max-w-sm"
        />
        <Button onClick={handleSearch}>Filtrer</Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Date</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Admin</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Action</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Cible</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Détails</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">IP</th>
                </tr>
              </thead>
              <tbody>
                {logs?.items.map((log) => (
                  <tr key={log.id} className="border-b border-border last:border-0 hover:bg-accent/50">
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString("fr-FR")}
                    </td>
                    <td className="px-4 py-3">{log.user_email || "-"}</td>
                    <td className="px-4 py-3">
                      <Badge variant={(actionColors[log.action] as "default" | "outline" | "destructive") || "outline"}>
                        {log.action}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {log.target_type ? `${log.target_type}` : "-"}
                      {log.target_id && <span className="text-xs ml-1">({log.target_id.slice(0, 8)}...)</span>}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground max-w-xs truncate">{log.details || "-"}</td>
                    <td className="px-4 py-3 text-muted-foreground">{log.ip_address || "-"}</td>
                  </tr>
                ))}
                {(!logs || logs.items.length === 0) && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                      Aucun log trouvé
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {logs && logs.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          {Array.from({ length: Math.min(logs.pages, 10) }, (_, i) => i + 1).map((p) => (
            <Button
              key={p}
              variant={p === logs.page ? "default" : "outline"}
              size="sm"
              onClick={() => fetchLogs(p, actionFilter)}
            >
              {p}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
