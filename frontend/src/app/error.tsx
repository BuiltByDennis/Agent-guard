"use client";

import { useEffect } from "react";
import { ShieldAlert, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service in production
    console.error("Global application error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 font-sans">
      <Card className="w-full max-w-md bg-card/50 backdrop-blur-md border-red-500/20 shadow-2xl">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto bg-red-900/20 p-3 rounded-full w-16 h-16 flex items-center justify-center mb-4 border border-red-500/20">
            <ShieldAlert className="w-8 h-8 text-red-500" />
          </div>
          <CardTitle className="text-2xl font-heading font-bold text-white tracking-tight">System Fault Detected</CardTitle>
          <CardDescription className="text-muted-foreground mt-2">
            The AgentGuard interface encountered an unexpected exception while processing your request.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-black/50 p-4 rounded-md border border-white/10 overflow-auto">
            <p className="font-mono text-xs text-red-400 break-words">
              {error.message || "Unknown rendering error occurred"}
            </p>
          </div>
          <div className="flex flex-col space-y-2">
            <Button 
              onClick={() => reset()} 
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-medium"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Reinitialize Interface
            </Button>
            <Button 
              variant="outline" 
              onClick={() => window.location.href = "/"}
              className="w-full border-white/10 hover:bg-white/5"
            >
              Return to Control Center
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
