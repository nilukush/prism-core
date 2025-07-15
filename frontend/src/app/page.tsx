import Link from 'next/link'
import { ArrowRight, BarChart3, Brain, Calendar, GitBranch, LineChart, Users, Zap, FileText } from 'lucide-react'

import { Button } from '@/components/ui/button'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-background">
        <div className="absolute inset-0 grid-pattern opacity-5" />
        <div className="container relative z-10 flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center py-20 text-center">
          <div className="mx-auto max-w-3xl space-y-6">
            <div className="inline-flex items-center rounded-full bg-muted px-4 py-1.5 text-sm font-medium">
              <Brain className="mr-2 h-4 w-4 text-primary" />
              AI-Powered Product Management Platform
            </div>
            <h1 className="text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
              Transform Your
              <span className="gradient-text"> Product Management</span>
            </h1>
            <p className="mx-auto max-w-2xl text-lg text-muted-foreground sm:text-xl">
              PRISM leverages AI to streamline product development, from ideation to delivery. 
              Generate user stories, manage sprints, and gain insights with intelligent automation.
            </p>
            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Button size="lg" asChild>
                <Link href="/auth/register">
                  Get Started Free
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link href="/app/demo">
                  View Demo
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container py-20">
        <div className="mx-auto max-w-5xl">
          <div className="text-center">
            <h2 className="text-3xl font-bold sm:text-4xl">Intelligent Product Management</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Accelerate your product development with AI-powered features designed for modern teams
            </p>
          </div>
          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={<FileText className="h-10 w-10" />}
              title="AI Story Generation"
              description="Generate detailed user stories, acceptance criteria, and test cases from simple descriptions using advanced AI."
            />
            <FeatureCard
              icon={<Calendar className="h-10 w-10" />}
              title="Sprint Planning"
              description="Intelligent sprint planning with AI-powered velocity predictions and workload balancing."
            />
            <FeatureCard
              icon={<LineChart className="h-10 w-10" />}
              title="Analytics & Insights"
              description="Real-time analytics and predictive insights to keep your projects on track and teams productive."
            />
            <FeatureCard
              icon={<GitBranch className="h-10 w-10" />}
              title="Workflow Automation"
              description="Automate repetitive tasks with customizable workflows and intelligent process optimization."
            />
            <FeatureCard
              icon={<Users className="h-10 w-10" />}
              title="Team Collaboration"
              description="Built-in collaboration tools with real-time updates, comments, and seamless integrations."
            />
            <FeatureCard
              icon={<BarChart3 className="h-10 w-10" />}
              title="Roadmap Planning"
              description="Visual roadmaps with AI-assisted prioritization and dependency management."
            />
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="border-t bg-muted/50 py-20">
        <div className="container">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-3xl font-bold sm:text-4xl">How PRISM Works</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Three simple steps to revolutionize your product management workflow
            </p>
          </div>
          <div className="mt-12 grid gap-8 lg:grid-cols-3">
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary text-2xl font-bold text-primary-foreground">
                1
              </div>
              <h3 className="mt-4 text-xl font-semibold">Create Your Workspace</h3>
              <p className="mt-2 text-muted-foreground">
                Set up your team, projects, and integrate with your existing tools in minutes.
              </p>
            </div>
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary text-2xl font-bold text-primary-foreground">
                2
              </div>
              <h3 className="mt-4 text-xl font-semibold">Leverage AI Assistance</h3>
              <p className="mt-2 text-muted-foreground">
                Use AI to generate stories, plan sprints, and get intelligent recommendations.
              </p>
            </div>
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary text-2xl font-bold text-primary-foreground">
                3
              </div>
              <h3 className="mt-4 text-xl font-semibold">Track & Optimize</h3>
              <p className="mt-2 text-muted-foreground">
                Monitor progress with real-time analytics and continuously improve your process.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="border-t">
        <div className="container py-20">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-3xl font-bold sm:text-4xl">
              Ready to Transform Your Product Management?
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Join forward-thinking teams using PRISM to build better products faster
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Button size="lg" asChild>
                <Link href="/auth/register">
                  Start Free Trial
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link href="/contact">
                  Contact Sales
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div className="group relative overflow-hidden rounded-lg border bg-card p-6 transition-all hover:shadow-lg">
      <div className="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-primary/10 transition-transform group-hover:scale-150" />
      <div className="relative space-y-3">
        <div className="text-primary">{icon}</div>
        <h3 className="text-xl font-semibold">{title}</h3>
        <p className="text-muted-foreground">{description}</p>
      </div>
    </div>
  )
}