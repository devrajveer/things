"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { 
  Zap, 
  Plus, 
  Search, 
  MoreHorizontal, 
  Trash2,
  AlertCircle,
  CheckCircle2,
  Settings2,
  Loader2,
  Mail,
  Globe
} from "lucide-react";
import { api } from "@/lib/api";
import { useOrg } from "@/lib/org-context";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

interface Rule {
  id: string;
  name: string;
  description?: string;
  is_enabled: boolean;
  condition: any;
  actions: any[];
}

export default function RulesPage() {
  const { activeProject } = useOrg();
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (activeProject) {
      fetchRules();
    }
  }, [activeProject]);

  const fetchRules = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/v1/projects/${activeProject?.id}/automation/rules`);
      setRules(res);
    } catch (err) {
      console.error("Failed to fetch rules", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this rule?")) return;
    try {
      await api.delete(`/v1/projects/${activeProject?.id}/automation/rules/${id}`);
      setRules(rules.filter(r => r.id !== id));
    } catch (err) {
      console.error("Failed to delete rule", err);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Automation Rules</h1>
            <p className="text-muted-foreground">Define logic to trigger actions based on your data streams.</p>
          </div>
          <Link href="/rules/create">
            <button className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold hover:opacity-90 transition-opacity">
              <Plus className="w-5 h-5" />
              Create Rule
            </button>
          </Link>
        </div>

        {loading ? (
          <div className="h-64 flex flex-col items-center justify-center gap-4 text-muted-foreground">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p>Loading automation rules...</p>
          </div>
        ) : rules.length > 0 ? (
          <div className="grid grid-cols-1 gap-4">
            {rules.map((rule) => (
              <motion.div 
                key={rule.id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="group p-6 rounded-3xl bg-card border glass-dark hover:border-primary/30 transition-all flex items-center gap-6"
              >
                <div className={cn(
                  "w-12 h-12 rounded-2xl flex items-center justify-center",
                  rule.is_enabled ? "bg-primary/10 text-primary" : "bg-white/5 text-muted-foreground"
                )}>
                  <Zap className="w-6 h-6" />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="font-bold text-lg truncate">{rule.name}</h3>
                    {rule.is_enabled ? (
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-bold uppercase tracking-wider">Enabled</span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full bg-white/5 text-muted-foreground text-[10px] font-bold uppercase tracking-wider">Disabled</span>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground truncate">{rule.description || "No description provided."}</p>
                </div>

                <div className="flex items-center gap-4">
                  <div className="flex -space-x-2">
                    {rule.actions.map((action, i) => (
                      <div key={i} className="w-8 h-8 rounded-full bg-secondary border-2 border-card flex items-center justify-center text-muted-foreground" title={action.type}>
                        {action.type === "webhook" ? <Globe className="w-4 h-4" /> : <Mail className="w-4 h-4" />}
                      </div>
                    ))}
                  </div>
                  
                  <div className="h-10 w-px bg-white/5" />
                  
                  <button 
                    onClick={() => handleDelete(rule.id)}
                    className="p-2.5 rounded-xl hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="h-96 rounded-[3rem] border-2 border-dashed border-white/5 flex flex-col items-center justify-center text-center p-8">
            <div className="w-20 h-20 rounded-[2rem] bg-white/5 flex items-center justify-center mb-6">
              <Zap className="w-10 h-10 text-muted-foreground" />
            </div>
            <h3 className="text-2xl font-bold mb-3">No automation rules</h3>
            <p className="text-muted-foreground max-w-sm mb-8 text-lg">
              Automate your workflow by creating rules that monitor your data and trigger real-time actions.
            </p>
            <Link href="/rules/create">
              <button className="flex items-center gap-2 px-8 py-4 rounded-2xl bg-primary text-primary-foreground font-bold hover:scale-105 transition-transform shadow-xl">
                <Plus className="w-6 h-6" />
                Create Your First Rule
              </button>
            </Link>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
