"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useOrg } from "@/lib/org-context";
import { api } from "@/lib/api";
import { 
  Box, 
  Plus, 
  Search, 
  MoreVertical, 
  ExternalLink,
  Trash2,
  Edit2,
  Loader2,
  AlertCircle
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export default function ProjectsPage() {
  const { activeOrg, projects, refresh } = useOrg();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const filteredProjects = projects.filter(p => p.organization_id === activeOrg?.id);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeOrg) return;
    
    setIsSubmitting(true);
    setError("");

    try {
      await api.post("/v1/projects", {
        name: projectName,
        organization_id: activeOrg.id,
        description: projectDescription
      });
      await refresh();
      setIsCreateModalOpen(false);
      setProjectName("");
      setProjectDescription("");
    } catch (err: any) {
      setError(err.message || "Failed to create project");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2">Projects</h1>
            <p className="text-muted-foreground">Manage your IoT environments and isolation boundaries.</p>
          </div>
          <button 
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl premium-gradient text-white font-bold shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all"
          >
            <Plus className="w-5 h-5" />
            New Project
          </button>
        </div>

        {/* Filter Bar */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-sm group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
            <input 
              type="text" 
              placeholder="Filter projects..." 
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-card border focus:border-primary/30 outline-none transition-all text-sm"
            />
          </div>
        </div>

        {/* Projects Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AnimatePresence>
            {filteredProjects.map((project) => (
              <motion.div 
                key={project.id}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="group p-6 rounded-3xl bg-card border glass-dark hover:border-primary/50 transition-all flex flex-col h-48 relative overflow-hidden"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                    <Box className="w-6 h-6 text-blue-500" />
                  </div>
                  <button className="p-2 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors">
                    <MoreVertical className="w-4 h-4" />
                  </button>
                </div>
                
                <h3 className="text-lg font-bold truncate group-hover:text-primary transition-colors">{project.name}</h3>
                <p className="text-sm text-muted-foreground mt-1 line-clamp-2 flex-1">
                  {project.id}
                </p>
                
                <div className="mt-4 flex items-center justify-between text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-500" />
                    Healthy
                  </div>
                  <div className="flex items-center gap-2 group-hover:text-primary cursor-pointer transition-colors">
                    Open console
                    <ExternalLink className="w-3 h-3" />
                  </div>
                </div>

                {/* Subtle hover background accent */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 blur-3xl -translate-y-1/2 translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity" />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Create Modal */}
        <AnimatePresence>
          {isCreateModalOpen && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setIsCreateModalOpen(false)}
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              />
              <motion.div 
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="w-full max-w-lg bg-card border glass-dark p-8 rounded-[2rem] shadow-2xl relative z-10"
              >
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 rounded-2xl bg-primary/20 flex items-center justify-center">
                    <Plus className="text-primary w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold">New Project</h2>
                    <p className="text-sm text-muted-foreground">Create a new isolated IoT environment.</p>
                  </div>
                </div>

                <form onSubmit={handleCreate} className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium ml-1">Project Name</label>
                    <input 
                      type="text" 
                      value={projectName}
                      onChange={(e) => setProjectName(e.target.value)}
                      placeholder="e.g. Smart Greenhouse"
                      required
                      className="w-full px-4 py-3 rounded-2xl bg-secondary/50 border border-transparent focus:border-primary/30 focus:bg-secondary transition-all outline-none"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium ml-1">Description (Optional)</label>
                    <textarea 
                      value={projectDescription}
                      onChange={(e) => setProjectDescription(e.target.value)}
                      placeholder="Describe the purpose of this project..."
                      className="w-full px-4 py-3 rounded-2xl bg-secondary/50 border border-transparent focus:border-primary/30 focus:bg-secondary transition-all outline-none resize-none h-24"
                    />
                  </div>

                  {error && (
                    <div className="p-4 rounded-2xl bg-destructive/10 border border-destructive/20 flex gap-3 text-destructive text-sm font-medium">
                      <AlertCircle className="w-5 h-5 shrink-0" />
                      {error}
                    </div>
                  )}

                  <div className="flex gap-4 pt-2">
                    <button 
                      type="button"
                      onClick={() => setIsCreateModalOpen(false)}
                      className="flex-1 py-3 rounded-2xl bg-secondary hover:bg-secondary/80 font-bold transition-all"
                    >
                      Cancel
                    </button>
                    <button 
                      type="submit"
                      disabled={isSubmitting}
                      className="flex-[2] py-3 rounded-2xl premium-gradient text-white font-bold shadow-lg shadow-primary/20 flex items-center justify-center gap-2"
                    >
                      {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : "Create Project"}
                    </button>
                  </div>
                </form>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </DashboardLayout>
  );
}
