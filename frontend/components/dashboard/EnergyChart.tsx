"use client";

import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";

interface DataPoint {
  date: string;
  total_kwh: number;
  total_cost_eur: number;
}

interface EnergyChartProps {
  data: DataPoint[];
}

export default function EnergyChart({ data }: EnergyChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-muted-foreground">
        Aucune donnée disponible
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="colorKwh" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="hsl(142.1, 76.2%, 36.3%)" stopOpacity={0.3} />
            <stop offset="95%" stopColor="hsl(142.1, 76.2%, 36.3%)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2, 32.6%, 17.5%)" />
        <XAxis
          dataKey="date"
          stroke="hsl(215, 20.2%, 65.1%)"
          fontSize={12}
          tickFormatter={(value) => {
            const d = new Date(value);
            return `${d.getDate()}/${d.getMonth() + 1}`;
          }}
        />
        <YAxis stroke="hsl(215, 20.2%, 65.1%)" fontSize={12} />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(222.2, 84%, 4.9%)",
            border: "1px solid hsl(217.2, 32.6%, 17.5%)",
            borderRadius: "8px",
            color: "hsl(210, 40%, 98%)",
          }}
          formatter={(value: number) => [`${value.toFixed(1)} kWh`, "Consommation"]}
          labelFormatter={(label) => {
            const d = new Date(label);
            return d.toLocaleDateString("fr-FR");
          }}
        />
        <Area
          type="monotone"
          dataKey="total_kwh"
          stroke="hsl(142.1, 76.2%, 36.3%)"
          fillOpacity={1}
          fill="url(#colorKwh)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
