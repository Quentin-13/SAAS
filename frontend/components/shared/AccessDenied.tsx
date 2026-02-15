"use client";

import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

/**
 * Reusable "Access Denied" screen shown when a non-admin user
 * tries to access a protected admin route.
 */
export default function AccessDenied() {
  const router = useRouter();

  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <div className="mx-auto mb-2 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
            <svg
              className="h-8 w-8 text-destructive"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
              />
            </svg>
          </div>
          <CardTitle className="text-2xl">Acces interdit</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            Vous n&apos;avez pas les permissions necessaires pour acceder a cette page.
            Seuls les administrateurs peuvent acceder au panneau d&apos;administration.
          </p>
          <div className="flex flex-col gap-2">
            <Button onClick={() => router.push("/dashboard")} className="w-full">
              Retour au dashboard
            </Button>
            <Button variant="outline" onClick={() => router.push("/login")} className="w-full">
              Se connecter avec un autre compte
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
