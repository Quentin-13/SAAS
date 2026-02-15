"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import AdminSidebar from "@/components/admin/AdminSidebar";
import AccessDenied from "@/components/shared/AccessDenied";
import { useAuthStore } from "@/lib/stores/authStore";
import { Button } from "@/components/ui/button";

/**
 * Auth states for the admin layout:
 *  - "loading"        : checking auth / performing auto-login
 *  - "authenticated"  : user is admin, render children
 *  - "access_denied"  : user is logged in but not admin
 */
type AuthPhase = "loading" | "authenticated" | "access_denied";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const initialized = useRef(false);
  const [phase, setPhase] = useState<AuthPhase>("loading");
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    async function boot() {
      const store = useAuthStore.getState();

      // Step 1: Try to initialize from existing token / demo mode
      await store.initialize();
      const { user } = useAuthStore.getState();

      // Step 2: If already authenticated, check role
      if (user) {
        if (user.role === "admin" || user.is_superuser) {
          setUserEmail(user.email);
          setPhase("authenticated");
          return;
        }
        // User is logged in but NOT admin
        setPhase("access_denied");
        return;
      }

      // Step 3: Not logged in — auto-login with demo admin credentials
      try {
        await store.loginAsAdmin();
        const { user: adminUser } = useAuthStore.getState();
        if (adminUser && (adminUser.role === "admin" || adminUser.is_superuser)) {
          setUserEmail(adminUser.email);
          setPhase("authenticated");
          return;
        }
        // loginAsAdmin succeeded but user is not admin (shouldn't happen)
        setPhase("access_denied");
      } catch {
        // All login attempts failed
        setPhase("access_denied");
      }
    }

    boot();
  }, [router]);

  // ── Loading state ─────────────────────────────────────────────────────
  if (phase === "loading") {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
          <p className="text-sm text-muted-foreground">Connexion admin en cours...</p>
        </div>
      </div>
    );
  }

  // ── Access denied ─────────────────────────────────────────────────────
  if (phase === "access_denied") {
    return <AccessDenied />;
  }

  // ── Authenticated admin ───────────────────────────────────────────────
  return (
    <div className="flex h-screen bg-background">
      <AdminSidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-16 items-center justify-between border-b border-border px-6">
          <span className="inline-flex items-center rounded-full bg-red-600/10 px-3 py-1 text-xs font-medium text-red-500">
            Admin
          </span>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">{userEmail}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                useAuthStore.getState().logout();
                router.push("/login");
              }}
            >
              Deconnexion
            </Button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
