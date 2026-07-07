"use client";

import { useState, useEffect } from "react";
import { Activity, Zap, Clock, ShieldAlert, Cpu, Power } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Switch } from "@/components/ui/switch";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export default function Dashboard() {
  const router = useRouter();
  
  // Auth Check
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  const { data: queryAgents, refetch, isLoading: loadingAgents } = useQuery({
    queryKey: ["agents"],
    queryFn: async () => {
      const res = await apiFetch("/v1/agents/metrics");
      if (!res.ok) throw new Error("Failed to fetch agents");
      return res.json();
    },
    refetchInterval: 5000,
  });

  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ["telemetry_summary"],
    queryFn: async () => {
      const res = await apiFetch("/v1/telemetry/summary");
      if (!res.ok) throw new Error("Failed to fetch summary");
      return res.json();
    },
    refetchInterval: 5000,
  });

  const agentsToDisplay = queryAgents || [];
  
  const toggleAgent = async (id: string) => {
    const agent = agentsToDisplay?.find((a: any) => a.id === id);
    if (!agent) return;
    
    const newStatus = agent.status === "Blocked" ? "active" : "suspended";
    
    try {
      const res = await apiFetch(`/v1/admin/agents/${id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        refetch();
      }
    } catch (e) {
      console.error("Failed to toggle agent status", e);
    }
  };

  const isLoading = loadingAgents || loadingSummary;

  return (
    <div className="min-h-screen bg-background text-foreground p-6 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-heading font-semibold tracking-tight">Vigilance Operations</h1>
            <p className="text-muted-foreground mt-1 text-sm">Agent Guardrail Proxy Control Center</p>
          </div>
          <div className="flex items-center space-x-2 text-emerald-500 bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20">
            <Activity className="w-4 h-4 animate-pulse" />
            <span className="text-xs font-bold tracking-wider uppercase">System Secure</span>
          </div>
        </div>

        {/* Top Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Live Token Odometer */}
          <Card className="bg-card/50 backdrop-blur-md border-white/10 md:col-span-1">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                <Zap className="w-4 h-4 mr-2 text-primary" />
                Live Token Odometer
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2 animate-pulse">
                  <div className="h-8 w-32 bg-white/10 rounded"></div>
                  <div className="h-4 w-24 bg-white/10 rounded"></div>
                </div>
              ) : (
                <div className="flex flex-col">
                  <span className="text-4xl font-mono font-bold tracking-tighter text-primary">
                    {summary?.tokens?.toLocaleString() || 0}
                  </span>
                  <span className="text-lg font-mono text-muted-foreground mt-1">
                    ${summary?.cost?.toFixed(4) || "0.0000"} USD
                  </span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Health Metrics */}
          <Card className="bg-card/50 backdrop-blur-md border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                <Clock className="w-4 h-4 mr-2 text-primary" />
                Avg Latency
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2 animate-pulse">
                  <div className="h-8 w-24 bg-white/10 rounded"></div>
                  <div className="h-4 w-32 bg-white/10 rounded"></div>
                </div>
              ) : (
                <>
                  <div className="text-3xl font-mono font-bold">
                    {summary?.latency?.toFixed(0) || 0}<span className="text-lg text-muted-foreground">ms</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">Real-time moving average</p>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="bg-card/50 backdrop-blur-md border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                <ShieldAlert className="w-4 h-4 mr-2 text-primary" />
                Success Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2 animate-pulse">
                  <div className="h-8 w-24 bg-white/10 rounded"></div>
                  <div className="h-4 w-32 bg-white/10 rounded"></div>
                </div>
              ) : (
                <>
                  <div className="text-3xl font-mono font-bold text-emerald-500">
                    {((summary?.success_rate || 0) * 100).toFixed(1)}%
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">Global policy enforcement</p>
                </>
              )}
            </CardContent>
          </Card>

        </div>

        {/* Real-Time Agent Feed */}
        <Card className="bg-card/50 backdrop-blur-md border-white/10">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Cpu className="w-5 h-5 mr-2 text-primary" />
              Real-Time Agent Feed
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
                    <TableHead className="font-heading text-xs tracking-wider uppercase text-right">Latency</TableHead>
                    <TableHead className="font-heading text-xs tracking-wider uppercase text-right">Cost</TableHead>
                    <TableHead className="font-heading text-xs tracking-wider uppercase text-right">Kill Switch</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8">
                        <div className="flex flex-col items-center justify-center space-y-3 text-muted-foreground animate-pulse">
                          <Cpu className="w-8 h-8 opacity-20" />
                          <p>Loading agent telemetry...</p>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : agentsToDisplay.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                        No active agents found.
                      </TableCell>
                    </TableRow>
                  ) : (
                    agentsToDisplay.map((agent: any) => (
                      <TableRow key={agent.id} className="border-white/10 hover:bg-white/5 transition-colors">
                        <TableCell className="font-mono text-sm font-medium">{agent.id}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="font-mono text-xs border-white/20 text-muted-foreground">
                            {agent.type}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {agent.status === "Emerald" && <Badge className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 border-emerald-500/20">Healthy</Badge>}
                          {agent.status === "Amber" && <Badge className="bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 border-amber-500/20">Warning</Badge>}
                          {agent.status === "Ruby" && <Badge className="bg-ruby-500/10 text-ruby-500 hover:bg-ruby-500/20 border-ruby-500/20">Critical</Badge>}
                          {agent.status === "Blocked" && <Badge className="bg-red-900/40 text-red-400 hover:bg-red-900/60 border-red-500/20">Blocked</Badge>}
                        </TableCell>
                        <TableCell className="text-right font-mono text-sm">
                          {agent.latency}ms
                        </TableCell>
                        <TableCell className="text-right font-mono text-sm">
                          ${agent.cost.toFixed(4)}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end items-center space-x-2">
                            <Switch 
                              checked={agent.status !== "Blocked"}
                              onCheckedChange={() => toggleAgent(agent.id)}
                              className="data-[state=checked]:bg-primary data-[state=unchecked]:bg-muted"
                            />
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
