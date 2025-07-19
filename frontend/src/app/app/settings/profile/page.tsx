'use client'

import { redirect } from 'next/navigation'
import { useEffect } from 'react'

export default function ProfileSettingsPage() {
  useEffect(() => {
    // Redirect to the main settings page with profile tab selected
    redirect('/app/settings?tab=profile')
  }, [])
  
  return null
}