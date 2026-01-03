'use client'

/**
 * Document Sharing Component
 *
 * Share documents securely with clients through the portal.
 * Supports password protection, expiration dates, and access tracking.
 */

import { useState, useEffect } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { clientsApi } from '@/lib/api/clients'
import type {
  SharedDocument,
  DocumentShareRequest,
  AccessLevel,
  DocumentShareStatus
} from '@/types/client'

interface DocumentSharingProps {
  clientId: number
  clientName: string
}

export default function DocumentSharing({ clientId, clientName }: DocumentSharingProps) {
  const [documents, setDocuments] = useState<SharedDocument[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showShareForm, setShowShareForm] = useState(false)

  // Form state
  const [filename, setFilename] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [filePath, setFilePath] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [expiresInDays, setExpiresInDays] = useState(30)
  const [accessLevel, setAccessLevel] = useState<AccessLevel>('download')
  const [shareLoading, setShareLoading] = useState(false)

  useEffect(() => {
    loadDocuments()
  }, [clientId])

  const loadDocuments = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await clientsApi.listSharedDocuments(clientId)
      setDocuments(response.documents)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load documents')
      console.error('Load documents error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleShare = async (e: React.FormEvent) => {
    e.preventDefault()
    setShareLoading(true)
    setError(null)

    try {
      const request: DocumentShareRequest = {
        filename: filename.trim(),
        title: title.trim() || undefined,
        description: description.trim() || undefined,
        file_path: filePath.trim(),
        password: password.trim() || undefined,
        expires_days: expiresInDays,
        access_level: accessLevel
      }

      await clientsApi.shareDocument(clientId, request)

      // Reset form
      setFilename('')
      setTitle('')
      setDescription('')
      setFilePath('')
      setPassword('')
      setExpiresInDays(30)
      setAccessLevel('download')
      setShowShareForm(false)

      // Reload documents
      loadDocuments()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to share document')
      console.error('Share document error:', err)
    } finally {
      setShareLoading(false)
    }
  }

  const handleRevoke = async (documentId: number) => {
    if (!confirm('Are you sure you want to revoke access to this document?')) {
      return
    }

    try {
      await clientsApi.revokeDocument(clientId, documentId)
      loadDocuments()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to revoke document')
      console.error('Revoke document error:', err)
    }
  }

  const getStatusColor = (status: DocumentShareStatus) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-800'
      case 'viewed':
        return 'bg-blue-100 text-blue-800'
      case 'downloaded':
        return 'bg-green-100 text-green-800'
      case 'acknowledged':
        return 'bg-purple-100 text-purple-800'
      case 'expired':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const isExpired = (expiresAt?: string) => {
    if (!expiresAt) return false
    return new Date(expiresAt) < new Date()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Document Sharing</h3>
          <p className="text-sm text-gray-600">Share documents securely with {clientName}</p>
        </div>
        <button
          onClick={() => setShowShareForm(!showShareForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
        >
          {showShareForm ? (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Cancel
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Share Document
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-sm text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Share Form */}
      {showShareForm && (
        <form onSubmit={handleShare} className="bg-white rounded-lg shadow p-6 space-y-4">
          <h4 className="font-semibold text-gray-900">Share New Document</h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="filename" className="block text-sm font-medium text-gray-700 mb-2">
                Filename *
              </label>
              <input
                id="filename"
                type="text"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="contract.pdf"
              />
            </div>

            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                Title
              </label>
              <input
                id="title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Employment Contract"
              />
            </div>
          </div>

          <div>
            <label htmlFor="filePath" className="block text-sm font-medium text-gray-700 mb-2">
              File Path *
            </label>
            <input
              id="filePath"
              type="text"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="/documents/client_123/contract.pdf"
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Brief description of the document..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Password (Optional)
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center z-10 hover:opacity-70 transition-opacity"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <Eye className="h-5 w-5 text-gray-500 hover:text-gray-700" />
                  ) : (
                    <EyeOff className="h-5 w-5 text-gray-500 hover:text-gray-700" />
                  )}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="expiresInDays" className="block text-sm font-medium text-gray-700 mb-2">
                Expires In (Days)
              </label>
              <input
                id="expiresInDays"
                type="number"
                value={expiresInDays}
                onChange={(e) => setExpiresInDays(Number(e.target.value))}
                min="1"
                max="365"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="accessLevel" className="block text-sm font-medium text-gray-700 mb-2">
                Access Level
              </label>
              <select
                id="accessLevel"
                value={accessLevel}
                onChange={(e) => setAccessLevel(e.target.value as AccessLevel)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="read_only">Read Only</option>
                <option value="download">Download</option>
                <option value="comment">Comment</option>
                <option value="full">Full Access</option>
              </select>
            </div>
          </div>

          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              type="submit"
              disabled={shareLoading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {shareLoading ? 'Sharing...' : 'Share Document'}
            </button>
          </div>
        </form>
      )}

      {/* Documents List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading documents...</p>
          </div>
        </div>
      ) : documents.length > 0 ? (
        <div className="space-y-4">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className={`bg-white rounded-lg shadow p-6 ${
                isExpired(doc.expires_at) ? 'opacity-60' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-semibold text-gray-900">
                      {doc.title || doc.filename}
                    </h4>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(doc.status)}`}>
                      {doc.status}
                    </span>
                    {doc.password_protected && (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
                        Password Protected
                      </span>
                    )}
                    {isExpired(doc.expires_at) && (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
                        Expired
                      </span>
                    )}
                  </div>

                  {doc.description && (
                    <p className="text-sm text-gray-600 mb-3">{doc.description}</p>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-500">
                    <div>
                      <span className="font-medium">Filename:</span>
                      <p className="text-gray-700">{doc.filename}</p>
                    </div>
                    <div>
                      <span className="font-medium">Size:</span>
                      <p className="text-gray-700">{formatFileSize(doc.file_size)}</p>
                    </div>
                    <div>
                      <span className="font-medium">Shared:</span>
                      <p className="text-gray-700">{formatDate(doc.shared_at)}</p>
                    </div>
                    {doc.expires_at && (
                      <div>
                        <span className="font-medium">Expires:</span>
                        <p className="text-gray-700">{formatDate(doc.expires_at)}</p>
                      </div>
                    )}
                  </div>

                  <div className="flex gap-4 mt-3 text-xs text-gray-600">
                    <div className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      {doc.view_count} views
                    </div>
                    <div className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      {doc.download_count} downloads
                    </div>
                    {doc.first_viewed_at && (
                      <div className="flex items-center gap-1">
                        First viewed: {formatDate(doc.first_viewed_at)}
                      </div>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => handleRevoke(doc.id)}
                  className="ml-4 text-red-600 hover:text-red-800 text-sm"
                >
                  Revoke
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No documents shared</h3>
          <p className="mt-2 text-sm text-gray-500">
            Share your first document with this client to get started
          </p>
        </div>
      )}
    </div>
  )
}
