"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useSitesStore } from "@/lib/stores/sitesStore";
import api from "@/lib/api";
import { isDemoMode } from "@/lib/demo";
import toast from "react-hot-toast";

interface Device {
  id: string;
  name: string;
  device_type: string;
  brand: string;
  status: "connected" | "pending" | "error";
}

const DEVICE_TYPES = [
  { value: "linky", label: "Compteur Linky" },
  { value: "netatmo", label: "Thermostat Netatmo" },
  { value: "nest", label: "Google Nest" },
  { value: "sonoff", label: "Relai Sonoff" },
  { value: "autre", label: "Autre" },
] as const;

const DEVICE_TYPE_LABELS: Record<string, string> = {
  linky: "Compteur Linky",
  netatmo: "Thermostat Netatmo",
  nest: "Google Nest",
  sonoff: "Relai Sonoff",
  autre: "Autre",
  thermostat: "Thermostat",
  meter: "Compteur",
  hvac: "HVAC",
};

const OAUTH_ROUTES: Record<string, string> = {
  linky: "/api/v1/auth/enedis/start",
  netatmo: "/api/v1/auth/netatmo/start",
  nest: "/api/v1/auth/nest/start",
};

function getDeviceIcon(type: string) {
  switch (type) {
    case "linky":
    case "meter":
      return (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
        </svg>
      );
    case "netatmo":
    case "nest":
    case "thermostat":
      return (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 18a3.75 3.75 0 00.495-7.467 5.99 5.99 0 00-1.925 3.546 5.974 5.974 0 01-2.133-1A3.75 3.75 0 0012 18z" />
        </svg>
      );
    case "sonoff":
      return (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5.636 5.636a9 9 0 1012.728 0M12 3v9" />
        </svg>
      );
    default:
      return (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.288 15.038a5.25 5.25 0 017.424 0M5.106 11.856c3.807-3.808 9.98-3.808 13.788 0M1.924 8.674c5.565-5.565 14.587-5.565 20.152 0M12.53 18.22l-.53.53-.53-.53a.75.75 0 011.06 0z" />
        </svg>
      );
  }
}

// Demo devices for mock mode
const DEMO_DEVICES: Device[] = [
  { id: "demo-dev-1", name: "Compteur Principal", device_type: "linky", brand: "linky", status: "connected" },
  { id: "demo-dev-2", name: "Thermostat Accueil", device_type: "thermostat", brand: "netatmo", status: "connected" },
  { id: "demo-dev-3", name: "Nest Bureau Direction", device_type: "thermostat", brand: "nest", status: "connected" },
];

/** Handles OAuth callback search params without causing Suspense on the parent */
function OAuthCallbackHandler({ siteId }: { siteId: string }) {
  const searchParams = useSearchParams();

  useEffect(() => {
    const oauthStatus = searchParams.get("oauth");
    const provider = searchParams.get("provider") || "";
    if (oauthStatus === "success") {
      toast.success(`${provider.charAt(0).toUpperCase() + provider.slice(1)} connecté avec succès !`);
      window.history.replaceState({}, "", `/dashboard/sites/${siteId}`);
    } else if (oauthStatus === "error") {
      toast.error(`Erreur de connexion ${provider}. Veuillez réessayer.`);
      window.history.replaceState({}, "", `/dashboard/sites/${siteId}`);
    }
  }, [searchParams, siteId]);

  return null;
}

