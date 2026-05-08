"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { 
  Cpu, 
  ArrowLeft,
  Settings,
  Activity,
  History,
  Info,
  Clock,
  ExternalLink,
  ChevronRight,
  Loader2,
  Trash2,
  Lock,
  Tag
} from "lucide-react";
import { api } from "@/lib/api";
import { useOrg } from "@/lib/org-context";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface Device {
  id: string;
  name: string;
  status: string;
  labels: Record<string, string>;
  description?: string;
  created_at: string;
}

interface Stream {
  id: string;
  key: string;
  value_type: string;
  unit?: string;
  display_name?: string;
  last_value: any;
  last_value_at?: string;
}

export default function DeviceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { activeProject } = useOrg();
  const [device, setDevice] = useState<Device | null>(null);
  const [streams, setStreams] = useState<Stream[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "streams" | "settings">("overview");

  useEffect(() => {
    if (activeProject && params.id) {
      fetchData();
    }
  }, [activeProject, params.id]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch device
      const deviceRes = await api.get(`/v1/projects/${activeProject?.id}/devices`);
      const found = deviceRes.data.find((d: any) => d.id === params.id);
      if (found) {
        setDevice(found);
      }

      // Fetch streams
      const streamsRes = await api.get(`/v1/projects/${activeProject?.id}/streams?device_id=${params.id}`);
      setStreams(streamsRes.data);
    } catch (err) {
      console.error("Failed to fetch device details", err);
    } finally {
      setLoading(false);
    }
  };

  // Real-time updates
  useEffect(() => {
    if (!activeProject || !params.id) return;

    const eventSource = new EventSource(`http://localhost:3001/v1/realtime/projects/${activeProject.id}`);
    
    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.schema === "telemetry.datapoint.v1" && payload.data.device_id === params.id) {
          const dp = payload.data;
          setStreams(prev => prev.map(s => {
            if (s.key === dp.key) {
              return {
                ...s,
                last_value: dp.value_num ?? dp.value_bool ?? dp.value_str ?? dp.value_json,
                last_value_at: dp.ts
              };
            }
            return s;
          }));
        }
      } catch (err) {
        console.error("Error parsing real-time message", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE Connection error", err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [activeProject, params.id]);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="h-[60vh] flex flex-col items-center justify-center gap-4 text-muted-foreground">
          <Loader2 className="w-10 h-10 animate-spin text-primary" />
          <p className="text-lg">Fetching device data...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (!device) {
    return (
      <DashboardLayout>
        <div className="text-center py-20">
          <h2 className="text-2xl font-bold mb-2">Device not found</h2>
          <button onClick={() => router.push("/devices")} className="text-primary hover:underline flex items-center gap-1 mx-auto">
            <ArrowLeft className="w-4 h-4" /> Back to devices
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Breadcrumbs & Header */}
        <div className="flex flex-col gap-4">
          <button 
            onClick={() => router.push("/devices")}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors w-fit"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Devices
          </button>
          
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                <Cpu className="w-8 h-8" />
              </div>
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h1 className="text-3xl font-bold tracking-tight">{device.name}</h1>
                  <span className={cn(
                    "px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider",
                    device.status === "active" ? "bg-emerald-500/10 text-emerald-500" : "bg-blue-500/10 text-blue-500"
                  )}>
                    {device.status}
                  </span>
                </div>
                <p className="text-sm font-mono text-muted-foreground">{device.id}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-card border glass-dark hover:bg-secondary transition-colors text-sm font-semibold">
                <History className="w-4 h-4" />
                Logs
              </button>
              <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-destructive/10 text-destructive border border-destructive/20 hover:bg-destructive/20 transition-colors text-sm font-semibold">
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 p-1 rounded-2xl bg-card/50 border w-fit">
          {[
            { id: "overview", label: "Overview", icon: Info },
            { id: "streams", label: "Streams", icon: Activity },
            { id: "settings", label: "Settings", icon: Settings },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={cn(
                "flex items-center gap-2 px-6 py-2 rounded-xl text-sm font-semibold transition-all",
                activeTab === tab.id 
                  ? "bg-primary text-primary-foreground shadow-lg" 
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {activeTab === "overview" && (
            <>
              <div className="lg:col-span-2 space-y-8">
                {/* Meta Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div className="p-6 rounded-3xl bg-card border glass-dark">
                    <div className="flex items-center gap-3 mb-4 text-muted-foreground">
                      <Clock className="w-5 h-5" />
                      <span className="text-sm font-medium">Last Activity</span>
                    </div>
                    <p className="text-2xl font-bold">2 minutes ago</p>
                    <p className="text-xs text-muted-foreground mt-1">2026-05-05 10:42:12 UTC</p>
                  </div>
                  <div className="p-6 rounded-3xl bg-card border glass-dark">
                    <div className="flex items-center gap-3 mb-4 text-muted-foreground">
                      <Tag className="w-5 h-5" />
                      <span className="text-sm font-medium">Profile</span>
                    </div>
                    <p className="text-2xl font-bold truncate">Generic MQTT</p>
                    <button className="text-xs text-primary hover:underline mt-1 flex items-center gap-1">
                      View Profile <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>

                {/* Description & Labels */}
                <div className="p-8 rounded-3xl bg-card border glass-dark space-y-6">
                  <div>
                    <h3 className="text-lg font-bold mb-4">Device Description</h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {device.description || "No description provided for this device."}
                    </p>
                  </div>
                  <div className="pt-6 border-t border-white/5">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-4">Labels</h3>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(device.labels).map(([key, val]) => (
                        <div key={key} className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 text-xs">
                          <span className="text-muted-foreground">{key}:</span> <span className="font-semibold">{val}</span>
                        </div>
                      ))}
                      {Object.keys(device.labels).length === 0 && (
                        <p className="text-sm italic text-muted-foreground">No labels assigned.</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Sidebar Info */}
              <div className="space-y-6">
                <div className="p-6 rounded-3xl bg-emerald-500/5 border border-emerald-500/10 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold flex items-center gap-2">
                      <Lock className="w-4 h-4" /> Connection
                    </h3>
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Device is currently communicating via <strong>MQTT</strong> with QoS 1. Connection is stable.
                  </p>
                  <button className="w-full py-2 rounded-xl bg-emerald-500/10 text-emerald-500 text-xs font-bold hover:bg-emerald-500/20 transition-colors">
                    View Network Stats
                  </button>
                </div>
              </div>
            </>
          )}

          {activeTab === "streams" && (
            <div className="lg:col-span-3 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {streams.map((stream) => (
                  <div key={stream.id} className="p-6 rounded-3xl bg-card border glass-dark hover:border-primary/30 transition-all cursor-pointer group">
                    <div className="flex items-center justify-between mb-4">
                      <div className="p-2 rounded-xl bg-primary/10 text-primary">
                        <Activity className="w-5 h-5" />
                      </div>
                      <span className="text-[10px] font-bold uppercase text-muted-foreground">{stream.value_type}</span>
                    </div>
                    <h4 className="text-sm font-medium text-muted-foreground mb-1">{stream.display_name || stream.key}</h4>
                    <div className="flex items-baseline gap-2">
                      <p className="text-3xl font-bold">
                        {typeof stream.last_value === 'number' ? stream.last_value.toFixed(2) : String(stream.last_value)}
                      </p>
                      <span className="text-lg text-muted-foreground font-medium">{stream.unit}</span>
                    </div>
                    <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between text-[10px]">
                      <span className="text-muted-foreground flex items-center gap-1">
                        <Clock className="w-3 h-3" /> {stream.last_value_at ? new Date(stream.last_value_at).toLocaleTimeString() : 'Never'}
                      </span>
                      <span className="text-primary opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                        View History <ExternalLink className="w-2.5 h-2.5" />
                      </span>
                    </div>
                  </div>
                ))}
                
                {streams.length === 0 && (
                  <div className="md:col-span-2 lg:col-span-3 h-64 flex flex-col items-center justify-center text-center p-8 border-2 border-dashed border-white/5 rounded-3xl">
                    <Activity className="w-8 h-8 text-muted-foreground mb-4" />
                    <h4 className="font-bold mb-1">No streams yet</h4>
                    <p className="text-sm text-muted-foreground max-w-xs">
                      Once this device starts sending telemetry, its data streams will automatically appear here.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === "settings" && (
            <div className="lg:col-span-2 p-8 rounded-3xl bg-card border glass-dark">
              <h3 className="text-xl font-bold mb-6">Device Settings</h3>
              {/* Settings form placeholder */}
              <p className="text-muted-foreground italic">Advanced settings and credential rotation coming soon.</p>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
