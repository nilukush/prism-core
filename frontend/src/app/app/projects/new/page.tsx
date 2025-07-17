'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Calendar, FolderKanban, Building2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
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
  const { toast } = useToast()
  const { data: session } = useSession()
  const [loading, setLoading] = useState(false)
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [loadingOrgs, setLoadingOrgs] = useState(true)
  
  const [formData, setFormData] = useState({
    name: '',
    key: '',
    description: '',
    status: 'planning',
    organization_id: '',
    start_date: '',
    target_end_date: ''
  })

  useEffect(() => {
    fetchOrganizations()
  }, [])

  const fetchOrganizations = async () => {
    try {
      setLoadingOrgs(true)
      const response = await api.organizations.list()
      
      if (response.organizations.length === 0) {
        // If no organizations, create a default one
        const defaultOrg: Organization = {
          id: 1,
          name: 'Personal Organization',
          slug: 'personal',
          plan: 'free',
          max_projects: 5
        }
        setOrganizations([defaultOrg])
        setFormData(prev => ({ ...prev, organization_id: '1' }))
      } else {
        setOrganizations(response.organizations)
        // Set the first organization as default
        setFormData(prev => ({ ...prev, organization_id: response.organizations[0].id.toString() }))
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error)
      // Fallback to default org if API fails
      const defaultOrg: Organization = {
        id: 1,
        name: 'Personal Organization',
        slug: 'personal',
        plan: 'free',
        max_projects: 5
      }
      setOrganizations([defaultOrg])
      setFormData(prev => ({ ...prev, organization_id: '1' }))
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
      
      toast({
        title: 'Success',
        description: 'Project created successfully'
      })
      
      // Redirect to the project page
      router.push(`/app/projects/${response.id}`)
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

  return (
    <div className="max-w-2xl mx-auto space-y-6">
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
  )
}