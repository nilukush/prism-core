// User types
export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  role: UserRole
  organizations: Organization[]
  createdAt: string
  updatedAt: string
}

export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  VIEWER = 'viewer',
}

// Organization types
export interface Organization {
  id: string
  name: string
  slug: string
  description?: string
  logo?: string
  createdAt: string
  updatedAt: string
}

// Workspace types
export interface Workspace {
  id: string
  name: string
  description?: string
  organizationId: string
  organization: Organization
  settings: WorkspaceSettings
  createdAt: string
  updatedAt: string
}

export interface WorkspaceSettings {
  defaultModel?: string
  maxAgents?: number
  features: {
    [key: string]: boolean
  }
}

// Agent types
export interface Agent {
  id: string
  name: string
  description?: string
  type: AgentType
  status: AgentStatus
  workspaceId: string
  workspace: Workspace
  config: AgentConfig
  capabilities: string[]
  metadata: Record<string, any>
  createdAt: string
  updatedAt: string
}

export enum AgentType {
  CONVERSATIONAL = 'conversational',
  TASK = 'task',
  REACTIVE = 'reactive',
  PROACTIVE = 'proactive',
  COLLABORATIVE = 'collaborative',
}

export enum AgentStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  TRAINING = 'training',
  ERROR = 'error',
}

export interface AgentConfig {
  model: string
  temperature: number
  maxTokens: number
  systemPrompt?: string
  tools: Tool[]
  memory: MemoryConfig
  behavior: BehaviorConfig
}

export interface Tool {
  id: string
  name: string
  description: string
  type: ToolType
  config: Record<string, any>
}

export enum ToolType {
  API = 'api',
  DATABASE = 'database',
  FILE = 'file',
  CUSTOM = 'custom',
}

export interface MemoryConfig {
  type: MemoryType
  maxMessages?: number
  ttl?: number
}

export enum MemoryType {
  NONE = 'none',
  BUFFER = 'buffer',
  SUMMARY = 'summary',
  VECTOR = 'vector',
}

export interface BehaviorConfig {
  personality?: string
  goals: string[]
  constraints: string[]
  examples?: Example[]
}

export interface Example {
  input: string
  output: string
}

// Execution types
export interface Execution {
  id: string
  agentId: string
  agent: Agent
  status: ExecutionStatus
  input: any
  output?: any
  error?: string
  startedAt: string
  completedAt?: string
  duration?: number
  tokens?: TokenUsage
  steps: ExecutionStep[]
}

export enum ExecutionStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export interface TokenUsage {
  prompt: number
  completion: number
  total: number
}

export interface ExecutionStep {
  id: string
  type: StepType
  status: ExecutionStatus
  input: any
  output?: any
  error?: string
  startedAt: string
  completedAt?: string
  metadata?: Record<string, any>
}

export enum StepType {
  LLM = 'llm',
  TOOL = 'tool',
  MEMORY = 'memory',
  DECISION = 'decision',
}

// Analytics types
export interface Analytics {
  executions: {
    total: number
    successful: number
    failed: number
    averageDuration: number
  }
  tokens: {
    total: number
    averagePerExecution: number
    cost: number
  }
  agents: {
    total: number
    active: number
    byType: Record<AgentType, number>
  }
}

// API Response types
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  hasMore: boolean
}

export interface ErrorResponse {
  error: string
  message: string
  statusCode: number
  details?: any
}