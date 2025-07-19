'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Building2, Plus, Users, FolderKanban, ArrowRight } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from './empty-state'
import { api } from '@/lib/api-client'
import { useToast } from '@/components/ui/use-toast'
import { Skeleton } from '@/components/ui/skeleton'

interface Organization {
  id: number
  name: string
  slug: string
  plan: string
  max_users: number
  max_projects: number
  is_owner: boolean
  projects_count?: number
  members_count?: number
}

export function OrganizationsView() {
  const router = useRouter()
  const { toast } = useToast()
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchOrganizations()
  }, [])

  const fetchOrganizations = async () => {
    try {
      setLoading(true)
      const response = await api.organizations.list()
      console.log('Organizations response:', response)
      
      // Filter out any invalid organizations
      const validOrgs = (response.organizations || []).filter((org: any) => {
        if (!org || typeof org !== 'object' || !org.id || !org.name) {
          console.warn('Skipping invalid organization:', org)
          return false
        }
        return true
      })
      
      setOrganizations(validOrgs)
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

  if (loading) {
    return (
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
    )
  }

  if (organizations.length === 0) {
    return (
      <EmptyState
        icon={<Building2 className="h-16 w-16" />}
        title="No Organizations Yet"
        description="Create your first organization to start managing projects and collaborating with your team."
        actions={[
          { label: "Create Organization", href: "/app/organizations/new" },
          { label: "Learn More", href: "/docs/organizations", variant: "outline" }
        ]}
      />
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {organizations.map((org) => {
        if (!org || !org.id || !org.name) {
          console.error('Invalid organization in render:', org)
          return null
        }
        
        return (
          <Card key={org.id} className="hover:shadow-lg transition-shadow cursor-pointer group">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg group-hover:text-primary transition-colors">
                    {org.name}
                  </CardTitle>
                  <CardDescription>{org.slug || 'No slug'}</CardDescription>
                </div>
                <Badge variant={org.plan === 'free' ? 'secondary' : 'default'}>
                  {org.plan || 'free'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm mb-4">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Users className="h-4 w-4" />
                  <span>{org.members_count || 0} members • Up to {org.max_users}</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <FolderKanban className="h-4 w-4" />
                  <span>{org.projects_count || 0} projects • Up to {org.max_projects}</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <Button
                  variant="ghost"
                  size="sm"
                  className="group-hover:bg-primary group-hover:text-primary-foreground transition-colors"
                  onClick={() => router.push(`/app/account?tab=organizations&org=${org.id}`)}
                >
                  View Details
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
                {org.is_owner && (
                  <Badge variant="outline" className="text-xs">
                    Owner
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>
        )
      })}
      
      <Card className="border-dashed hover:shadow-lg transition-shadow cursor-pointer group">
        <CardHeader>
          <CardTitle className="text-lg text-muted-foreground group-hover:text-primary transition-colors">
            Create New Organization
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <Button
            variant="outline"
            size="lg"
            className="group-hover:bg-primary group-hover:text-primary-foreground group-hover:border-primary transition-all"
            onClick={() => router.push('/app/organizations/new')}
          >
            <Plus className="mr-2 h-5 w-5" />
            New Organization
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}