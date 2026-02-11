"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useSitesStore } from "@/lib/stores/sitesStore";

export default function NewSitePage() {
  const router = useRouter();
  const { createSite } = useSitesStore();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    address: "",
    postal_code: "",
    city: "",
    surface_area: "",
    building_type: "office",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await createSite({
        ...formData,
        surface_area: formData.surface_area ? parseInt(formData.surface_area) : undefined,
      });
      router.push("/sites");
    } catch {
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Ajouter un site</h1>
        <p className="text-muted-foreground">Enregistrez un nouveau bâtiment</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Informations du site</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nom du site</Label>
              <Input
                id="name"
                placeholder="Bureau Paris 11e"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="address">Adresse</Label>
              <Input
                id="address"
                placeholder="123 Rue de la République"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="postal_code">Code postal</Label>
                <Input
                  id="postal_code"
                  placeholder="75011"
                  value={formData.postal_code}
                  onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="city">Ville</Label>
                <Input
                  id="city"
                  placeholder="Paris"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="surface_area">Surface (m²)</Label>
                <Input
                  id="surface_area"
                  type="number"
                  placeholder="1200"
                  value={formData.surface_area}
                  onChange={(e) => setFormData({ ...formData, surface_area: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="building_type">Type de bâtiment</Label>
                <select
                  id="building_type"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={formData.building_type}
                  onChange={(e) => setFormData({ ...formData, building_type: e.target.value })}
                >
                  <option value="office">Bureau</option>
                  <option value="retail">Commerce</option>
                  <option value="warehouse">Entrepôt</option>
                  <option value="hotel">Hôtel</option>
                  <option value="restaurant">Restaurant</option>
                </select>
              </div>
            </div>
            <div className="flex gap-4 pt-4">
              <Button type="submit" disabled={isLoading}>
                {isLoading ? "Création..." : "Créer le site"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Annuler
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
