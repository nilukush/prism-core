'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, FileText, Search, Filter, Calendar, User, Download, Eye } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { api } from '@/lib/api-client'
import { useToast } from '@/components/ui/use-toast'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDistanceToNow } from 'date-fns'

interface PRDDocument {
  id: string
  title: string
  type: string
  status: 'draft' | 'review' | 'approved' | 'published'
  summary?: string
  project: {
    id: number
    name: string
    key: string
  }
  creator: {
    id: number
    full_name?: string
    email: string
  }
  created_at: string
  updated_at: string
  ai_generated?: boolean
}

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  review: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  published: 'bg-blue-100 text-blue-800'
}

const statusLabels = {
  draft: 'Draft',
  review: 'In Review',
  approved: 'Approved',
  published: 'Published'
}

export default function PRDsPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [documents, setDocuments] = useState<PRDDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [projectFilter, setProjectFilter] = useState<string>('all')
  const [projects, setProjects] = useState<any[]>([])

  useEffect(() => {
    fetchDocuments()
    fetchProjects()
  }, [])

  const fetchDocuments = async () => {
    try {
      setLoading(true)
      const response = await api.documents.list({ document_type: 'prd' })
      setDocuments(response.documents || [])
    } catch (error: any) {
      console.error('Failed to fetch PRDs:', error)
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch PRD documents',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchProjects = async () => {
    try {
      const response = await api.projects.list()
      setProjects(response.projects || [])
    } catch (error) {
      console.error('Failed to fetch projects:', error)
    }
  }

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         doc.summary?.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesStatus = statusFilter === 'all' || doc.status === statusFilter
    const matchesProject = projectFilter === 'all' || doc.project.id.toString() === projectFilter
    
    return matchesSearch && matchesStatus && matchesProject
  })

  const handleExport = async (doc: PRDDocument, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      // In a real implementation, this would call an export API
      toast({
        title: 'Export Started',
        description: `Exporting "${doc.title}" as PDF...`
      })
    } catch (error) {
      toast({
        title: 'Export Failed',
        description: 'Failed to export document',
        variant: 'destructive'
      })
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-64" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Product Requirements</h1>
          <p className="text-muted-foreground">
            Manage your PRD documents and specifications
          </p>
        </div>
        <Button onClick={() => router.push('/app/prds/new')}>
          <Plus className="mr-2 h-4 w-4" />
          New PRD
        </Button>
      </div>

      <div className="flex flex-col gap-4 md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search PRDs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full md:w-48">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="review">In Review</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="published">Published</SelectItem>
          </SelectContent>
        </Select>
        {projects.length > 0 && (
          <Select value={projectFilter} onValueChange={setProjectFilter}>
            <SelectTrigger className="w-full md:w-48">
              <FileText className="mr-2 h-4 w-4" />
              <SelectValue placeholder="Filter by project" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Projects</SelectItem>
              {projects.map((project) => (
                <SelectItem key={project.id} value={project.id.toString()}>
                  {project.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {filteredDocuments.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No PRDs found</h3>
            <p className="text-muted-foreground text-center mb-4">
              {searchQuery || statusFilter !== 'all' || projectFilter !== 'all'
                ? 'Try adjusting your filters'
                : 'Get started by creating your first PRD'}
            </p>
            {!searchQuery && statusFilter === 'all' && projectFilter === 'all' && (
              <Button onClick={() => router.push('/app/prds/new')}>
                <Plus className="mr-2 h-4 w-4" />
                Create PRD
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredDocuments.map((doc) => (
            <Card 
              key={doc.id} 
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => router.push(`/app/prds/${doc.id}`)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-xl line-clamp-2">{doc.title}</CardTitle>
                    <CardDescription>
                      {doc.project.name} ({doc.project.key})
                    </CardDescription>
                  </div>
                  <Badge className={statusColors[doc.status]}>
                    {statusLabels[doc.status]}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {doc.summary && (
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {doc.summary}
                  </p>
                )}
                
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <User className="h-4 w-4" />
                    <span>
                      {doc.creator 
                        ? (doc.creator.full_name || doc.creator.email)
                        : `User ${doc.creator_id}`
                      }
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>
                      Updated {formatDistanceToNow(new Date(doc.updated_at), { addSuffix: true })}
                    </span>
                  </div>
                </div>

                {doc.ai_generated && (
                  <Badge variant="secondary" className="text-xs">
                    AI Generated
                  </Badge>
                )}

                <div className="flex gap-2 pt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation()
                      router.push(`/app/prds/${doc.id}`)
                    }}
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    View
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => handleExport(doc, e)}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Export
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}