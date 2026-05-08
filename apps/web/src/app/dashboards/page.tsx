"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { 
  LayoutDashboard, 
  Plus, 
  Search, 
  MoreHorizontal, 
  Trash2,
  ExternalLink,
  Loader2,
  Clock
} from "lucide-react";
import { api } from "@/lib/api";
import { useOrg } from "@/lib/org-context";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

interface Dashboard {
  id: string;
  name: string;
  layout: any;
}

export default function DashboardsPage() {
  const { activeProject } = useOrg();
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newDashboard, setNewDashboard] = useState({ name: "" });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (activeProject) {
      fetchDashboards();
    }
  }, [activeProject]);

  const fetchDashboards = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/v1/projects/${activeProject?.id}/dashboards`);
      setDashboards(res);
    } catch (err) {
      console.error("Failed to fetch dashboards", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) return;
    setCreating(true);
    try {
      await api.post(`/v1/projects/${activeProject.id}/dashboards`, {
        name: newDashboard.name,
        layout: { widgets: [] }
      });
      await fetchDashboards();
      setShowCreateModal(false);
      setNewDashboard({ name: "" });
    } catch (err) {
      console.error("Failed to create dashboard", err);
    } finally {
      setCreating(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboards</h1>
            <p className="text-muted-foreground">Visualize your data with custom real-time dashboards.</p>
          </div>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold hover:opacity-90 transition-opacity"
          >
            <Plus className="w-5 h-5" />
            Create Dashboard
          </button>
        </div>

        {/* Dashboards Grid */}
        {loading ? (
          <div className="h-64 flex flex-col items-center justify-center gap-4 text-muted-foreground">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p>Loading dashboards...</p>
          </div>
        ) : dashboards.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {dashboards.map((dashboard) => (
              <Link key={dashboard.id} href={`/dashboards/${dashboard.id}`}>
                <motion.div 
                  layout
                  whileHover={{ y: -4 }}
                  className="group p-6 rounded-3xl bg-card border glass-dark hover:border-primary/30 transition-all cursor-pointer h-full flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between mb-4">
                      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                        <LayoutDashboard className="w-6 h-6" />
                      </div>
                      <button className="p-2 rounded-lg hover:bg-white/5 transition-colors text-muted-foreground opacity-0 group-hover:opacity-100">
                        <MoreHorizontal className="w-5 h-5" />
                      </button>
                    </div>
                    <h3 className="font-bold text-lg mb-1">{dashboard.name}</h3>
                    <p className="text-xs text-muted-foreground font-mono mb-4">{dashboard.id}</p>
                  </div>
                  
                  <div className="flex items-center justify-between pt-4 border-t border-white/5">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Active
                    </span>
                    <span className="text-primary text-xs font-bold flex items-center gap-1 group-hover:underline">
                      Open <ExternalLink className="w-3 h-3" />
                    </span>
                  </div>
                </motion.div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="h-96 rounded-3xl border-2 border-dashed border-white/5 flex flex-col items-center justify-center text-center p-8">
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
              <LayoutDashboard className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-bold mb-2">No dashboards found</h3>
            <p className="text-muted-foreground max-w-sm mb-6">
              Create your first dashboard to start visualizing your project's telemetry data in real-time.
            </p>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-bold hover:scale-105 transition-transform"
            >
              <Plus className="w-5 h-5" />
              Create Your First Dashboard
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
              <div className="mb-6">
                <h2 className="text-2xl font-bold">New Dashboard</h2>
                <p className="text-muted-foreground">Give your dashboard a name to get started.</p>
              </div>

              <form onSubmit={handleCreate} className="space-y-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Dashboard Name</label>
                  <input 
                    required
                    type="text" 
                    placeholder="e.g. Production Overview"
                    className="w-full px-4 py-3 rounded-xl bg-background border focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                    value={newDashboard.name}
                    onChange={(e) => setNewDashboard({ name: e.target.value })}
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
                    Create Dashboard
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
