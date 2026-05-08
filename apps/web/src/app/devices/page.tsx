"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { 
  Cpu, 
  Plus, 
  Search, 
  Filter, 
  MoreHorizontal, 
  ExternalLink,
  Copy,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Key,
  Database
} from "lucide-react";
import { api } from "@/lib/api";
import { useOrg } from "@/lib/org-context";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

interface Device {
  id: string;
  name: string;
  status: string;
  labels: Record<string, string>;
  description?: string;
  created_at: string;
}

export default function DevicesPage() {
  const { activeProject } = useOrg();
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newDevice, setNewDevice] = useState({ name: "", description: "" });
  const [creating, setCreating] = useState(false);
  const [credentials, setCredentials] = useState<any>(null);

  useEffect(() => {
    if (activeProject) {
      fetchDevices();
    }
  }, [activeProject]);

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/v1/projects/${activeProject?.id}/devices`);
      setDevices(res.data);
    } catch (err) {
      console.error("Failed to fetch devices", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) return;
    setCreating(true);
    try {
      const res = await api.post(`/v1/projects/${activeProject.id}/devices`, newDevice);
      setCredentials(res.credentials);
      await fetchDevices();
      setNewDevice({ name: "", description: "" });
    } catch (err) {
      console.error("Failed to create device", err);
    } finally {
      setCreating(false);
    }
  };

  const filteredDevices = devices.filter(d => 
    d.name.toLowerCase().includes(search.toLowerCase()) || 
    d.id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Devices</h1>
            <p className="text-muted-foreground">Manage and monitor your connected hardware.</p>
          </div>
          <button 
            onClick={() => {
              setCredentials(null);
              setShowCreateModal(true);
            }}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold hover:opacity-90 transition-opacity"
          >
            <Plus className="w-5 h-5" />
            Provision Device
          </button>
        </div>

        {/* Filters & Search */}
        <div className="flex flex-col md:flex-row gap-4 items-center">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input 
              type="text" 
              placeholder="Search by name or ID..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-card border glass-dark focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2 w-full md:w-auto">
            <button className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-card border glass-dark hover:bg-secondary transition-colors text-sm font-medium">
              <Filter className="w-4 h-4" />
              Filters
            </button>
            <button className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-card border glass-dark hover:bg-secondary transition-colors text-sm font-medium">
              <Database className="w-4 h-4" />
              All Projects
            </button>
          </div>
        </div>

        {/* Devices Table/Grid */}
        {loading ? (
          <div className="h-64 flex flex-col items-center justify-center gap-4 text-muted-foreground">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p>Loading devices...</p>
          </div>
        ) : filteredDevices.length > 0 ? (
          <div className="grid grid-cols-1 gap-4">
            {filteredDevices.map((device) => (
              <motion.div 
                layout
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                key={device.id}
                className="group p-5 rounded-2xl bg-card border glass-dark hover:border-primary/30 transition-all flex items-center gap-6"
              >
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                  <Cpu className="w-6 h-6" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-bold text-lg truncate">{device.name}</h3>
                    <span className={cn(
                      "px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider",
                      device.status === "active" ? "bg-emerald-500/10 text-emerald-500" : "bg-blue-500/10 text-blue-500"
                    )}>
                      {device.status}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground font-mono">{device.id}</p>
                </div>
                <div className="hidden lg:flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">Created</p>
                    <p className="text-sm font-medium">{new Date(device.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button className="p-2 rounded-lg hover:bg-white/5 transition-colors text-muted-foreground hover:text-foreground">
                    <ExternalLink className="w-4 h-4" />
                  </button>
                  <button className="p-2 rounded-lg hover:bg-white/5 transition-colors text-muted-foreground hover:text-foreground">
                    <MoreHorizontal className="w-5 h-5" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="h-96 rounded-3xl border-2 border-dashed border-white/5 flex flex-col items-center justify-center text-center p-8">
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
              <Cpu className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-bold mb-2">No devices found</h3>
            <p className="text-muted-foreground max-w-sm mb-6">
              You haven't provisioned any devices in this project yet. Connect your first sensor or gateway to get started.
            </p>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-bold hover:scale-105 transition-transform"
            >
              <Plus className="w-5 h-5" />
              Provision Now
            </button>
          </div>
        )}
      </div>

      {/* Create Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowCreateModal(false)}
              className="absolute inset-0 bg-background/80 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-lg p-8 rounded-3xl bg-card border glass-dark shadow-2xl"
            >
              {!credentials ? (
                <>
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold">Provision New Device</h2>
                    <p className="text-muted-foreground">Fill in the details to generate unique credentials.</p>
                  </div>

                  <form onSubmit={handleCreate} className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Device Name</label>
                      <input 
                        required
                        type="text" 
                        placeholder="e.g. Greenhouse Sensor 01"
                        className="w-full px-4 py-3 rounded-xl bg-background border focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                        value={newDevice.name}
                        onChange={(e) => setNewDevice({ ...newDevice, name: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Description (Optional)</label>
                      <textarea 
                        rows={3}
                        placeholder="Briefly describe what this device does..."
                        className="w-full px-4 py-3 rounded-xl bg-background border focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all resize-none"
                        value={newDevice.description}
                        onChange={(e) => setNewDevice({ ...newDevice, description: e.target.value })}
                      />
                    </div>

                    <div className="pt-4 flex items-center justify-end gap-3">
                      <button 
                        type="button"
                        onClick={() => setShowCreateModal(false)}
                        className="px-6 py-2.5 rounded-xl hover:bg-secondary transition-colors font-medium"
                      >
                        Cancel
                      </button>
                      <button 
                        disabled={creating}
                        className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-primary text-primary-foreground font-bold hover:opacity-90 disabled:opacity-50 transition-all"
                      >
                        {creating && <Loader2 className="w-4 h-4 animate-spin" />}
                        Generate Credentials
                      </button>
                    </div>
                  </form>
                </>
              ) : (
                <div className="space-y-6">
                  <div className="flex items-center gap-3 text-emerald-500">
                    <CheckCircle2 className="w-8 h-8" />
                    <div>
                      <h2 className="text-2xl font-bold text-foreground">Device Provisioned!</h2>
                      <p className="text-muted-foreground">Store these credentials securely. They won't be shown again.</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <CredentialItem label="MQTT Username" value={credentials.mqtt_username} />
                    <CredentialItem label="MQTT Password" value={credentials.mqtt_password} isSecret />
                    <CredentialItem label="HTTP Token" value={credentials.http_token} isSecret />
                    
                    <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex gap-3">
                      <AlertCircle className="w-5 h-5 text-amber-500 shrink-0" />
                      <p className="text-xs text-amber-200 leading-relaxed">
                        Treat the MQTT password and HTTP token like private keys. If compromised, you'll need to rotate them in the device settings.
                      </p>
                    </div>
                  </div>

                  <button 
                    onClick={() => setShowCreateModal(false)}
                    className="w-full py-3 rounded-xl bg-white/5 hover:bg-white/10 font-bold transition-colors"
                  >
                    Done
                  </button>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </DashboardLayout>
  );
}

function CredentialItem({ label, value, isSecret = false }: { label: string, value: string, isSecret?: boolean }) {
  const [copied, setCopied] = useState(false);
  const [show, setShow] = useState(!isSecret);

  const copy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-1.5">
      <label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground ml-1">{label}</label>
      <div className="relative group">
        <div className={cn(
          "w-full px-4 py-3 pr-20 rounded-xl bg-background/50 border font-mono text-sm break-all",
          !show && "blur-sm select-none"
        )}>
          {value}
        </div>
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {isSecret && (
            <button 
              onClick={() => setShow(!show)}
              className="p-1.5 rounded-lg hover:bg-white/10 text-muted-foreground transition-colors"
            >
              {show ? <Loader2 className="w-4 h-4" /> : <Key className="w-4 h-4" />}
            </button>
          )}
          <button 
            onClick={copy}
            className="p-1.5 rounded-lg hover:bg-white/10 text-muted-foreground transition-colors relative"
          >
            {copied ? <CheckCircle2 className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}
