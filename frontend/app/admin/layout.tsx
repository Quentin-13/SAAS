"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import AdminSidebar from "@/components/admin/AdminSidebar";
import { useAuthStore } from "@/lib/stores/authStore";
import { Button } from "@/components/ui/button";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const initialized = useRef(false);
  const [ready, setReady] = useState(false);
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    // Auto-enable demo mode for admin access
    const store = useAuthStore.getState();
    store.initialize().then(() => {
      const { user } = useAuthStore.getState();
      if (user && (user.role === "admin" || user.is_superuser)) {
        setUserEmail(user.email);
        setReady(true);
      } else {
        // Auto-login as demo admin
        store.loginDemo();
        setUserEmail("demo@energy-autopilot.fr");
        setReady(true);
      }
    }).catch(() => {
      store.loginDemo();
      setUserEmail("demo@energy-autopilot.fr");
      setReady(true);
    });
  }, [router]);

  if (!ready) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

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
            <Button variant="ghost" size="sm" onClick={() => {
              useAuthStore.getState().logout();
              router.push("/login");
            }}>
              Déconnexion
            </Button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
