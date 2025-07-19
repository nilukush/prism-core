'use client'

import { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import Link from 'next/link'

interface EmptyStateAction {
  label: string
  href?: string
  onClick?: () => void
  variant?: 'default' | 'outline' | 'secondary'
}

interface EmptyStateProps {
  icon: ReactNode
  title: string
  description: string
  actions?: EmptyStateAction[]
}

export function EmptyState({ icon, title, description, actions }: EmptyStateProps) {
  return (
    <Card className="p-12 text-center max-w-md mx-auto">
      <div className="flex justify-center mb-4">
        <div className="h-16 w-16 text-muted-foreground">
          {icon}
        </div>
      </div>
      <h2 className="text-2xl font-semibold mb-2">{title}</h2>
      <p className="text-muted-foreground mb-6">{description}</p>
      {actions && actions.length > 0 && (
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {actions.map((action, index) => (
            action.href ? (
              <Button
                key={index}
                variant={action.variant || (index === 0 ? 'default' : 'outline')}
                asChild
              >
                <Link href={action.href}>{action.label}</Link>
              </Button>
            ) : (
              <Button
                key={index}
                variant={action.variant || (index === 0 ? 'default' : 'outline')}
                onClick={action.onClick}
              >
                {action.label}
              </Button>
            )
          ))}
        </div>
      )}
    </Card>
  )
}