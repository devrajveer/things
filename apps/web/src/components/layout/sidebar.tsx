"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Cpu, 
  Zap, 
  BarChart3, 
  Settings, 
  Users, 
  Box,
  ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

const menuItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Devices", href: "/devices", icon: Cpu },
  { name: "Fleets", href: "/fleets", icon: Box },
  { name: "Firmwares", href: "/firmwares", icon: Box },
  { name: "Rules", href: "/rules", icon: Zap },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Organization", href: "/org", icon: Users },
  { name: "Projects", href: "/projects", icon: Box },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="w-64 h-screen border-r bg-card flex flex-col glass-dark">
      <div className="p-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg premium-gradient flex items-center justify-center">
            <Zap className="text-white w-5 h-5" />
          </div>
          <span className="text-xl font-bold tracking-tight">MegaIoT</span>
        </div>
      </div>

      <nav className="flex-1 px-4 py-2 space-y-1">
        {menuItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link key={item.name} href={item.href}>
              <div
                className={cn(
                  "group flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 cursor-pointer",
                  isActive 
                    ? "bg-primary/10 text-primary" 
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                )}
              >
                <item.icon className={cn("w-5 h-5", isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
                <span className="flex-1 font-medium">{item.name}</span>
                {isActive && (
                  <motion.div 
                    layoutId="active-pill"
                    className="w-1.5 h-1.5 rounded-full bg-primary"
                  />
                )}
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 mt-auto border-t border-white/5">
        <div className="bg-white/5 rounded-2xl p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-500" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold truncate">Rajveer Singh</p>
              <p className="text-xs text-muted-foreground truncate">Free Tier</p>
            </div>
          </div>
          <button className="w-full py-2 px-4 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-semibold transition-colors">
            Upgrade to Pro
          </button>
        </div>
      </div>
    </div>
  );
}
