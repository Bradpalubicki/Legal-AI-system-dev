export interface User {
  id: string
  email: string
  firstName: string
  lastName: string
  role: UserRole
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export enum UserRole {
  ADMIN = 'admin',
  ATTORNEY = 'attorney',
  PARALEGAL = 'paralegal',
  CLIENT = 'client'
}

export interface Client {
  id: string
  name: string
  email: string
  phone?: string
  address?: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface APIResponse<T> {
  data?: T
  error?: string
  message?: string
  status: number
  timestamp: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// Re-export document types
export * from './document'
export * from './case'