'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FileText, Sparkles, Calendar, Users, BarChart3 } from 'lucide-react'
import Link from 'next/link'

export default function DemoPage() {
  return (
    <div className="container mx-auto py-8 space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">PRISM Demo</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Experience how PRISM transforms product management with AI-powered features
        </p>
      </div>

      <Tabs defaultValue="stories" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="stories">AI Story Generation</TabsTrigger>
          <TabsTrigger value="planning">Sprint Planning</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="stories" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                AI-Powered User Story Generation
              </CardTitle>
              <CardDescription>
                Transform simple ideas into detailed user stories with acceptance criteria
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-muted p-4 rounded-lg">
                <p className="text-sm font-medium mb-2">Input:</p>
                <p className="text-sm">"Users should be able to filter products by category"</p>
              </div>
              
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium">AI generates:</span>
              </div>

              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">Filter Products by Category</CardTitle>
                    <Badge>5 Story Points</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-sm mb-2">User Story:</h4>
                    <p className="text-sm">As a customer, I want to filter products by category so that I can quickly find items I'm interested in without browsing through irrelevant products.</p>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-sm mb-2">Acceptance Criteria:</h4>
                    <ul className="text-sm space-y-1 list-disc list-inside">
                      <li>Category filter dropdown appears on product listing page</li>
                      <li>Users can select one or multiple categories</li>
                      <li>Product list updates in real-time when filters are applied</li>
                      <li>Active filters are clearly displayed with option to remove</li>
                      <li>Filter state persists when navigating between pages</li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-semibold text-sm mb-2">Test Cases:</h4>
                    <ul className="text-sm space-y-1 list-disc list-inside">
                      <li>Verify category dropdown displays all available categories</li>
                      <li>Test single and multi-category selection</li>
                      <li>Confirm product count updates when filters are applied</li>
                      <li>Test filter removal functionality</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="planning" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Intelligent Sprint Planning
              </CardTitle>
              <CardDescription>
                AI helps optimize sprint capacity and predict velocity
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">Sprint 24</CardTitle>
                    <CardDescription>Jan 8 - Jan 22, 2024</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Team Capacity</span>
                      <span className="font-medium">42 points</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Committed</span>
                      <span className="font-medium">38 points</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">AI Predicted Velocity</span>
                      <span className="font-medium text-green-600">40 points</span>
                    </div>
                    <div className="pt-2">
                      <Badge variant="outline" className="text-xs">
                        <Users className="h-3 w-3 mr-1" />
                        5 team members
                      </Badge>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">AI Recommendations</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="text-sm space-y-2">
                      <div className="flex items-start gap-2">
                        <div className="h-2 w-2 rounded-full bg-green-500 mt-1.5" />
                        <p>Sprint is well-balanced with 90% capacity utilization</p>
                      </div>
                      <div className="flex items-start gap-2">
                        <div className="h-2 w-2 rounded-full bg-yellow-500 mt-1.5" />
                        <p>Consider moving 1 low-priority story to next sprint</p>
                      </div>
                      <div className="flex items-start gap-2">
                        <div className="h-2 w-2 rounded-full bg-blue-500 mt-1.5" />
                        <p>Team velocity trending upward by 15%</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Predictive Analytics & Insights
              </CardTitle>
              <CardDescription>
                AI-powered insights to keep your projects on track
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">Project Health</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600">On Track</div>
                    <p className="text-xs text-muted-foreground mt-1">
                      92% probability of on-time delivery
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">Burndown Trend</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">Healthy</div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Projected to complete 2 days early
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">Risk Detection</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-yellow-600">1 Risk</div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Backend API dependency may cause delay
                    </p>
                  </CardContent>
                </Card>
              </div>

              <Card className="mt-4">
                <CardHeader>
                  <CardTitle className="text-base">AI Insights</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-start gap-3">
                    <Sparkles className="h-4 w-4 text-primary mt-0.5" />
                    <div className="text-sm">
                      <p className="font-medium">Velocity Improvement Opportunity</p>
                      <p className="text-muted-foreground">Based on historical data, reducing meeting time by 20% could increase team velocity by 3-5 story points per sprint.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Sparkles className="h-4 w-4 text-primary mt-0.5" />
                    <div className="text-sm">
                      <p className="font-medium">Bottleneck Detected</p>
                      <p className="text-muted-foreground">Code review process is taking 40% longer than average. Consider adding a second reviewer or implementing automated checks.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Card className="bg-primary text-primary-foreground">
        <CardContent className="pt-6">
          <div className="text-center space-y-4">
            <h3 className="text-2xl font-bold">Ready to Transform Your Product Management?</h3>
            <p className="text-primary-foreground/90 max-w-2xl mx-auto">
              This is just a glimpse of what PRISM can do. Start your free trial to experience the full power of AI-driven product management.
            </p>
            <div className="flex gap-4 justify-center pt-2">
              <Button size="lg" variant="secondary" asChild>
                <Link href="/auth/register">Start Free Trial</Link>
              </Button>
              <Button size="lg" variant="outline" className="bg-transparent border-primary-foreground/20 text-primary-foreground hover:bg-primary-foreground/10" asChild>
                <Link href="/contact">Contact Sales</Link>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}