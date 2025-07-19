'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api-client'
import { useToast } from '@/components/ui/use-toast'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle, Trash2, RefreshCw } from 'lucide-react'

// Only show debug features in development
const isDevelopment = process.env.NODE_ENV === 'development'

export function FixOrgModal() {
  const { toast } = useToast()

  const handleRefresh = () => {
    toast({
      title: 'Refreshing...',
      description: 'Reloading page to check for organizations',
    })
    // Hard refresh to ensure we get fresh data
    window.location.reload()
  }

  const handleDeleteExistingOrg = async () => {
    try {
      // First, get the organizations
      const response = await api.organizations.list()
      
      if (response.organizations && response.organizations.length > 0) {
        const org = response.organizations[0]
        
        toast({
          title: 'Deleting organization...',
          description: `Attempting to delete "${org.name}"`,
        })

        // Use the API client for proper authentication
        await api.organizations.delete(org.id)
        
        toast({
          title: 'Success!',
          description: 'Organization deleted. Refreshing page...',
        })
        
        // Clear any cached data
        localStorage.removeItem('selectedProjectId')
        sessionStorage.clear()
        
        // Reload the page
        setTimeout(() => {
          window.location.reload()
        }, 1000)
      } else {
        toast({
          title: 'No organizations found',
          description: 'The modal should already be showing.',
        })
      }
    } catch (error) {
      console.error('Delete error:', error)
      toast({
        title: 'Error',
        description: 'Failed to delete organization. See console for details.',
        variant: 'destructive'
      })
    }
  }

  useEffect(() => {
    // Log the current state for debugging (only in development)
    if (isDevelopment) {
      api.organizations.list().then(response => {
        console.log('Current organizations:', response)
        if (response.organizations && response.organizations.length > 0) {
          console.log('Organization exists - this is why modal is not showing')
          console.log('Organization details:', response.organizations[0])
        }
      }).catch(console.error)
    }
  }, [])

  return (
    <Card className="mt-6 border-orange-200 bg-orange-50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-orange-800">
          <AlertCircle className="h-5 w-5" />
          Organization Already Exists
        </CardTitle>
        <CardDescription className="text-orange-700">
          An organization already exists, preventing the creation modal from appearing.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <p className="text-sm text-orange-700">
            To fix this issue, you have two options:
          </p>
          
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-orange-800">Organization Already Exists</h4>
              <p className="text-sm text-orange-700 mb-2">
                {isDevelopment ? (
                  <>Click the button below to delete the existing organization:</>
                ) : (
                  <>Please contact your administrator to resolve this issue.</>
                )}
              </p>
              {isDevelopment && (
                <Button 
                  onClick={handleDeleteExistingOrg}
                  variant="destructive"
                  className="w-full"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete Existing Organization
                </Button>
              )}
            </div>

            <div className="border-t pt-4">
              <h4 className="font-semibold text-orange-800">Try Refreshing</h4>
              <p className="text-sm text-orange-700 mb-2">
                If this issue persists, try refreshing the page:
              </p>
              <Button 
                onClick={handleRefresh}
                variant="outline"
                className="w-full mb-4"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh Page
              </Button>
            </div>

            {isDevelopment && (
              <div className="border-t pt-4">
                <h4 className="font-semibold text-orange-800">Option 3: Delete via Database (Dev Only)</h4>
                <p className="text-sm text-orange-700 mb-2">
                  If the API delete doesn't work (backend not deployed), run this in Neon SQL Editor:
                </p>
                <pre className="bg-gray-900 text-gray-100 p-3 rounded text-xs overflow-x-auto">
{`-- Delete all organization data
DELETE FROM documents WHERE project_id IN 
  (SELECT id FROM projects WHERE organization_id = 1);
DELETE FROM project_members WHERE project_id IN 
  (SELECT id FROM projects WHERE organization_id = 1);
DELETE FROM projects WHERE organization_id = 1;
DELETE FROM organization_members WHERE organization_id = 1;
DELETE FROM organizations WHERE id = 1;`}
                </pre>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}