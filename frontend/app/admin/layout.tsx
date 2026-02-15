"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import AdminSidebar from "@/components/admin/AdminSidebar";
import { useAuthStore } from "@/lib/stores/authStore";
import { Button } from "@/components/ui/button";

type AuthStatus = "checking" | "not_logged_in" | "not_admin" | "authorized";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const initialized = useRef(false);
  const [status, setStatus] = useState<AuthStatus>("checking");
  const [userEmail, setUserEmail] = useState<string>("");

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    useAuthStore.getState().initialize().then(() => {
      const { user } = useAuthStore.getState();
      if (!user) {
        setStatus("not_logged_in");
        return;
      }
      setUserEmail(user.email);
      if (user.role === "admin" || user.is_superuser) {
        setStatus("authorized");
      } else {
        setStatus("not_admin");
      }
    }).catch(() => {
      setStatus("not_logged_in");
    });
  }, [router]);

  if (status === "checking") {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <div className="h-8 w-8 mx-auto animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
          <p className="text-sm text-muted-foreground">Vérification des droits...</p>
        </div>
      </div>
    );
  }

  if (status === "not_logged_in") {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <div className="h-16 w-16 mx-auto rounded-full bg-red-600/10 flex items-center justify-center">
            <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold">Connexion requise</h1>
          <p className="text-muted-foreground">Connectez-vous pour accéder au panneau admin.</p>
          <div className="flex gap-3 justify-center">
            <Button onClick={() => router.push("/login")}>
              Se connecter
            </Button>
            <Button variant="outline" onClick={() => {
              useAuthStore.getState().loginDemo();
              window.location.reload();
            }}>
              Accéder à la démo
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (status === "not_admin") {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <div className="h-16 w-16 mx-auto rounded-full bg-red-600/10 flex items-center justify-center">
            <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold">Accès refusé</h1>
          <p className="text-muted-foreground">Vous n&apos;avez pas les droits administrateur.</p>
          <Button onClick={() => router.push("/dashboard")}>
            Retour au dashboard
          </Button>
        </div>
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
            <span className="text-sm text-muted-foreground">
              {userEmail}
            </span>
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
