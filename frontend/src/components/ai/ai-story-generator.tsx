'use client'

import { useState } from 'react'
import { 
  Sparkles, 
  FileText, 
  Loader2, 
  Check, 
  ChevronRight,
  Brain,
  Wand2,
  Info
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface GeneratedStory {
  id: string
  title: string
  userStory: string
  acceptanceCriteria: string[]
  storyPoints?: number
  priority?: 'high' | 'medium' | 'low'
  testCases?: string[]
}

export function AIStoryGenerator() {
  const [open, setOpen] = useState(false)
  const [requirements, setRequirements] = useState('')
  const [generating, setGenerating] = useState(false)
  const [generatedStories, setGeneratedStories] = useState<GeneratedStory[]>([])
  const [selectedStories, setSelectedStories] = useState<string[]>([])
  const [activeTab, setActiveTab] = useState('generate')
  const [progress, setProgress] = useState(0)
  
  // AI Configuration
  const [storyCount, setStoryCount] = useState(3)
  const [includeTestCases, setIncludeTestCases] = useState(true)
  const [storyFormat, setStoryFormat] = useState('standard')

  const handleGenerate = async () => {
    setGenerating(true)
    setProgress(0)
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return 90
        }
        return prev + 10
      })
    }, 200)

    // Simulate AI generation
    setTimeout(() => {
      const mockStories: GeneratedStory[] = [
        {
          id: '1',
          title: 'User Password Reset',
          userStory: 'As a registered user, I want to reset my password via email, so that I can regain access to my account if I forget my password.',
          acceptanceCriteria: [
            'Given I am on the login page, when I click "Forgot Password", then I should see the password reset form',
            'Given I enter a valid email address, when I submit the form, then I should receive a password reset email within 5 minutes',
            'Given I click the reset link in the email, when I enter a new password, then my password should be updated and I should be able to login'
          ],
          storyPoints: 5,
          priority: 'high',
          testCases: includeTestCases ? [
            'Test password reset with valid email address',
            'Test password reset with invalid email address',
            'Test password reset link expiration after 24 hours',
            'Test password complexity requirements'
          ] : undefined
        },
        {
          id: '2',
          title: 'Admin Password Reset Management',
          userStory: 'As a system administrator, I want to view and manage password reset requests, so that I can help users who have issues with the automated process.',
          acceptanceCriteria: [
            'Given I am an admin, when I access the admin panel, then I should see a "Password Reset Requests" section',
            'Given I view the requests list, when I filter by date, then I should see only requests within the selected range',
            'Given I select a request, when I click "Manually Reset", then the user should receive a new password reset email'
          ],
          storyPoints: 3,
          priority: 'medium',
          testCases: includeTestCases ? [
            'Test admin access permissions',
            'Test filtering and sorting of reset requests',
            'Test manual password reset functionality',
            'Test audit logging of admin actions'
          ] : undefined
        },
        {
          id: '3',
          title: 'Password Reset Analytics',
          userStory: 'As a product manager, I want to track password reset metrics, so that I can identify potential UX issues with our authentication flow.',
          acceptanceCriteria: [
            'Given I access the analytics dashboard, when I view authentication metrics, then I should see password reset statistics',
            'Given I view the metrics, when I select a time range, then I should see reset frequency, success rate, and average completion time',
            'Given I view failed resets, when I analyze the data, then I should see common failure reasons'
          ],
          storyPoints: 8,
          priority: 'low',
          testCases: includeTestCases ? [
            'Test data collection for reset events',
            'Test analytics dashboard accuracy',
            'Test time range filtering',
            'Test export functionality for reports'
          ] : undefined
        }
      ]
      
      clearInterval(progressInterval)
      setProgress(100)
      setGeneratedStories(mockStories.slice(0, storyCount))
      setGenerating(false)
      setActiveTab('review')
    }, 2000)
  }

  const handleSaveStories = () => {
    const storiesToSave = generatedStories.filter(story => 
      selectedStories.includes(story.id)
    )
    console.log('Saving stories:', storiesToSave)
    setOpen(false)
    // Reset state
    setRequirements('')
    setGeneratedStories([])
    setSelectedStories([])
    setActiveTab('generate')
  }

  const toggleStorySelection = (storyId: string) => {
    setSelectedStories(prev =>
      prev.includes(storyId)
        ? prev.filter(id => id !== storyId)
        : [...prev, storyId]
    )
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2">
          <Sparkles className="h-4 w-4" />
          Generate with AI
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            <DialogTitle>AI Story Generator</DialogTitle>
          </div>
          <DialogDescription>
            Transform your requirements into detailed user stories with AI assistance
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 overflow-hidden">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="generate" disabled={generating}>
              <Wand2 className="h-4 w-4 mr-2" />
              Generate
            </TabsTrigger>
            <TabsTrigger value="configure" disabled={generating}>
              <Info className="h-4 w-4 mr-2" />
              Configure
            </TabsTrigger>
            <TabsTrigger value="review" disabled={generatedStories.length === 0}>
              <FileText className="h-4 w-4 mr-2" />
              Review ({generatedStories.length})
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-y-auto py-4">
            <TabsContent value="generate" className="space-y-4 mt-0">
              <div className="space-y-2">
                <Label htmlFor="requirements">Describe your requirements</Label>
                <Textarea
                  id="requirements"
                  placeholder="Example: Users need to reset their password if they forget it. Admins should be able to help users who have issues. We also want to track metrics around password resets."
                  className="min-h-[150px]"
                  value={requirements}
                  onChange={(e) => setRequirements(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Tip: Be specific about user roles, actions, and expected outcomes
                </p>
              </div>

              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  AI will generate {storyCount} user stories based on your requirements. 
                  Each story will include acceptance criteria{includeTestCases ? ' and test cases' : ''}.
                </AlertDescription>
              </Alert>

              {generating && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Generating stories...</span>
                    <span>{progress}%</span>
                  </div>
                  <Progress value={progress} className="h-2" />
                </div>
              )}
            </TabsContent>

            <TabsContent value="configure" className="space-y-4 mt-0">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Generation Settings</CardTitle>
                  <CardDescription>Customize how AI generates your stories</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Number of stories to generate</Label>
                    <div className="flex items-center gap-4">
                      <Slider
                        value={[storyCount]}
                        onValueChange={([value]) => setStoryCount(value)}
                        min={1}
                        max={10}
                        step={1}
                        className="flex-1"
                      />
                      <span className="w-12 text-sm font-medium">{storyCount}</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Story format</Label>
                    <Select value={storyFormat} onValueChange={setStoryFormat}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="standard">Standard (As a... I want... So that...)</SelectItem>
                        <SelectItem value="job">Job Story (When... I want... So I can...)</SelectItem>
                        <SelectItem value="feature">Feature Story (Title + Description)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox 
                      id="test-cases" 
                      checked={includeTestCases}
                      onCheckedChange={(checked) => setIncludeTestCases(checked as boolean)}
                    />
                    <Label htmlFor="test-cases" className="text-sm font-normal">
                      Generate test cases for each story
                    </Label>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">AI Model Settings</CardTitle>
                  <CardDescription>Advanced configuration options</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>AI Model</Label>
                    <Select defaultValue="gpt-4">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gpt-4">GPT-4 (Most accurate)</SelectItem>
                        <SelectItem value="gpt-3.5">GPT-3.5 (Faster)</SelectItem>
                        <SelectItem value="claude">Claude 3 (Balanced)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Creativity level</Label>
                    <Select defaultValue="balanced">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="conservative">Conservative (Predictable)</SelectItem>
                        <SelectItem value="balanced">Balanced (Recommended)</SelectItem>
                        <SelectItem value="creative">Creative (More varied)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="review" className="space-y-4 mt-0">
              {generatedStories.map((story) => (
                <Card 
                  key={story.id} 
                  className={selectedStories.includes(story.id) ? 'ring-2 ring-primary' : ''}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Checkbox
                          checked={selectedStories.includes(story.id)}
                          onCheckedChange={() => toggleStorySelection(story.id)}
                        />
                        <CardTitle className="text-base">{story.title}</CardTitle>
                      </div>
                      <div className="flex gap-2">
                        {story.priority && (
                          <Badge variant={
                            story.priority === 'high' ? 'destructive' : 
                            story.priority === 'medium' ? 'secondary' : 'outline'
                          }>
                            {story.priority}
                          </Badge>
                        )}
                        {story.storyPoints && (
                          <Badge variant="outline">{story.storyPoints} pts</Badge>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <p className="text-sm font-medium mb-1">User Story</p>
                      <p className="text-sm text-muted-foreground">{story.userStory}</p>
                    </div>
                    
                    <div>
                      <p className="text-sm font-medium mb-2">Acceptance Criteria</p>
                      <ul className="space-y-1">
                        {story.acceptanceCriteria.map((criteria, index) => (
                          <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                            <Check className="h-3 w-3 text-green-500 mt-0.5 flex-shrink-0" />
                            <span>{criteria}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {story.testCases && (
                      <div>
                        <p className="text-sm font-medium mb-2">Test Cases</p>
                        <ul className="space-y-1">
                          {story.testCases.map((testCase, index) => (
                            <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                              <ChevronRight className="h-3 w-3 mt-0.5 flex-shrink-0" />
                              <span>{testCase}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
          </div>
        </Tabs>

        <DialogFooter className="flex-shrink-0">
          {activeTab === 'generate' && (
            <Button 
              onClick={handleGenerate} 
              disabled={!requirements.trim() || generating}
              className="w-full sm:w-auto"
            >
              {generating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Generate Stories
                </>
              )}
            </Button>
          )}
          {activeTab === 'review' && (
            <div className="flex gap-2 w-full sm:w-auto">
              <Button variant="outline" onClick={() => setActiveTab('generate')}>
                Back
              </Button>
              <Button 
                onClick={handleSaveStories}
                disabled={selectedStories.length === 0}
              >
                Save Selected ({selectedStories.length})
              </Button>
            </div>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}