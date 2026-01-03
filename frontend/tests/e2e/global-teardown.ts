async function globalTeardown() {
  console.log('Starting global teardown...')
  
  // Clean up test data
  try {
    // You can make API calls here to clean up test data
    // await fetch('http://localhost:3000/api/test/cleanup', { method: 'POST' })
    
    console.log('Test data cleanup completed')
  } catch (error) {
    console.warn('Test data cleanup failed:', error)
  }
  
  // Clean up any temporary files
  const fs = require('fs').promises
  try {
    await fs.unlink('test-results/auth-state.json').catch(() => {})
    console.log('Temporary files cleaned up')
  } catch (error) {
    console.warn('File cleanup failed:', error)
  }
  
  console.log('Global teardown completed')
}

export default globalTeardown