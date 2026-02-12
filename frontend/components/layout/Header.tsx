"use client";

import { useAuthStore } from "@/lib/stores/authStore";
import { isDemoMode } from "@/lib/demo";
import { Button } from "@/components/ui/button";

export default function Header() {
  const { user, logout } = useAuthStore();

  return (
    <header className="flex h-16 items-center justify-between border-b border-border px-6">
      <div>
        {isDemoMode() && (
          <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800 dark:bg-amber-900/30 dark:text-amber-400">
            Mode démo
          </span>
        )}
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">
          {user?.full_name || user?.email}
        </span>
        <Button variant="ghost" size="sm" onClick={logout}>
          Déconnexion
        </Button>
      </div>
    </header>
  );
}
