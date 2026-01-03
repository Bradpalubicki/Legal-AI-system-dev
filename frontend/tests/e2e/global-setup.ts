import { chromium, FullConfig } from '@playwright/test'

async function globalSetup(config: FullConfig) {
  console.log('Starting global setup...')
  
  // Launch browser for setup
  const browser = await chromium.launch()
  const context = await browser.newContext()
  const page = await context.newPage()
  
  try {
    // Wait for application to be available
    console.log('Checking application availability...')
    await page.goto('http://localhost:3000', { 
      waitUntil: 'networkidle',
      timeout: 60000 
    })
    
    // Perform any necessary authentication setup
    console.log('Setting up test authentication...')
    
    // Check if login is required and create test user session
    const loginButton = page.locator('button:has-text("Login")')
    if (await loginButton.isVisible({ timeout: 5000 })) {
      await loginButton.click()
      
      // Fill login form
      await page.fill('input[type="email"]', 'test@example.com')
      await page.fill('input[type="password"]', 'password123')
      await page.click('button[type="submit"]')
      
      // Wait for successful login
      await page.waitForSelector('[data-testid="dashboard"]', { timeout: 10000 })
      
      // Save authentication state
      await context.storageState({ path: 'test-results/auth-state.json' })
    }
    
    // Seed test data if needed
    console.log('Seeding test data...')
    
    // You can make API calls here to set up test data
    // await page.request.post('/api/test/seed-data')
    
    console.log('Global setup completed successfully')
    
  } catch (error) {
    console.error('Global setup failed:', error)
    throw error
  } finally {
    await context.close()
    await browser.close()
  }
}

export default globalSetup