"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/lib/stores/authStore";

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Paramètres</h1>
        <p className="text-muted-foreground">Gérez votre compte et vos préférences</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profil</CardTitle>
          <CardDescription>Vos informations personnelles</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Nom complet</Label>
            <Input defaultValue={user?.full_name || ""} />
          </div>
          <div className="space-y-2">
            <Label>Email</Label>
            <Input defaultValue={user?.email || ""} disabled />
          </div>
          <div className="space-y-2">
            <Label>Téléphone</Label>
            <Input defaultValue={user?.phone || ""} placeholder="+33 6 12 34 56 78" />
          </div>
          <Button>Sauvegarder</Button>
        </CardContent>
      </Card>

      {/* Subscription management */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Abonnement</CardTitle>
              <CardDescription>Gérez votre formule et votre facturation</CardDescription>
            </div>
            <Badge>Actif</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="rounded-lg border border-border p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-lg">Plan Pro</p>
                <p className="text-sm text-muted-foreground">200&euro; / mois</p>
              </div>
              <Badge variant="outline">Jusqu&apos;à 3 000 m²</Badge>
            </div>
            <Separator className="my-4" />
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Prochaine facturation</p>
                <p className="font-medium">1 mars 2026</p>
              </div>
              <div>
                <p className="text-muted-foreground">Moyen de paiement</p>
                <p className="font-medium">**** **** **** 4242</p>
              </div>
              <div>
                <p className="text-muted-foreground">Sites utilisés</p>
                <p className="font-medium">2 / 5</p>
              </div>
              <div>
                <p className="text-muted-foreground">Équipements connectés</p>
                <p className="font-medium">8 / 25</p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button variant="outline">
              <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 7.5L7.5 3m0 0L12 7.5M7.5 3v13.5m13.5 0L16.5 21m0 0L12 16.5m4.5 4.5V7.5" />
              </svg>
              Changer de formule
            </Button>
            <Button variant="outline">
              <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
              </svg>
              Modifier le paiement
            </Button>
            <Button variant="outline">
              <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              Télécharger les factures
            </Button>
          </div>

          <Separator />

          {!showCancelConfirm ? (
            <button
              onClick={() => setShowCancelConfirm(true)}
              className="text-sm text-destructive hover:underline"
            >
              Annuler mon abonnement
            </button>
          ) : (
            <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4">
              <p className="text-sm font-medium text-destructive mb-2">
                Êtes-vous sûr de vouloir annuler votre abonnement ?
              </p>
              <p className="text-xs text-muted-foreground mb-4">
                Votre accès sera maintenu jusqu&apos;au 1 mars 2026. Après cette date,
                l&apos;autopilot sera désactivé et vous perdrez l&apos;accès aux fonctionnalités Pro.
              </p>
              <div className="flex gap-2">
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setShowCancelConfirm(false)}
                >
                  Confirmer l&apos;annulation
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCancelConfirm(false)}
                >
                  Garder mon abonnement
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
          <CardDescription>Configurez vos préférences de notification</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Actions Autopilot</p>
              <p className="text-sm text-muted-foreground">
                Recevez un résumé des actions prises
              </p>
            </div>
            <Button variant="outline" size="sm">Email</Button>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Anomalies détectées</p>
              <p className="text-sm text-muted-foreground">
                Alertes en cas de surconsommation
              </p>
            </div>
            <Button variant="outline" size="sm">Email</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
