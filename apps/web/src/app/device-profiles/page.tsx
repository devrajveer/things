"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { 
  Cpu, 
  Plus, 
  Search, 
  MoreHorizontal, 
  Trash2,
  Code2,
  FileJson,
  Loader2,
  AlertTriangle
} from "lucide-react";
import { api } from "@/lib/api";
import { useOrg } from "@/lib/org-context";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

interface DeviceProfile {
  id: string;
  name: string;
  schema: any;
  payload_format: string;
  decoder_js?: string;
  created_at: string;
}

export default function DeviceProfilesPage() {
  const { activeProject } = useOrg();
  const [profiles, setProfiles] = useState<DeviceProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newProfile, setNewProfile] = useState({
    name: "",
    payload_format: "json",
    schema: "{}"
  });

  useEffect(() => {
    if (activeProject) {
      fetchProfiles();
    }
  }, [activeProject]);

  const fetchProfiles = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/v1/projects/${activeProject?.id}/device-profiles`);
      setProfiles(res.data);
    } catch (err) {
      console.error("Failed to fetch profiles", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) return;
    setCreating(true);
    try {
      await api.post(`/v1/projects/${activeProject.id}/device-profiles`, {
        ...newProfile,
        schema: JSON.parse(newProfile.schema)
      });
      await fetchProfiles();
      setShowCreateModal(false);
      setNewProfile({ name: "", payload_format: "json", schema: "{}" });
    } catch (err) {
      console.error("Failed to create profile", err);
      alert("Failed to create profile. Check if JSON schema is valid.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Device Profiles</h1>
            <p className="text-muted-foreground">Define how devices communicate and validate their data.</p>
          </div>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold hover:opacity-90 transition-opacity"
          >
            <Plus className="w-5 h-5" />
            Create Profile
          </button>
        </div>

        {/* Profiles Grid */}
        {loading ? (
          <div className="h-64 flex flex-col items-center justify-center gap-4 text-muted-foreground">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p>Loading profiles...</p>
          </div>
        ) : profiles.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {profiles.map((profile) => (
              <motion.div 
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                key={profile.id}
                className="group p-6 rounded-3xl bg-card border glass-dark hover:border-primary/30 transition-all flex flex-col justify-between h-full"
              >
                <div>
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                      <FileJson className="w-6 h-6" />
                    </div>
                    <button className="p-2 rounded-lg hover:bg-white/5 transition-colors text-muted-foreground">
                      <MoreHorizontal className="w-5 h-5" />
                    </button>
                  </div>
                  <h3 className="font-bold text-lg mb-1">{profile.name}</h3>
                  <div className="flex items-center gap-2 mb-4">
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-white/5 border border-white/5 text-muted-foreground tracking-widest">
                      {profile.payload_format}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-6">
                    {profile.id}
                  </p>
                </div>
                
                <div className="flex items-center justify-between pt-4 border-t border-white/5">
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Code2 className="w-3.5 h-3.5" />
                    <span>{profile.decoder_js ? "Custom JS" : "No Decoder"}</span>
                  </div>
                  <button className="text-xs font-bold text-primary hover:underline flex items-center gap-1">
                    Edit Profile <MoreHorizontal className="w-3 h-3" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="h-96 rounded-3xl border-2 border-dashed border-white/5 flex flex-col items-center justify-center text-center p-8">
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
              <FileJson className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-bold mb-2">No profiles yet</h3>
            <p className="text-muted-foreground max-w-sm mb-6">
              Create a profile to define telemetry schemas and custom decoding logic for your devices.
            </p>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-bold hover:scale-105 transition-transform"
            >
              <Plus className="w-5 h-5" />
              Create First Profile
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
              className="relative w-full max-w-2xl p-8 rounded-3xl bg-card border glass-dark shadow-2xl overflow-y-auto max-h-[90vh]"
            >
              <div className="mb-6">
                <h2 className="text-2xl font-bold">New Device Profile</h2>
                <p className="text-muted-foreground">Define the communication standard for a group of devices.</p>
              </div>

              <form onSubmit={handleCreate} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Profile Name</label>
                    <input 
                      required
                      type="text" 
                      placeholder="e.g. Weather Station"
                      className="w-full px-4 py-3 rounded-xl bg-background border focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                      value={newProfile.name}
                      onChange={(e) => setNewProfile({ ...newProfile, name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Payload Format</label>
                    <select 
                      className="w-full px-4 py-3 rounded-xl bg-background border focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                      value={newProfile.payload_format}
                      onChange={(e) => setNewProfile({ ...newProfile, payload_format: e.target.value })}
                    >
                      <option value="json">JSON</option>
                      <option value="cbor">CBOR</option>
                      <option value="cayenne_lpp">Cayenne LPP</option>
                      <option value="binary">Custom Binary</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Validation Schema (JSON)</label>
                    <span className="text-[10px] text-muted-foreground font-mono">Optional</span>
                  </div>
                  <textarea 
                    rows={8}
                    placeholder='{ "type": "object", "properties": { ... } }'
                    className="w-full px-4 py-3 rounded-xl bg-background border font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all resize-none"
                    value={newProfile.schema}
                    onChange={(e) => setNewProfile({ ...newProfile, schema: e.target.value })}
                  />
                </div>

                <div className="p-4 rounded-2xl bg-primary/5 border border-primary/10 flex gap-3">
                  <AlertTriangle className="w-5 h-5 text-primary shrink-0" />
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Custom JavaScript decoders (Phase 2) will allow you to transform raw binary payloads into JSON streams. For now, we support direct JSON mapping.
                  </p>
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
                    Create Profile
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
