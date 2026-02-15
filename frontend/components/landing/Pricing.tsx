"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

const plans = [
  {
    name: "Starter",
    price: "99",
    period: "/mois",
    description: "Pour un site unique < 1 000 m²",
    features: [
      "1 site connecté",
      "Jusqu\u2019à 5 appareils",
      "Optimisation toutes les 15 min",
      "Dashboard temps réel",
      "Support email",
    ],
    cta: "Essai gratuit 60 jours",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "249",
    period: "/mois",
    description: "Multi-sites & décret tertiaire",
    features: [
      "Jusqu\u2019à 5 sites",
      "Appareils illimités",
      "Rapport OPERAT automatique",
      "Autopilot IA avancé",
      "Alertes & notifications",
      "Support prioritaire",
    ],
    cta: "Essai gratuit 60 jours",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Sur mesure",
    period: "",
    description: "Grands parcs tertiaires & ESG",
    features: [
      "Sites illimités",
      "Appareils illimités",
      "API & intégrations custom",
      "Reporting ESG complet",
      "Account manager dédié",
      "SLA garanti 99,9 %",
    ],
    cta: "Nous contacter",
    highlighted: false,
  },
];

export default function Pricing() {
  return (
    <section className="px-6 py-20" id="tarifs">
      <div className="mx-auto max-w-7xl">
        <h2 className="text-3xl font-bold text-center mb-4">
          Tarifs simples, sans surprise
        </h2>
        <p className="text-center text-muted-foreground mb-14 max-w-2xl mx-auto">
          Tous les plans incluent un essai gratuit de 60 jours. Sans engagement,
          sans carte bancaire.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl border p-8 flex flex-col ${
                plan.highlighted
                  ? "border-primary bg-primary/5 shadow-lg shadow-primary/10"
                  : "border-border"
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-primary px-4 py-1 text-xs font-semibold text-primary-foreground">
                  Le plus populaire
                </div>
              )}

              <h3 className="text-xl font-bold">{plan.name}</h3>
              <p className="text-sm text-muted-foreground mt-1 mb-6">
                {plan.description}
              </p>

              <div className="mb-6">
                <span className="text-4xl font-bold">
                  {plan.price.includes("Sur") ? "" : ""}
                  {plan.price}
                  {!plan.price.includes("Sur") && "\u00A0\u20AC"}
                </span>
                {plan.period && (
                  <span className="text-muted-foreground">{plan.period}</span>
                )}
              </div>

              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm">
                    <svg
                      className="h-5 w-5 shrink-0 text-primary mt-0.5"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={2}
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M4.5 12.75l6 6 9-13.5"
                      />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>

              <Link href="/register" className="mt-auto">
                <Button
                  className="w-full"
                  variant={plan.highlighted ? "default" : "outline"}
                  size="lg"
                >
                  {plan.cta}
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
