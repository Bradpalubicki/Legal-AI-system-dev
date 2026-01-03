'use client';

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { clsx } from 'clsx'
import { useAuth } from '@/hooks/useAuth'
import {
  HomeIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
  ChartBarIcon,
  CogIcon,
  UsersIcon,
  FolderIcon,
  BanknotesIcon,
  BookOpenIcon,
  ScaleIcon,
  ArrowRightOnRectangleIcon,
  ChatBubbleLeftRightIcon,
  CreditCardIcon
} from '@heroicons/react/24/outline'

interface SidebarProps {
  isCollapsed?: boolean
  onToggle?: () => void
}

interface NavigationItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  current?: boolean
  children?: NavigationItem[]
}

const navigation: NavigationItem[] = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Documents', href: '/?tab=documents', icon: DocumentTextIcon },
  { name: 'AI Assistant', href: '/ai-assistant', icon: ChatBubbleLeftRightIcon },
  { name: 'Legal Research', href: '/research', icon: BookOpenIcon },
  { name: 'PACER Search', href: '/?tab=pacer', icon: ScaleIcon },
  { name: 'Credits', href: '/credits', icon: CreditCardIcon },
  { name: 'Search', href: '/search', icon: MagnifyingGlassIcon },
  { name: 'Cases', href: '/?tab=cases', icon: FolderIcon },
  { name: 'Clients', href: '/clients', icon: UsersIcon },
  { name: 'Cost Management', href: '/costs', icon: BanknotesIcon },
  { name: 'Analytics', href: '/dashboard', icon: ChartBarIcon },
  { name: 'Settings', href: '/settings', icon: CogIcon },
]

export default function Sidebar({ isCollapsed = false, onToggle }: SidebarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const { user, logout, isAuthenticated } = useAuth()

  const handleLogout = async () => {
    await logout()
    router.push('/auth/login')
  }

  // Get user initials for avatar
  const getUserInitials = () => {
    if (!user) return 'U'
    const nameParts = user.full_name?.split(' ') || []
    if (nameParts.length >= 2) {
      return nameParts[0][0] + nameParts[1][0]
    }
    return user.full_name?.[0] || user.email?.[0] || 'U'
  }

  return (
    <div className={clsx(
      'flex flex-col bg-gray-900 text-white transition-all duration-300',
      isCollapsed ? 'w-16' : 'w-64'
    )}>
      {/* Logo */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center">
          <div className="flex items-center justify-center w-8 h-8 bg-primary-600 rounded-lg">
            <span className="text-white font-bold text-sm">LA</span>
          </div>
          {!isCollapsed && (
            <span className="ml-3 text-lg font-semibold">Legal AI</span>
          )}
        </div>
        {onToggle && (
          <button
            onClick={onToggle}
            className="p-1 rounded-md hover:bg-gray-800 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors',
                isActive
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              )}
            >
              <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
              {!isCollapsed && <span>{item.name}</span>}
            </Link>
          )
        })}
      </nav>

      {/* User Profile & Logout */}
      {!isCollapsed && isAuthenticated && (
        <div className="p-4 border-t border-gray-700 space-y-3">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
              <span className="text-sm font-semibold text-white">✓</span>
            </div>
            <div className="ml-3 flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                Logged in
              </p>
              <p className="text-xs text-green-400 capitalize">
                Verified
              </p>
            </div>
          </div>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="w-full flex items-center px-2 py-2 text-sm font-medium text-gray-300 rounded-md hover:bg-gray-700 hover:text-white transition-colors"
          >
            <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5 flex-shrink-0" />
            <span>Log Out</span>
          </button>
        </div>
      )}

      {/* Collapsed view - just logout icon */}
      {isCollapsed && isAuthenticated && (
        <div className="p-4 border-t border-gray-700">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center p-2 text-gray-300 rounded-md hover:bg-gray-700 hover:text-white transition-colors"
            title="Log Out"
          >
            <ArrowRightOnRectangleIcon className="h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  )
}