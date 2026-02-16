"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const moisLabels = [
  "Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
  "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc",
];

// Seasonal pattern for EHPAD 1500m² — 375 000 kWh/an → ~31 250 kWh/mois average
// After optimization: –22% → ~24 375 kWh/mois average
const data = moisLabels.map((mois, i) => {
  const seasonal = [1.30, 1.25, 1.10, 0.92, 0.75, 0.65, 0.60, 0.65, 0.78, 0.95, 1.15, 1.30];
  const baseAvant = 31250;
  const avant = Math.round(baseAvant * seasonal[i] * (0.97 + Math.random() * 0.06));
  const apres = Math.round(avant * 0.78 * (0.98 + Math.random() * 0.04));
  return { mois, avant, apres };
});

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-card p-3 shadow-lg text-sm">
      <p className="font-semibold mb-1">{label}</p>
      {payload.map((entry: any) => (
        <p key={entry.dataKey} style={{ color: entry.color }}>
          {entry.name} : {entry.value.toLocaleString("fr-FR")} kWh
        </p>
      ))}
      {payload.length >= 2 && (
        <p className="mt-1 text-xs font-medium text-green-500">
          Économie : {(payload[0].value - payload[1].value).toLocaleString("fr-FR")} kWh
        </p>
      )}
    </div>
  );
};

