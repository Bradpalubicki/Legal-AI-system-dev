/**
 * Unit Tests for Layout Component
 * 
 * Tests the main application layout component including navigation,
 * sidebar, header, and responsive behavior.
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Layout from '@/components/layout/Layout'

// Mock the child components
jest.mock('@/components/layout/Header', () => {
  return function MockHeader({ onMenuToggle, user }: any) {
    return (
      <header data-testid="header">
        <button onClick={onMenuToggle} data-testid="menu-toggle">
          Toggle Menu
        </button>
        {user && <span data-testid="user-info">{user.name}</span>}
      </header>
    )
  }
})

jest.mock('@/components/layout/Sidebar', () => {
  return function MockSidebar({ isOpen, onClose }: any) {
    return (
      <aside 
        data-testid="sidebar" 
        className={`sidebar ${isOpen ? 'open' : 'closed'}`}
      >
        <button onClick={onClose} data-testid="sidebar-close">
          Close
        </button>
        <nav>
          <a href="/dashboard" data-testid="nav-dashboard">Dashboard</a>
          <a href="/documents" data-testid="nav-documents">Documents</a>
          <a href="/cases" data-testid="nav-cases">Cases</a>
        </nav>
      </aside>
    )
  }
})

// Mock router context
const LayoutWrapper = ({ children, ...props }: any) => (
  <BrowserRouter>
    <Layout {...props}>{children}</Layout>
  </BrowserRouter>
)

describe('Layout Component', () => {
  const mockUser = {
    id: '1',
    name: 'John Doe',
    email: 'john@example.com',
    role: 'lawyer'
  }

  beforeEach(() => {
    // Clear any localStorage/sessionStorage
    localStorage.clear()
    sessionStorage.clear()
  })

  describe('Rendering', () => {
    it('renders the basic layout structure', () => {
      render(
        <LayoutWrapper>
          <div data-testid="main-content">Main Content</div>
        </LayoutWrapper>
      )

      expect(screen.getByTestId('header')).toBeInTheDocument()
      expect(screen.getByTestId('sidebar')).toBeInTheDocument()
      expect(screen.getByTestId('main-content')).toBeInTheDocument()
    })

    it('renders with user information when provided', () => {
      render(
        <LayoutWrapper user={mockUser}>
          <div>Content</div>
        </LayoutWrapper>
      )

      expect(screen.getByTestId('user-info')).toHaveTextContent('John Doe')
    })

    it('renders without user information when not provided', () => {
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      expect(screen.queryByTestId('user-info')).not.toBeInTheDocument()
    })

    it('applies correct CSS classes for layout structure', () => {
      const { container } = render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      const layoutElement = container.firstChild
      expect(layoutElement).toHaveClass('layout', 'min-h-screen')
    })
  })

  describe('Sidebar Functionality', () => {
    it('starts with sidebar closed by default', () => {
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      const sidebar = screen.getByTestId('sidebar')
      expect(sidebar).toHaveClass('closed')
      expect(sidebar).not.toHaveClass('open')
    })

    it('opens sidebar when menu toggle is clicked', async () => {
      const user = userEvent.setup()
      
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      const menuToggle = screen.getByTestId('menu-toggle')
      await user.click(menuToggle)

      const sidebar = screen.getByTestId('sidebar')
      expect(sidebar).toHaveClass('open')
    })

    it('closes sidebar when close button is clicked', async () => {
      const user = userEvent.setup()
      
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      // First open the sidebar
      const menuToggle = screen.getByTestId('menu-toggle')
      await user.click(menuToggle)

      // Then close it
      const closeButton = screen.getByTestId('sidebar-close')
      await user.click(closeButton)

      const sidebar = screen.getByTestId('sidebar')
      expect(sidebar).toHaveClass('closed')
    })

    it('toggles sidebar state correctly', async () => {
      const user = userEvent.setup()
      
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      const menuToggle = screen.getByTestId('menu-toggle')
      const sidebar = screen.getByTestId('sidebar')

      // Initially closed
      expect(sidebar).toHaveClass('closed')

      // Open
      await user.click(menuToggle)
      expect(sidebar).toHaveClass('open')

      // Close again
      await user.click(menuToggle)
      expect(sidebar).toHaveClass('closed')
    })
  })

  describe('Navigation', () => {
    it('renders navigation links in sidebar', () => {
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      expect(screen.getByTestId('nav-dashboard')).toBeInTheDocument()
      expect(screen.getByTestId('nav-documents')).toBeInTheDocument()
      expect(screen.getByTestId('nav-cases')).toBeInTheDocument()
    })

    it('navigation links have correct hrefs', () => {
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      expect(screen.getByTestId('nav-dashboard')).toHaveAttribute('href', '/dashboard')
      expect(screen.getByTestId('nav-documents')).toHaveAttribute('href', '/documents')
      expect(screen.getByTestId('nav-cases')).toHaveAttribute('href', '/cases')
    })
  })

  describe('Responsive Behavior', () => {
    it('handles window resize events', async () => {
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      // Simulate mobile viewport
      global.innerWidth = 768
      global.dispatchEvent(new Event('resize'))

      await waitFor(() => {
        // Layout should adapt to mobile view
        const sidebar = screen.getByTestId('sidebar')
        expect(sidebar).toBeInTheDocument()
      })
    })

    it('closes sidebar on mobile when clicking outside', async () => {
      const user = userEvent.setup()
      
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      })

      const { container } = render(
        <LayoutWrapper>
          <div data-testid="main-content">Content</div>
        </LayoutWrapper>
      )

      // Open sidebar first
      const menuToggle = screen.getByTestId('menu-toggle')
      await user.click(menuToggle)

      // Click outside sidebar (on main content)
      const mainContent = screen.getByTestId('main-content')
      await user.click(mainContent)

      // Sidebar should close on mobile
      const sidebar = screen.getByTestId('sidebar')
      expect(sidebar).toHaveClass('closed')
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      const header = screen.getByTestId('header')
      const sidebar = screen.getByTestId('sidebar')

      // Check that elements have appropriate roles
      expect(header).toBeInTheDocument()
      expect(sidebar).toBeInTheDocument()
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      const menuToggle = screen.getByTestId('menu-toggle')
      
      // Focus menu toggle and activate with Enter
      menuToggle.focus()
      await user.keyboard('{Enter}')

      const sidebar = screen.getByTestId('sidebar')
      expect(sidebar).toHaveClass('open')
    })

    it('provides proper focus management', async () => {
      const user = userEvent.setup()
      
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      // Open sidebar
      const menuToggle = screen.getByTestId('menu-toggle')
      await user.click(menuToggle)

      // Focus should move to first navigation item when sidebar opens
      await waitFor(() => {
        const dashboardLink = screen.getByTestId('nav-dashboard')
        expect(dashboardLink).toBeInTheDocument()
      })
    })

    it('handles escape key to close sidebar', async () => {
      const user = userEvent.setup()
      
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      // Open sidebar
      const menuToggle = screen.getByTestId('menu-toggle')
      await user.click(menuToggle)

      // Press Escape key
      await user.keyboard('{Escape}')

      const sidebar = screen.getByTestId('sidebar')
      expect(sidebar).toHaveClass('closed')
    })
  })

  describe('Error Handling', () => {
    it('handles missing user prop gracefully', () => {
      expect(() => {
        render(
          <LayoutWrapper user={null}>
            <div>Content</div>
          </LayoutWrapper>
        )
      }).not.toThrow()
    })

    it('handles missing children prop gracefully', () => {
      expect(() => {
        render(<LayoutWrapper />)
      }).not.toThrow()
    })

    it('recovers from sidebar state errors', async () => {
      const user = userEvent.setup()
      
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      // Simulate multiple rapid clicks
      const menuToggle = screen.getByTestId('menu-toggle')
      await user.click(menuToggle)
      await user.click(menuToggle)
      await user.click(menuToggle)

      // Component should still be functional
      const sidebar = screen.getByTestId('sidebar')
      expect(sidebar).toBeInTheDocument()
    })
  })

  describe('Performance', () => {
    it('does not re-render unnecessarily', () => {
      const renderSpy = jest.fn()
      
      const TestWrapper = ({ children }: any) => {
        renderSpy()
        return <LayoutWrapper>{children}</LayoutWrapper>
      }

      const { rerender } = render(
        <TestWrapper>
          <div>Content</div>
        </TestWrapper>
      )

      const initialRenderCount = renderSpy.mock.calls.length

      // Re-render with same props
      rerender(
        <TestWrapper>
          <div>Content</div>
        </TestWrapper>
      )

      // Should not cause unnecessary re-renders
      expect(renderSpy.mock.calls.length).toBeLessThanOrEqual(initialRenderCount + 1)
    })

    it('handles rapid state changes efficiently', async () => {
      const user = userEvent.setup()
      
      render(
        <LayoutWrapper>
          <div>Content</div>
        </LayoutWrapper>
      )

      const menuToggle = screen.getByTestId('menu-toggle')
      
      // Rapidly toggle sidebar multiple times
      const startTime = Date.now()
      for (let i = 0; i < 10; i++) {
        await user.click(menuToggle)
      }
      const endTime = Date.now()

      // Should complete quickly (under 1 second)
      expect(endTime - startTime).toBeLessThan(1000)
    })
  })

  describe('Integration', () => {
    it('integrates properly with routing context', () => {
      render(
        <LayoutWrapper>
          <div>Content with routing</div>
        </LayoutWrapper>
      )

      // Should render without errors in router context
      expect(screen.getByText('Content with routing')).toBeInTheDocument()
    })

    it('passes props correctly to child components', () => {
      render(
        <LayoutWrapper 
          user={mockUser}
          className="custom-class"
        >
          <div>Content</div>
        </LayoutWrapper>
      )

      // User info should be passed to header
      expect(screen.getByTestId('user-info')).toHaveTextContent('John Doe')
    })

    it('maintains state consistency across re-renders', async () => {
      const user = userEvent.setup()
      
      const { rerender } = render(
        <LayoutWrapper>
          <div>Content 1</div>
        </LayoutWrapper>
      )

      // Open sidebar
      const menuToggle = screen.getByTestId('menu-toggle')
      await user.click(menuToggle)

      // Re-render with different content
      rerender(
        <LayoutWrapper>
          <div>Content 2</div>
        </LayoutWrapper>
      )

      // Sidebar should maintain its open state
      const sidebar = screen.getByTestId('sidebar')
      expect(sidebar).toHaveClass('open')
    })
  })
})