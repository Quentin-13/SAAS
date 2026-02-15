"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAdminStore } from "@/lib/stores/adminStore";

export default function AdminOrganizationsPage() {
  const { organizations, fetchOrganizations } = useAdminStore();
  const loaded = useRef(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;
    fetchOrganizations();
  }, [fetchOrganizations]);

  const handleSearch = () => {
    fetchOrganizations(1, search);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Organisations</h1>
        <p className="text-muted-foreground">
          {organizations?.total || 0} organisation{(organizations?.total || 0) > 1 ? "s" : ""}
        </p>
      </div>

      <div className="flex gap-3">
        <Input
          placeholder="Rechercher par nom..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="max-w-sm"
        />
        <Button onClick={handleSearch}>Rechercher</Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Nom</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Plan</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Statut</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Utilisateurs</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Sites</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Créé le</th>
                </tr>
              </thead>
              <tbody>
                {organizations?.items.map((org) => (
                  <tr key={org.id} className="border-b border-border last:border-0 hover:bg-accent/50">
                    <td className="px-4 py-3 font-medium">{org.name}</td>
                    <td className="px-4 py-3">
                      <Badge variant="outline" className="capitalize">{org.subscription_tier}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={org.subscription_status === "active" ? "default" : "destructive"}>
                        {org.subscription_status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">{org.user_count}</td>
                    <td className="px-4 py-3">{org.site_count}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(org.created_at).toLocaleDateString("fr-FR")}
                    </td>
                  </tr>
                ))}
                {(!organizations || organizations.items.length === 0) && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                      Aucune organisation trouvée
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {organizations && organizations.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          {Array.from({ length: organizations.pages }, (_, i) => i + 1).map((p) => (
            <Button
              key={p}
              variant={p === organizations.page ? "default" : "outline"}
              size="sm"
              onClick={() => fetchOrganizations(p, search)}
            >
              {p}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
