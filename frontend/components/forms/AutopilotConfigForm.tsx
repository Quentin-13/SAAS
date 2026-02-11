"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface AutopilotConfigFormProps {
  siteId?: string;
  initialConfig?: {
    temp_min: number;
    temp_max: number;
    eco_temp: number;
    frost_protection_temp: number;
  };
  onSubmit?: (config: Record<string, number>) => Promise<void>;
}

export default function AutopilotConfigForm({ initialConfig, onSubmit }: AutopilotConfigFormProps) {
  const [config, setConfig] = useState({
    temp_min: initialConfig?.temp_min ?? 19,
    temp_max: initialConfig?.temp_max ?? 22,
    eco_temp: initialConfig?.eco_temp ?? 17,
    frost_protection_temp: initialConfig?.frost_protection_temp ?? 16,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit?.(config);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Température minimale de confort</Label>
          <div className="flex items-center gap-2">
            <Input type="number" step="0.5" value={config.temp_min} onChange={(e) => setConfig({ ...config, temp_min: parseFloat(e.target.value) })} />
            <span className="text-sm text-muted-foreground">°C</span>
          </div>
        </div>
        <div className="space-y-2">
          <Label>Température maximale de confort</Label>
          <div className="flex items-center gap-2">
            <Input type="number" step="0.5" value={config.temp_max} onChange={(e) => setConfig({ ...config, temp_max: parseFloat(e.target.value) })} />
            <span className="text-sm text-muted-foreground">°C</span>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Température mode éco</Label>
          <div className="flex items-center gap-2">
            <Input type="number" step="0.5" value={config.eco_temp} onChange={(e) => setConfig({ ...config, eco_temp: parseFloat(e.target.value) })} />
            <span className="text-sm text-muted-foreground">°C</span>
          </div>
        </div>
        <div className="space-y-2">
          <Label>Protection antigel</Label>
          <div className="flex items-center gap-2">
            <Input type="number" step="0.5" value={config.frost_protection_temp} onChange={(e) => setConfig({ ...config, frost_protection_temp: parseFloat(e.target.value) })} />
            <span className="text-sm text-muted-foreground">°C</span>
          </div>
        </div>
      </div>
      <Button type="submit">Sauvegarder la configuration</Button>
    </form>
  );
}
