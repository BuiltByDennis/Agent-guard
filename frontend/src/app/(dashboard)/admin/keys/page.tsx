"use client";

import { Key } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function KeysPage() {
  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-heading font-semibold tracking-tight">API Keys</h1>
        <p className="text-muted-foreground mt-1 text-sm">Provision and manage agent authentication keys</p>
      </div>

      <Card className="bg-card/50 backdrop-blur-md border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Key className="w-5 h-5 mr-2 text-primary" />
            Key Management
          </CardTitle>
          <CardDescription>
            API Keys are uniquely tied to Agents. To generate a new API key, you must provision a new Agent identity.
            For security reasons, existing keys cannot be viewed after creation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="p-6 bg-white/5 border border-white/10 rounded-md text-center space-y-4">
            <p className="text-muted-foreground text-sm">
              Need to rotate a compromised key? Suspend the existing agent and provision a new one.
            </p>
            <Link href="/agents">
              <Button>Go to Agent Provisioning</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
