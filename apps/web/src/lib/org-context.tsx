"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "./api";
import { useAuth } from "./auth-context";

interface Organization {
  id: string;
  name: string;
  tier: string;
}

interface Project {
  id: string;
  name: string;
  organization_id: string;
}

interface OrgContextType {
  organizations: Organization[];
  projects: Project[];
  activeOrg: Organization | null;
  activeProject: Project | null;
  setActiveOrg: (org: Organization) => void;
  setActiveProject: (project: Project | null) => void;
  refresh: () => Promise<void>;
}

const OrgContext = createContext<OrgContextType | undefined>(undefined);

export function OrgProvider({ children }: { children: React.ReactNode }) {
  const { user, token } = useAuth();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeOrg, setActiveOrg] = useState<Organization | null>(null);
  const [activeProject, setActiveProject] = useState<Project | null>(null);

  const refresh = async () => {
    if (!token) return;
    try {
      const orgsData = await api.get("/v1/organizations");
      setOrganizations(orgsData.data);
      
      const projectsData = await api.get("/v1/projects");
      setProjects(projectsData.data);

      // Default active org/project if not set
      if (!activeOrg && orgsData.data.length > 0) {
        const savedOrgId = localStorage.getItem("activeOrgId");
        const found = orgsData.data.find((o: any) => o.id === savedOrgId) || orgsData.data[0];
        setActiveOrg(found);
      }

      if (!activeProject && projectsData.data.length > 0) {
        const savedProjId = localStorage.getItem("activeProjectId");
        const found = projectsData.data.find((p: any) => p.id === savedProjId) || projectsData.data[0];
        setActiveProject(found);
      }
    } catch (err) {
      console.error("Failed to fetch orgs/projects", err);
    }
  };

  useEffect(() => {
    if (token) {
      refresh();
    }
  }, [token]);

  const handleSetActiveOrg = (org: Organization) => {
    setActiveOrg(org);
    localStorage.setItem("activeOrgId", org.id);
    // When switching org, clear active project if it doesn't belong to new org
    if (activeProject && activeProject.organization_id !== org.id) {
      setActiveProject(null);
      localStorage.removeItem("activeProjectId");
    }
  };

  const handleSetActiveProject = (project: Project | null) => {
    setActiveProject(project);
    if (project) {
      localStorage.setItem("activeProjectId", project.id);
    } else {
      localStorage.removeItem("activeProjectId");
    }
  };

  return (
    <OrgContext.Provider 
      value={{ 
        organizations, 
        projects, 
        activeOrg, 
        activeProject, 
        setActiveOrg: handleSetActiveOrg, 
        setActiveProject: handleSetActiveProject,
        refresh
      }}
    >
      {children}
    </OrgContext.Provider>
  );
}

export function useOrg() {
  const context = useContext(OrgContext);
  if (context === undefined) {
    throw new Error("useOrg must be used within an OrgProvider");
  }
  return context;
}
