const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: '../',
})

// Custom Jest configuration
const customJestConfig = {
  // Test environment
  testEnvironment: 'jsdom',
  
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  
  // Test patterns
  testMatch: [
    '<rootDir>/**/__tests__/**/*.(ts|tsx|js|jsx)',
    '<rootDir>/**/*.(test|spec).(ts|tsx|js|jsx)'
  ],
  
  // Module paths
  moduleDirectories: ['node_modules', '<rootDir>/'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/../src/$1',
    '^@/components/(.*)$': '<rootDir>/../src/components/$1',
    '^@/hooks/(.*)$': '<rootDir>/../src/hooks/$1',
    '^@/utils/(.*)$': '<rootDir>/../src/utils/$1',
    '^@/types/(.*)$': '<rootDir>/../src/types/$1',
    '^@/tests/(.*)$': '<rootDir>/$1'
  },
  
  // Transform configuration
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', { presets: ['next/babel'] }]
  },
  
  // File transformations
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  
  // Coverage configuration
  collectCoverage: true,
  collectCoverageFrom: [
    '../src/**/*.{ts,tsx,js,jsx}',
    '!../src/**/*.d.ts',
    '!../src/**/*.stories.{ts,tsx,js,jsx}',
    '!../src/**/index.{ts,tsx,js,jsx}',
    '!../src/**/*.config.{ts,tsx,js,jsx}',
    '!../src/app/layout.tsx',
    '!../src/app/globals.css'
  ],
  coverageDirectory: '<rootDir>/coverage',
  coverageReporters: ['text', 'lcov', 'html', 'json-summary'],
  coverageThreshold: {
    global: {
      branches: 95,
      functions: 95,
      lines: 95,
      statements: 95
    }
  },
  
  // Test environment options
  testEnvironmentOptions: {
    url: 'http://localhost:3000'
  },
  
  // Mock handling
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true,
  
  // Timeouts
  testTimeout: 30000,
  
  // Reporters
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: '<rootDir>/test-results',
      outputName: 'junit.xml'
    }]
  ],
  
  // Watch plugins
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname'
  ],
  
  // Globals
  globals: {
    'ts-jest': {
      useESM: true
    }
  }
}

// Create Jest config with Next.js integration
module.exports = createJestConfig(customJestConfig)