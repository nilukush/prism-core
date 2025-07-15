import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'

import { authOptions } from '@/lib/auth'
import { AppShell } from '@/components/app-shell'
import { ProjectProvider } from '@/contexts/ProjectContext'

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await getServerSession(authOptions)

  if (!session) {
    redirect('/auth/login')
  }

  return (
    <ProjectProvider>
      <AppShell>{children}</AppShell>
    </ProjectProvider>
  )
}