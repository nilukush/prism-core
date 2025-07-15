'use client'

import { Brain, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

interface AIMetric {
  label: string
  value: string | number
  trend?: {
    value: number
    direction: 'up' | 'down' | 'neutral'
  }
  aiInsight?: string
  confidence?: number
  predicted?: boolean
}

interface AIMetricsCardProps {
  title: string
  icon: React.ElementType
  metrics: AIMetric[]
  className?: string
}

export function AIMetricsCard({ title, icon: Icon, metrics, className }: AIMetricsCardProps) {
  const getTrendIcon = (direction: 'up' | 'down' | 'neutral') => {
    switch (direction) {
      case 'up':
        return <TrendingUp className="h-3 w-3" />
      case 'down':
        return <TrendingDown className="h-3 w-3" />
      default:
        return <Minus className="h-3 w-3" />
    }
  }

  const getTrendColor = (direction: 'up' | 'down' | 'neutral') => {
    switch (direction) {
      case 'up':
        return 'text-green-500'
      case 'down':
        return 'text-red-500'
      default:
        return 'text-gray-500'
    }
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-muted-foreground" />
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
        </div>
        <Badge variant="secondary" className="text-xs">
          <Brain className="h-3 w-3 mr-1" />
          AI Enhanced
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        {metrics.map((metric, index) => (
          <div key={index} className="space-y-1">
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">{metric.label}</p>
              {metric.predicted && (
                <Badge variant="outline" className="text-xs">
                  Predicted
                </Badge>
              )}
            </div>
            <div className="flex items-baseline gap-2">
              <div className="text-2xl font-bold">{metric.value}</div>
              {metric.trend && (
                <div className={cn('flex items-center gap-1 text-xs', getTrendColor(metric.trend.direction))}>
                  {getTrendIcon(metric.trend.direction)}
                  <span>{Math.abs(metric.trend.value)}%</span>
                </div>
              )}
            </div>
            {metric.aiInsight && (
              <p className="text-xs text-muted-foreground italic">
                💡 {metric.aiInsight}
              </p>
            )}
            {metric.confidence !== undefined && (
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">AI Confidence</span>
                  <span>{metric.confidence}%</span>
                </div>
                <Progress value={metric.confidence} className="h-1" />
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  )
}