"use client";

import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function SiteDevicesPage() {
  const params = useParams();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Équipements</h1>
          <p className="text-muted-foreground">Gérez les équipements de ce site</p>
        </div>
        <Button>Ajouter un équipement</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Équipements connectés</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Connectez vos thermostats Nest, Netatmo ou compteurs Linky pour commencer.
          </p>
          <div className="mt-4 flex gap-2">
            <Button variant="outline" size="sm">Sync Nest</Button>
            <Button variant="outline" size="sm">Sync Netatmo</Button>
            <Button variant="outline" size="sm">Connecter Linky</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
