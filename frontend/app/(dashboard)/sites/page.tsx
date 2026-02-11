"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import SiteCard from "@/components/dashboard/SiteCard";
import { useSitesStore } from "@/lib/stores/sitesStore";

export default function SitesPage() {
  const { sites, isLoading, fetchSites } = useSitesStore();

  useEffect(() => {
    fetchSites();
  }, [fetchSites]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sites</h1>
          <p className="text-muted-foreground">Gérez vos bâtiments et équipements</p>
        </div>
        <Link href="/sites/new">
          <Button>Ajouter un site</Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : sites.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border p-12 text-center">
          <h3 className="text-lg font-semibold">Aucun site</h3>
          <p className="mt-2 text-muted-foreground">
            Commencez par ajouter votre premier bâtiment
          </p>
          <Link href="/sites/new">
            <Button className="mt-4">Ajouter un site</Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sites.map((site) => (
            <SiteCard key={site.id} site={site} />
          ))}
        </div>
      )}
    </div>
  );
}
