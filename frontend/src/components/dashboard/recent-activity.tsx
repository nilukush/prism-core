'use client'

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { formatRelativeTime } from '@/lib/utils'

const activities = [
  {
    id: 1,
    user: {
      name: 'Sarah Chen',
      avatar: '/avatars/user-1.svg',
    },
    action: 'Created user story "Implement OAuth login"',
    type: 'story_created',
    project: 'Auth System',
    timestamp: new Date(Date.now() - 1000 * 60 * 5), // 5 minutes ago
  },
  {
    id: 2,
    user: {
      name: 'Mike Johnson',
      avatar: '/avatars/user-2.svg',
    },
    action: 'Updated PRD for Payment Integration',
    type: 'prd_updated',
    project: 'Payments',
    timestamp: new Date(Date.now() - 1000 * 60 * 15), // 15 minutes ago
  },
  {
    id: 3,
    user: {
      name: 'Emily Davis',
      avatar: '/avatars/user-3.svg',
    },
    action: 'Moved 3 stories to "In Progress"',
    type: 'sprint_update',
    project: 'Mobile App',
    timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
  },
  {
    id: 4,
    user: {
      name: 'Alex Kim',
      avatar: '/avatars/user-4.svg',
    },
    action: 'Completed Sprint 23 retrospective',
    type: 'sprint_complete',
    project: 'Dashboard',
    timestamp: new Date(Date.now() - 1000 * 60 * 60), // 1 hour ago
  },
  {
    id: 5,
    user: {
      name: 'James Wilson',
      avatar: '/avatars/user-5.svg',
    },
    action: 'Created new Epic "Q1 Feature Release"',
    type: 'epic_created',
    project: 'Platform',
    timestamp: new Date(Date.now() - 1000 * 60 * 120), // 2 hours ago
  },
]

const typeColors = {
  story_created: 'default',
  prd_updated: 'secondary',
  sprint_update: 'info',
  sprint_complete: 'success',
  epic_created: 'outline',
} as const

export function RecentActivity() {
  return (
    <div className="space-y-4">
      {activities.map((activity) => (
        <div key={activity.id} className="flex items-center">
          <Avatar className="h-9 w-9">
            <AvatarImage src={activity.user.avatar} alt={activity.user.name} />
            <AvatarFallback>
              {activity.user.name.split(' ').map(n => n[0]).join('').toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="ml-4 space-y-1 flex-1">
            <p className="text-sm font-medium leading-none">
              {activity.user.name}
            </p>
            <p className="text-sm text-muted-foreground">
              {activity.action}
            </p>
          </div>
          <div className="ml-auto flex flex-col items-end gap-1">
            <Badge variant={typeColors[activity.type]}>
              {activity.project}
            </Badge>
            <p className="text-xs text-muted-foreground">
              {formatRelativeTime(activity.timestamp)}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}