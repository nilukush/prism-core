'use client'

import { useState, useEffect } from 'react'
import { Brain, TrendingUp, AlertTriangle, Lightbulb, Sparkles, ChevronRight } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

interface AIInsight {
  id: string
  type: 'recommendation' | 'warning' | 'opportunity' | 'trend'
  title: string
  description: string
  impact: 'high' | 'medium' | 'low'
  actionable: boolean
  action?: {
    label: string
    onClick: () => void
  }
  metadata?: {
    confidence: number
    dataPoints: number
  }
}

const mockInsights: AIInsight[] = [
  {
    id: '1',
    type: 'recommendation',
    title: 'Optimize Sprint Capacity',
    description: 'Based on your team\'s velocity trend, you can add 2 more story points to Sprint 24 without risk.',
    impact: 'high',
    actionable: true,
    action: {
      label: 'View Sprint',
      onClick: () => console.log('View sprint')
    },
    metadata: {
      confidence: 92,
      dataPoints: 12
    }
  },
  {
    id: '2',
    type: 'warning',
    title: 'Story Dependencies Detected',
    description: 'AUTH-123 and AUTH-124 have unresolved dependencies that may block sprint completion.',
    impact: 'high',
    actionable: true,
    action: {
      label: 'Resolve Dependencies',
      onClick: () => console.log('Resolve dependencies')
    },
    metadata: {
      confidence: 88,
      dataPoints: 5
    }
  },
  {
    id: '3',
    type: 'opportunity',
    title: 'AI Story Generation Available',
    description: 'Convert 5 pending requirements into detailed user stories with AI assistance.',
    impact: 'medium',
    actionable: true,
    action: {
      label: 'Generate Stories',
      onClick: () => console.log('Generate stories')
    },
    metadata: {
      confidence: 95,
      dataPoints: 8
    }
  },
  {
    id: '4',
    type: 'trend',
    title: 'Velocity Improving',
    description: 'Team velocity has increased by 15% over the last 3 sprints. Current trend suggests 52 points next sprint.',
    impact: 'medium',
    actionable: false,
    metadata: {
      confidence: 85,
      dataPoints: 15
    }
  }
]

const insightIcons = {
  recommendation: Lightbulb,
  warning: AlertTriangle,
  opportunity: Sparkles,
  trend: TrendingUp
}

const insightColors = {
  recommendation: 'text-blue-500',
  warning: 'text-amber-500',
  opportunity: 'text-purple-500',
  trend: 'text-green-500'
}

const impactBadgeVariants = {
  high: 'destructive',
  medium: 'secondary',
  low: 'outline'
} as const

export function AIInsightsPanel() {
  const [insights, setInsights] = useState<AIInsight[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedFilter, setSelectedFilter] = useState<'all' | AIInsight['type']>('all')

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setInsights(mockInsights)
      setLoading(false)
    }, 1500)
  }, [])

  const filteredInsights = selectedFilter === 'all' 
    ? insights 
    : insights.filter(insight => insight.type === selectedFilter)

  const filterButtons = [
    { value: 'all', label: 'All' },
    { value: 'recommendation', label: 'Recommendations' },
    { value: 'warning', label: 'Warnings' },
    { value: 'opportunity', label: 'Opportunities' },
    { value: 'trend', label: 'Trends' }
  ] as const

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            <CardTitle>AI Insights</CardTitle>
          </div>
          <Badge variant="secondary" className="text-xs">
            {insights.length} insights
          </Badge>
        </div>
        <CardDescription>
          Real-time AI-powered recommendations and insights
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Filter buttons */}
        <div className="flex flex-wrap gap-2">
          {filterButtons.map((filter) => (
            <Button
              key={filter.value}
              variant={selectedFilter === filter.value ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedFilter(filter.value)}
              className="text-xs"
            >
              {filter.label}
            </Button>
          ))}
        </div>

        {/* Insights list */}
        <div className="space-y-3">
          {loading ? (
            <>
              {[...Array(3)].map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-5/6" />
                </div>
              ))}
            </>
          ) : filteredInsights.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No {selectedFilter === 'all' ? '' : selectedFilter} insights available
            </p>
          ) : (
            filteredInsights.map((insight) => {
              const Icon = insightIcons[insight.type]
              return (
                <div
                  key={insight.id}
                  className="p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <Icon className={cn('h-5 w-5 mt-0.5', insightColors[insight.type])} />
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-medium">{insight.title}</h4>
                        <Badge variant={impactBadgeVariants[insight.impact]} className="text-xs">
                          {insight.impact} impact
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {insight.description}
                      </p>
                      {insight.metadata && (
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span>{insight.metadata.confidence}% confidence</span>
                          <span>{insight.metadata.dataPoints} data points</span>
                        </div>
                      )}
                      {insight.actionable && insight.action && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2 text-xs"
                          onClick={insight.action.onClick}
                        >
                          {insight.action.label}
                          <ChevronRight className="ml-1 h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>

        {/* View all insights link */}
        <div className="pt-2">
          <Button variant="link" className="w-full text-xs" onClick={() => console.log('View all insights')}>
            View All AI Insights
            <ChevronRight className="ml-1 h-3 w-3" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}