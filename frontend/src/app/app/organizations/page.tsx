'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useSession } from 'next-auth/react'
import { Building2, Plus, Trash2, Users, FolderKanban, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { api } from '@/lib/api-client'
import { useToast } from '@/components/ui/use-toast'
import { Skeleton } from '@/components/ui/skeleton'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'

interface Organization {
  id: number
  name: string
  slug: string
  plan: string
  max_users: number
  max_projects: number
  is_owner: boolean
}

export default function OrganizationsPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { data: session } = useSession()
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [loading, setLoading] = useState(true)
  const [deleteOrgId, setDeleteOrgId] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    fetchOrganizations()
  }, [])

  const fetchOrganizations = async () => {
    try {
      setLoading(true)
      const response = await api.organizations.list()
      setOrganizations(response.organizations || [])
    } catch (error) {
      console.error('Failed to fetch organizations:', error)
      toast({
        title: 'Error',
        description: 'Failed to fetch organizations',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (orgId: number) => {
    try {
      setDeleting(true)
      console.log('Deleting organization:', orgId)
      
      // Optimistically update the UI
      const originalOrgs = [...organizations]
      setOrganizations(orgs => orgs.filter(org => org.id !== orgId))
      
      // Use the API client which handles auth properly
      await api.organizations.delete(orgId)
      console.log('Organization deleted successfully')
      
      // Success - the optimistic update was correct
      toast({
        title: 'Success',
        description: 'Organization deleted successfully'
      })
      
      // Clear any cached data
      localStorage.removeItem('selectedProjectId')
      sessionStorage.clear()
      
      // If no organizations left, redirect to create project page
      if (originalOrgs.length === 1) {
        setTimeout(() => {
          router.push('/app/projects/new')
        }, 500)
      }
    } catch (error: any) {
      // Rollback on error
      setOrganizations(organizations)
      console.error('Delete error:', error)
      
      // Refresh to get current state
      await fetchOrganizations()
      
      if (error.status === 404) {
        toast({
          title: 'Backend Not Ready',
          description: 'The delete endpoint is not deployed yet. Please use the SQL method or wait for deployment.',
          variant: 'destructive'
        })
      } else if (error.status === 401) {
        toast({
          title: 'Authentication Error',
          description: 'Your session has expired. Please login again.',
          variant: 'destructive'
        })
        setTimeout(() => router.push('/auth/login'), 1000)
      } else if (error.status === 403) {
        toast({
          title: 'Permission Denied',
          description: 'You do not have permission to delete this organization.',
          variant: 'destructive'
        })
      } else {
        toast({
          title: 'Error',
          description: error.data?.detail || error.message || 'Failed to delete organization',
          variant: 'destructive'
        })
      }
    } finally {
      setDeleting(false)
      setDeleteOrgId(null)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Organizations</h1>
            <p className="text-muted-foreground">Manage your organizations</p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-24 mt-2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Organizations</h1>
          <p className="text-muted-foreground">
            Manage your organizations and their settings
          </p>
        </div>
        <Button onClick={() => router.push('/app/projects/new')}>
          <Plus className="mr-2 h-4 w-4" />
          Create Organization
        </Button>
      </div>

      {organizations.length === 0 ? (
        <Card className="p-12 text-center">
          <Building2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">No Organizations</h2>
          <p className="text-muted-foreground mb-6">
            Create your first organization to start managing projects
          </p>
          <Button onClick={() => router.push('/app/projects/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Create Organization
          </Button>
        </Card>
      ) : (
        <>
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Organization Management</AlertTitle>
            <AlertDescription>
              You can only delete organizations that you own. Deleting an organization will permanently remove all associated projects and data.
            </AlertDescription>
          </Alert>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {organizations.map((org) => (
              <Card key={org.id} className="relative">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{org.name}</CardTitle>
                      <CardDescription>{org.slug}</CardDescription>
                    </div>
                    <Badge variant={org.plan === 'free' ? 'secondary' : 'default'}>
                      {org.plan}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Users className="h-4 w-4" />
                      <span>Up to {org.max_users} users</span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <FolderKanban className="h-4 w-4" />
                      <span>Up to {org.max_projects} projects</span>
                    </div>
                  </div>
                  
                  {org.is_owner && (
                    <div className="mt-4 pt-4 border-t">
                      <Button
                        variant="destructive"
                        size="sm"
                        className="w-full"
                        onClick={() => setDeleteOrgId(org.id)}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete Organization
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteOrgId !== null} onOpenChange={() => setDeleteOrgId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the organization
              and all associated projects, documents, and data.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteOrgId && handleDelete(deleteOrgId)}
              disabled={deleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleting ? 'Deleting...' : 'Delete Organization'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}