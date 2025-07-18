'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { ArrowLeft, FolderKanban, Calendar, Users, Archive, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api-client'
import { useToast } from '@/components/ui/use-toast'
import { Skeleton } from '@/components/ui/skeleton'

interface Project {
  id: number
  name: string
  key: string
  description?: string
  status: 'planning' | 'active' | 'on_hold' | 'completed' | 'archived'
  start_date?: string
  target_end_date?: string
  owner: {
    id: number
    full_name: string
    email: string
  }
  organization: {
    id: number
    name: string
  }
  created_at: string
  updated_at: string
}

const statusColors = {
  planning: 'bg-blue-100 text-blue-800',
  active: 'bg-green-100 text-green-800',
  on_hold: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-gray-100 text-gray-800',
  archived: 'bg-gray-100 text-gray-600'
}

const statusLabels = {
  planning: 'Planning',
  active: 'Active',
  on_hold: 'On Hold',
  completed: 'Completed',
  archived: 'Archived'
}

export default function ProjectDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { toast } = useToast()
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (params.id) {
      fetchProject(params.id as string)
    }
  }, [params.id])

  const fetchProject = async (id: string) => {
    try {
      setLoading(true)
      const response = await api.projects.get(id)
      setProject(response)
    } catch (error: any) {
      console.error('Failed to fetch project:', error)
      if (error.status === 404) {
        toast({
          title: 'Project not found',
          description: 'The project you are looking for does not exist.',
          variant: 'destructive'
        })
        router.push('/app/projects')
      } else {
        toast({
          title: 'Error',
          description: 'Failed to load project details',
          variant: 'destructive'
        })
      }
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div>
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-64 mt-2" />
          </div>
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-48 mt-2" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card className="p-12 text-center">
          <FolderKanban className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Project Not Found</h2>
          <p className="text-muted-foreground mb-6">
            The project you're looking for doesn't exist or has been deleted.
          </p>
          <Button onClick={() => router.push('/app/projects')}>
            Back to Projects
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/app/projects')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
            <p className="text-muted-foreground">
              {project.key} • {project.organization.name}
            </p>
          </div>
        </div>
        <Badge className={statusColors[project.status]}>
          {statusLabels[project.status]}
        </Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Project Details</CardTitle>
          <CardDescription>
            View and manage project information
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {project.description && (
            <div>
              <h3 className="font-medium mb-2">Description</h3>
              <p className="text-sm text-muted-foreground">
                {project.description}
              </p>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <Users className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Owner:</span>
                <span>{project.owner.full_name}</span>
              </div>
              
              {project.start_date && (
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Start Date:</span>
                  <span>{new Date(project.start_date).toLocaleDateString()}</span>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <Archive className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Created:</span>
                <span>{new Date(project.created_at).toLocaleDateString()}</span>
              </div>
              
              {project.target_end_date && (
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Target End:</span>
                  <span>{new Date(project.target_end_date).toLocaleDateString()}</span>
                </div>
              )}
            </div>
          </div>

          <div className="pt-6 border-t">
            <div className="flex gap-4">
              <Button variant="outline" onClick={() => router.push('/app/projects')}>
                Back to Projects
              </Button>
              <Button variant="outline">
                Edit Project
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}