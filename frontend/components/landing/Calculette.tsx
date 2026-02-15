"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const TYPES_BATIMENT = [
  { value: "ehpad", label: "Ehpad / Santé", multiplicateur: 1.2 },
  { value: "hotel", label: "Hôtel", multiplicateur: 1.1 },
  { value: "bureaux", label: "Bureaux", multiplicateur: 1.0 },
];

const TARIF_KWH = 0.18;
const REDUCTION = 0.20;
const CONSO_BASE_MIN = 100; // kWh/m²/an
const CONSO_BASE_MAX = 150; // kWh/m²/an

export default function Calculette() {
  const [typeBatiment, setTypeBatiment] = useState("bureaux");
  const [surface, setSurface] = useState("");
  const [consoManuelle, setConsoManuelle] = useState("");
  const [resultat, setResultat] = useState<{
    econoMin: number;
    econoMax: number;
    roiMin: number;
    roiMax: number;
    co2: number;
  } | null>(null);

  const calculer = () => {
    const s = parseFloat(surface);
    if (!s || s <= 0) return;

    const type = TYPES_BATIMENT.find((t) => t.value === typeBatiment);
    const mult = type?.multiplicateur ?? 1;

    let consoMin: number;
    let consoMax: number;

    if (consoManuelle && parseFloat(consoManuelle) > 0) {
      const conso = parseFloat(consoManuelle);
      consoMin = conso;
      consoMax = conso;
    } else {
      consoMin = s * CONSO_BASE_MIN * mult;
      consoMax = s * CONSO_BASE_MAX * mult;
    }

    const econoMin = Math.round(consoMin * REDUCTION * TARIF_KWH);
    const econoMax = Math.round(consoMax * REDUCTION * TARIF_KWH);

    // ROI: coût abonnement ~200€/mois = 2400€/an
    const coutAnnuel = 2400;
    const roiMin = Math.round((coutAnnuel / econoMax) * 12);
    const roiMax = Math.round((coutAnnuel / econoMin) * 12);

    // CO2: ~0.06 kgCO2/kWh (France)
    const co2 = Math.round(((consoMin + consoMax) / 2) * REDUCTION * 0.06 / 1000);

    setResultat({ econoMin, econoMax, roiMin, roiMax, co2 });
  };

  return (
    <section className="px-6 py-20" id="calculette">
      <div className="mx-auto max-w-3xl">
        <h2 className="text-3xl font-bold text-center mb-2">
          Calculez vos économies en 30 secondes
        </h2>
        <p className="text-center text-muted-foreground mb-10">
          Estimation personnalisée basée sur votre type de bâtiment et surface
        </p>

        <Card className="border-primary/20">
          <CardHeader>
            <CardTitle className="text-xl">Simulateur d&apos;économies</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              {/* Type bâtiment */}
              <div className="space-y-2">
                <Label htmlFor="type-batiment">Type de bâtiment</Label>
                <select
                  id="type-batiment"
                  value={typeBatiment}
                  onChange={(e) => setTypeBatiment(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  {TYPES_BATIMENT.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Surface */}
              <div className="space-y-2">
                <Label htmlFor="surface">Surface (m²) *</Label>
                <Input
                  id="surface"
                  type="number"
                  placeholder="ex: 1500"
                  min={100}
                  value={surface}
                  onChange={(e) => setSurface(e.target.value)}
                />
              </div>

              {/* Conso optionnelle */}
              <div className="space-y-2">
                <Label htmlFor="conso">Conso annuelle kWh (optionnel)</Label>
                <Input
                  id="conso"
                  type="number"
                  placeholder="ex: 180000"
                  min={0}
                  value={consoManuelle}
                  onChange={(e) => setConsoManuelle(e.target.value)}
                />
              </div>
            </div>

            <Button onClick={calculer} size="lg" className="w-full md:w-auto">
              Calculer mes économies
            </Button>

            {resultat && (
              <div className="mt-8 rounded-xl bg-primary/10 border border-primary/20 p-6">
                <h3 className="text-lg font-semibold text-primary mb-4">
                  Résultats estimés
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <p className="text-3xl font-bold text-foreground">
                      {resultat.econoMin.toLocaleString("fr-FR")}–{resultat.econoMax.toLocaleString("fr-FR")} &euro;
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Économies estimées / an
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-3xl font-bold text-foreground">
                      {resultat.roiMin}–{resultat.roiMax} mois
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Retour sur investissement
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-3xl font-bold text-foreground">
                      {resultat.co2} tonnes
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Réduction CO₂ / an
                    </p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