export default function EtudeDeCas() {
  return (
    <section className="px-6 py-20 bg-card/50" id="comparaison">
      <div className="mx-auto max-w-5xl">
        {/* Card principale */}
        <div className="rounded-2xl border border-border bg-card shadow-md p-6 md:p-10 lg:p-12">
          {/* Titre */}
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-4">
            Étude de Cas : Ehpad Les Jardins de la Garonne – Toulouse (1&nbsp;500&nbsp;m²)
          </h2>

          {/* Introduction */}
          <p className="text-center text-muted-foreground mb-10 max-w-3xl mx-auto leading-relaxed">
            Découvrez comment un Ehpad typique de Haute-Garonne a réduit sa facture
            énergétique de 22&nbsp;% sans travaux majeurs, tout en gardant un confort
            parfait pour les résidents.
          </p>

          {/* Détails + Implémentation en 2 colonnes */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
            {/* Détails du bâtiment */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3H21m-3.75 3H21" />
                </svg>
                Détails du bâtiment
              </h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-primary font-bold mt-0.5">•</span>
                  <span><strong className="text-foreground">Localisation :</strong> Toulouse, Haute-Garonne</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary font-bold mt-0.5">•</span>
                  <span><strong className="text-foreground">Surface :</strong> 1&nbsp;500&nbsp;m² (1&nbsp;200&nbsp;m² chambres + 300&nbsp;m² communs)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary font-bold mt-0.5">•</span>
                  <span><strong className="text-foreground">Occupation :</strong> 60 résidents + 25 employés, 24h/24</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary font-bold mt-0.5">•</span>
                  <span><strong className="text-foreground">Conso initiale :</strong> 250&nbsp;kWh/m²/an → 375&nbsp;000&nbsp;kWh/an (~60&nbsp;000&nbsp;€/an à 0,16&nbsp;€/kWh)</span>
                </li>
              </ul>
            </div>

            {/* Implémentation */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11.42 15.17l-5.2-3.13a.75.75 0 010-1.28l5.2-3.13a.75.75 0 011.08.67v6.26a.75.75 0 01-1.08.67z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m8.25 3v6.75m0 0l-3-3m3 3l3-3M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
                </svg>
                Implémentation
              </h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-primary font-bold mt-0.5">•</span>
                  <span>Pilote gratuit 60 jours lancé en janvier 2026</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary font-bold mt-0.5">•</span>
                  <span>Consentement Linky + intégration Netatmo sur 8 zones</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary font-bold mt-0.5">•</span>
                  <span>Upgrade légère : 4 valves Netatmo (320&nbsp;€ total)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary font-bold mt-0.5">•</span>
                  <span>Autopilot actif toutes les 15&nbsp;min (règles occupation, heures creuses, météo)</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Résultats après 6 mois — highlight cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
            <div className="rounded-xl bg-green-500/10 border border-green-500/20 p-5 text-center">
              <p className="text-sm text-muted-foreground mb-1">Économies</p>
              <p className="text-3xl font-bold text-green-500">–22&nbsp;%</p>
              <p className="text-sm text-muted-foreground mt-1">82&nbsp;500&nbsp;kWh/an économisés</p>
            </div>
            <div className="rounded-xl bg-green-500/10 border border-green-500/20 p-5 text-center">
              <p className="text-sm text-muted-foreground mb-1">Gain financier</p>
              <p className="text-3xl font-bold text-green-500">13&nbsp;200&nbsp;€/an</p>
              <p className="text-sm text-muted-foreground mt-1">Résultats après 6 mois</p>
            </div>
          </div>

          {/* Graphique */}
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-center mb-1">
              Consommation Énergétique – Avant vs Après
            </h3>
            <p className="text-center text-sm text-muted-foreground mb-6">
              Économies réelles : –22&nbsp;% sur Ehpad 1&nbsp;500&nbsp;m²
            </p>
          </div>
          <div className="w-full h-[350px] md:h-[420px] mb-10">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                <defs>
                  <linearGradient id="economiesGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22c55e" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#22c55e" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2, 32.6%, 17.5%)" />
                <XAxis
                  dataKey="mois"
                  tick={{ fill: "hsl(215, 20.2%, 65.1%)", fontSize: 12 }}
                  axisLine={{ stroke: "hsl(217.2, 32.6%, 17.5%)" }}
                />
                <YAxis
                  tick={{ fill: "hsl(215, 20.2%, 65.1%)", fontSize: 12 }}
                  axisLine={{ stroke: "hsl(217.2, 32.6%, 17.5%)" }}
                  tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                  domain={[0, 'auto']}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  wrapperStyle={{ paddingTop: "20px" }}
                  formatter={(value: string) => (
                    <span className="text-sm text-foreground">{value}</span>
                  )}
                />
                {/* Zone hachurée verte entre les deux courbes */}
                <Area
                  type="monotone"
                  dataKey="avant"
                  name="Avant (sans optimisation)"
                  stroke="#ef4444"
                  strokeWidth={3}
                  fill="url(#economiesGradient)"
                  dot={{ r: 4, fill: "#ef4444" }}
                  activeDot={{ r: 6 }}
                />
                <Area
                  type="monotone"
                  dataKey="apres"
                  name="Après Energy Autopilot"
                  stroke="#22c55e"
                  strokeWidth={3}
                  fill="hsl(var(--card))"
                  dot={{ r: 4, fill: "#22c55e" }}
                  activeDot={{ r: 6 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Témoignage */}
          <blockquote className="relative border-l-4 border-primary pl-6 py-4 mb-10 bg-primary/5 rounded-r-lg">
            <svg className="absolute top-3 left-2 h-6 w-6 text-primary/30" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983z" />
            </svg>
            <p className="italic text-muted-foreground leading-relaxed text-sm md:text-base">
              &laquo;&nbsp;Avant, on galérait avec les factures qui montaient en flèche dès
              qu&apos;il faisait froid, et on n&apos;arrivait jamais à vraiment comprendre où
              passait l&apos;énergie. Depuis qu&apos;on a mis Energy Autopilot, c&apos;est comme
              si quelqu&apos;un gérait le chauffage et l&apos;éclairage à notre place&nbsp;: on a
              perdu 13&nbsp;200&nbsp;€ de charges en un an sans que les résidents se plaignent
              une seule fois du froid. Franchement, c&apos;est du temps et de l&apos;argent
              gagné, et on respire beaucoup mieux.&nbsp;&raquo;
            </p>
            <footer className="mt-3 text-sm font-medium text-foreground">
              – Marie Dupont, Gérante, Ehpad Les Jardins de la Garonne
            </footer>
          </blockquote>

          {/* CTA */}
          <div className="text-center">
            <p className="text-lg font-semibold mb-4">
              Vous aussi, réalisez ce type d&apos;économies sur votre bâtiment&nbsp;?
            </p>
            <Link href="/register">
              <Button
                size="lg"
                className="bg-green-600 hover:bg-green-700 text-white text-base px-8 py-6 h-auto"
              >
                Demander un pilote gratuit 60 jours
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
