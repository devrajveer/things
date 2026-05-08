"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { 
  Plus, 
  Trash2, 
  Loader2, 
  Cpu,
  Link as LinkIcon,
  FileCode2
} from "lucide-react";
import { api } from "@/lib/api";
import { useOrg } from "@/lib/org-context";
import { motion, AnimatePresence } from "framer-motion";

export default function FirmwaresPage() {
  const { activeProject } = useOrg();
  const [firmwares, setFirmwares] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newVersion, setNewVersion] = useState("");
  const [newUrl, setNewUrl] = useState("");
  const [newChecksum, setNewChecksum] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (activeProject) {
      fetchData();
    }
  }, [activeProject]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/v1/projects/${activeProject?.id}/firmwares`);
      setFirmwares(res);
    } catch (err) {
      console.error("Failed to fetch firmwares", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post(`/v1/projects/${activeProject?.id}/firmwares`, {
        version: newVersion,
        url: newUrl,
        checksum: newChecksum || null
      });
      await fetchData();
      setShowCreateModal(false);
      setNewVersion("");
      setNewUrl("");
      setNewChecksum("");
    } catch (err) {
      console.error("Failed to create firmware", err);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this firmware version? Fleets targeting it will lose their target.")) return;
    try {
      await api.delete(`/v1/projects/${activeProject?.id}/firmwares/${id}`);
      setFirmwares(firmwares.filter(f => f.id !== id));
    } catch (err) {
      console.error("Failed to delete firmware", err);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Firmwares</h1>
            <p className="text-muted-foreground">Register external firmware binaries for OTA updates.</p>
          </div>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold hover:opacity-90 transition-opacity"
          >
            <Plus className="w-5 h-5" />
            Add Firmware
          </button>
        </div>

        {loading ? (
          <div className="h-64 flex flex-col items-center justify-center gap-4 text-muted-foreground">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p>Loading firmwares...</p>
          </div>
        ) : firmwares.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {firmwares.map((fw) => (
              <motion.div 
                key={fw.id}
                layout
                className="p-8 rounded-[2.5rem] bg-card border glass-dark hover:border-primary/30 transition-all space-y-6"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center">
                      <FileCode2 className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold font-mono">v{fw.version}</h3>
                      <p className="text-xs text-muted-foreground">ID: {fw.id}</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => handleDelete(fw.id)}
                    className="p-3 rounded-xl hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>

                <div className="space-y-3 pt-6 border-t border-white/5">
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-background border border-white/5">
                    <LinkIcon className="w-4 h-4 text-muted-foreground shrink-0" />
                    <span className="text-sm truncate opacity-80" title={fw.url}>{fw.url}</span>
                  </div>
                  {fw.checksum && (
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-background border border-white/5">
                      <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider shrink-0">SHA256</span>
                      <span className="text-sm font-mono truncate opacity-80 text-primary">{fw.checksum}</span>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="h-64 rounded-[3rem] border-2 border-dashed border-white/5 flex flex-col items-center justify-center text-center p-8">
            <Cpu className="w-10 h-10 mb-4 text-muted-foreground opacity-50" />
            <h3 className="text-xl font-bold mb-2">No Firmwares</h3>
            <p className="text-muted-foreground mb-6">Register a firmware version to deploy it via fleets.</p>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 rounded-xl bg-primary text-primary-foreground font-semibold"
            >
              Add Firmware
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
              <h2 className="text-2xl font-bold mb-6">Register Firmware</h2>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Version</label>
                  <input 
                    required
                    type="text" 
                    placeholder="1.0.4-beta"
                    className="w-full px-4 py-3 rounded-xl bg-background border outline-none font-mono"
                    value={newVersion}
                    onChange={(e) => setNewVersion(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Binary URL</label>
                  <input 
                    required
                    type="url" 
                    placeholder="https://s3.amazonaws.com/..."
                    className="w-full px-4 py-3 rounded-xl bg-background border outline-none"
                    value={newUrl}
                    onChange={(e) => setNewUrl(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Checksum (SHA256) - Optional</label>
                  <input 
                    type="text" 
                    className="w-full px-4 py-3 rounded-xl bg-background border outline-none font-mono"
                    value={newChecksum}
                    onChange={(e) => setNewChecksum(e.target.value)}
                  />
                </div>
                <div className="pt-4 flex items-center justify-end gap-3">
                  <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 hover:bg-white/5 rounded-xl font-medium">Cancel</button>
                  <button type="submit" disabled={creating} className="px-6 py-2 bg-primary text-primary-foreground font-bold rounded-xl flex items-center gap-2">
                    {creating && <Loader2 className="w-4 h-4 animate-spin" />} Register
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
