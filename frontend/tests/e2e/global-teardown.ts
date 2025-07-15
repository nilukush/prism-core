import { FullConfig } from '@playwright/test'

async function globalTeardown(config: FullConfig) {
  console.log('Running global teardown for E2E tests...')
  
  // Clean up after tests
  // You can add teardown logic here, such as:
  // - Cleaning up test database
  // - Removing test users
  // - Stopping mock servers
  // - Clearing test data
  
  console.log('Global teardown completed')
}

export default globalTeardown