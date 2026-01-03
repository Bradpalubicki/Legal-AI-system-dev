'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import DocumentViewer from '../../../components/document/DocumentViewer'
// TEMPORARILY DISABLED: import AnnotationToolbar from '../../../components/document/AnnotationToolbar'
// TEMPORARILY DISABLED: import CollaborationPanel from '../../../components/document/CollaborationPanel'
import { 
  Document as DocumentType, 
  Annotation, 
  AnnotationTool, 
  AnnotationStyle,
  DocumentSession,
  ExportFormat 
} from '../../../types/document'
import { Layout } from '../../../components/layout'
// TEMPORARILY DISABLED: import { Button } from '../../../components/ui'
import {
  ArrowLeftIcon,
  ShareIcon,
  UserGroupIcon,
  ChatBubbleBottomCenterTextIcon
} from '@heroicons/react/24/outline'

// Mock data for demonstration
const mockDocument: DocumentType = {
  id: 'doc-123',
  fileName: 'Contract_Analysis_2024.pdf',
  fileSize: 2048000,
  fileType: 'application/pdf',
  title: 'Software Development Contract Analysis',
  uploadedBy: 'john.doe@company.com',
  uploadedAt: '2024-08-28T10:00:00Z',
  lastModified: '2024-08-28T14:30:00Z',
  url: '/sample-document.pdf', // This would be a real PDF URL
  thumbnailUrl: '/sample-thumbnail.jpg',
  pageCount: 25,
  status: 'ready' as any,
  tags: ['contract', 'software', 'legal-review'],
  category: 'contract' as any,
  permissions: [],
  version: 1,
  checksum: 'abc123',
  metadata: {
    author: 'Legal Department',
    subject: 'Software Development Agreement',
    keywords: ['contract', 'development', 'software'],
    confidentialityLevel: 'confidential' as any,
    wordCount: 5000,
    characterCount: 25000
  }
}

const mockAnnotations: Annotation[] = [
  {
    id: 'ann-1',
    documentId: 'doc-123',
    userId: 'user-1',
    userName: 'John Doe',
    type: 'highlight' as any,
    content: 'Important clause about intellectual property rights',
    position: {
      x: 100,
      y: 200,
      width: 200,
      height: 20,
      pageNumber: 1
    },
    style: {
      color: '#FFEB3B',
      backgroundColor: '#FFEB3B',
      opacity: 0.5,
      borderColor: '#FBC02D',
      borderWidth: 1
    },
    page: 1,
    createdAt: '2024-08-28T12:00:00Z',
    updatedAt: '2024-08-28T12:00:00Z',
    isResolved: false,
    replies: [
      {
        id: 'reply-1',
        userId: 'user-2',
        userName: 'Jane Smith',
        content: 'This clause needs clarification on derivative works.',
        createdAt: '2024-08-28T13:00:00Z',
        updatedAt: '2024-08-28T13:00:00Z'
      }
    ],
    tags: ['ip-rights'],
    isPrivate: false
  },
  {
    id: 'ann-2',
    documentId: 'doc-123',
    userId: 'user-2',
    userName: 'Jane Smith',
    type: 'comment' as any,
    content: 'Payment terms seem favorable but need to verify with finance team',
    position: {
      x: 150,
      y: 400,
      width: 180,
      height: 60,
      pageNumber: 3
    },
    style: {
      color: '#333333',
      backgroundColor: '#4CAF50',
      opacity: 0.9,
      borderColor: '#388E3C',
      borderWidth: 2,
      fontSize: 12
    },
    page: 3,
    createdAt: '2024-08-28T14:00:00Z',
    updatedAt: '2024-08-28T14:00:00Z',
    isResolved: false,
    replies: [],
    tags: ['payment', 'finance'],
    isPrivate: false
  }
]

const mockSession: DocumentSession = {
  id: 'session-123',
  documentId: 'doc-123',
  participants: [
    {
      userId: 'user-1',
      userName: 'John Doe',
      role: 'owner' as any,
      joinedAt: '2024-08-28T10:00:00Z',
      lastSeen: '2024-08-28T15:30:00Z',
      isOnline: true,
      cursor: {
        page: 1,
        x: 200,
        y: 300,
        color: '#FF6B6B'
      }
    },
    {
      userId: 'user-2',
      userName: 'Jane Smith',
      role: 'editor' as any,
      joinedAt: '2024-08-28T11:00:00Z',
      lastSeen: '2024-08-28T15:28:00Z',
      isOnline: true,
      cursor: {
        page: 3,
        x: 150,
        y: 400,
        color: '#4ECDC4'
      }
    },
    {
      userId: 'user-3',
      userName: 'Mike Johnson',
      role: 'reviewer' as any,
      joinedAt: '2024-08-28T13:00:00Z',
      lastSeen: '2024-08-28T14:45:00Z',
      isOnline: false
    }
  ],
  createdAt: '2024-08-28T10:00:00Z',
  lastActivity: '2024-08-28T15:30:00Z',
  isActive: true
}

