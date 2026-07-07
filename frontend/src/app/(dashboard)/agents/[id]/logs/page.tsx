"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { List } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function AgentLogsPage() {
  const params = useParams();
  const agentId = params.id as string;
  const [statusFilter, setStatusFilter] = useState<string>("");

  const { data: logs, isLoading } = useQuery({
    queryKey: ["agent_logs", agentId, statusFilter],
    queryFn: async () => {
      let url = `/v1/agents/${agentId}/logs?limit=50`;
      if (statusFilter) url += `&status_filter=${statusFilter}`;
      const res = await apiFetch(url);
      if (!res.ok) throw new Error("Failed to fetch logs");
      return res.json();
    },
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-semibold tracking-tight">Logs: {agentId}</h1>
          <p className="text-muted-foreground mt-1 text-sm">Interaction spans and firewall traces</p>
        </div>
        <select 
          className="bg-black border border-white/10 rounded-md p-2 text-sm focus:outline-none"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          <option value="200">200 OK</option>
          <option value="403">403 Blocked</option>
          <option value="402">402 Suspended</option>
        </select>
      </div>

      <Card className="bg-card/50 backdrop-blur-md border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center">
            <List className="w-5 h-5 mr-2 text-primary" />
            Recent Spans
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-white/10">
            <Table>
              <TableHeader className="bg-white/5">
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead className="font-heading text-xs tracking-wider uppercase">Timestamp</TableHead>
                  <TableHead className="font-heading text-xs tracking-wider uppercase">Type</TableHead>
                  <TableHead className="font-heading text-xs tracking-wider uppercase">Tokens</TableHead>
                  <TableHead className="font-heading text-xs tracking-wider uppercase">Latency</TableHead>
                  <TableHead className="font-heading text-xs tracking-wider uppercase">Status</TableHead>
                  <TableHead className="font-heading text-xs tracking-wider uppercase">Error</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={6} className="text-center py-8 text-muted-foreground">Loading logs...</TableCell></TableRow>
                ) : logs?.map((log: any) => (
                  <TableRow key={log.id} className="border-white/10 hover:bg-white/5 transition-colors">
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {new Date(log.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="font-mono text-xs">{log.agent_type}</TableCell>
                    <TableCell className="font-mono text-xs">{log.tokens_used}</TableCell>
                    <TableCell className="font-mono text-xs">{log.latency_ms?.toFixed(0)}ms</TableCell>
                    <TableCell>
                      {log.status_code === 200 ? (
                        <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">200</Badge>
                      ) : (
                        <Badge className="bg-red-900/40 text-red-400 border-red-500/20">{log.status_code}</Badge>
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-red-400 max-w-[200px] truncate" title={log.error_log}>
                      {log.error_log || "-"}
                    </TableCell>
                  </TableRow>
                ))}
                {!isLoading && (!logs || logs.length === 0) && (
                  <TableRow><TableCell colSpan={6} className="text-center py-8 text-muted-foreground">No logs found.</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
