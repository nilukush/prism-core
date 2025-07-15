'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { 
  Brain, 
  Sparkles, 
  TrendingUp, 
  FileText, 
  Calendar,
  Zap,
  MessageSquare,
  HelpCircle
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { useToast } from '@/components/ui/use-toast'

interface QuickAction {
  id: string
  label: string
  description: string
  icon: React.ElementType
  color: string
  badge?: string
  route?: string
}

export function AIQuickActions() {
  const [loadingAction, setLoadingAction] = useState<string | null>(null)
  const router = useRouter()
  const { toast } = useToast()

  const handleAction = async (action: QuickAction) => {
    setLoadingAction(action.id)
    
    try {
      // Route to specific pages or modals based on action
      switch (action.id) {
        case 'generate-stories':
          router.push('/ai/story-generator')
          break
        case 'estimate-sprint':
          router.push('/sprints?action=estimate')
          break
        case 'generate-prd':
          router.push('/app/prds/new?ai=true')
          break
        case 'optimize-sprint':
          router.push('/sprints?action=optimize')
          break
        case 'analyze-velocity':
          router.push('/analytics/velocity')
          break
        case 'chat-assistant':
          router.push('/ai/assistant')
          break
        default:
          toast({
            title: 'Coming Soon',
            description: `${action.label} feature is being implemented.`,
          })
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to perform action. Please try again.',
        variant: 'destructive',
      })
    } finally {
      setLoadingAction(null)
    }
  }

  const quickActions: QuickAction[] = [
    {
      id: 'generate-stories',
      label: 'Generate Stories',
      description: 'Create user stories from requirements',
      icon: Sparkles,
      color: 'text-purple-500',
      badge: '5 pending',
      route: '/ai/story-generator'
    },
    {
      id: 'estimate-sprint',
      label: 'Estimate Sprint',
      description: 'AI-powered story point estimation',
      icon: TrendingUp,
      color: 'text-blue-500',
      badge: 'Sprint 24',
      route: '/sprints?action=estimate'
    },
    {
      id: 'generate-prd',
      label: 'Generate PRD',
      description: 'Create product requirements document',
      icon: FileText,
      color: 'text-green-500',
      route: '/app/prds/new?ai=true'
    },
    {
      id: 'optimize-sprint',
      label: 'Optimize Sprint',
      description: 'Balance workload and dependencies',
      icon: Calendar,
      color: 'text-orange-500',
      route: '/sprints?action=optimize'
    },
    {
      id: 'analyze-velocity',
      label: 'Analyze Velocity',
      description: 'Predict sprint completion',
      icon: Zap,
      color: 'text-yellow-500',
      route: '/analytics/velocity'
    },
    {
      id: 'chat-assistant',
      label: 'AI Assistant',
      description: 'Chat with AI for help',
      icon: MessageSquare,
      color: 'text-indigo-500',
      route: '/ai/assistant'
    }
  ]

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            <h3 className="font-semibold">AI Quick Actions</h3>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <HelpCircle className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p className="max-w-xs text-sm">
                  Use AI to automate common product management tasks and get intelligent recommendations
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {quickActions.map((action) => {
            const Icon = action.icon
            const isLoading = loadingAction === action.id
            
            return (
              <TooltipProvider key={action.id}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      className="relative h-auto flex-col gap-2 p-4 hover:shadow-md transition-all"
                      onClick={() => handleAction(action)}
                      disabled={isLoading}
                    >
                      <Icon className={cn('h-6 w-6', action.color, isLoading && 'animate-pulse')} />
                      <span className="text-xs font-medium">{action.label}</span>
                      {action.badge && (
                        <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground text-[10px] font-medium px-1.5 py-0.5 rounded-full">
                          {action.badge}
                        </span>
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-sm">{action.description}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}