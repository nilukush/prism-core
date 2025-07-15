'use client'

import { Activity, FolderKanban, Zap, TrendingUp } from 'lucide-react'
import { AIMetricsCard } from '@/components/ai/ai-metrics-card'

const stats = [
  {
    title: 'Active Projects',
    icon: FolderKanban,
    metrics: [
      {
        label: 'Current Projects',
        value: '12',
        trend: { value: 20, direction: 'up' as const },
        aiInsight: 'Project count increased due to Q4 initiatives'
      },
      {
        label: 'Predicted Next Month',
        value: '14',
        predicted: true,
        confidence: 85
      }
    ]
  },
  {
    title: 'Current Sprint',
    icon: Zap,
    metrics: [
      {
        label: 'Sprint Progress',
        value: 'Sprint 24',
        aiInsight: 'On track to complete 95% of stories'
      },
      {
        label: 'Completion Forecast',
        value: '5 days',
        predicted: true,
        confidence: 92
      }
    ]
  },
  {
    title: 'Sprint Velocity',
    icon: Activity,
    metrics: [
      {
        label: 'Current Velocity',
        value: '47 pts',
        trend: { value: 11, direction: 'up' as const },
        aiInsight: 'Team performing above average'
      },
      {
        label: 'Next Sprint Prediction',
        value: '52 pts',
        predicted: true,
        confidence: 88
      }
    ]
  },
  {
    title: 'Story Completion',
    icon: TrendingUp,
    metrics: [
      {
        label: 'Completion Rate',
        value: '92%',
        trend: { value: 8, direction: 'up' as const },
        aiInsight: 'Best performance in 6 months'
      },
      {
        label: 'End of Sprint Forecast',
        value: '95%',
        predicted: true,
        confidence: 90
      }
    ]
  },
]

export function StatsCards() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <AIMetricsCard
          key={stat.title}
          title={stat.title}
          icon={stat.icon}
          metrics={stat.metrics}
        />
      ))}
    </div>
  )
}