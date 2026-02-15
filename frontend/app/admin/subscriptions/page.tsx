"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAdminStore, type AdminSubscription } from "@/lib/stores/adminStore";
import { formatCurrency } from "@/lib/utils";

export default function AdminSubscriptionsPage() {
  const { subscriptions, fetchSubscriptions, updateSubscription } = useAdminStore();
  const loaded = useRef(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [editingSub, setEditingSub] = useState<AdminSubscription | null>(null);
  const [newPlan, setNewPlan] = useState("");

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;
    fetchSubscriptions();
  }, [fetchSubscriptions]);

  const handleCancel = async (sub: AdminSubscription) => {
    if (!confirm("Confirmer l'annulation de cet abonnement ?")) return;
    await updateSubscription(sub.id, { status: "cancelled" });
    fetchSubscriptions(subscriptions?.page || 1, statusFilter);
  };

  const handleReactivate = async (sub: AdminSubscription) => {
    await updateSubscription(sub.id, { status: "active" });
    fetchSubscriptions(subscriptions?.page || 1, statusFilter);
  };

  const handleChangePlan = async () => {
    if (!editingSub || !newPlan) return;
    await updateSubscription(editingSub.id, { plan: newPlan });
    setEditingSub(null);
    setNewPlan("");
    fetchSubscriptions(subscriptions?.page || 1, statusFilter);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Abonnements</h1>
        <p className="text-muted-foreground">
          {subscriptions?.total || 0} abonnement{(subscriptions?.total || 0) > 1 ? "s" : ""}
        </p>
      </div>

      <div className="flex gap-3">
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            fetchSubscriptions(1, e.target.value);
          }}
          className="rounded-md border border-border bg-background px-3 py-2 text-sm"
        >
          <option value="">Tous les statuts</option>
          <option value="active">Actif</option>
          <option value="cancelled">Annulé</option>
          <option value="expired">Expiré</option>
        </select>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Organisation</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Plan</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Statut</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Prix/mois</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Début</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Fin</th>
                  <th className="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {subscriptions?.items.map((sub) => (
                  <tr key={sub.id} className="border-b border-border last:border-0 hover:bg-accent/50">
                    <td className="px-4 py-3 font-medium">{sub.organization_name || sub.organization_id}</td>
                    <td className="px-4 py-3">
                      <Badge variant="outline" className="capitalize">{sub.plan}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={sub.status === "active" ? "default" : sub.status === "cancelled" ? "destructive" : "outline"}>
                        {sub.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">{sub.monthly_price_eur ? formatCurrency(sub.monthly_price_eur) : "-"}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(sub.start_date).toLocaleDateString("fr-FR")}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {sub.end_date ? new Date(sub.end_date).toLocaleDateString("fr-FR") : "-"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => { setEditingSub(sub); setNewPlan(sub.plan); }}
                        >
                          Changer plan
                        </Button>
                        {sub.status === "active" ? (
                          <Button variant="ghost" size="sm" onClick={() => handleCancel(sub)} className="text-destructive">
                            Annuler
                          </Button>
                        ) : (
                          <Button variant="ghost" size="sm" onClick={() => handleReactivate(sub)}>
                            Réactiver
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {(!subscriptions || subscriptions.items.length === 0) && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                      Aucun abonnement trouvé
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {subscriptions && subscriptions.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          {Array.from({ length: subscriptions.pages }, (_, i) => i + 1).map((p) => (
            <Button
              key={p}
              variant={p === subscriptions.page ? "default" : "outline"}
              size="sm"
              onClick={() => fetchSubscriptions(p, statusFilter)}
            >
              {p}
            </Button>
          ))}
        </div>
      )}

      {/* Change plan modal */}
      {editingSub && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Changer de plan</CardTitle>
              <p className="text-sm text-muted-foreground">{editingSub.organization_name}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <select
                value={newPlan}
                onChange={(e) => setNewPlan(e.target.value)}
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
              >
                <option value="free">Free (0 &euro;)</option>
                <option value="starter">Starter (100 &euro;/mois)</option>
                <option value="pro">Pro (200 &euro;/mois)</option>
                <option value="enterprise">Enterprise (500 &euro;/mois)</option>
              </select>
              <div className="flex gap-2">
                <Button onClick={handleChangePlan}>Confirmer</Button>
                <Button variant="outline" onClick={() => setEditingSub(null)}>Annuler</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
