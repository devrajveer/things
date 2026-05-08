"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Responsive, WidthProvider } from "react-grid-layout";
import { 
  Plus, 
  Save, 
  Settings, 
  Trash2, 
  ChevronLeft,
  Loader2,
  Layout,
  MousePointer2,
  PieChart,
  Type
} from "lucide-react";
import { api } from "@/lib/api";
import { useOrg } from "@/lib/org-context";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { ValueWidget, ChartWidget } from "@/components/widgets/Widgets";

const ResponsiveGridLayout = WidthProvider(Responsive);

interface Widget {
  id: string;
  type: "value" | "chart" | "gauge";
  title: string;
  streamId: string;
  unit?: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

export default function DashboardBuilderPage() {
  const params = useParams();
  const router = useRouter();
  const { activeProject } = useOrg();
  const [dashboard, setDashboard] = useState<any>(null);
  const [widgets, setWidgets] = useState<Widget[]>([]);
  const [streams, setStreams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [showAddPanel, setShowAddPanel] = useState(false);

  useEffect(() => {
    if (activeProject && params.id) {
      fetchData();
    }
  }, [activeProject, params.id]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const db = await api.get(`/v1/projects/${activeProject?.id}/dashboards/${params.id}`);
      setDashboard(db);
      setWidgets(db.layout.widgets || []);
      
      const st = await api.get(`/v1/projects/${activeProject?.id}/streams`);
      setStreams(st.data);
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.patch(`/v1/projects/${activeProject?.id}/dashboards/${params.id}`, {
        name: dashboard.name,
        layout: { widgets }
      });
      setEditMode(false);
    } catch (err) {
      console.error("Failed to save dashboard", err);
    } finally {
      setSaving(false);
    }
  };

  const onLayoutChange = (currentLayout: any) => {
    if (!editMode) return;
    const updatedWidgets = widgets.map(w => {
      const l = currentLayout.find((x: any) => x.i === w.id);
      if (l) {
        return { ...w, x: l.x, y: l.y, w: l.w, h: l.h };
      }
      return w;
    });
    setWidgets(updatedWidgets);
  };

  const addWidget = (type: Widget["type"], stream: any) => {
    const newWidget: Widget = {
      id: `w_${Math.random().toString(36).substr(2, 9)}`,
      type,
      title: stream.display_name || stream.key,
      streamId: stream.id,
      unit: stream.unit,
      x: 0,
      y: Infinity,
      w: type === "chart" ? 4 : 2,
      h: type === "chart" ? 4 : 2
    };
    setWidgets([...widgets, newWidget]);
    setShowAddPanel(false);
    setEditMode(true);
  };

  const removeWidget = (id: string) => {
    setWidgets(widgets.filter(w => w.id !== id));
    setEditMode(true);
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
      <div className="flex flex-col h-[calc(100vh-12rem)]">
        {/* Toolbar */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => router.push("/dashboards")}
              className="p-2 rounded-xl hover:bg-white/5 transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <h1 className="text-2xl font-bold">{dashboard?.name}</h1>
          </div>

          <div className="flex items-center gap-3">
            {editMode ? (
              <>
                <button 
                  onClick={() => setShowAddPanel(true)}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-sm font-semibold transition-all"
                >
                  <Plus className="w-4 h-4" />
                  Add Widget
                </button>
                <button 
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-sm font-bold hover:opacity-90 transition-all shadow-lg"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Save Layout
                </button>
              </>
            ) : (
              <button 
                onClick={() => setEditMode(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-card border glass-dark hover:bg-secondary text-sm font-semibold transition-all"
              >
                <Settings className="w-4 h-4" />
                Customize
              </button>
            )}
          </div>
        </div>

        {/* Grid Canvas */}
        <div className="flex-1 overflow-y-auto -mx-4 px-4 custom-scrollbar">
          <ResponsiveGridLayout
            className="layout"
            layouts={{ lg: widgets.map(w => ({ i: w.id, x: w.x, y: w.y, w: w.w, h: w.h })) }}
            breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
            cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
            rowHeight={80}
            isDraggable={editMode}
            isResizable={editMode}
            onLayoutChange={onLayoutChange}
            draggableHandle=".widget-drag-handle"
            margin={[16, 16]}
          >
            {widgets.map((widget) => (
              <div key={widget.id} className="group">
                <div className="relative h-full p-6 rounded-[2rem] bg-card border glass-dark shadow-xl overflow-hidden group">
                  {editMode && (
                    <div className="absolute top-3 right-3 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                      <div className="widget-drag-handle p-1.5 rounded-lg bg-white/5 hover:bg-white/10 cursor-grab active:cursor-grabbing text-muted-foreground">
                        <MousePointer2 className="w-3.5 h-3.5" />
                      </div>
                      <button 
                        onClick={() => removeWidget(widget.id)}
                        className="p-1.5 rounded-lg bg-destructive/10 hover:bg-destructive/20 text-destructive"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                  
                  {widget.type === "value" ? (
                    <ValueWidget 
                      projectId={activeProject!.id} 
                      streamId={widget.streamId} 
                      title={widget.title} 
                      unit={widget.unit} 
                    />
                  ) : (
                    <ChartWidget 
                      projectId={activeProject!.id} 
                      streamId={widget.streamId} 
                      title={widget.title} 
                      unit={widget.unit} 
                    />
                  )}
                </div>
              </div>
            ))}
          </ResponsiveGridLayout>

          {widgets.length === 0 && !loading && (
            <div className="h-full flex flex-col items-center justify-center text-center p-12 text-muted-foreground border-2 border-dashed border-white/5 rounded-[3rem]">
              <Layout className="w-12 h-12 mb-4 opacity-20" />
              <h3 className="text-xl font-bold text-foreground">Empty Dashboard</h3>
              <p className="max-w-xs mt-2 mb-6">Start building your view by adding widgets from your project's data streams.</p>
              <button 
                onClick={() => {setEditMode(true); setShowAddPanel(true);}}
                className="px-6 py-2.5 rounded-xl bg-primary text-primary-foreground font-bold hover:scale-105 transition-transform"
              >
                Add First Widget
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Add Widget Panel */}
      <AnimatePresence>
        {showAddPanel && (
          <div className="fixed inset-0 z-50 flex items-center justify-end">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowAddPanel(false)}
              className="absolute inset-0 bg-background/40 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              className="relative w-full max-w-md h-full bg-card border-l glass-dark shadow-2xl p-8 flex flex-col"
            >
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-2xl font-bold">Add Widget</h2>
                <button onClick={() => setShowAddPanel(false)} className="text-muted-foreground hover:text-foreground font-bold">X</button>
              </div>

              <div className="flex-1 overflow-y-auto space-y-8 pr-2 custom-scrollbar">
                {streams.length === 0 ? (
                  <p className="text-center text-muted-foreground italic pt-12">No data streams found in this project.</p>
                ) : (
                  streams.map((stream) => (
                    <div key={stream.id} className="space-y-4">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                        <h4 className="font-bold text-sm truncate">{stream.display_name || stream.key}</h4>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <button 
                          onClick={() => addWidget("value", stream)}
                          className="p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-primary/50 hover:bg-white/10 transition-all text-left group"
                        >
                          <Type className="w-5 h-5 text-muted-foreground mb-2 group-hover:text-primary transition-colors" />
                          <span className="text-xs font-bold block">Status Value</span>
                          <span className="text-[10px] text-muted-foreground">Real-time number</span>
                        </button>
                        {stream.value_type === "number" && (
                          <button 
                            onClick={() => addWidget("chart", stream)}
                            className="p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-primary/50 hover:bg-white/10 transition-all text-left group"
                          >
                            <PieChart className="w-5 h-5 text-muted-foreground mb-2 group-hover:text-primary transition-colors" />
                            <span className="text-xs font-bold block">Area Chart</span>
                            <span className="text-[10px] text-muted-foreground">Historical trend</span>
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </DashboardLayout>
  );
}
