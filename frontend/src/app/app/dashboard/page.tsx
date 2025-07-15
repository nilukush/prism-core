'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Overview } from '@/components/dashboard/overview'
import { RecentActivity } from '@/components/dashboard/recent-activity'
import { StatsCards } from '@/components/dashboard/stats-cards'
import { AIQuickActions } from '@/components/ai/ai-quick-actions'
import { AIInsightsPanel } from '@/components/ai/ai-insights-panel'
import { AIStoryGenerator } from '@/components/ai/ai-story-generator'

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here's an overview of your projects and product management activity.
          </p>
        </div>
        <AIStoryGenerator />
      </div>

      <AIQuickActions />

      <StatsCards />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Overview</CardTitle>
            <CardDescription>
              Sprint progress and team velocity over the last 7 days
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <Overview />
          </CardContent>
        </Card>
        <div className="col-span-3 space-y-4">
          <AIInsightsPanel />
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>
                Latest story updates and team activities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RecentActivity />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}