"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import api from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [debugToken, setDebugToken] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const res = await api.post("/auth/password-reset/request", { email });
      setSent(true);
      // In dev mode, the API returns a debug token
      if (res.data.debug_token) {
        setDebugToken(res.data.debug_token);
      }
    } catch {
      setError("Une erreur est survenue. Veuillez reessayer.");
    } finally {
      setIsLoading(false);
    }
  };

  if (sent) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-600/10">
            <svg
              className="h-6 w-6 text-green-600"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
              />
            </svg>
          </div>
          <CardTitle className="text-2xl">Email envoye</CardTitle>
          <CardDescription>
            Si un compte existe avec cette adresse email, vous recevrez un lien
            de reinitialisation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {debugToken && (
            <div className="rounded-md bg-yellow-600/10 p-3 text-xs text-yellow-600 break-all">
              <p className="font-medium mb-1">Mode demo - Token de reset :</p>
              <Link
                href={`/reset-password?token=${debugToken}`}
                className="text-primary underline"
              >
                Cliquer ici pour reinitialiser le mot de passe
              </Link>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex justify-center">
          <Link href="/login" className="text-sm text-primary hover:underline">
            Retour a la connexion
          </Link>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        <div className="mx-auto mb-4 h-12 w-12 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-bold text-lg">
          EA
        </div>
        <CardTitle className="text-2xl">Mot de passe oublie</CardTitle>
        <CardDescription>
          Entrez votre email pour recevoir un lien de reinitialisation
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="vous@entreprise.fr"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Envoi en cours..." : "Envoyer le lien"}
          </Button>
          <Link
            href="/login"
            className="text-sm text-muted-foreground hover:underline"
          >
            Retour a la connexion
          </Link>
        </CardFooter>
      </form>
    </Card>
  );
}
