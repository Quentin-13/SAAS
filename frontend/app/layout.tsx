import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Energy Autopilot",
  description:
    "Plateforme de gestion énergétique prédictive avec autopilot IA",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className="dark">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
