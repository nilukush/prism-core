'use client'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Plus, Zap } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useProject } from '@/contexts/ProjectContext'

export default function SprintsPage() {
  const router = useRouter()
  const { currentProject } = useProject()

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Sprints</h1>
          <p className="text-muted-foreground">
            Plan and manage your project sprints
          </p>
        </div>
        <Button disabled>
          <Plus className="mr-2 h-4 w-4" />
          Create Sprint
        </Button>
      </div>

      {!currentProject ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground text-center">
              Please select a project to view sprints
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Sprint Management
            </CardTitle>
            <CardDescription>
              Sprint management features coming soon
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12">
              <Zap className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                Sprint planning and tracking features will be available soon.
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                You'll be able to create sprints, manage backlog items, and track progress.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}