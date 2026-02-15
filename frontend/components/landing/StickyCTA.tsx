"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function StickyCTA() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setVisible(window.scrollY > 600);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 px-4 py-3">
      <div className="mx-auto max-w-5xl flex flex-col sm:flex-row items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground hidden sm:block">
          Prêt à réduire vos factures de 20 % ?
        </p>
        <div className="flex items-center gap-3">
          <a href="#calculette">
            <Button variant="outline" size="sm">
              Calculer mes économies
            </Button>
          </a>
          <Link href="/register">
            <Button size="sm">
              Pilote gratuit 60 jours
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
