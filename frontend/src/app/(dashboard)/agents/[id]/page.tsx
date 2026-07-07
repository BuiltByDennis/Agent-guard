"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Activity, ShieldAlert, Cpu, List, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { apiFetch } from "@/lib/api";

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;

  const { data: performance, isLoading: loadingPerf } = useQuery({
    queryKey: ["agent_performance", agentId],
    queryFn: async () => {
      const res = await apiFetch(`/v1/agents/${agentId}/performance`);
      if (!res.ok) throw new Error("Failed to fetch performance");
      return res.json();
    },
  });

  const { data: agents, refetch: refetchAgents } = useQuery({
    queryKey: ["agents"],
    queryFn: async () => {
      const res = await apiFetch("/v1/agents/metrics");
      if (!res.ok) throw new Error("Failed to fetch agents");
      return res.json();
    },
  });

  const agent = agents?.find((a: any) => a.id === agentId);
  const isSuspended = agent?.status === "Blocked";

  const toggleStatus = async () => {
    const newStatus = isSuspended ? "active" : "suspended";
    try {
      const res = await apiFetch(`/v1/admin/agents/${agentId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        refetchAgents();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const deleteAgent = async () => {
    if (!confirm("Are you sure you want to permanently revoke and delete this agent?")) return;
    try {
      const res = await apiFetch(`/v1/admin/agents/${agentId}`, { method: "DELETE" });
      if (res.ok) {
        router.push("/agents");
      } else {
        alert("Failed to delete agent.");
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (loadingPerf || !agents) return <div className="p-6 text-muted-foreground">Loading agent data...</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-3xl font-heading font-semibold tracking-tight">{agentId}</h1>
            {isSuspended && <span className="bg-red-900/40 text-red-400 border border-red-500/20 text-xs px-2 py-0.5 rounded-full">Suspended</span>}
          </div>
          <p className="text-muted-foreground mt-1 text-sm">Agent detail and performance metrics</p>
        </div>
        <div className="flex space-x-3">
          <Link href={`/agents/${agentId}/logs`}>
            <Button variant="outline" className="border-white/10 hover:bg-white/5">
              <List className="w-4 h-4 mr-2" />
              View Logs
            </Button>
          </Link>
          <Button variant="destructive" onClick={deleteAgent}>
            <Trash2 className="w-4 h-4 mr-2" />
            Delete Agent
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-card/50 backdrop-blur-md border-white/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
              <Activity className="w-4 h-4 mr-2 text-primary" />
              Performance Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col">
              <span className="text-4xl font-mono font-bold tracking-tighter text-emerald-400">
                {performance?.overall_score ?? 100} / 100
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur-md border-white/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
              <ShieldAlert className="w-4 h-4 mr-2 text-primary" />
              Kill Switch
            </CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <div className="text-sm">
              <p className="font-medium text-white">{isSuspended ? "Agent is Suspended" : "Agent is Active"}</p>
              <p className="text-muted-foreground text-xs mt-1">Toggle to block API access instantly.</p>
            </div>
            <Switch 
              checked={!isSuspended}
              onCheckedChange={toggleStatus}
              className="data-[state=checked]:bg-primary data-[state=unchecked]:bg-red-500"
            />
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur-md border-white/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
              <Cpu className="w-4 h-4 mr-2 text-primary" />
              Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 text-sm font-mono">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Trace Type:</span>
                <span>{agent?.type || "unknown"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Cost:</span>
                <span>${agent?.cost?.toFixed(4) || "0.0000"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Avg Latency:</span>
                <span>{agent?.latency || 0}ms</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-card/50 backdrop-blur-md border-white/10">
        <CardHeader>
          <CardTitle>Score Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 font-mono text-sm">
            <div className="bg-black/20 p-4 rounded-md border border-white/5">
              <p className="text-muted-foreground mb-1">Success Rate</p>
              <p className="text-xl">{(performance?.breakdown?.success_rate * 100 || 100).toFixed(1)}%</p>
            </div>
            <div className="bg-black/20 p-4 rounded-md border border-white/5">
              <p className="text-muted-foreground mb-1">Format Accuracy</p>
              <p className="text-xl">{(performance?.breakdown?.format_accuracy * 100 || 100).toFixed(1)}%</p>
            </div>
            <div className="bg-black/20 p-4 rounded-md border border-white/5">
              <p className="text-muted-foreground mb-1">Budget Efficiency</p>
              <p className="text-xl">{(performance?.breakdown?.budget_efficiency * 100 || 100).toFixed(1)}%</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
