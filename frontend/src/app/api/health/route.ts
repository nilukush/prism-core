import { NextRequest, NextResponse } from 'next/server'

export async function GET(_request: NextRequest) {
  const healthCheck = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'prism-frontend',
    version: process.env['npm_package_version'] || '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    uptime: process.uptime(),
    checks: {
      server: 'ok',
      environment: process.env.NODE_ENV === 'production' ? 'ok' : 'development',
    } as Record<string, string>,
  }

  // You can add more health checks here, such as:
  // - Database connectivity
  // - External API availability
  // - Memory usage
  // - etc.

  try {
    // Example: Check if API is reachable (optional)
    if (process.env['NEXT_PUBLIC_API_URL']) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5000)
        
        const response = await fetch(`${process.env['NEXT_PUBLIC_API_URL']}/health`, {
          signal: controller.signal,
        })
        
        clearTimeout(timeoutId)
        healthCheck.checks = {
          ...healthCheck.checks,
          api: response.ok ? 'ok' : 'degraded',
        }
      } catch (error) {
        healthCheck.checks = {
          ...healthCheck.checks,
          api: 'unavailable',
        }
      }
    }

    return NextResponse.json(healthCheck, { status: 200 })
  } catch (error) {
    return NextResponse.json(
      {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        service: 'prism-frontend',
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 503 }
    )
  }
}