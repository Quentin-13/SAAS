"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import dynamic from "next/dynamic";
import Testimonials from "@/components/landing/Testimonials";
import Calculette from "@/components/landing/Calculette";
import FAQ from "@/components/landing/FAQ";
import Pricing from "@/components/landing/Pricing";
import StickyCTA from "@/components/landing/StickyCTA";

const EtudeDeCas = dynamic(
  () => import("@/components/landing/EtudeDeCas"),
  { ssr: false }
);

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
          <div className="hidden md:flex items-center gap-4">
            <a
              href="#comparaison"
              className="text-sm text-muted-foreground hover:text-foreground transition"
            >
              Résultats
            </a>
            <a
              href="#preuves"
              className="text-sm text-muted-foreground hover:text-foreground transition"
            >
              Témoignages
            </a>
            <a
              href="#calculette"
              className="text-sm text-muted-foreground hover:text-foreground transition"
            >
              Calculette
            </a>
            <a
              href="#tarifs"
              className="text-sm text-muted-foreground hover:text-foreground transition"
            >
              Tarifs
            </a>
            <a
              href="#faq"
              className="text-sm text-muted-foreground hover:text-foreground transition"
            >
              FAQ
            </a>
            <Link
              href="/login"
              className="text-sm text-muted-foreground hover:text-foreground transition"
            >
              Se connecter
            </Link>
            <Link href="/register">
              <Button size="sm">Commencer</Button>
            </Link>
          </div>
          {/* Mobile menu button */}
          <div className="md:hidden">
            <Link href="/register">
              <Button size="sm">Commencer</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden px-6 py-20 md:py-28">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-background to-blue-900/10 pointer-events-none" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative mx-auto max-w-5xl text-center">
          {/* Badge */}
          <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
            <Badge variant="outline" className="px-3 py-1 text-xs">
              Compatible Enedis Linky
            </Badge>
            <Badge variant="outline" className="px-3 py-1 text-xs">
              Conforme décret tertiaire &amp; OPERAT
            </Badge>
            <Badge variant="outline" className="px-3 py-1 text-xs">
              Testé sur PME Occitanie
            </Badge>
          </div>

          {/* Headline */}
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-tight">
            Factures énergétiques qui explosent et pénalités ADEME en vue ?{" "}
            <span className="text-primary">
              Respectez le décret tertiaire 2030 sans travaux ni stress
            </span>{" "}
            – Automatiquement.
          </h1>

          {/* Sous-titre */}
          <p className="mt-6 md:mt-8 text-base md:text-lg text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            L&apos;autopilot IA optimise votre conso Linky + thermostats toutes
            les 15 min : heures creuses, occupation intelligente, prévisions
            météo. Économies moyennes 18-25 % sur Ehpad, hôtels et bureaux
            tertiaires &gt;1 000 m². Déclaration OPERAT générée en 1 clic.
          </p>

          {/* CTAs */}
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/register">
              <Button size="lg" className="text-base px-8 py-6 h-auto">
                Demander un pilote gratuit 60 jours sur mon bâtiment
              </Button>
            </Link>
            <a href="#calculette">
              <Button variant="outline" size="lg" className="text-base px-8 py-6 h-auto">
                Calculer mes économies en 30s
              </Button>
            </a>
          </div>

          {/* Stats rapides */}
          <div className="mt-14 grid grid-cols-3 gap-6 max-w-3xl mx-auto">
            {[
              { value: "18-25 %", label: "d\u2019économies moyennes" },
              { value: "15 min", label: "fréquence d\u2019optimisation" },
              { value: "1 clic", label: "déclaration OPERAT" },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-2xl md:text-3xl font-bold text-primary">
                  {stat.value}
                </p>
                <p className="text-xs md:text-sm text-muted-foreground mt-1">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Comment ça marche (court) */}
      <section id="how-it-works" className="px-6 py-20 bg-card/50">
        <div className="mx-auto max-w-7xl">
          <h2 className="text-3xl font-bold text-center mb-4">
            Comment ça marche
          </h2>
          <p className="text-center text-muted-foreground mb-14 max-w-2xl mx-auto">
            En 4 étapes simples, passez d&apos;une gestion manuelle à un
            pilotage intelligent de votre énergie
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8">
            {[
              {
                step: "1",
                title: "Connectez vos équipements",
                desc: "Reliez vos compteurs Linky, thermostats Nest, capteurs Netatmo en quelques clics. Aucune installation physique.",
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.86-2.813a4.5 4.5 0 00-6.364-6.364L4.5 8.257" />
                ),
              },
              {
                step: "2",
                title: "L\u2019IA analyse vos données",
                desc: "Historiques de conso, météo locale, tarifs énergétiques : un profil optimisé est créé en 48h.",
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                ),
              },
              {
                step: "3",
                title: "L\u2019Autopilot optimise",
                desc: "Ajustement automatique toutes les 15 minutes : chauffage, clim, heures creuses, pré-chauffage intelligent.",
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                ),
              },
              {
                step: "4",
                title: "Suivez vos économies",
                desc: "Dashboard temps réel, alertes, rapports OPERAT automatiques. Gardez le contrôle total.",
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                ),
              },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="mx-auto h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <svg
                    className="h-7 w-7 text-primary"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                  >
                    {item.icon}
                  </svg>
                </div>
                <div className="text-xs font-bold text-primary mb-1">
                  ÉTAPE {item.step}
                </div>
                <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                <p className="text-sm text-muted-foreground">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Étude de cas */}
      <EtudeDeCas />

      {/* Preuves sociales */}
      <Testimonials />

      {/* Calculette */}
      <Calculette />

      {/* Tarifs */}
      <Pricing />

      {/* FAQ */}
      <FAQ />

      {/* CTA Footer */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-4xl text-center">
          <div className="rounded-2xl bg-gradient-to-br from-primary/20 via-primary/10 to-blue-900/10 border border-primary/20 p-10 md:p-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Prêt à réduire vos factures de 20 % ?
            </h2>
            <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
              Rejoignez les PME tertiaires qui économisent déjà avec Energy
              Autopilot. Pilote gratuit 60 jours, sans engagement, sans
              travaux.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg" className="text-base px-8 py-6 h-auto">
                  Demander un pilote gratuit 60 jours
                </Button>
              </Link>
              <button
                onClick={handleDemo}
                className="text-sm text-muted-foreground hover:text-foreground underline underline-offset-4 transition cursor-pointer"
              >
                Voir la démo interactive
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40 px-6 py-8">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded bg-primary flex items-center justify-center text-primary-foreground font-bold text-xs">
                EA
              </div>
              <span className="text-sm font-semibold">Energy Autopilot</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-muted-foreground">
              <a href="#how-it-works" className="hover:text-foreground transition">
                Comment ça marche
              </a>
              <a href="#preuves" className="hover:text-foreground transition">
                Témoignages
              </a>
              <a href="#faq" className="hover:text-foreground transition">
                FAQ
              </a>
              <Link href="/login" className="hover:text-foreground transition">
                Se connecter
              </Link>
            </div>
            <p className="text-sm text-muted-foreground">
              &copy; 2025 Energy Autopilot. Tous droits réservés.
            </p>
          </div>
        </div>
      </footer>

      {/* Sticky CTA */}
      <StickyCTA />
    </div>
  );
}
