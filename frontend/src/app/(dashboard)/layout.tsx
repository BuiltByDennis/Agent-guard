"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, Users, Activity, Key, Settings, Menu, X, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Agents", href: "/agents", icon: ShieldAlert },
    { name: "Telemetry", href: "/telemetry", icon: Activity },
    { name: "Users", href: "/admin/users", icon: Users },
    { name: "API Keys", href: "/admin/keys", icon: Key },
    { name: "Settings", href: "/settings", icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row font-sans">
      {/* Mobile Header */}
      <div className="md:hidden flex items-center justify-between p-4 border-b border-white/10 bg-card/50">
        <div className="flex items-center space-x-2 text-emerald-500">
          <ShieldAlert className="w-6 h-6" />
          <span className="font-heading font-bold text-lg tracking-tight text-white">AgentGuard</span>
        </div>
        <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)}>
          {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </Button>
      </div>

      {/* Sidebar */}
      <aside className={`
        ${sidebarOpen ? "block" : "hidden"} 
        md:block w-full md:w-64 border-r border-white/10 bg-card/30 flex-shrink-0
      `}>
        <div className="h-full flex flex-col p-4">
          <div className="hidden md:flex items-center space-x-2 text-emerald-500 px-2 py-4 mb-6">
            <ShieldAlert className="w-6 h-6" />
            <span className="font-heading font-bold text-xl tracking-tight text-white">AgentGuard</span>
          </div>

          <nav className="space-y-1 flex-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`
                    flex items-center px-3 py-2.5 text-sm font-medium rounded-md transition-colors
                    ${isActive 
                      ? "bg-primary/10 text-primary" 
                      : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                    }
                  `}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className={`mr-3 flex-shrink-0 h-5 w-5 ${isActive ? "text-primary" : "text-muted-foreground"}`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
          
          <div className="mt-8 pt-4 border-t border-white/10">
            <Button 
              variant="ghost" 
              className="w-full justify-start text-muted-foreground hover:text-red-400 hover:bg-red-900/20"
              onClick={() => {
                localStorage.removeItem("token");
                document.cookie = "token=; path=/; max-age=0";
                router.push("/login");
              }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-3 h-5 w-5"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
              Logout
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
