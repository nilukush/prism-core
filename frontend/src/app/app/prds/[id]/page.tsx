'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/use-toast'
import { api } from '@/lib/api-client'
import { exportToPdf } from '@/lib/pdf-export'
import { FileText, Edit, Loader2, ArrowLeft } from 'lucide-react'

export default function PRDViewPage() {
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()
  const [loading, setLoading] = useState(true)
  const [exportingPdf, setExportingPdf] = useState(false)
  const [document, setDocument] = useState<any>(null)

  useEffect(() => {
    loadDocument()
  }, [params['id']])

  const loadDocument = async () => {
    try {
      const response = await api.documents.get(params['id'] as string)
      // The backend returns the document data directly
      setDocument(response)
    } catch (error: any) {
      console.error('Error loading document:', error)
      toast({
        title: 'Error Loading Document',
        description: error.message || 'Failed to load document',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const exportPDF = async () => {
    if (!document) return

    setExportingPdf(true)
    try {
      await exportToPdf({
        prd: document.content.raw_prd || '',
        metadata: {
          productName: document.title,
          targetAudience: document.content.target_audience || '',
          generatedAt: document.created_at,
          model: document.ai_model,
          provider: document.ai_generated ? 'AI Generated' : 'Manual'
        }
      })
      
      toast({
        title: 'PDF Exported!',
        description: 'Your PRD has been exported as PDF successfully.',
      })
    } catch (error: any) {
      console.error('Error exporting PDF:', error)
      toast({
        title: 'Export Failed',
        description: error.message || 'Failed to export PDF. Please try again.',
        variant: 'destructive'
      })
    } finally {
      setExportingPdf(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (!document) {
    return (
      <div className="container max-w-4xl py-6">
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-muted-foreground">Document not found</p>
            <Button 
              variant="outline" 
              className="mt-4"
              onClick={() => router.push('/app/prds')}
            >
              Back to PRDs
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container max-w-4xl py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/app/prds')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{document.title}</h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={document.status === 'draft' ? 'secondary' : 'default'}>
                {document.status}
              </Badge>
              {document.ai_generated && (
                <Badge variant="outline">AI Generated</Badge>
              )}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => router.push(`/app/prds/${params['id']}/edit`)}
          >
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <Button 
            variant="outline" 
            onClick={exportPDF}
            disabled={exportingPdf}
          >
            {exportingPdf ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <FileText className="h-4 w-4 mr-2" />
                Export PDF
              </>
            )}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Product Requirements Document</CardTitle>
          {document.summary && (
            <p className="text-sm text-muted-foreground mt-2">
              {document.summary}
            </p>
          )}
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none">
            <pre className="whitespace-pre-wrap font-sans">
              {document.content.raw_prd || JSON.stringify(document.content, null, 2)}
            </pre>
          </div>
        </CardContent>
      </Card>

      {document.content.key_features && document.content.key_features.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Key Features</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-1">
              {document.content.key_features.map((feature: string, index: number) => (
                <li key={index}>{feature}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {document.content.constraints && document.content.constraints.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Constraints</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-1">
              {document.content.constraints.map((constraint: string, index: number) => (
                <li key={index}>{constraint}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Document Information</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="font-medium text-muted-foreground">Created</dt>
              <dd>{new Date(document.created_at).toLocaleString()}</dd>
            </div>
            <div>
              <dt className="font-medium text-muted-foreground">Updated</dt>
              <dd>{new Date(document.updated_at).toLocaleString()}</dd>
            </div>
            {document.ai_model && (
              <div>
                <dt className="font-medium text-muted-foreground">AI Model</dt>
                <dd>{document.ai_model}</dd>
              </div>
            )}
            <div>
              <dt className="font-medium text-muted-foreground">Document ID</dt>
              <dd className="font-mono text-xs">{document.id}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </div>
  )
}