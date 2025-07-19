'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ArrowLeft, Calendar, FolderKanban, Building2, Plus } from 'lucide-react'
import { FixOrgModal } from './fix-org-modal'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { api } from '@/lib/api-client'
import { useToast } from '@/components/ui/use-toast'
import { useSession } from 'next-auth/react'

interface Organization {
  id: number
  name: string
  slug: string
  plan: string
  max_projects: number
}

export default function NewProjectPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const { data: session } = useSession()
  const [loading, setLoading] = useState(false)
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [loadingOrgs, setLoadingOrgs] = useState(true)
  const [showCreateOrgModal, setShowCreateOrgModal] = useState(false)
  const [creatingOrg, setCreatingOrg] = useState(false)
  
  const [formData, setFormData] = useState({
    name: '',
    key: '',
    description: '',
    status: 'planning',
    organization_id: '',
    start_date: '',
    target_end_date: ''
  })

  const [orgFormData, setOrgFormData] = useState({
    name: '',
    slug: '',
    description: ''
  })

  useEffect(() => {
    // Fetch organizations on mount
    fetchOrganizations()
    
    // If we have a refresh parameter, it means we're coming from a deletion
    if (searchParams.get('refresh')) {
      console.log('Refresh parameter detected - ensuring fresh data')
      // Remove the refresh parameter from URL
      const newUrl = window.location.pathname
      window.history.replaceState({}, '', newUrl)
    }
  }, [searchParams])

  // Refetch organizations when window gains focus (e.g., after deleting from another tab/page)
  useEffect(() => {
    const handleFocus = () => {
      console.log('Window gained focus - refetching organizations')
      fetchOrganizations()
    }

    window.addEventListener('focus', handleFocus)
    // Also refetch when page becomes visible (handles tab switching)
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        console.log('Page became visible - refetching organizations')
        fetchOrganizations()
      }
    })

    return () => {
      window.removeEventListener('focus', handleFocus)
      document.removeEventListener('visibilitychange', handleFocus)
    }
  }, [])

  // Debug log for modal state
  useEffect(() => {
    console.log('showCreateOrgModal state:', showCreateOrgModal)
    console.log('organizations:', organizations)
    console.log('loadingOrgs:', loadingOrgs)
  }, [showCreateOrgModal, organizations, loadingOrgs])

  // Redirect to account page when no organizations exist
  useEffect(() => {
    if (!loadingOrgs && organizations.length === 0) {
      console.log('No organizations found, redirecting to account page')
      router.push('/app/account')
    }
  }, [loadingOrgs, organizations.length, router])

  const fetchOrganizations = async () => {
    try {
      setLoadingOrgs(true)
      console.log('Fetching organizations...', new Date().toISOString())
      
      // Force fresh data by bypassing any potential cache
      const response = await api.organizations.list()
      console.log('Organizations API response:', response)
      console.log('Number of organizations:', response.organizations?.length || 0)
      
      // Check if organizations is actually an array
      const orgs = response.organizations || []
      console.log('Organizations array:', orgs, 'Is Array:', Array.isArray(orgs))
      
      // Filter out any invalid organizations
      const validOrgs = orgs.filter((org: any) => org && org.id && org.name)
      console.log('Valid organizations after filtering:', validOrgs)
      
      if (validOrgs.length === 0) {
        // No organizations exist - will redirect to account page
        console.log('No valid organizations found')
        setOrganizations([])
      } else {
        console.log('Valid organizations found:', validOrgs)
        setOrganizations(validOrgs)
        // Set the first organization as default
        setFormData(prev => ({ ...prev, organization_id: validOrgs[0].id.toString() }))
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error)
      toast({
        title: 'Error',
        description: 'Failed to fetch organizations. Please try again.',
        variant: 'destructive'
      })
    } finally {
      setLoadingOrgs(false)
    }
  }

  const generateProjectKey = (name: string) => {
    // Generate a project key from the name (e.g., "My Project" -> "MP")
    const words = name.trim().split(/\s+/)
    if (words.length === 1) {
      return words[0].substring(0, 4).toUpperCase()
    }
    return words
      .map(word => word[0])
      .join('')
      .substring(0, 4)
      .toUpperCase()
  }

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .substring(0, 50)
  }

  const handleNameChange = (name: string) => {
    setFormData(prev => ({
      ...prev,
      name,
      key: generateProjectKey(name)
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.name || !formData.key || !formData.organization_id) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in all required fields',
        variant: 'destructive'
      })
      return
    }

    try {
      setLoading(true)
      
      // Create the project
      const projectData = {
        name: formData.name,
        key: formData.key,
        description: formData.description || undefined,
        status: formData.status,
        organization_id: parseInt(formData.organization_id),
        start_date: formData.start_date || undefined,
        target_end_date: formData.target_end_date || undefined
      }

      const response = await api.projects.create(projectData)
      console.log('Project creation response:', response)
      
      toast({
        title: 'Success',
        description: 'Project created successfully'
      })
      
      // Redirect to the project page - check response structure
      const projectId = response.project?.id || response.id
      if (projectId) {
        router.push(`/app/projects/${projectId}`)
      } else {
        console.error('No project ID in response:', response)
        router.push('/app/projects')
      }
    } catch (error: any) {
      console.error('Failed to create project:', error)
      toast({
        title: 'Error',
        description: error.data?.detail || error.message || 'Failed to create project',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCreateOrganization = async (orgData: { name: string; slug: string; description: string }) => {
    try {
      setCreatingOrg(true)
      const newOrg = await api.organizations.create(orgData)
      
      toast({
        title: 'Success',
        description: 'Organization created successfully'
      })
      
      // Refresh organizations list
      await fetchOrganizations()
      setShowCreateOrgModal(false)
      
      // Select the newly created organization
      setFormData(prev => ({ ...prev, organization_id: newOrg.id.toString() }))
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.data?.detail || 'Failed to create organization',
        variant: 'destructive'
      })
    } finally {
      setCreatingOrg(false)
    }
  }

  if (loadingOrgs) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <FolderKanban className="h-12 w-12 text-muted-foreground mx-auto mb-4 animate-pulse" />
          <p className="text-muted-foreground">Loading organizations...</p>
        </div>
      </div>
    )
  }

  // The redirect effect will handle the no-organizations case
  if (!loadingOrgs && organizations.length === 0) {
    return null // Component will redirect, no need to render
  }

  // If we're here, either loading or have organizations
  if (!loadingOrgs && organizations.length > 0) {
    // Have organizations, proceed with normal flow
    console.log('Organizations exist:', organizations.length, '- proceeding with form')
  }

  // Main render
  return (
    <>
      <div className="max-w-2xl mx-auto space-y-6">
      {/* Show fix component ONLY in development if organizations exist but modal isn't showing */}
      {process.env.NODE_ENV === 'development' && organizations.length > 0 && !showCreateOrgModal && (
        <FixOrgModal />
      )}
      
      
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push('/app/projects')}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Create New Project</h1>
          <p className="text-muted-foreground">
            Set up a new project for your team
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Project Information</CardTitle>
            <CardDescription>
              Enter the basic details for your new project
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">Project Name *</Label>
                <Input
                  id="name"
                  placeholder="e.g., Mobile App Redesign"
                  value={formData.name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="key">Project Key *</Label>
                <Input
                  id="key"
                  placeholder="e.g., MAR"
                  value={formData.key}
                  onChange={(e) => setFormData(prev => ({ ...prev, key: e.target.value.toUpperCase() }))}
                  maxLength={10}
                  required
                />
                <p className="text-sm text-muted-foreground">
                  Used as prefix for issues (e.g., MAR-123)
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe the project goals and objectives..."
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={4}
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="organization">Organization *</Label>
                <Select 
                  value={formData.organization_id} 
                  onValueChange={(value) => setFormData(prev => ({ ...prev, organization_id: value }))}
                >
                  <SelectTrigger id="organization">
                    <Building2 className="mr-2 h-4 w-4" />
                    <SelectValue placeholder="Select organization" />
                  </SelectTrigger>
                  <SelectContent>
                    {organizations.map((org) => (
                      <SelectItem key={org.id} value={org.id.toString()}>
                        {org.name}
                      </SelectItem>
                    ))}
                    <div className="px-2 py-1.5 border-t">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full justify-start"
                        onClick={() => router.push('/app/organizations/new')}
                      >
                        <Plus className="mr-2 h-4 w-4" />
                        Create New Organization
                      </Button>
                    </div>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="status">Status *</Label>
                <Select 
                  value={formData.status} 
                  onValueChange={(value) => setFormData(prev => ({ ...prev, status: value }))}
                >
                  <SelectTrigger id="status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="planning">Planning</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="on_hold">On Hold</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date</Label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="start_date"
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
                    className="pl-10"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="target_end_date">Target End Date</Label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="target_end_date"
                    type="date"
                    value={formData.target_end_date}
                    onChange={(e) => setFormData(prev => ({ ...prev, target_end_date: e.target.value }))}
                    className="pl-10"
                    min={formData.start_date}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-4 mt-6">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push('/app/projects')}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            {loading ? 'Creating...' : 'Create Project'}
          </Button>
        </div>
      </form>
      </div>

      {/* Create Organization Modal - Always render at root level */}
      <Dialog 
        open={showCreateOrgModal} 
        onOpenChange={(open) => {
          console.log('Root Dialog onOpenChange called with:', open)
          setShowCreateOrgModal(open)
        }}
      >
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Create Your First Organization</DialogTitle>
            <DialogDescription>
              You need to create an organization before you can create projects. Organizations help you manage teams and projects.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="org-name-root">Organization Name *</Label>
              <Input
                id="org-name-root"
                placeholder="e.g., My Company"
                value={orgFormData.name}
                onChange={(e) => {
                  const name = e.target.value
                  setOrgFormData(prev => ({
                    ...prev,
                    name,
                    slug: generateSlug(name)
                  }))
                }}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="org-slug-root">URL Slug *</Label>
              <Input
                id="org-slug-root"
                placeholder="e.g., my-company"
                value={orgFormData.slug}
                onChange={(e) => setOrgFormData(prev => ({ ...prev, slug: e.target.value }))}
                pattern="[a-z0-9-]+"
              />
              <p className="text-sm text-muted-foreground">
                This will be used in URLs and must be unique
              </p>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="org-description-root">Description</Label>
              <Textarea
                id="org-description-root"
                placeholder="What does your organization do?"
                value={orgFormData.description}
                onChange={(e) => setOrgFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowCreateOrgModal(false)
                router.push('/app/dashboard')
              }}
              disabled={creatingOrg}
            >
              Cancel
            </Button>
            <Button
              onClick={() => handleCreateOrganization(orgFormData)}
              disabled={creatingOrg || !orgFormData.name || !orgFormData.slug}
            >
              {creatingOrg ? 'Creating...' : 'Create Organization'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}