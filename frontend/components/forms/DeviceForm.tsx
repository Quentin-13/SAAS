"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface DeviceFormProps {
  siteId: string;
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  isLoading?: boolean;
}

export default function DeviceForm({ siteId, onSubmit, isLoading }: DeviceFormProps) {
  const [formData, setFormData] = useState({
    name: "",
    device_type: "thermostat",
    brand: "generic",
    is_controllable: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({ ...formData, site_id: siteId });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="device-name">Nom de l&apos;équipement</Label>
        <Input id="device-name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Type</Label>
          <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={formData.device_type} onChange={(e) => setFormData({ ...formData, device_type: e.target.value })}>
            <option value="thermostat">Thermostat</option>
            <option value="meter">Compteur</option>
            <option value="hvac">HVAC</option>
            <option value="water_heater">Chauffe-eau</option>
            <option value="lighting">Éclairage</option>
          </select>
        </div>
        <div className="space-y-2">
          <Label>Marque</Label>
          <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={formData.brand} onChange={(e) => setFormData({ ...formData, brand: e.target.value })}>
            <option value="generic">Générique</option>
            <option value="nest">Nest</option>
            <option value="netatmo">Netatmo</option>
            <option value="linky">Linky</option>
          </select>
        </div>
      </div>
      <Button type="submit" disabled={isLoading}>
        {isLoading ? "Ajout..." : "Ajouter l'équipement"}
      </Button>
    </form>
  );
}
