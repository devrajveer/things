"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { 
  ChevronLeft, 
  Zap, 
  Plus, 
  Trash2, 
  Loader2, 
  Globe, 
  Mail,
  ArrowRight,
  Database
} from "lucide-react";
import { api } from "@/lib/api";
import { useOrg } from "@/lib/org-context";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

export default function CreateRulePage() {
  const router = useRouter();
  const { activeProject } = useOrg();
  const [streams, setStreams] = useState<any[]>([]);
  const [webhooks, setWebhooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [streamId, setStreamId] = useState("");
  const [operator, setOperator] = useState("gt");
  const [value, setValue] = useState("");
  const [selectedWebhooks, setSelectedWebhooks] = useState<string[]>([]);

  useEffect(() => {
    if (activeProject) {
      fetchData();
    }
  }, [activeProject]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sRes, wRes] = await Promise.all([
        api.get(`/v1/projects/${activeProject?.id}/streams`),
        api.get(`/v1/projects/${activeProject?.id}/automation/webhooks`)
      ]);
      setStreams(sRes.data || []);
      setWebhooks(wRes || []);
    } catch (err) {
      console.error("Failed to fetch data", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const actions = selectedWebhooks.map(id => ({
        type: "webhook",
        target_id: id
      }));

      await api.post(`/v1/projects/${activeProject?.id}/automation/rules`, {
        name,
        description,
        stream_id: streamId,
        condition: {
          operator,
          value: parseFloat(value)
        },
        actions,
        is_enabled: true
      });
      router.push("/rules");
    } catch (err) {
      console.error("Failed to create rule", err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <DashboardLayout>
      <div className="h-96 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    </DashboardLayout>
  );

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-8">
          <button onClick={() => router.back()} className="p-2 rounded-xl hover:bg-white/5 transition-colors">
            <ChevronLeft className="w-6 h-6" />
          </button>
          <h1 className="text-3xl font-bold">Create New Rule</h1>
        </div>

        <form onSubmit={handleSave} className="space-y-8 pb-20">
          {/* Step 1: Basic Info */}
          <section className="p-8 rounded-[2.5rem] bg-card border glass-dark space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                <Zap className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-bold">Rule Basics</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Rule Name</label>
                <input 
                  required
                  type="text" 
                  placeholder="High Temperature Alert"
                  className="w-full px-4 py-3 rounded-xl bg-background border focus:ring-2 focus:ring-primary/50 outline-none transition-all"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Description (Optional)</label>
                <input 
                  type="text" 
                  placeholder="Triggers when temp exceeds 50C"
                  className="w-full px-4 py-3 rounded-xl bg-background border focus:ring-2 focus:ring-primary/50 outline-none transition-all"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
            </div>
          </section>

          {/* Step 2: Condition */}
          <section className="p-8 rounded-[2.5rem] bg-card border glass-dark space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center">
                <Database className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-bold">Condition</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Monitor Stream</label>
                <select 
                  required
                  className="w-full px-4 py-3 rounded-xl bg-background border focus:ring-2 focus:ring-primary/50 outline-none transition-all"
                  value={streamId}
                  onChange={(e) => setStreamId(e.target.value)}
                >
                  <option value="">Select a stream...</option>
                  {streams.map(s => (
                    <option key={s.id} value={s.id}>{s.display_name || s.key} ({s.id})</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Operator</label>
                <select 
                  className="w-full px-4 py-3 rounded-xl bg-background border focus:ring-2 focus:ring-primary/50 outline-none transition-all"
                  value={operator}
                  onChange={(e) => setOperator(e.target.value)}
                >
                  <option value="gt">Greater Than (&gt;)</option>
                  <option value="lt">Less Than (&lt;)</option>
                  <option value="eq">Equals (==)</option>
                  <option value="gte">Greater or Equal (&gt;=)</option>
                  <option value="lte">Less or Equal (&lt;=)</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Threshold Value</label>
                <input 
                  required
                  type="number" 
                  step="any"
                  placeholder="0.00"
                  className="w-full px-4 py-3 rounded-xl bg-background border focus:ring-2 focus:ring-primary/50 outline-none transition-all"
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                />
              </div>
            </div>
          </section>

          {/* Step 3: Actions */}
          <section className="p-8 rounded-[2.5rem] bg-card border glass-dark space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                <Globe className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-bold">Actions</h2>
            </div>

            <div className="space-y-4">
              <label className="text-sm font-medium text-muted-foreground">Trigger Webhooks</label>
              {webhooks.length === 0 ? (
                <div className="p-4 rounded-xl border-2 border-dashed border-white/5 text-center">
                  <p className="text-sm text-muted-foreground">No webhooks configured. <Link href="/settings/webhooks" className="text-primary hover:underline">Add one in settings.</Link></p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {webhooks.map((wh) => (
                    <div 
                      key={wh.id}
                      onClick={() => {
                        if (selectedWebhooks.includes(wh.id)) {
                          setSelectedWebhooks(selectedWebhooks.filter(id => id !== wh.id));
                        } else {
                          setSelectedWebhooks([...selectedWebhooks, wh.id]);
                        }
                      }}
                      className={cn(
                        "p-4 rounded-2xl border cursor-pointer transition-all flex items-center gap-4",
                        selectedWebhooks.includes(wh.id) 
                          ? "bg-primary/10 border-primary text-primary shadow-lg shadow-primary/10" 
                          : "bg-background/50 border-white/5 text-muted-foreground hover:border-white/20"
                      )}
                    >
                      <div className={cn(
                        "w-8 h-8 rounded-lg flex items-center justify-center",
                        selectedWebhooks.includes(wh.id) ? "bg-primary text-white" : "bg-white/5"
                      )}>
                        <Globe className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold truncate">{wh.name}</p>
                        <p className="text-[10px] opacity-60 truncate">{wh.url}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          <div className="flex items-center justify-end gap-4 pt-6">
            <button 
              type="button" 
              onClick={() => router.back()}
              className="px-6 py-3 rounded-xl font-bold hover:bg-white/5 transition-all"
            >
              Cancel
            </button>
            <button 
              disabled={saving}
              className="flex items-center gap-2 px-10 py-3 rounded-2xl bg-primary text-primary-foreground font-bold hover:opacity-90 disabled:opacity-50 transition-all shadow-xl shadow-primary/20"
            >
              {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
              Create Rule
            </button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  );
}
