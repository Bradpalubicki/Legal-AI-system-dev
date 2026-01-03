import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../../mocks/server'
import { rest } from 'msw'
import SearchInterface from '../../../src/components/search/SearchInterface'
import { mockSearchResults } from '../../utils/test-utils'

describe('SearchInterface', () => {
  const defaultProps = {
    onResultSelect: jest.fn(),
    onSearchSubmit: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders search input and controls', () => {
      render(<SearchInterface {...defaultProps} />)
      
      expect(screen.getByPlaceholderText(/search legal documents/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /filters/i })).toBeInTheDocument()
    })

    it('shows recent searches when input is focused', async () => {
      const user = userEvent.setup()
      render(<SearchInterface {...defaultProps} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.click(searchInput)
      
      expect(screen.getByText(/recent searches/i)).toBeInTheDocument()
    })

    it('displays loading state during search', async () => {
      const user = userEvent.setup()
      
      // Delay the API response
      server.use(
        rest.get('/api/search', (req, res, ctx) => {
          return res(ctx.delay(100), ctx.json({ results: mockSearchResults }))
        })
      )
      
      render(<SearchInterface {...defaultProps} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'contract law')
      await user.keyboard('{Enter}')
      
      expect(screen.getByText(/searching/i)).toBeInTheDocument()
    })
  })

  describe('Search Functionality', () => {
    it('performs search on form submission', async () => {
      const user = userEvent.setup()
      const mockOnSearchSubmit = jest.fn()
      
      render(<SearchInterface {...defaultProps} onSearchSubmit={mockOnSearchSubmit} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'contract law')
      
      const searchButton = screen.getByRole('button', { name: /search/i })
      await user.click(searchButton)
      
      expect(mockOnSearchSubmit).toHaveBeenCalledWith('contract law', expect.any(Object))
    })

    it('performs search on Enter key press', async () => {
      const user = userEvent.setup()
      const mockOnSearchSubmit = jest.fn()
      
      render(<SearchInterface {...defaultProps} onSearchSubmit={mockOnSearchSubmit} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'tort law')
      await user.keyboard('{Enter}')
      
      expect(mockOnSearchSubmit).toHaveBeenCalledWith('tort law', expect.any(Object))
    })

    it('displays search results', async () => {
      const user = userEvent.setup()
      
      render(<SearchInterface {...defaultProps} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'contract')
      await user.keyboard('{Enter}')
      
      await waitFor(() => {
        expect(screen.getByText('Case Law regarding "contract"')).toBeInTheDocument()
        expect(screen.getByText('Statute about "contract"')).toBeInTheDocument()
      })
    })

    it('handles empty search results', async () => {
      const user = userEvent.setup()
      
      server.use(
        rest.get('/api/search', (req, res, ctx) => {
          return res(ctx.json({ results: [], totalResults: 0 }))
        })
      )
      
      render(<SearchInterface {...defaultProps} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'nonexistent query')
      await user.keyboard('{Enter}')
      
      await waitFor(() => {
        expect(screen.getByText(/no results found/i)).toBeInTheDocument()
      })
    })

    it('handles search API errors', async () => {
      const user = userEvent.setup()
      
      server.use(
        rest.get('/api/search', (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ message: 'Server error' }))
        })
      )
      
      render(<SearchInterface {...defaultProps} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'error query')
      await user.keyboard('{Enter}')
      
      await waitFor(() => {
        expect(screen.getByText(/search failed/i)).toBeInTheDocument()
      })
    })
  })

  describe('Search Filters', () => {
    it('opens filter panel', async () => {
      const user = userEvent.setup()
      render(<SearchInterface {...defaultProps} />)
      
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)
      
      expect(screen.getByText(/document type/i)).toBeInTheDocument()
      expect(screen.getByText(/jurisdiction/i)).toBeInTheDocument()
      expect(screen.getByText(/date range/i)).toBeInTheDocument()
    })

    it('applies filters to search', async () => {
      const user = userEvent.setup()
      const mockOnSearchSubmit = jest.fn()
      
      render(<SearchInterface {...defaultProps} onSearchSubmit={mockOnSearchSubmit} />)
      
      // Open filters
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)
      
      // Select case type filter
      const caseFilter = screen.getByText('Cases')
      await user.click(caseFilter)
      
      // Select federal jurisdiction
      const federalFilter = screen.getByText('Federal')
      await user.click(federalFilter)
      
      // Perform search
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'constitutional law')
      await user.keyboard('{Enter}')
      
      expect(mockOnSearchSubmit).toHaveBeenCalledWith(
        'constitutional law',
        expect.objectContaining({
          type: ['case'],
          jurisdiction: ['federal']
        })
      )
    })

    it('clears all filters', async () => {
      const user = userEvent.setup()
      render(<SearchInterface {...defaultProps} />)
      
      // Open filters and select some
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)
      
      const caseFilter = screen.getByText('Cases')
      await user.click(caseFilter)
      
      // Clear all filters
      const clearButton = screen.getByText(/clear all/i)
      await user.click(clearButton)
      
      expect(caseFilter).not.toHaveClass('bg-blue-500')
    })

    it('shows active filter count', async () => {
      const user = userEvent.setup()
      render(<SearchInterface {...defaultProps} />)
      
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)
      
      // Select multiple filters
      await user.click(screen.getByText('Cases'))
      await user.click(screen.getByText('Federal'))
      
      expect(screen.getByText('2')).toBeInTheDocument() // Filter count badge
    })
  })

  describe('Advanced Search Features', () => {
    it('supports voice search', async () => {
      const user = userEvent.setup()
      
      // Mock speech recognition
      const mockSpeechRecognition = {
        start: jest.fn(),
        stop: jest.fn(),
        addEventListener: jest.fn()
      }
      
      global.webkitSpeechRecognition = jest.fn(() => mockSpeechRecognition)
      
      render(<SearchInterface {...defaultProps} showVoiceSearch={true} />)
      
      const voiceButton = screen.getByLabelText(/voice search/i)
      await user.click(voiceButton)
      
      expect(mockSpeechRecognition.start).toHaveBeenCalled()
    })

    it('shows search suggestions', async () => {
      const user = userEvent.setup()
      
      // Mock suggestions API
      server.use(
        rest.get('/api/search/suggestions', (req, res, ctx) => {
          return res(ctx.json({
            suggestions: ['contract law', 'contract dispute', 'contract breach']
          }))
        })
      )
      
      render(<SearchInterface {...defaultProps} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'contr')
      
      await waitFor(() => {
        expect(screen.getByText('contract law')).toBeInTheDocument()
        expect(screen.getByText('contract dispute')).toBeInTheDocument()
      })
    })

    it('handles search suggestion selection', async () => {
      const user = userEvent.setup()
      const mockOnSearchSubmit = jest.fn()
      
      server.use(
        rest.get('/api/search/suggestions', (req, res, ctx) => {
          return res(ctx.json({
            suggestions: ['contract law']
          }))
        })
      )
      
      render(<SearchInterface {...defaultProps} onSearchSubmit={mockOnSearchSubmit} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'contr')
      
      await waitFor(() => {
        expect(screen.getByText('contract law')).toBeInTheDocument()
      })
      
      await user.click(screen.getByText('contract law'))
      
      expect(mockOnSearchSubmit).toHaveBeenCalledWith('contract law', expect.any(Object))
    })
  })

  describe('Search History', () => {
    it('saves searches to history', async () => {
      const user = userEvent.setup()
      
      render(<SearchInterface {...defaultProps} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'criminal law')
      await user.keyboard('{Enter}')
      
      // Focus input again to show history
      await user.click(searchInput)
      await user.clear(searchInput)
      
      expect(screen.getByText('criminal law')).toBeInTheDocument()
    })

    it('limits search history size', async () => {
      const user = userEvent.setup()
      
      render(<SearchInterface {...defaultProps} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      
      // Add many searches
      for (let i = 0; i < 15; i++) {
        await user.clear(searchInput)
        await user.type(searchInput, `search ${i}`)
        await user.keyboard('{Enter}')
        await waitFor(() => screen.queryByText(/searching/i) === null)
      }
      
      // Check history is limited
      await user.click(searchInput)
      await user.clear(searchInput)
      
      const historyItems = screen.getAllByText(/search \d+/)
      expect(historyItems.length).toBeLessThanOrEqual(10)
    })
  })

  describe('Result Selection', () => {
    it('calls onResultSelect when result is clicked', async () => {
      const user = userEvent.setup()
      const mockOnResultSelect = jest.fn()
      
      render(<SearchInterface {...defaultProps} onResultSelect={mockOnResultSelect} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'contract')
      await user.keyboard('{Enter}')
      
      await waitFor(() => {
        expect(screen.getByText('Case Law regarding "contract"')).toBeInTheDocument()
      })
      
      const firstResult = screen.getByText('Case Law regarding "contract"')
      await user.click(firstResult)
      
      expect(mockOnResultSelect).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Case Law regarding "contract"',
          type: 'case'
        })
      )
    })

    it('highlights search terms in results', async () => {
      const user = userEvent.setup()
      
      render(<SearchInterface {...defaultProps} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'contract')
      await user.keyboard('{Enter}')
      
      await waitFor(() => {
        const highlightedText = screen.getByText(
          (content, element) => {
            return element?.innerHTML.includes('<mark>') || false
          }
        )
        expect(highlightedText).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(<SearchInterface {...defaultProps} />)
      
      const searchInput = screen.getByRole('searchbox')
      expect(searchInput).toHaveAccessibleName()
      
      const searchButton = screen.getByRole('button', { name: /search/i })
      expect(searchButton).toBeInTheDocument()
      
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      expect(filtersButton).toBeInTheDocument()
    })

    it('announces search results to screen readers', async () => {
      const user = userEvent.setup()
      
      render(<SearchInterface {...defaultProps} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'contract')
      await user.keyboard('{Enter}')
      
      await waitFor(() => {
        const announcement = screen.getByRole('status')
        expect(announcement).toHaveTextContent(/found \d+ results/i)
      })
    })

    it('supports keyboard navigation in results', async () => {
      const user = userEvent.setup()
      
      render(<SearchInterface {...defaultProps} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      await user.type(searchInput, 'contract')
      await user.keyboard('{Enter}')
      
      await waitFor(() => {
        expect(screen.getByText('Case Law regarding "contract"')).toBeInTheDocument()
      })
      
      // Use arrow keys to navigate results
      await user.keyboard('{ArrowDown}')
      expect(document.activeElement).toHaveTextContent(/case law/i)
      
      await user.keyboard('{ArrowDown}')
      expect(document.activeElement).toHaveTextContent(/statute/i)
    })

    it('supports screen reader-friendly filter descriptions', async () => {
      const user = userEvent.setup()
      render(<SearchInterface {...defaultProps} />)
      
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)
      
      const caseFilter = screen.getByText('Cases')
      expect(caseFilter.closest('button')).toHaveAttribute(
        'aria-describedby',
        expect.stringContaining('filter-description')
      )
    })
  })

  describe('Performance', () => {
    it('debounces search input', async () => {
      const user = userEvent.setup()
      const mockOnSearchSubmit = jest.fn()
      
      render(<SearchInterface {...defaultProps} onSearchSubmit={mockOnSearchSubmit} autoSearch={true} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      
      // Type rapidly
      await user.type(searchInput, 'contract law')
      
      // Should not search immediately
      expect(mockOnSearchSubmit).not.toHaveBeenCalled()
      
      // Wait for debounce
      await waitFor(() => {
        expect(mockOnSearchSubmit).toHaveBeenCalledWith('contract law', expect.any(Object))
      }, { timeout: 1000 })
    })

    it('cancels previous search requests', async () => {
      const user = userEvent.setup()
      
      // Mock fetch with delay
      const mockFetch = jest.fn(() => 
        new Promise(resolve => setTimeout(() => 
          resolve({
            ok: true,
            json: () => Promise.resolve({ results: mockSearchResults })
          }), 100)
        )
      )
      
      global.fetch = mockFetch
      
      render(<SearchInterface {...defaultProps} />)
      
      const searchInput = screen.getByPlaceholderText(/search legal documents/i)
      
      // Start first search
      await user.type(searchInput, 'first query')
      await user.keyboard('{Enter}')
      
      // Immediately start second search
      await user.clear(searchInput)
      await user.type(searchInput, 'second query')
      await user.keyboard('{Enter}')
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2)
      })
    })
  })
})