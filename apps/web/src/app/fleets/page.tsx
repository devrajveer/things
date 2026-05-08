"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { 
  Box, 
  Plus, 
  Trash2, 
  Loader2, 
  Cpu,
  RefreshCw,
  AlertCircle
} from "lucide-react";
import { api } from "@/lib/api";
import { useOrg } from "@/lib/org-context";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

export default function FleetsPage() {
  const { activeProject } = useOrg();
  const [fleets, setFleets] = useState<any[]>([]);
  const [firmwares, setFirmwares] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newFleetName, setNewFleetName] = useState("");
  const [newFleetDesc, setNewFleetDesc] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (activeProject) {
      fetchData();
    }
  }, [activeProject]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [fRes, fwRes] = await Promise.all([
        api.get(`/v1/projects/${activeProject?.id}/fleets`),
        api.get(`/v1/projects/${activeProject?.id}/firmwares`)
      ]);
      setFleets(fRes);
      setFirmwares(fwRes);
    } catch (err) {
      console.error("Failed to fetch fleets", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post(`/v1/projects/${activeProject?.id}/fleets`, {
        name: newFleetName,
        description: newFleetDesc
      });
      await fetchData();
      setShowCreateModal(false);
      setNewFleetName("");
      setNewFleetDesc("");
    } catch (err) {
      console.error("Failed to create fleet", err);
    } finally {
      setCreating(false);
    }
  };

  const handleUpdateTarget = async (fleetId: string, firmwareId: string) => {
    try {
      // Find current fleet data
      const fleet = fleets.find(f => f.id === fleetId);
      if (!fleet) return;
      
      await api.patch(`/v1/projects/${activeProject?.id}/fleets/${fleetId}`, {
        name: fleet.name,
        description: fleet.description,
        target_firmware_id: firmwareId === "" ? null : firmwareId
      });
      await fetchData();
    } catch (err) {
      console.error("Failed to update fleet target", err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this fleet? Devices will become unassigned.")) return;
    try {
      await api.delete(`/v1/projects/${activeProject?.id}/fleets/${id}`);
      setFleets(fleets.filter(f => f.id !== id));
    } catch (err) {
      console.error("Failed to delete fleet", err);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Fleets</h1>
            <p className="text-muted-foreground">Group devices and manage OTA updates.</p>
          </div>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold hover:opacity-90 transition-opacity"
          >
            <Plus className="w-5 h-5" />
            Create Fleet
          </button>
        </div>

        {loading ? (
          <div className="h-64 flex flex-col items-center justify-center gap-4 text-muted-foreground">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p>Loading fleets...</p>
          </div>
        ) : fleets.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {fleets.map((fleet) => (
              <motion.div 
                key={fleet.id}
                layout
                className="p-8 rounded-[2.5rem] bg-card border glass-dark hover:border-primary/30 transition-all flex flex-col h-full"
              >
                <div className="flex items-start justify-between mb-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center">
                      <Box className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold">{fleet.name}</h3>
                      <p className="text-sm text-muted-foreground truncate">{fleet.description || "No description"}</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => handleDelete(fleet.id)}
                    className="p-3 rounded-xl hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>

                <div className="mt-auto space-y-4 pt-6 border-t border-white/5">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <RefreshCw className="w-4 h-4" />
                      <span>Target Firmware</span>
                    </div>
                    
                    <select 
                      className="px-3 py-2 rounded-lg bg-background border focus:ring-1 focus:ring-primary/50 outline-none text-sm font-mono max-w-[200px]"
                      value={fleet.target_firmware_id || ""}
                      onChange={(e) => handleUpdateTarget(fleet.id, e.target.value)}
                    >
                      <option value="">None</option>
                      {firmwares.map(fw => (
                        <option key={fw.id} value={fw.id}>{fw.version}</option>
                      ))}
                    </select>
                  </div>
                  
                  {fleet.target_firmware_id && (
                    <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs text-blue-500 flex flex-col gap-1">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span className="font-semibold">OTA Update Armed</span>
                      </div>
                      <span className="opacity-80 pl-6">Devices checking in to this fleet will be instructed to update to {firmwares.find(f => f.id === fleet.target_firmware_id)?.version}.</span>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="h-64 rounded-[3rem] border-2 border-dashed border-white/5 flex flex-col items-center justify-center text-center p-8">
            <Box className="w-10 h-10 mb-4 text-muted-foreground opacity-50" />
            <h3 className="text-xl font-bold mb-2">No Fleets</h3>
            <p className="text-muted-foreground mb-6">Group your devices to manage them at scale.</p>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 rounded-xl bg-primary text-primary-foreground font-semibold"
            >
              Create Fleet
            </button>
          </div>
        )}
      </div>

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
              className="relative w-full max-w-md p-10 rounded-[3rem] bg-card border glass-dark shadow-2xl"
            >
              <h2 className="text-2xl font-bold mb-6">Create Fleet</h2>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Fleet Name</label>
                  <input 
                    required
                    type="text" 
                    className="w-full px-4 py-3 rounded-xl bg-background border outline-none"
                    value={newFleetName}
                    onChange={(e) => setNewFleetName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Description</label>
                  <input 
                    type="text" 
                    className="w-full px-4 py-3 rounded-xl bg-background border outline-none"
                    value={newFleetDesc}
                    onChange={(e) => setNewFleetDesc(e.target.value)}
                  />
                </div>
                <div className="pt-4 flex items-center justify-end gap-3">
                  <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 hover:bg-white/5 rounded-xl font-medium">Cancel</button>
                  <button type="submit" disabled={creating} className="px-6 py-2 bg-primary text-primary-foreground font-bold rounded-xl flex items-center gap-2">
                    {creating && <Loader2 className="w-4 h-4 animate-spin" />} Create
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </DashboardLayout>
  );
}
