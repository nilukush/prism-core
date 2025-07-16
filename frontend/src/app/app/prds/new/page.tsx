'use client'

import { useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useSession } from 'next-auth/react'
import { useProject, useRequireProject } from '@/contexts/ProjectContext'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/components/ui/use-toast'
import { apiClient, api } from '@/lib/api-client'
import { exportToPdf } from '@/lib/pdf-export'
import { Sparkles, FileText, Plus, X, Loader2 } from 'lucide-react'

export default function NewPRDPage() {
  const searchParams = useSearchParams()
  const isAIEnabled = searchParams.get('ai') === 'true'
  const { toast } = useToast()
  const { data: session, status } = useSession()
  const router = useRouter()
  const { currentProject, isProjectRequired } = useRequireProject()

  const [loading, setLoading] = useState(false)
  const [exportingPdf, setExportingPdf] = useState(false)
  const [savingDraft, setSavingDraft] = useState(false)
  const [generatedPRD, setGeneratedPRD] = useState('')
  const [prdMetadata, setPrdMetadata] = useState<any>(null)
  const [formData, setFormData] = useState({
    productName: '',
    description: '',
    targetAudience: '',
    keyFeatures: [''],
    constraints: ['']
  })

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleFeatureChange = (index: number, value: string) => {
    const newFeatures = [...formData.keyFeatures]
    newFeatures[index] = value
    setFormData(prev => ({
      ...prev,
      keyFeatures: newFeatures
    }))
  }

  const addFeature = () => {
    setFormData(prev => ({
      ...prev,
      keyFeatures: [...prev.keyFeatures, '']
    }))
  }

  const removeFeature = (index: number) => {
    setFormData(prev => ({
      ...prev,
      keyFeatures: prev.keyFeatures.filter((_, i) => i !== index)
    }))
  }

  const handleConstraintChange = (index: number, value: string) => {
    const newConstraints = [...formData.constraints]
    newConstraints[index] = value
    setFormData(prev => ({
      ...prev,
      constraints: newConstraints
    }))
  }

  const addConstraint = () => {
    setFormData(prev => ({
      ...prev,
      constraints: [...prev.constraints, '']
    }))
  }

  const removeConstraint = (index: number) => {
    setFormData(prev => ({
      ...prev,
      constraints: prev.constraints.filter((_, i) => i !== index)
    }))
  }

  const exportPDF = async () => {
    if (!generatedPRD) {
      toast({
        title: 'No PRD to Export',
        description: 'Please generate a PRD first.',
        variant: 'destructive'
      })
      return
    }

    setExportingPdf(true)
    try {
      await exportToPdf({
        prd: generatedPRD,
        metadata: prdMetadata || {
          productName: formData.productName,
          targetAudience: formData.targetAudience
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

  const saveDraft = async () => {
    if (!generatedPRD) {
      toast({
        title: 'No PRD to Save',
        description: 'Please generate a PRD first.',
        variant: 'destructive'
      })
      return
    }

    setSavingDraft(true)
    try {
      if (!currentProject) {
        toast({
          title: 'No Project Selected',
          description: 'Please select a project before saving documents.',
          variant: 'destructive'
        })
        router.push('/app/projects')
        return
      }

      const response = await api.documents.create({
        title: formData.productName,
        type: 'prd',
        content: {
          raw_prd: generatedPRD,
          product_description: formData.description,
          target_audience: formData.targetAudience,
          key_features: formData.keyFeatures.filter(f => f.trim()),
          constraints: formData.constraints.filter(c => c.trim())
        },
        summary: `Product Requirements Document for ${formData.productName}`,
        project_id: currentProject.id,
        status: 'draft',
        ai_generated: true,
        ai_model: prdMetadata?.model || 'mock',
        generation_context: {
          provider: prdMetadata?.provider || 'mock',
          generated_at: prdMetadata?.generatedAt || new Date().toISOString()
        }
      })

      if (response.success) {
        toast({
          title: 'Draft Saved!',
          description: 'Your PRD has been saved as a draft.',
        })
        
        // Redirect to the document view page
        router.push(`/app/prds/${response.document.id}`)
      }
    } catch (error: any) {
      console.error('Error saving draft:', error)
      toast({
        title: 'Save Failed',
        description: error.message || 'Failed to save draft. Please try again.',
        variant: 'destructive'
      })
    } finally {
      setSavingDraft(false)
    }
  }

  const generatePRD = async () => {
    // Check session first
    if (status === 'unauthenticated' || !session) {
      toast({
        title: 'Authentication Required',
        description: 'Please log in to generate PRDs.',
        variant: 'destructive'
      })
      router.push('/auth/login')
      return
    }

    if (!formData.productName || !formData.description || !formData.targetAudience) {
      toast({
        title: 'Missing Information',
        description: 'Please fill in all required fields.',
        variant: 'destructive'
      })
      return
    }

    const validFeatures = formData.keyFeatures.filter(f => f.trim())
    if (validFeatures.length === 0) {
      toast({
        title: 'Missing Features',
        description: 'Please add at least one key feature.',
        variant: 'destructive'
      })
      return
    }

    setLoading(true)
    try {
      console.log('Sending PRD generation request...')
      const response = await apiClient.post('/api/v1/ai/generate/prd', {
        product_name: formData.productName,
        description: formData.description,
        target_audience: formData.targetAudience,
        key_features: validFeatures,
        constraints: formData.constraints.filter(c => c.trim())
        // Provider will use backend's DEFAULT_LLM_PROVIDER setting
      })

      console.log('Raw API Response:', response)
      
      // The backend returns the response directly, not wrapped in data
      if (response && response.success) {
        console.log('PRD Content Length:', response.prd?.length || 0)
        console.log('PRD Content Preview:', response.prd?.substring(0, 100) || 'No content')
        
        if (!response.prd) {
          throw new Error('PRD content is empty')
        }
        
        setGeneratedPRD(response.prd)
        setPrdMetadata({
          productName: formData.productName,
          targetAudience: formData.targetAudience,
          generatedAt: response.metadata?.generated_at,
          model: response.metadata?.model,
          provider: response.metadata?.provider
        })
        toast({
          title: 'PRD Generated!',
          description: 'Your PRD has been generated successfully.',
        })
      } else {
        throw new Error(response?.message || 'Invalid response format')
      }
    } catch (error: any) {
      console.error('Error generating PRD:', error)
      console.error('Error details:', {
        message: error.message,
        status: error.status,
        data: error.data,
        stack: error.stack
      })
      
      // Check if it's an authentication error
      if (error.status === 401) {
        toast({
          title: 'Authentication Error',
          description: 'Your session has expired. Please log in again.',
          variant: 'destructive'
        })
        // Optionally redirect to login
        // window.location.href = '/auth/login'
      } else {
        toast({
          title: 'Generation Failed',
          description: error.message || 'Failed to generate PRD. Please try again.',
          variant: 'destructive'
        })
      }
    } finally {
      setLoading(false)
    }
  }

  // Show project selection prompt if no project is selected
  if (isProjectRequired) {
    return (
      <div className="container max-w-6xl py-6">
        <Card>
          <CardHeader>
            <CardTitle>No Project Selected</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              You need to select a project before creating a PRD. This ensures your document is properly organized.
            </p>
            <Button onClick={() => router.push('/app/projects')}>
              Select Project
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container max-w-6xl py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Create Product Requirements Document</h1>
          {currentProject && (
            <p className="text-sm text-muted-foreground mt-1">
              Project: {currentProject.name} ({currentProject.key})
            </p>
          )}
        </div>
        {isAIEnabled && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Sparkles className="h-4 w-4" />
            AI-Powered Generation
          </div>
        )}
      </div>

      <Tabs defaultValue={isAIEnabled ? 'ai' : 'manual'} className="w-full">
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="ai" disabled={!isAIEnabled}>
            <Sparkles className="h-4 w-4 mr-2" />
            AI Generation
          </TabsTrigger>
          <TabsTrigger value="manual">
            <FileText className="h-4 w-4 mr-2" />
            Manual Creation
          </TabsTrigger>
        </TabsList>

        <TabsContent value="ai" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Product Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="productName">Product Name *</Label>
                <Input
                  id="productName"
                  placeholder="e.g., Customer Analytics Dashboard"
                  value={formData.productName}
                  onChange={(e) => handleInputChange('productName', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Product Description *</Label>
                <Textarea
                  id="description"
                  placeholder="Describe what your product does and the problem it solves..."
                  rows={4}
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="targetAudience">Target Audience *</Label>
                <Input
                  id="targetAudience"
                  placeholder="e.g., Product managers at enterprise SaaS companies"
                  value={formData.targetAudience}
                  onChange={(e) => handleInputChange('targetAudience', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label>Key Features *</Label>
                {formData.keyFeatures.map((feature, index) => (
                  <div key={index} className="flex gap-2">
                    <Input
                      placeholder="e.g., Real-time customer behavior tracking"
                      value={feature}
                      onChange={(e) => handleFeatureChange(index, e.target.value)}
                    />
                    {formData.keyFeatures.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => removeFeature(index)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addFeature}
                  className="mt-2"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Feature
                </Button>
              </div>

              <div className="space-y-2">
                <Label>Constraints (Optional)</Label>
                {formData.constraints.map((constraint, index) => (
                  <div key={index} className="flex gap-2">
                    <Input
                      placeholder="e.g., Must integrate with existing CRM"
                      value={constraint}
                      onChange={(e) => handleConstraintChange(index, e.target.value)}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removeConstraint(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addConstraint}
                  className="mt-2"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Constraint
                </Button>
              </div>

              <Button
                onClick={generatePRD}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating PRD...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generate PRD
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {generatedPRD && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Generated PRD</CardTitle>
                  {prdMetadata && (
                    <div className="text-sm text-muted-foreground">
                      <span>Provider: {prdMetadata.provider}</span>
                      {prdMetadata.model && (
                        <span className="ml-2">Model: {prdMetadata.model}</span>
                      )}
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  {/* Debug: Show length */}
                  <div className="text-xs text-muted-foreground mb-2">
                    PRD Length: {generatedPRD.length} characters
                  </div>
                  <div className="bg-muted/50 rounded-lg p-4 border border-border">
                    <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed overflow-x-auto">
                      {generatedPRD}
                    </pre>
                  </div>
                  {/* Fallback display if pre doesn't work */}
                  {generatedPRD && generatedPRD.length > 0 && (
                    <details className="mt-4">
                      <summary className="cursor-pointer text-sm text-muted-foreground">Raw PRD Text (Debug)</summary>
                      <div className="mt-2 p-2 bg-muted rounded text-xs font-mono overflow-x-auto">
                        {JSON.stringify(generatedPRD)}
                      </div>
                    </details>
                  )}
                </div>
                <div className="mt-4 flex gap-2">
                  <Button 
                    onClick={saveDraft}
                    disabled={savingDraft}
                  >
                    {savingDraft ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      'Save as Draft'
                    )}
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
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="manual" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Manual PRD Creation</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Create your PRD manually using our template editor.
              </p>
              <Button className="mt-4">Open Template Editor</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}