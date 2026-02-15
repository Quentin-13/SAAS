"use client";

import { Card, CardContent } from "@/components/ui/card";

const temoignages = [
  {
    titre: "Hôtel indépendant Toulouse",
    detail: "80 chambres",
    texte:
      "–19 % sur chauffage/clim en 3 mois, sans changer d\u2019équipements. Économies 12 500 \u20AC/an.",
    stat: "–19 %",
    statLabel: "chauffage/clim",
    note: "Anonymisé",
    icon: (
      <svg className="h-10 w-10 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3H21m-3.75 3H21" />
      </svg>
    ),
  },
  {
    titre: "Ehpad PME",
    detail: "1 800 m²",
    texte:
      "–22 % conso globale, déclaration OPERAT simplifiée. ROI < 9 mois.",
    citation: "Enfin serein pour 2030 !",
    stat: "–22 %",
    statLabel: "conso globale",
    icon: (
      <svg className="h-10 w-10 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 21v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21m0 0h4.5V3.545M12.75 21h7.5V10.75M2.25 21h1.5m18 0h-18M2.25 9l4.5-1.636M18.75 3l-1.5.545m0 6.205l3 1m1.5.5l-1.5-.5M6.75 7.364V3h-3v18m3-13.636l10.5-3.819" />
      </svg>
    ),
  },
  {
    titre: "Bureaux PME",
    detail: "2 200 m²",
    texte: "–17 % en hiver, alerte gel évitée.",
    stat: "+15 %",
    statLabel: "confort occupant",
    icon: (
      <svg className="h-10 w-10 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
      </svg>
    ),
  },
];

const logos = [
  { name: "Enedis", label: "compatible" },
  { name: "Netatmo", label: "compatible" },
  { name: "Google Nest", label: "compatible" },
  { name: "ADEME", label: "conforme" },
];

export default function Testimonials() {
  return (
    <section className="px-6 py-20" id="preuves">
      <div className="mx-auto max-w-7xl">
        <h2 className="text-3xl font-bold text-center mb-2">
          Ils économisent déjà avec Energy Autopilot
        </h2>
        <p className="text-center text-muted-foreground mb-12">
          Résultats réels sur des bâtiments tertiaires PME en Occitanie
        </p>

        {/* Témoignages */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {temoignages.map((t, i) => (
            <Card key={i} className="relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-primary/50" />
              <CardContent className="p-6 pt-8">
                <div className="flex items-start gap-4 mb-4">
                  <div className="shrink-0 rounded-lg bg-primary/10 p-3">
                    {t.icon}
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{t.titre}</h3>
                    <p className="text-sm text-muted-foreground">{t.detail}</p>
                  </div>
                </div>

                <p className="text-foreground mb-4">{t.texte}</p>

                {t.citation && (
                  <blockquote className="border-l-2 border-primary pl-4 italic text-muted-foreground mb-4">
                    &laquo; {t.citation} &raquo;
                  </blockquote>
                )}

                <div className="flex items-center gap-3 rounded-lg bg-primary/5 p-3">
                  <span className="text-2xl font-bold text-primary">{t.stat}</span>
                  <span className="text-sm text-muted-foreground">{t.statLabel}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Logos partenaires */}
        <div className="text-center">
          <p className="text-sm text-muted-foreground mb-6 uppercase tracking-wider">
            Compatible avec vos équipements
          </p>
          <div className="flex flex-wrap items-center justify-center gap-8">
            {logos.map((logo) => (
              <div
                key={logo.name}
                className="flex flex-col items-center gap-1 opacity-70 hover:opacity-100 transition"
              >
                <div className="h-12 w-28 rounded-lg border border-border bg-card flex items-center justify-center text-sm font-semibold text-foreground">
                  {logo.name}
                </div>
                <span className="text-xs text-muted-foreground">{logo.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
