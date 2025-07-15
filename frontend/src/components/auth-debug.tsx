'use client'

import { useSession } from 'next-auth/react'
import { useEffect, useState } from 'react'

export function AuthDebug() {
  const { data: session, status } = useSession()
  const [debugInfo, setDebugInfo] = useState<any>({})

  useEffect(() => {
    // Fetch session directly to debug
    const fetchSession = async () => {
      try {
        const response = await fetch('/api/auth/session', {
          credentials: 'include',
        })
        
        const responseText = await response.text()
        let data
        try {
          data = JSON.parse(responseText)
        } catch {
          data = responseText
        }

        setDebugInfo({
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries()),
          data,
          cookies: document.cookie,
        })
      } catch (error) {
        setDebugInfo({
          error: error instanceof Error ? error.message : 'Unknown error',
          stack: error instanceof Error ? error.stack : undefined,
        })
      }
    }

    fetchSession()
  }, [])

  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  return (
    <div className="fixed bottom-4 right-4 p-4 bg-black/80 text-white text-xs max-w-md rounded-lg z-50">
      <h3 className="font-bold mb-2">Auth Debug</h3>
      <div className="space-y-1">
        <div>Status: {status}</div>
        <div>Session: {session ? 'Present' : 'None'}</div>
        {session?.error && <div className="text-red-400">Error: {session.error}</div>}
        <details className="mt-2">
          <summary className="cursor-pointer">Direct Fetch Debug</summary>
          <pre className="mt-2 text-[10px] overflow-auto max-h-60">
            {JSON.stringify(debugInfo, null, 2)}
          </pre>
        </details>
        <details className="mt-2">
          <summary className="cursor-pointer">Session Data</summary>
          <pre className="mt-2 text-[10px] overflow-auto max-h-60">
            {JSON.stringify(session, null, 2)}
          </pre>
        </details>
      </div>
    </div>
  )
}