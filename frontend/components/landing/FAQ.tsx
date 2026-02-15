"use client";

import { useState } from "react";

const faqs = [
  {
    question: "Ai-je besoin d\u2019installer du matériel supplémentaire ?",
    answer:
      "Non, si vous disposez déjà de thermostats connectés (Nest, Netatmo, etc.) et d\u2019un compteur Linky. Energy Autopilot se connecte à vos équipements existants via API, sans intervention physique.",
  },
  {
    question: "Comment fonctionne la déclaration OPERAT ?",
    answer:
      "Notre plateforme collecte automatiquement vos données de consommation et génère le rapport conforme au format OPERAT en 1 clic. Vous n\u2019avez plus qu\u2019à le télécharger et le soumettre.",
  },
  {
    question: "Quel est le délai pour voir des résultats ?",
    answer:
      "Les premières optimisations sont visibles dès la 1ère semaine. Les économies significatives (15-25 %) se confirment généralement après 2 à 3 mois de pilotage, le temps que l\u2019IA apprenne vos patterns d\u2019occupation.",
  },
  {
    question: "Est-ce que le confort des occupants est impacté ?",
    answer:
      "Non. L\u2019autopilot respecte vos contraintes de confort (plages de température, horaires). Il optimise les périodes d\u2019inoccupation, les heures creuses et le pré-chauffage intelligent. Nos clients rapportent même +15 % de satisfaction occupant.",
  },
];

export default function FAQ() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section className="px-6 py-20 bg-card/50" id="faq">
      <div className="mx-auto max-w-3xl">
        <h2 className="text-3xl font-bold text-center mb-10">
          Questions fréquentes
        </h2>

        <div className="space-y-4">
          {faqs.map((faq, i) => (
            <div
              key={i}
              className="rounded-xl border border-border overflow-hidden"
            >
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="flex w-full items-center justify-between p-5 text-left hover:bg-accent/50 transition cursor-pointer"
              >
                <span className="font-medium text-foreground pr-4">
                  {faq.question}
                </span>
                <svg
                  className={`h-5 w-5 shrink-0 text-muted-foreground transition-transform ${
                    open === i ? "rotate-180" : ""
                  }`}
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                </svg>
              </button>
              {open === i && (
                <div className="px-5 pb-5 text-muted-foreground">
                  {faq.answer}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