export default function DocumentPage() {
  const params = useParams()
  const documentId = params?.id as string

  const [document] = useState<DocumentType>(mockDocument)
  const [annotations, setAnnotations] = useState<Annotation[]>(mockAnnotations)
  const [session, setSession] = useState<DocumentSession>(mockSession)
  
  const [selectedTool, setSelectedTool] = useState<AnnotationTool>('select' as any)
  const [annotationStyle, setAnnotationStyle] = useState<AnnotationStyle>({
    color: '#FFEB3B',
    backgroundColor: '#FFEB3B',
    opacity: 0.5,
    borderColor: '#FBC02D',
    borderWidth: 1,
    fontSize: 12
  })
  
  const [showCollaboration, setShowCollaboration] = useState(false)
  const [showAnnotationToolbar, setShowAnnotationToolbar] = useState(true)

  const currentUserId = 'user-1' // This would come from auth context

  const handleAnnotationCreate = (annotation: Partial<Annotation>) => {
    const newAnnotation: Annotation = {
      ...annotation,
      id: `ann-${Date.now()}`,
      documentId,
      userId: currentUserId,
      userName: 'Current User',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isResolved: false,
      replies: [],
      tags: [],
      isPrivate: false
    } as Annotation

    setAnnotations(prev => [...prev, newAnnotation])
  }

  const handleAnnotationUpdate = (id: string, updates: Partial<Annotation>) => {
    setAnnotations(prev => 
      prev.map(ann => 
        ann.id === id 
          ? { ...ann, ...updates, updatedAt: new Date().toISOString() }
          : ann
      )
    )
  }

  const handleAnnotationDelete = (id: string) => {
    setAnnotations(prev => prev.filter(ann => ann.id !== id))
  }

  const handleExport = (format: ExportFormat) => {
    console.log('Exporting document in format:', format)
    // Implementation would handle actual export
  }

  const handlePrint = () => {
    console.log('Printing document')
    window.print()
  }

  const handleShare = () => {
    console.log('Sharing document')
    // Implementation would handle sharing
  }

  if (!document) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading document...</p>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="flex flex-col h-screen">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => window.history.back()}
              className="flex items-center px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded"
            >
              <ArrowLeftIcon className="w-4 h-4 mr-2" />
              Back
            </button>
            
            <div>
              <h1 className="text-xl font-semibold text-gray-900">{document.title}</h1>
              <p className="text-sm text-gray-500">
                {document.pageCount} pages • Last modified {new Date(document.lastModified).toLocaleDateString()}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAnnotationToolbar(!showAnnotationToolbar)}
              className="flex items-center px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded"
            >
              <ChatBubbleBottomCenterTextIcon className="w-4 h-4 mr-2" />
              Annotations
            </button>
            
            <button
              onClick={() => setShowCollaboration(!showCollaboration)}
              className="flex items-center px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded"
            >
              <UserGroupIcon className="w-4 h-4 mr-2" />
              Collaborate ({session.participants.filter(p => p.isOnline).length})
            </button>
            
            <button
              onClick={handleShare}
              className="flex items-center px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded"
            >
              <ShareIcon className="w-4 h-4 mr-2" />
              Share
            </button>
          </div>
        </div>

        {/* Annotation Toolbar */}
        {showAnnotationToolbar && (
          <div className="p-4 bg-gray-50 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-900">Annotation Toolbar Placeholder</h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setSelectedTool(AnnotationTool.SELECT)}
                  className={`px-3 py-1 text-xs rounded ${selectedTool === AnnotationTool.SELECT ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
                >
                  Select
                </button>
                <button
                  onClick={() => setSelectedTool(AnnotationTool.HIGHLIGHT)}
                  className={`px-3 py-1 text-xs rounded ${selectedTool === AnnotationTool.HIGHLIGHT ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
                >
                  Highlight
                </button>
                <button
                  onClick={() => setSelectedTool(AnnotationTool.NOTE)}
                  className={`px-3 py-1 text-xs rounded ${selectedTool === AnnotationTool.NOTE ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
                >
                  Note
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden relative">
          <DocumentViewer
            document={document}
            annotations={annotations}
            onAnnotationCreate={handleAnnotationCreate}
            onAnnotationUpdate={handleAnnotationUpdate}
            onAnnotationDelete={handleAnnotationDelete}
            onExport={handleExport}
            onPrint={handlePrint}
            onShare={handleShare}
            showAnnotations={true}
            showToolbar={true}
            className="flex-1"
          />

          {/* Collaboration Panel */}
          {/* FUTURE FEATURE: Collaboration Panel not yet implemented
          {showCollaboration && (
            <div className="absolute top-4 right-4 z-40">
              <CollaborationPanel
                documentId={documentId}
                session={session}
                currentUserId={currentUserId}
                onShareDocument={handleShare}
                onClose={() => setShowCollaboration(false)}
              />
            </div>
          )}
          */}
        </div>
      </div>
    </Layout>
  )
}