"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Users, Plus, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

export default function UsersPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("viewer");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: users, refetch, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: async () => {
      const res = await apiFetch("/v1/admin/users");
      if (!res.ok) throw new Error("Failed to fetch users");
      return res.json();
    },
  });

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await apiFetch("/v1/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, role })
      });
      if (res.ok) {
        setIsModalOpen(false);
        setEmail("");
        setPassword("");
        refetch();
      } else {
        alert("Failed to create user. Ensure email is valid and password >= 8 chars.");
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRevoke = async (userId: string) => {
    if (!confirm("Are you sure you want to revoke this user's access?")) return;
    try {
      const res = await apiFetch(`/v1/admin/users/${userId}`, { method: "DELETE" });
      if (res.ok) {
        refetch();
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-semibold tracking-tight">Users</h1>
          <p className="text-muted-foreground mt-1 text-sm">Manage dashboard access and roles</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Invite User
        </Button>
      </div>

      <Card className="bg-card/50 backdrop-blur-md border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Users className="w-5 h-5 mr-2 text-primary" />
            Active Users
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-white/10">
            <Table>
              <TableHeader className="bg-white/5">
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead className="font-heading text-xs tracking-wider uppercase">User ID</TableHead>
                  <TableHead className="font-heading text-xs tracking-wider uppercase">Email</TableHead>
                  <TableHead className="font-heading text-xs tracking-wider uppercase">Role</TableHead>
                  <TableHead className="font-heading text-xs tracking-wider uppercase text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={4} className="text-center py-8 text-muted-foreground">Loading users...</TableCell></TableRow>
                ) : users?.map((user: any) => (
                  <TableRow key={user.id} className="border-white/10 hover:bg-white/5 transition-colors">
                    <TableCell className="font-mono text-xs text-muted-foreground">{user.id}</TableCell>
                    <TableCell className="font-medium text-sm">{user.email}</TableCell>
                    <TableCell>
                      {user.role === "admin" ? (
                        <Badge className="bg-purple-500/10 text-purple-400 border-purple-500/20">Admin</Badge>
                      ) : (
                        <Badge variant="outline" className="text-muted-foreground border-white/20">Viewer</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" className="text-red-400 hover:text-red-300 hover:bg-red-900/20" onClick={() => handleRevoke(user.id)}>
                        <Trash2 className="w-4 h-4 mr-2" />
                        Revoke
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Modal Overlay */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <Card className="w-full max-w-md bg-zinc-950 border-white/10 shadow-2xl">
            <CardHeader>
              <CardTitle>Invite New User</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateUser} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-muted-foreground">Email Address</label>
                  <input 
                    required 
                    type="email" 
                    className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-sm text-white focus:outline-none focus:border-primary" 
                    value={email} 
                    onChange={e => setEmail(e.target.value)} 
                    placeholder="name@example.com"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-muted-foreground">Temporary Password</label>
                  <input 
                    required 
                    type="password" 
                    minLength={8}
                    className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-sm text-white focus:outline-none focus:border-primary" 
                    value={password} 
                    onChange={e => setPassword(e.target.value)} 
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-muted-foreground">Role</label>
                  <select 
                    className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-sm text-white focus:outline-none focus:border-primary"
                    value={role}
                    onChange={e => setRole(e.target.value)}
                  >
                    <option value="viewer">Viewer</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                <div className="flex justify-end space-x-2 pt-4">
                  <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                  <Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Creating..." : "Create User"}</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