export default function SiteDetailPage() {
  const params = useParams();
  const siteId = params.id as string;
  const { currentSite, isLoading, error, fetchSite, toggleAutopilot } = useSitesStore();

  const [devices, setDevices] = useState<Device[]>([]);
  const [devicesLoading, setDevicesLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    name: "",
    device_type: "linky",
    description: "",
  });

  useEffect(() => {
    fetchSite(siteId);
    loadDevices();
  }, [siteId, fetchSite]);

  async function loadDevices() {
    if (isDemoMode()) {
      setDevices(DEMO_DEVICES);
      return;
    }
    setDevicesLoading(true);
    try {
      const res = await api.get(`/devices/?site_id=${siteId}`);
      setDevices(res.data);
    } catch {
      // Silently fail — empty list shown
    } finally {
      setDevicesLoading(false);
    }
  }

  async function handleConnect(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) return;

    setSubmitting(true);

    const oauthRoute = OAUTH_ROUTES[form.device_type];

    // For OAuth-based integrations, redirect
    if (oauthRoute) {
      if (isDemoMode()) {
        // In demo mode, simulate OAuth success
        const newDevice: Device = {
          id: `demo-dev-${Date.now()}`,
          name: form.name,
          device_type: form.device_type,
          brand: form.device_type,
          status: "connected",
        };
        setDevices((prev) => [...prev, newDevice]);
        toast.success("Équipement connecté avec succès !");
        setForm({ name: "", device_type: "linky", description: "" });
        setModalOpen(false);
        setSubmitting(false);
        return;
      }

      // Real OAuth: call backend /start endpoint then redirect
      try {
        const res = await api.get(`${oauthRoute}?site_id=${siteId}&device_name=${encodeURIComponent(form.name)}`);
        const { redirect_url, mock } = res.data;
        if (mock) {
          // Mock mode: device already created server-side, just reload
          toast.success("Équipement connecté avec succès !");
          setForm({ name: "", device_type: "linky", description: "" });
          setModalOpen(false);
          setSubmitting(false);
          loadDevices();
          return;
        }
        window.location.href = redirect_url;
      } catch {
        toast.error("Erreur lors de l'initialisation OAuth.");
        setSubmitting(false);
      }
      return;
    }

    // For non-OAuth devices (Sonoff, Autre): POST to API
    try {
      if (isDemoMode()) {
        const newDevice: Device = {
          id: `demo-dev-${Date.now()}`,
          name: form.name,
          device_type: form.device_type,
          brand: form.device_type,
          status: "connected",
        };
        setDevices((prev) => [...prev, newDevice]);
      } else {
        const res = await api.post("/devices/", {
          name: form.name,
          device_type: form.device_type === "sonoff" ? "hvac" : "thermostat",
          brand: form.device_type,
          description: form.description,
          site_id: siteId,
          is_controllable: form.device_type === "sonoff",
        });
        setDevices((prev) => [...prev, { ...res.data, status: "connected" }]);
      }
      toast.success("Équipement connecté avec succès !");
      setForm({ name: "", device_type: "linky", description: "" });
      setModalOpen(false);
    } catch {
      toast.error("Erreur lors de l'ajout de l'équipement.");
    } finally {
      setSubmitting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!currentSite) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <p className="text-lg text-muted-foreground">{error || "Site introuvable."}</p>
        <Button variant="outline" onClick={() => window.history.back()}>
          Retour
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* OAuth callback handler (wrapped in Suspense to avoid blocking render) */}
      <Suspense fallback={null}>
        <OAuthCallbackHandler siteId={siteId} />
      </Suspense>

      {/* Header du site */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">{currentSite.name}</h1>
          <p className="text-muted-foreground">
            {currentSite.address && `${currentSite.address}, `}
            {currentSite.city}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Autopilot</span>
            <Switch
              checked={currentSite.autopilot_enabled}
              onCheckedChange={(checked) => toggleAutopilot(siteId, checked)}
            />
          </div>
          <Badge variant={currentSite.autopilot_enabled ? "default" : "outline"}>
            {currentSite.autopilot_enabled ? "Actif" : "Inactif"}
          </Badge>
        </div>
      </div>

      {/* Métriques */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Surface</p>
            <p className="text-2xl font-bold">{currentSite.surface_area || "-"} m²</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Type</p>
            <p className="text-2xl font-bold capitalize">{currentSite.building_type || "-"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Pays</p>
            <p className="text-2xl font-bold">{currentSite.country}</p>
          </CardContent>
        </Card>
      </div>

      {/* Équipements */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Équipements</CardTitle>
          <Dialog open={modalOpen} onOpenChange={setModalOpen}>
            <DialogTrigger asChild>
              <Button size="sm">Ajouter un équipement</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Ajouter un équipement</DialogTitle>
                <DialogDescription>
                  Connectez un compteur, thermostat ou capteur à ce site.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleConnect} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="eq-name">Nom de l&apos;équipement</Label>
                  <Input
                    id="eq-name"
                    placeholder="Ex : Compteur RDC, Thermostat Salle A…"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="eq-type">Type</Label>
                  <select
                    id="eq-type"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    value={form.device_type}
                    onChange={(e) => setForm({ ...form, device_type: e.target.value })}
                  >
                    {DEVICE_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="eq-desc">Description (optionnelle)</Label>
                  <textarea
                    id="eq-desc"
                    className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    placeholder="Précisions sur l'emplacement ou l'usage…"
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                  />
                </div>

                {OAUTH_ROUTES[form.device_type] && (
                  <p className="text-xs text-muted-foreground rounded-md bg-primary/5 p-3">
                    Vous serez redirigé vers{" "}
                    <strong>
                      {form.device_type === "linky" ? "Enedis" : form.device_type === "netatmo" ? "Netatmo" : "Google"}
                    </strong>{" "}
                    pour autoriser la connexion sécurisée (OAuth).
                  </p>
                )}

                <DialogFooter>
                  <Button
                    type="submit"
                    disabled={submitting || !form.name.trim()}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    {submitting ? (
                      <>
                        <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent inline-block" />
                        Connexion…
                      </>
                    ) : (
                      "Connecter"
                    )}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent>
          {devicesLoading ? (
            <div className="flex justify-center py-6">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : devices.length === 0 ? (
            <p className="text-muted-foreground">
              Aucun équipement connecté. Cliquez sur &laquo;&nbsp;Ajouter un équipement&nbsp;&raquo; pour commencer.
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {devices.map((device) => (
                <div
                  key={device.id}
                  className="flex items-center gap-3 rounded-lg border border-border p-4"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    {getDeviceIcon(device.device_type || device.brand)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">{device.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {DEVICE_TYPE_LABELS[device.brand] || DEVICE_TYPE_LABELS[device.device_type] || device.device_type}
                    </p>
                  </div>
                  <Badge
                    variant={device.status === "connected" ? "default" : "outline"}
                    className={device.status === "connected" ? "bg-green-600 hover:bg-green-700" : ""}
                  >
                    {device.status === "connected" && (
                      <svg className="mr-1 h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    )}
                    {device.status === "connected" ? "Connecté" : device.status === "pending" ? "En attente" : "Erreur"}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
