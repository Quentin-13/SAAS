"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";

export default function LandingPage() {
  const router = useRouter();
  const { loginDemo } = useAuthStore();

  const handleDemo = () => {
    loginDemo();
    router.push("/dashboard");
  };
  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="border-b border-border/40 px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-bold text-sm">
              EA
            </div>
            <span className="text-xl font-bold">Energy Autopilot</span>
          </div>
          <div className="flex items-center gap-4">
            <a
              href="#how-it-works"
              className="text-sm text-muted-foreground hover:text-foreground transition"
            >
              Comment ça marche
            </a>
            <a
              href="#pricing"
              className="text-sm text-muted-foreground hover:text-foreground transition"
            >
              Tarifs
            </a>
            <Link
              href="/login"
              className="text-sm text-muted-foreground hover:text-foreground transition"
            >
              Se connecter
            </Link>
            <Link
              href="/register"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition"
            >
              Commencer
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="px-6 py-24 text-center">
        <div className="mx-auto max-w-4xl">
          <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
            Réduisez vos coûts énergétiques de{" "}
            <span className="text-primary">25-30%</span>
          </h1>
          <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto">
            Notre IA analyse vos patterns de consommation et pilote
            automatiquement vos équipements pour optimiser votre facture
            énergétique. Sans compromis sur le confort.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              href="/register"
              className="rounded-lg bg-primary px-8 py-3 text-lg font-semibold text-primary-foreground hover:bg-primary/90 transition"
            >
              Essai gratuit
            </Link>
            <button
              onClick={handleDemo}
              className="rounded-lg border border-border px-8 py-3 text-lg font-semibold hover:bg-accent transition cursor-pointer"
            >
              Voir la démo
            </button>
          </div>
        </div>
      </section>

      {/* Comment ça marche — detailed */}
      <section id="how-it-works" className="px-6 py-24 bg-card/50">
        <div className="mx-auto max-w-7xl">
          <h2 className="text-3xl font-bold text-center mb-4">
            Comment ça marche
          </h2>
          <p className="text-center text-muted-foreground mb-16 max-w-2xl mx-auto">
            En 4 étapes simples, passez d&apos;une gestion manuelle à un pilotage
            intelligent de votre énergie
          </p>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Step 1 */}
            <div className="relative text-center">
              <div className="mx-auto h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <span className="text-2xl font-bold text-primary">1</span>
              </div>
              <h3 className="text-lg font-semibold mb-2">Connectez vos équipements</h3>
              <p className="text-sm text-muted-foreground">
                Reliez vos compteurs Linky, thermostats Nest, capteurs Netatmo
                en quelques clics. Aucune installation physique nécessaire.
              </p>
            </div>

            {/* Step 2 */}
            <div className="relative text-center">
              <div className="mx-auto h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <span className="text-2xl font-bold text-primary">2</span>
              </div>
              <h3 className="text-lg font-semibold mb-2">L&apos;IA analyse vos données</h3>
              <p className="text-sm text-muted-foreground">
                Notre intelligence artificielle étudie vos historiques de
                consommation, la météo locale et les tarifs énergétiques pour
                créer un profil optimisé.
              </p>
            </div>

            {/* Step 3 */}
            <div className="relative text-center">
              <div className="mx-auto h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <span className="text-2xl font-bold text-primary">3</span>
              </div>
              <h3 className="text-lg font-semibold mb-2">L&apos;Autopilot optimise</h3>
              <p className="text-sm text-muted-foreground">
                L&apos;autopilot ajuste automatiquement vos équipements toutes
                les 15 minutes : chauffage, climatisation, éclairage — tout en
                respectant vos contraintes de confort.
              </p>
            </div>

            {/* Step 4 */}
            <div className="relative text-center">
              <div className="mx-auto h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <span className="text-2xl font-bold text-primary">4</span>
              </div>
              <h3 className="text-lg font-semibold mb-2">Suivez vos économies</h3>
              <p className="text-sm text-muted-foreground">
                Visualisez en temps réel vos économies, les actions de
                l&apos;autopilot et gardez le contrôle total depuis votre
                dashboard.
              </p>
            </div>
          </div>

          {/* Feature highlights */}
          <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="rounded-xl border border-border bg-card p-8">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <svg className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">IA Prédictive</h3>
              <p className="text-muted-foreground">
                Nos algorithmes analysent vos données historiques, la météo et
                les tarifs pour prédire votre consommation avec 95% de
                précision.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-card p-8">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <svg className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">
                Autopilot Intelligent
              </h3>
              <p className="text-muted-foreground">
                L&apos;autopilot ajuste automatiquement vos thermostats et
                équipements toutes les 15 minutes pour maximiser les économies.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-card p-8">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <svg className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">
                Dashboard Temps Réel
              </h3>
              <p className="text-muted-foreground">
                Suivez vos économies en temps réel, visualisez les actions de
                l&apos;autopilot et gardez le contrôle total sur vos bâtiments.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="px-6 py-24">
        <div className="mx-auto max-w-7xl">
          <h2 className="text-3xl font-bold text-center mb-4">Tarifs</h2>
          <p className="text-center text-muted-foreground mb-16">
            Des formules adaptées à la taille de votre entreprise
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Starter — now includes AI */}
            <div className="rounded-xl border border-border p-8">
              <h3 className="text-lg font-semibold">Starter</h3>
              <p className="text-3xl font-bold mt-4">
                100<span className="text-lg text-muted-foreground">&euro;/mois</span>
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Jusqu&apos;à 1 000 m²
              </p>
              <ul className="mt-6 space-y-3 text-sm">
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  1 site
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  5 équipements
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Autopilot intelligent
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  IA prédictive incluse
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Dashboard temps réel
                </li>
              </ul>
              <Link
                href="/register"
                className="mt-8 block w-full rounded-lg border border-border py-2 text-center text-sm font-medium hover:bg-accent transition"
              >
                Commencer
              </Link>
            </div>

            {/* Pro — enriched */}
            <div className="rounded-xl border-2 border-primary p-8 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs font-bold px-3 py-1 rounded-full">
                Populaire
              </div>
              <h3 className="text-lg font-semibold">Pro</h3>
              <p className="text-3xl font-bold mt-4">
                200<span className="text-lg text-muted-foreground">&euro;/mois</span>
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Jusqu&apos;à 3 000 m²
              </p>
              <ul className="mt-6 space-y-3 text-sm">
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  5 sites
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  25 équipements
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  IA avancée + prévisions 7 jours
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Autopilot multi-zones
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Détection d&apos;anomalies avancée
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Rapports mensuels automatiques
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Support prioritaire
                </li>
              </ul>
              <Link
                href="/register"
                className="mt-8 block w-full rounded-lg bg-primary py-2 text-center text-sm font-medium text-primary-foreground hover:bg-primary/90 transition"
              >
                Commencer
              </Link>
            </div>

            {/* Enterprise */}
            <div className="rounded-xl border border-border p-8">
              <h3 className="text-lg font-semibold">Enterprise</h3>
              <p className="text-3xl font-bold mt-4">Sur devis</p>
              <p className="text-sm text-muted-foreground mt-2">
                Plus de 3 000 m²
              </p>
              <ul className="mt-6 space-y-3 text-sm">
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Sites illimités
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Équipements illimités
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  API dédiée
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Account manager dédié
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  SLA garanti 99.9%
                </li>
                <li className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-primary" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Intégrations sur mesure
                </li>
              </ul>
              <Link
                href="/register"
                className="mt-8 block w-full rounded-lg border border-border py-2 text-center text-sm font-medium hover:bg-accent transition"
              >
                Nous contacter
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40 px-6 py-8">
        <div className="mx-auto max-w-7xl text-center text-sm text-muted-foreground">
          <p>&copy; 2024 Energy Autopilot. Tous droits réservés.</p>
        </div>
      </footer>
    </div>
  );
}
