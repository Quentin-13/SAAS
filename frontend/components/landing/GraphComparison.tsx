"use client";

import {
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

const data = moisLabels.map((mois, i) => {
  // Seasonal pattern: higher in winter, lower in summer
  const seasonal = [1.25, 1.20, 1.10, 0.95, 0.80, 0.70, 0.65, 0.70, 0.80, 0.95, 1.10, 1.25];
  const base = 1200;
  const sansSolution = Math.round(base * seasonal[i] * (1 + i * 0.02));
  const avecAutopilot = Math.round(sansSolution * 0.80);
  return { mois, sansSolution, avecAutopilot };
});

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-card p-3 shadow-lg text-sm">
      <p className="font-semibold mb-1">{label}</p>
      {payload.map((entry: any) => (
        <p key={entry.dataKey} style={{ color: entry.color }}>
          {entry.name} : {entry.value.toLocaleString("fr-FR")} &euro;
        </p>
      ))}
      {payload.length === 2 && (
        <p className="mt-1 text-xs text-muted-foreground">
          Économie : {(payload[0].value - payload[1].value).toLocaleString("fr-FR")} &euro;
        </p>
      )}
    </div>
  );
};

export default function GraphComparison() {
  return (
    <section className="px-6 py-20 bg-card/50" id="comparaison">
      <div className="mx-auto max-w-5xl">
        <h2 className="text-3xl font-bold text-center mb-2">
          Conso énergétique : Avant vs Après autopilot
        </h2>
        <p className="text-center text-muted-foreground mb-10">
          Économies visibles : –20 % moyen sur 1 an (bâtiment 1 500 m²)
        </p>
        <div className="w-full h-[400px] md:h-[450px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2, 32.6%, 17.5%)" />
              <XAxis
                dataKey="mois"
                tick={{ fill: "hsl(215, 20.2%, 65.1%)", fontSize: 12 }}
                axisLine={{ stroke: "hsl(217.2, 32.6%, 17.5%)" }}
              />
              <YAxis
                tick={{ fill: "hsl(215, 20.2%, 65.1%)", fontSize: 12 }}
                axisLine={{ stroke: "hsl(217.2, 32.6%, 17.5%)" }}
                tickFormatter={(v) => `${v} €`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ paddingTop: "20px" }}
                formatter={(value: string) => (
                  <span className="text-sm text-foreground">{value}</span>
                )}
              />
              <Line
                type="monotone"
                dataKey="sansSolution"
                name="Sans solution"
                stroke="#ef4444"
                strokeWidth={3}
                dot={{ r: 5, fill: "#ef4444" }}
                activeDot={{ r: 7 }}
              />
              <Line
                type="monotone"
                dataKey="avecAutopilot"
                name="Avec Energy Autopilot"
                stroke="#22c55e"
                strokeWidth={3}
                dot={{ r: 5, fill: "#22c55e" }}
                activeDot={{ r: 7 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}
