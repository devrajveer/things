"use client";

import React, { useState } from "react";
import { 
  Search, 
  Bell, 
  HelpCircle,
  ChevronDown,
  Building2,
  Box,
  Plus
} from "lucide-react";
import { useOrg } from "@/lib/org-context";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export function Navbar() {
  const { organizations, projects, activeOrg, activeProject, setActiveOrg, setActiveProject } = useOrg();
  const [isOrgOpen, setIsOrgOpen] = useState(false);
  const [isProjectOpen, setIsProjectOpen] = useState(false);

  return (
    <header className="h-16 border-b bg-card/50 backdrop-blur-md flex items-center justify-between px-8 sticky top-0 z-50">
      <div className="flex items-center gap-8">
        {/* Switchers */}
        <div className="flex items-center gap-4">
          {/* Org Switcher */}
          <div className="relative">
            <button 
              onClick={() => setIsOrgOpen(!isOrgOpen)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-secondary transition-colors group"
            >
              <div className="w-6 h-6 rounded bg-primary/20 flex items-center justify-center">
                <Building2 className="w-4 h-4 text-primary" />
              </div>
              <span className="text-sm font-medium">{activeOrg?.name || "Select Org"}</span>
              <ChevronDown className={cn("w-4 h-4 text-muted-foreground transition-transform", isOrgOpen && "rotate-180")} />
            </button>

            <AnimatePresence>
              {isOrgOpen && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute top-full left-0 mt-2 w-56 rounded-xl border bg-card glass-dark shadow-2xl p-2 z-50"
                >
                  <div className="text-[10px] font-bold text-muted-foreground px-3 py-2 uppercase tracking-wider">Organizations</div>
                  {organizations.map((org) => (
                    <button
                      key={org.id}
                      onClick={() => {
                        setActiveOrg(org);
                        setIsOrgOpen(false);
                      }}
                      className={cn(
                        "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                        activeOrg?.id === org.id ? "bg-primary/10 text-primary" : "hover:bg-secondary"
                      )}
                    >
                      <Building2 className="w-4 h-4" />
                      {org.name}
                    </button>
                  ))}
                  <div className="h-px bg-border my-2" />
                  <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm hover:bg-secondary text-primary font-medium">
                    <Plus className="w-4 h-4" />
                    New Organization
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="h-4 w-px bg-border" />

          {/* Project Switcher */}
          <div className="relative">
            <button 
              onClick={() => setIsProjectOpen(!isProjectOpen)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-secondary transition-colors group"
            >
              <div className="w-6 h-6 rounded bg-blue-500/20 flex items-center justify-center">
                <Box className="w-4 h-4 text-blue-500" />
              </div>
              <span className="text-sm font-medium">{activeProject?.name || "Select Project"}</span>
              <ChevronDown className={cn("w-4 h-4 text-muted-foreground transition-transform", isProjectOpen && "rotate-180")} />
            </button>

            <AnimatePresence>
              {isProjectOpen && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute top-full left-0 mt-2 w-56 rounded-xl border bg-card glass-dark shadow-2xl p-2 z-50"
                >
                  <div className="text-[10px] font-bold text-muted-foreground px-3 py-2 uppercase tracking-wider">Projects</div>
                  {projects.filter(p => p.organization_id === activeOrg?.id).map((proj) => (
                    <button
                      key={proj.id}
                      onClick={() => {
                        setActiveProject(proj);
                        setIsProjectOpen(false);
                      }}
                      className={cn(
                        "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                        activeProject?.id === proj.id ? "bg-blue-500/10 text-blue-500" : "hover:bg-secondary"
                      )}
                    >
                      <Box className="w-4 h-4" />
                      {proj.name}
                    </button>
                  ))}
                  <div className="h-px bg-border my-2" />
                  <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm hover:bg-secondary text-blue-500 font-medium">
                    <Plus className="w-4 h-4" />
                    New Project
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Search */}
        <div className="relative group hidden lg:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
          <input 
            type="text" 
            placeholder="Search anything..." 
            className="pl-10 pr-4 py-2 w-64 rounded-xl bg-secondary/50 border border-transparent focus:border-primary/30 focus:bg-secondary transition-all outline-none text-sm"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="p-2 rounded-xl hover:bg-secondary text-muted-foreground hover:text-foreground transition-all">
          <HelpCircle className="w-5 h-5" />
        </button>
        <button className="p-2 rounded-xl hover:bg-secondary text-muted-foreground hover:text-foreground transition-all relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-destructive" />
        </button>
        <div className="h-8 w-px bg-border mx-2" />
        <div className="w-8 h-8 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-xs font-bold text-primary uppercase">
          {activeOrg?.name.slice(0, 2) || "RS"}
        </div>
      </div>
    </header>
  );
}
