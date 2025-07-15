'use client'

import React from 'react'
import { ChevronDown, Plus, Building2, Folder } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useProject } from '@/contexts/ProjectContext'
import { useRouter } from 'next/navigation'

export function ProjectSelector() {
  const { currentProject, projects, isLoading, setCurrentProject } = useProject()
  const router = useRouter()

  if (isLoading) {
    return (
      <Button variant="ghost" size="sm" disabled>
        <Folder className="h-4 w-4 mr-2" />
        Loading...
      </Button>
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="max-w-[200px]">
          <Folder className="h-4 w-4 mr-2 flex-shrink-0" />
          <span className="truncate">
            {currentProject?.name || 'Select Project'}
          </span>
          <ChevronDown className="h-4 w-4 ml-2 flex-shrink-0" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[250px]">
        <DropdownMenuLabel className="flex items-center gap-2">
          <Building2 className="h-4 w-4" />
          Projects
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        {projects.length === 0 ? (
          <DropdownMenuItem disabled>
            <span className="text-muted-foreground">No projects available</span>
          </DropdownMenuItem>
        ) : (
          projects.map((project) => (
            <DropdownMenuItem
              key={project.id}
              onClick={() => setCurrentProject(project)}
              className="cursor-pointer"
            >
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-2">
                  <Folder className="h-4 w-4" />
                  <div>
                    <div className="font-medium">{project.name}</div>
                    <div className="text-xs text-muted-foreground">{project.key}</div>
                  </div>
                </div>
                {currentProject?.id === project.id && (
                  <Badge variant="secondary" className="text-xs">
                    Current
                  </Badge>
                )}
              </div>
            </DropdownMenuItem>
          ))
        )}
        
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => router.push('/app/projects/new')}
          className="cursor-pointer"
        >
          <Plus className="h-4 w-4 mr-2" />
          Create New Project
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => router.push('/app/projects')}
          className="cursor-pointer"
        >
          View All Projects
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}