'use client'

import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { signIn, useSession } from 'next-auth/react'
import { useState, useEffect, Suspense } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import { z } from 'zod'
import { Github, Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

type LoginFormData = z.infer<typeof loginSchema>

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { data: session, status } = useSession()
  const callbackUrl = searchParams.get('callbackUrl') || '/app/dashboard'
  const [isLoading, setIsLoading] = useState(false)
  const [isGoogleLoading, setIsGoogleLoading] = useState(false)
  const [isGithubLoading, setIsGithubLoading] = useState(false)
  const [debugInfo, setDebugInfo] = useState<any>(null)
  
  // Redirect if already authenticated
  useEffect(() => {
    if (status === 'authenticated' && session) {
      router.push(callbackUrl)
    }
  }, [status, session, router, callbackUrl])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true)
    setDebugInfo(null)
    
    try {
      console.log('[Login] Starting login process...')
      
      // First, test direct API login to verify credentials
      console.log('[Login] Testing direct API login...')
      const formData = new URLSearchParams()
      formData.append('username', data.email)
      formData.append('password', data.password)
      formData.append('grant_type', 'password')
      
      try {
        const directResponse = await fetch('http://localhost:8100/api/v1/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: formData.toString(),
        })
        
        const directResult = await directResponse.json()
        console.log('[Login] Direct API response:', {
          status: directResponse.status,
          ok: directResponse.ok,
          hasToken: !!directResult.access_token
        })
        
        if (!directResponse.ok) {
          console.error('[Login] Direct API login failed:', directResult)
          setDebugInfo({
            step: 'Direct API Login',
            error: directResult,
            status: directResponse.status
          })
          toast.error(directResult.detail || 'Invalid credentials')
          setIsLoading(false)
          return
        }
      } catch (error) {
        console.error('[Login] Direct API error:', error)
        setDebugInfo({
          step: 'Direct API Login',
          error: error instanceof Error ? error.message : 'Network error',
          hint: 'Check if backend is running on http://localhost:8100'
        })
      }
      
      // Now try NextAuth signIn
      console.log('[Login] Attempting NextAuth signIn...')
      const result = await signIn('credentials', {
        email: data.email,
        password: data.password,
        redirect: false,
      })

      console.log('[Login] NextAuth signIn result:', result)
      setDebugInfo({
        step: 'NextAuth SignIn',
        result: result,
        sessionStatus: status
      })
      
      if (result?.error) {
        console.error('[Login] NextAuth signIn error:', result.error)
        toast.error('Login failed. Check console for debug info.')
      } else if (result?.ok) {
        console.log('[Login] SignIn successful, fetching session...')
        toast.success('Login successful')
        
        // Force session refresh
        const sessionResponse = await fetch('/api/auth/session')
        const sessionData = await sessionResponse.json()
        console.log('[Login] Session data after login:', sessionData)
        
        setDebugInfo({
          step: 'Session Check',
          session: sessionData,
          hasToken: !!sessionData?.accessToken
        })
        
        // Redirect after a delay
        setTimeout(() => {
          router.push(callbackUrl)
        }, 1000)
      }
    } catch (error) {
      console.error('[Login] Unexpected error:', error)
      setDebugInfo({
        step: 'Unexpected Error',
        error: error instanceof Error ? error.message : 'Unknown error'
      })
      toast.error('An unexpected error occurred. Check console.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSocialLogin = async (provider: string) => {
    if (provider === 'google') setIsGoogleLoading(true)
    if (provider === 'github') setIsGithubLoading(true)
    
    try {
      await signIn(provider, { callbackUrl })
    } catch (error) {
      toast.error(`Failed to login with ${provider}`)
      if (provider === 'google') setIsGoogleLoading(false)
      if (provider === 'github') setIsGithubLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold">Welcome back</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Sign in to your account to continue
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-6">
          <div className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                {...register('email')}
                disabled={isLoading}
              />
              {errors.email && (
                <p className="mt-1 text-sm text-destructive">{errors.email.message}</p>
              )}
            </div>

            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                {...register('password')}
                disabled={isLoading}
              />
              {errors.password && (
                <p className="mt-1 text-sm text-destructive">{errors.password.message}</p>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="text-sm">
              <Link
                href="/auth/forgot-password"
                className="font-medium text-primary hover:underline"
              >
                Forgot password?
              </Link>
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Sign in
          </Button>
        </form>

        {/* Debug Information */}
        {debugInfo && (
          <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <h3 className="font-semibold text-sm mb-2">Debug Information:</h3>
            <pre className="text-xs overflow-auto">
              {JSON.stringify(debugInfo, null, 2)}
            </pre>
          </div>
        )}

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <Separator />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Button
            variant="outline"
            onClick={() => handleSocialLogin('google')}
            disabled={isGoogleLoading}
          >
            {isGoogleLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <svg className="h-4 w-4" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
            )}
            <span className="ml-2">Google</span>
          </Button>
          <Button
            variant="outline"
            onClick={() => handleSocialLogin('github')}
            disabled={isGithubLoading}
          >
            {isGithubLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Github className="h-4 w-4" />
            )}
            <span className="ml-2">GitHub</span>
          </Button>
        </div>

        <p className="text-center text-sm text-muted-foreground">
          Don&apos;t have an account?{' '}
          <Link href="/auth/register" className="font-medium text-primary hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    }>
      <LoginForm />
    </Suspense>
  )
}