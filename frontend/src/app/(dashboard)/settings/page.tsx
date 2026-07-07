"use client";

import { Settings as SettingsIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-heading font-semibold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1 text-sm">Personal preferences and security</p>
      </div>

      <Card className="bg-card/50 backdrop-blur-md border-white/10 max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center">
            <SettingsIcon className="w-5 h-5 mr-2 text-primary" />
            Account Security
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={e => e.preventDefault()}>
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">Current Password</label>
              <input 
                type="password" 
                className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-sm text-white focus:outline-none focus:border-primary" 
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">New Password</label>
              <input 
                type="password" 
                className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-sm text-white focus:outline-none focus:border-primary" 
              />
            </div>
            <div className="flex justify-end pt-4">
              <Button type="button" onClick={() => alert("Password update mock success.")}>Update Password</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
