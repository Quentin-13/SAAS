"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAdminStore, type AdminUser } from "@/lib/stores/adminStore";

export default function AdminUsersPage() {
  const { users, fetchUsers, updateUser } = useAdminStore();
  const loaded = useRef(false);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [newPassword, setNewPassword] = useState("");

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;
    fetchUsers();
  }, [fetchUsers]);

  const handleSearch = () => {
    fetchUsers(1, search, roleFilter);
  };

  const handleToggleActive = async (user: AdminUser) => {
    await updateUser(user.id, { is_active: !user.is_active });
    fetchUsers(users?.page || 1, search, roleFilter);
  };

  const handleToggleRole = async (user: AdminUser) => {
    const newRole = user.role === "admin" ? "user" : "admin";
    await updateUser(user.id, { role: newRole });
    fetchUsers(users?.page || 1, search, roleFilter);
  };

  const handleResetPassword = async () => {
    if (!editingUser || !newPassword) return;
    await updateUser(editingUser.id, { reset_password: newPassword });
    setEditingUser(null);
    setNewPassword("");
    fetchUsers(users?.page || 1, search, roleFilter);
  };

  const handleExport = () => {
    const token = localStorage.getItem("access_token");
    const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/admin/export/users`;
    const a = document.createElement("a");
    a.href = url;
    // Using fetch to add auth header
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => res.blob())
      .then((blob) => {
        const blobUrl = URL.createObjectURL(blob);
        a.href = blobUrl;
        a.download = "users_export.csv";
        a.click();
        URL.revokeObjectURL(blobUrl);
      });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Utilisateurs</h1>
          <p className="text-muted-foreground">
            {users?.total || 0} utilisateur{(users?.total || 0) > 1 ? "s" : ""} au total
          </p>
        </div>
        <Button variant="outline" onClick={handleExport}>
          <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          Exporter CSV
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <Input
          placeholder="Rechercher par email ou nom..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="max-w-sm"
        />
        <select
          value={roleFilter}
          onChange={(e) => {
            setRoleFilter(e.target.value);
            fetchUsers(1, search, e.target.value);
          }}
          className="rounded-md border border-border bg-background px-3 py-2 text-sm"
        >
          <option value="">Tous les rôles</option>
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>
        <Button onClick={handleSearch}>Rechercher</Button>
      </div>

      {/* Users table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Email</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Nom</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Rôle</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Organisation</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Statut</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Créé le</th>
                  <th className="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users?.items.map((user) => (
                  <tr key={user.id} className="border-b border-border last:border-0 hover:bg-accent/50">
                    <td className="px-4 py-3 font-medium">{user.email}</td>
                    <td className="px-4 py-3">{user.full_name || "-"}</td>
                    <td className="px-4 py-3">
                      <Badge variant={user.role === "admin" ? "default" : "outline"}>
                        {user.role}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{user.organization_name || "-"}</td>
                    <td className="px-4 py-3">
                      <Badge variant={user.is_active ? "default" : "destructive"}>
                        {user.is_active ? "Actif" : "Inactif"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(user.created_at).toLocaleDateString("fr-FR")}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleActive(user)}
                          title={user.is_active ? "Désactiver" : "Activer"}
                        >
                          {user.is_active ? "Désactiver" : "Activer"}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleRole(user)}
                          title={user.role === "admin" ? "Rétrograder" : "Promouvoir admin"}
                        >
                          {user.role === "admin" ? "Rétrograder" : "Promouvoir"}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setEditingUser(user)}
                        >
                          MDP
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
                {(!users || users.items.length === 0) && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                      Aucun utilisateur trouvé
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Pagination */}
      {users && users.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          {Array.from({ length: users.pages }, (_, i) => i + 1).map((p) => (
            <Button
              key={p}
              variant={p === users.page ? "default" : "outline"}
              size="sm"
              onClick={() => fetchUsers(p, search, roleFilter)}
            >
              {p}
            </Button>
          ))}
        </div>
      )}

      {/* Password reset modal */}
      {editingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Reset mot de passe</CardTitle>
              <p className="text-sm text-muted-foreground">{editingUser.email}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                type="password"
                placeholder="Nouveau mot de passe"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
              <div className="flex gap-2">
                <Button onClick={handleResetPassword} disabled={!newPassword}>
                  Confirmer
                </Button>
                <Button variant="outline" onClick={() => { setEditingUser(null); setNewPassword(""); }}>
                  Annuler
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
