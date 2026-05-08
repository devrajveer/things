"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { 
  Activity, 
  Cpu, 
  Zap, 
  Box 
} from "lucide-react";
import { useOrg } from "@/lib/org-context";
import { api } from "@/lib/api";
import { motion } from "framer-motion";
import Link from "next/link";

export default function Home() {
  const { activeProject } = useOrg();
  const [stats, setStats] = useState({
    devices: 0,
    rules: 0,
    fleets: 0,
    firmwares: 0
  });

  useEffect(() => {
    if (activeProject) {
      fetchStats();
    }
  }, [activeProject]);

  const fetchStats = async () => {
    try {
      const [dRes, rRes, fRes, fwRes] = await Promise.all([
        api.get(`/v1/projects/${activeProject?.id}/devices`),
        api.get(`/v1/projects/${activeProject?.id}/automation/rules`),
        api.get(`/v1/projects/${activeProject?.id}/fleets`),
        api.get(`/v1/projects/${activeProject?.id}/firmwares`)
      ]);
      setStats({
        devices: dRes.data?.length || 0,
        rules: rRes?.length || 0,
        fleets: fRes?.length || 0,
        firmwares: fwRes?.length || 0
      });
    } catch (err) {
      console.error("Failed to fetch stats", err);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">Welcome to MegaIoT</h1>
          <p className="text-muted-foreground">Here's the overview for {activeProject?.name || "your project"}.</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { name: "Total Devices", value: stats.devices, icon: Cpu, color: "text-blue-500", bg: "bg-blue-500/10", href: "/devices" },
            { name: "Active Rules", value: stats.rules, icon: Zap, color: "text-amber-500", bg: "bg-amber-500/10", href: "/rules" },
            { name: "Fleets", value: stats.fleets, icon: Box, color: "text-primary", bg: "bg-primary/10", href: "/fleets" },
            { name: "Firmwares", value: stats.firmwares, icon: Activity, color: "text-emerald-500", bg: "bg-emerald-500/10", href: "/firmwares" },
          ].map((stat, i) => (
            <Link key={stat.name} href={stat.href}>
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="p-6 rounded-2xl bg-card border glass-dark group hover:border-primary/50 hover:-translate-y-1 transition-all cursor-pointer h-full"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-2 rounded-lg ${stat.bg}`}>
                    <stat.icon className={`w-5 h-5 ${stat.color}`} />
                  </div>
                </div>
                <p className="text-sm font-medium text-muted-foreground">{stat.name}</p>
                <p className="text-3xl font-bold mt-1">{stat.value}</p>
              </motion.div>
            </Link>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="p-8 rounded-3xl bg-card border glass-dark space-y-4">
             <h2 className="text-xl font-bold">Quick Actions</h2>
             <div className="flex flex-col gap-2">
                <Link href="/devices" className="p-4 rounded-xl bg-background border hover:border-primary/50 transition-colors flex items-center justify-between">
                  <span>Register a Device</span>
                  <span className="text-muted-foreground">&rarr;</span>
                </Link>
                <Link href="/rules/create" className="p-4 rounded-xl bg-background border hover:border-primary/50 transition-colors flex items-center justify-between">
                  <span>Create an Automation Rule</span>
                  <span className="text-muted-foreground">&rarr;</span>
                </Link>
                <Link href="/fleets" className="p-4 rounded-xl bg-background border hover:border-primary/50 transition-colors flex items-center justify-between">
                  <span>Manage Fleets</span>
                  <span className="text-muted-foreground">&rarr;</span>
                </Link>
             </div>
          </div>
          <div className="p-8 rounded-3xl bg-primary/5 border border-primary/20 space-y-4 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-primary/30 transition-colors" />
            <h2 className="text-xl font-bold relative z-10">Data Pipeline Simulation</h2>
            <p className="text-muted-foreground relative z-10">
              Want to see the dashboards light up? You can use the provided Python script to simulate a device sending telemetry points every few seconds.
            </p>
            <div className="p-4 rounded-xl bg-black/40 font-mono text-sm relative z-10 text-primary-foreground border border-white/10">
              <code>python scripts/simulate_device.py</code>
            </div>
            <p className="text-xs text-muted-foreground mt-2 relative z-10">
              Requires a local environment with the backend running.
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
