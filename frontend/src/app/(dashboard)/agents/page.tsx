"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Plus, Cpu } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

export default function AgentsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newAgentName, setNewAgentName] = useState("");
  const [newAgentId, setNewAgentId] = useState("");
  const [generatedKey, setGeneratedKey] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: agents, refetch, isLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: async () => {
      const res = await apiFetch("/v1/agents/metrics");
      if (!res.ok) throw new Error("Failed to fetch");
      return res.json();
    },
  });

  const handleCreateAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await apiFetch("/v1/admin/agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newAgentName, agent_id: newAgentId })
      });
      if (res.ok) {
        const data = await res.json();
        setGeneratedKey(data.api_key);
        refetch();
      } else {
        alert("Failed to create agent. Check if ID already exists.");
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-semibold tracking-tight">Agents</h1>
          <p className="text-muted-foreground mt-1 text-sm">Manage autonomous agents and API access</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Provision Agent
        </Button>
      </div>

      <Card className="bg-card/50 backdrop-blur-md border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Cpu className="w-5 h-5 mr-2 text-primary" />
            Active Fleet
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-white/10">
            <Table>
              <TableHeader className="bg-white/5">
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead className="font-heading text-xs tracking-wider uppercase">Agent ID</TableHead>
                  <TableHead className="font-heading text-xs tracking-wider uppercase">Trace Type</TableHead>
                  <TableHead className="font-heading text-xs tracking-wider uppercase">Status</TableHead>
                  <TableHead className="font-heading text-xs tracking-wider uppercase text-right">Avg Latency</TableHead>
                  <TableHead className="font-heading text-xs tracking-wider uppercase text-right">Total Cost</TableHead>
                  <TableHead className="font-heading text-xs tracking-wider uppercase text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={6} className="text-center py-8 text-muted-foreground">Loading fleet data...</TableCell></TableRow>
                ) : agents?.map((agent: any) => (
                  <TableRow key={agent.id} className="border-white/10 hover:bg-white/5 transition-colors">
                    <TableCell className="font-mono text-sm font-medium">{agent.id}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-xs border-white/20 text-muted-foreground">
                        {agent.type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {agent.status === "Emerald" && <Badge className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 border-emerald-500/20">Healthy</Badge>}
                      {agent.status === "Blocked" && <Badge className="bg-red-900/40 text-red-400 hover:bg-red-900/60 border-red-500/20">Suspended</Badge>}
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm">{agent.latency}ms</TableCell>
                    <TableCell className="text-right font-mono text-sm">${agent.cost.toFixed(4)}</TableCell>
                    <TableCell className="text-right">
                      <Link href={`/agents/${agent.id}`}>
                        <Button variant="outline" size="sm" className="border-white/20 hover:bg-white/10">
                          Inspect
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
                {!isLoading && (!agents || agents.length === 0) && (
                  <TableRow><TableCell colSpan={6} className="text-center py-8 text-muted-foreground">No agents provisioned yet.</TableCell></TableRow>
                )}
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
              <CardTitle>Provision New Agent</CardTitle>
            </CardHeader>
            <CardContent>
              {generatedKey ? (
                <div className="space-y-4">
                  <div className="bg-emerald-500/10 text-emerald-500 p-3 rounded-md text-sm border border-emerald-500/20">
                    Agent successfully provisioned!
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">API Key (Save this now!)</label>
                    <div className="p-3 bg-black border border-white/10 rounded-md font-mono text-xs text-emerald-400 break-all mt-1">
                      {generatedKey}
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">This key will not be shown again.</p>
                  </div>
                  <div className="flex justify-end pt-4">
                    <Button onClick={() => { setIsModalOpen(false); setGeneratedKey(""); setNewAgentId(""); setNewAgentName(""); }}>Done</Button>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleCreateAgent} className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-muted-foreground">Agent Display Name</label>
                    <input 
                      required 
                      type="text" 
                      className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-sm text-white focus:outline-none focus:border-primary" 
                      value={newAgentName} 
                      onChange={e => setNewAgentName(e.target.value)} 
                      placeholder="e.g. Research Assistant"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-muted-foreground">Agent ID (Alphanumeric/Dashes)</label>
                    <input 
                      required 
                      type="text" 
                      pattern="^[a-zA-Z0-9_-]+$"
                      className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-sm text-white focus:outline-none focus:border-primary font-mono" 
                      value={newAgentId} 
                      onChange={e => setNewAgentId(e.target.value)} 
                      placeholder="e.g. research-bot-01"
                    />
                  </div>
                  <div className="flex justify-end space-x-2 pt-4">
                    <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                    <Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Provisioning..." : "Generate Key"}</Button>
                  </div>
                </form>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
