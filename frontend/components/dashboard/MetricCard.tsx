import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string;
  change?: string;
  trend?: "up" | "down" | "neutral";
  subtitle?: string;
  icon?: React.ReactNode;
}

export default function MetricCard({ title, value, change, trend, subtitle, icon }: MetricCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          {icon && <div className="text-muted-foreground">{icon}</div>}
        </div>
        <p className="mt-2 text-3xl font-bold">{value}</p>
        {(change || subtitle) && (
          <p className="mt-1 text-sm">
            {change && (
              <span
                className={cn(
                  "font-medium",
                  trend === "up" && "text-green-500",
                  trend === "down" && "text-red-500",
                  trend === "neutral" && "text-muted-foreground"
                )}
              >
                {change}
              </span>
            )}
            {subtitle && <span className="text-muted-foreground"> {subtitle}</span>}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
