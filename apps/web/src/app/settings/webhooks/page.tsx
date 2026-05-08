"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { 
  Globe, 
  Plus, 
  Trash2, 
  Loader2, 
  Copy, 
  Eye, 
  EyeOff,
  ShieldCheck,
  ExternalLink
} from "lucide-react";
import { api } from "@/lib/api";
import { useOrg } from "@/lib/org-context";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

interface Webhook {
  id: string;
  name: string;
  url: string;
  secret: string;
  is_enabled: boolean;
}

export default function WebhooksPage() {
  const { activeProject } = useOrg();
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newWebhook, setNewWebhook] = useState({ name: "", url: "" });
  const [showSecretId, setShowSecretId] = useState<string | null>(null);

  useEffect(() => {
    if (activeProject) {
      fetchWebhooks();
    }
  }, [activeProject]);

  const fetchWebhooks = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/v1/projects/${activeProject?.id}/automation/webhooks`);
      setWebhooks(res);
    } catch (err) {
      console.error("Failed to fetch webhooks", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post(`/v1/projects/${activeProject?.id}/automation/webhooks`, newWebhook);
      await fetchWebhooks();
      setShowCreateModal(false);
      setNewWebhook({ name: "", url: "" });
    } catch (err) {
      console.error("Failed to create webhook", err);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this webhook? Rules using it will stop firing.")) return;
    try {
      await api.delete(`/v1/projects/${activeProject?.id}/automation/webhooks/${id}`);
      setWebhooks(webhooks.filter(w => w.id !== id));
    } catch (err) {
      console.error("Failed to delete webhook", err);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Webhooks</h1>
            <p className="text-muted-foreground">Manage external endpoints for real-time alert notifications.</p>
          </div>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold hover:opacity-90 transition-opacity"
          >
            <Plus className="w-5 h-5" />
            Add Webhook
          </button>
        </div>

        <div className="p-6 rounded-[2rem] bg-emerald-500/5 border border-emerald-500/20 flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h4 className="font-bold text-emerald-500">Secure Delivery</h4>
            <p className="text-sm text-muted-foreground max-w-2xl">
              All webhooks are signed with an HMAC-SHA256 signature using your unique secret. 
              Verify the <code className="text-primary font-bold">X-MegaIoT-Signature</code> header on your server to ensure authenticity.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="h-64 flex flex-col items-center justify-center gap-4 text-muted-foreground">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p>Loading webhooks...</p>
          </div>
        ) : webhooks.length > 0 ? (
          <div className="grid grid-cols-1 gap-6">
            {webhooks.map((webhook) => (
              <motion.div 
                key={webhook.id}
                layout
                className="p-8 rounded-[2.5rem] bg-card border glass-dark hover:border-primary/30 transition-all space-y-6"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center">
                      <Globe className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold">{webhook.name}</h3>
                      <div className="flex items-center gap-2 text-muted-foreground text-sm">
                        <span className="truncate max-w-md">{webhook.url}</span>
                        <ExternalLink className="w-3 h-3" />
                      </div>
                    </div>
                  </div>
                  <button 
                    onClick={() => handleDelete(webhook.id)}
                    className="p-3 rounded-xl hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t border-white/5">
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Signing Secret</label>
                    <div className="flex items-center gap-2 p-3 rounded-xl bg-background border border-white/5 font-mono text-sm group">
                      <div className="flex-1 truncate">
                        {showSecretId === webhook.id ? webhook.secret : "••••••••••••••••••••••••••••••••"}
                      </div>
                      <button 
                        onClick={() => setShowSecretId(showSecretId === webhook.id ? null : webhook.id)}
                        className="p-1 hover:text-primary transition-colors"
                      >
                        {showSecretId === webhook.id ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                      <button 
                        onClick={() => navigator.clipboard.writeText(webhook.secret)}
                        className="p-1 hover:text-primary transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="flex items-end justify-end gap-2">
                    <span className="text-[10px] text-muted-foreground font-mono bg-white/5 px-2 py-1 rounded">ID: {webhook.id}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="h-64 rounded-[3rem] border-2 border-dashed border-white/5 flex flex-col items-center justify-center text-center p-8 text-muted-foreground">
            <Globe className="w-10 h-10 mb-4 opacity-20" />
            <p>No webhooks configured yet.</p>
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
              className="relative w-full max-w-lg p-10 rounded-[3rem] bg-card border glass-dark shadow-2xl"
            >
              <h2 className="text-2xl font-bold mb-2">Add Webhook</h2>
              <p className="text-muted-foreground mb-8 text-sm">External notifications will be sent to this URL.</p>

              <form onSubmit={handleCreate} className="space-y-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Friendly Name</label>
                  <input 
                    required
                    type="text" 
                    placeholder="Production Slack"
                    className="w-full px-4 py-3 rounded-xl bg-background border focus:ring-2 focus:ring-primary/50 outline-none transition-all"
                    value={newWebhook.name}
                    onChange={(e) => setNewWebhook({ ...newWebhook, name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Endpoint URL</label>
                  <input 
                    required
                    type="url" 
                    placeholder="https://hooks.example.com/..."
                    className="w-full px-4 py-3 rounded-xl bg-background border focus:ring-2 focus:ring-primary/50 outline-none transition-all"
                    value={newWebhook.url}
                    onChange={(e) => setNewWebhook({ ...newWebhook, url: e.target.value })}
                  />
                </div>

                <div className="pt-6 flex items-center justify-end gap-3">
                  <button 
                    type="button" 
                    onClick={() => setShowCreateModal(false)}
                    className="px-6 py-2.5 rounded-xl font-medium hover:bg-secondary transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    disabled={creating}
                    className="flex items-center gap-2 px-8 py-2.5 rounded-xl bg-primary text-primary-foreground font-bold hover:opacity-90 disabled:opacity-50 transition-all shadow-lg"
                  >
                    {creating && <Loader2 className="w-4 h-4 animate-spin" />}
                    Add Webhook
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
