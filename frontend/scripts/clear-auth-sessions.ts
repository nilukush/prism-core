#!/usr/bin/env node

/**
 * Script to clear NextAuth sessions
 * Usage: npx ts-node scripts/clear-auth-sessions.ts [--all]
 * 
 * Options:
 *   --all    Clear all sessions (requires database access)
 *   --help   Show this help message
 */

import { parse } from 'url'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'

async function clearLocalSession() {
  try {
    const response = await fetch(`${API_URL}/api/auth/clear-session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    const data = await response.json()
    
    if (response.ok) {
      console.log('✅ Session cleared successfully')
      console.log(data)
    } else {
      console.error('❌ Failed to clear session:', data)
      process.exit(1)
    }
  } catch (error) {
    console.error('❌ Error clearing session:', error)
    process.exit(1)
  }
}

async function clearAllSessions() {
  console.log('⚠️  Clearing all sessions is not implemented yet')
  console.log('This would require direct database access to clear all session records')
  console.log('Please implement based on your session storage strategy (JWT/Database)')
}

async function main() {
  const args = process.argv.slice(2)
  
  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
NextAuth Session Clear Utility

Usage: npx ts-node scripts/clear-auth-sessions.ts [options]

Options:
  --all     Clear all sessions (requires database configuration)
  --help    Show this help message
  
Environment Variables:
  NEXT_PUBLIC_API_URL    API URL (default: http://localhost:3000)
  
Examples:
  # Clear current session
  npx ts-node scripts/clear-auth-sessions.ts
  
  # Clear all sessions (when implemented)
  npx ts-node scripts/clear-auth-sessions.ts --all
    `)
    process.exit(0)
  }
  
  if (args.includes('--all')) {
    await clearAllSessions()
  } else {
    await clearLocalSession()
  }
}

// Run the script
if (require.main === module) {
  main().catch((error) => {
    console.error('❌ Script failed:', error)
    process.exit(1)
  })
}