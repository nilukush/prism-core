'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useSession } from 'next-auth/react'
import { api } from '@/lib/api-client'
import { useToast } from '@/components/ui/use-toast'

interface Project {
  id: number
  name: string
  key: string
  description?: string
  status: string
  organization_id: number
  workspace_id?: string
  owner_id: number
}

interface ProjectContextValue {
  currentProject: Project | null
  projects: Project[]
  isLoading: boolean
  error: string | null
  setCurrentProject: (project: Project) => void
  refreshProjects: () => Promise<void>
}

const ProjectContext = createContext<ProjectContextValue | undefined>(undefined)

const PROJECT_STORAGE_KEY = 'prism_current_project'

export function ProjectProvider({ children }: { children: ReactNode }) {
  const { data: session, status } = useSession()
  const { toast } = useToast()
  const [currentProject, setCurrentProjectState] = useState<Project | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load saved project from localStorage
  useEffect(() => {
    const savedProjectId = localStorage.getItem(PROJECT_STORAGE_KEY)
    if (savedProjectId && projects.length > 0) {
      const project = projects.find(p => p.id === parseInt(savedProjectId))
      if (project) {
        setCurrentProjectState(project)
      }
    }
  }, [projects])

  // Fetch user's projects
  const refreshProjects = async () => {
    if (status !== 'authenticated') return

    setIsLoading(true)
    setError(null)
    
    try {
      const response = await api.projects.list()
      const projectList = response.projects || []
      
      setProjects(projectList)
      
      // If no current project is set, use the first available project
      if (!currentProject && projectList.length > 0) {
        setCurrentProject(projectList[0])
      }
    } catch (err: any) {
      console.error('Error fetching projects:', err)
      setError(err.message || 'Failed to fetch projects')
      
      // For now, create a mock project to allow testing
      // Remove this in production
      if (process.env.NODE_ENV === 'development') {
        const mockProject: Project = {
          id: 2,
          name: 'Default Project',
          key: 'PRISM',
          description: 'Default project for development',
          status: 'active',
          organization_id: 2,
          owner_id: session?.user?.id ? parseInt(session.user.id) : 4
        }
        setProjects([mockProject])
        setCurrentProject(mockProject)
      }
    } finally {
      setIsLoading(false)
    }
  }

  // Fetch projects when session is ready
  useEffect(() => {
    if (status === 'authenticated') {
      refreshProjects()
    }
  }, [status])

  const setCurrentProject = (project: Project) => {
    setCurrentProjectState(project)
    localStorage.setItem(PROJECT_STORAGE_KEY, project.id.toString())
    
    toast({
      title: 'Project Changed',
      description: `Switched to ${project.name}`,
    })
  }

  const value: ProjectContextValue = {
    currentProject,
    projects,
    isLoading,
    error,
    setCurrentProject,
    refreshProjects
  }

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  )
}

export function useProject() {
  const context = useContext(ProjectContext)
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider')
  }
  return context
}

// Utility hook to ensure a project is selected
export function useRequireProject() {
  const { currentProject, isLoading } = useProject()
  const { toast } = useToast()
  
  useEffect(() => {
    if (!isLoading && !currentProject) {
      toast({
        title: 'No Project Selected',
        description: 'Please select a project to continue',
        variant: 'destructive'
      })
    }
  }, [currentProject, isLoading, toast])
  
  return { currentProject, isProjectRequired: !isLoading && !currentProject }
}