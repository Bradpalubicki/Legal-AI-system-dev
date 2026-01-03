export interface Document {
  id: string
  fileName: string
  fileSize: number
  fileType: string
  title: string
  uploadedBy: string
  uploadedAt: string
  lastModified: string
  url: string
  thumbnailUrl?: string
  pageCount?: number
  status: DocumentStatus
  processingProgress?: number
  tags: string[]
  category: DocumentCategory
  clientId?: string
  caseId?: string
  permissions: DocumentPermission[]
  version: number
  checksum: string
  metadata: DocumentMetadata
}

export enum DocumentStatus {
  UPLOADING = 'uploading',
  PROCESSING = 'processing',
  READY = 'ready',
  ERROR = 'error',
  ARCHIVED = 'archived'
}

export enum DocumentCategory {
  CONTRACT = 'contract',
  BRIEF = 'brief',
  MOTION = 'motion',
  CORRESPONDENCE = 'correspondence',
  DISCOVERY = 'discovery',
  EVIDENCE = 'evidence',
  RESEARCH = 'research',
  OTHER = 'other'
}

export interface DocumentMetadata {
  author?: string
  subject?: string
  keywords?: string[]
  createdDate?: string
  modifiedDate?: string
  language?: string
  wordCount?: number
  characterCount?: number
  confidentialityLevel: ConfidentialityLevel
}

export enum ConfidentialityLevel {
  PUBLIC = 'public',
  INTERNAL = 'internal',
  CONFIDENTIAL = 'confidential',
  RESTRICTED = 'restricted'
}

export interface DocumentPermission {
  userId: string
  role: PermissionRole
  canRead: boolean
  canWrite: boolean
  canAnnotate: boolean
  canShare: boolean
  canDelete: boolean
}

export enum PermissionRole {
  OWNER = 'owner',
  EDITOR = 'editor',
  REVIEWER = 'reviewer',
  VIEWER = 'viewer'
}

// Annotation Types
export interface Annotation {
  id: string
  documentId: string
  userId: string
  userName: string
  userAvatar?: string
  type: AnnotationType
  content: string
  position: AnnotationPosition
  style: AnnotationStyle
  page: number
  createdAt: string
  updatedAt: string
  isResolved: boolean
  replies: AnnotationReply[]
  tags: string[]
  isPrivate: boolean
}

export enum AnnotationType {
  HIGHLIGHT = 'highlight',
  NOTE = 'note',
  COMMENT = 'comment',
  DRAWING = 'drawing',
  STAMP = 'stamp',
  REDACTION = 'redaction',
  LINK = 'link',
  BOOKMARK = 'bookmark'
}

export interface AnnotationPosition {
  x: number
  y: number
  width: number
  height: number
  pageNumber: number
  textContent?: string
  selectionRanges?: TextRange[]
}

export interface TextRange {
  start: number
  end: number
  text: string
}

export interface AnnotationStyle {
  color: string
  backgroundColor?: string
  borderColor?: string
  borderWidth?: number
  opacity: number
  fontSize?: number
  fontFamily?: string
  strokeWidth?: number
  strokeStyle?: 'solid' | 'dashed' | 'dotted'
}

export interface AnnotationReply {
  id: string
  userId: string
  userName: string
  userAvatar?: string
  content: string
  createdAt: string
  updatedAt: string
}

// Viewer Types
export interface ViewerState {
  currentPage: number
  totalPages: number
  zoom: number
  rotation: number
  viewMode: ViewMode
  isFullscreen: boolean
  selectedTool: AnnotationTool
  selectedAnnotations: string[]
  searchTerm: string
  searchResults: SearchResult[]
  currentSearchIndex: number
}

export enum ViewMode {
  SINGLE_PAGE = 'single_page',
  TWO_PAGE = 'two_page',
  CONTINUOUS = 'continuous',
  THUMBNAIL = 'thumbnail'
}

export enum AnnotationTool {
  SELECT = 'select',
  HIGHLIGHT = 'highlight',
  NOTE = 'note',
  COMMENT = 'comment',
  DRAWING = 'drawing',
  REDACTION = 'redaction',
  STAMP = 'stamp'
}

export interface SearchResult {
  page: number
  text: string
  position: {
    x: number
    y: number
    width: number
    height: number
  }
}

// Collaboration Types
export interface DocumentSession {
  id: string
  documentId: string
  participants: SessionParticipant[]
  createdAt: string
  lastActivity: string
  isActive: boolean
}

export interface SessionParticipant {
  userId: string
  userName: string
  userAvatar?: string
  role: PermissionRole
  joinedAt: string
  lastSeen: string
  isOnline: boolean
  cursor?: CursorPosition
}

export interface CursorPosition {
  page: number
  x: number
  y: number
  color: string
}

// Export/Print Types
export interface ExportOptions {
  format: ExportFormat
  includeAnnotations: boolean
  annotationTypes: AnnotationType[]
  pageRange?: {
    start: number
    end: number
  }
  quality: 'low' | 'medium' | 'high'
  watermark?: {
    text: string
    position: 'center' | 'corner'
    opacity: number
  }
}

export enum ExportFormat {
  PDF = 'pdf',
  PNG = 'png',
  JPEG = 'jpeg',
  DOCX = 'docx',
  TXT = 'txt'
}

// Comparison Types
export interface DocumentComparison {
  id: string
  documentA: string
  documentB: string
  createdAt: string
  differences: DocumentDifference[]
  summary: ComparisonSummary
}

export interface DocumentDifference {
  type: DifferenceType
  pageA?: number
  pageB?: number
  positionA?: AnnotationPosition
  positionB?: AnnotationPosition
  content: string
  severity: 'low' | 'medium' | 'high'
}

export enum DifferenceType {
  ADDED = 'added',
  REMOVED = 'removed',
  MODIFIED = 'modified',
  MOVED = 'moved'
}

export interface ComparisonSummary {
  totalDifferences: number
  addedContent: number
  removedContent: number
  modifiedContent: number
  similarityScore: number
}

// API Response Types
export interface DocumentUploadResponse {
  document: Document
  uploadUrl?: string
}

export interface AnnotationResponse {
  annotations: Annotation[]
  total: number
  page: number
  pageSize: number
}

export interface DocumentAnalysis {
  id: string
  documentId: string
  summary: string
  keyTerms: string[]
  entities: NamedEntity[]
  riskScore: number
  compliance: ComplianceIssue[]
  citations: LegalCitation[]
  confidence: number
  processingTime: number
  createdAt: string
}

export interface NamedEntity {
  text: string
  type: EntityType
  confidence: number
  startIndex: number
  endIndex: number
  page: number
}

export enum EntityType {
  PERSON = 'PERSON',
  ORGANIZATION = 'ORGANIZATION',
  DATE = 'DATE',
  MONEY = 'MONEY',
  LOCATION = 'LOCATION',
  LAW = 'LAW',
  COURT = 'COURT',
  CASE_NUMBER = 'CASE_NUMBER',
  STATUTE = 'STATUTE'
}

export interface ComplianceIssue {
  type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  location?: AnnotationPosition
  recommendation?: string
}

export interface LegalCitation {
  id: string
  text: string
  type: CitationType
  isValid: boolean
  url?: string
  court?: string
  year?: number
  jurisdiction?: string
  confidence: number
  location: AnnotationPosition
}

export enum CitationType {
  CASE = 'case',
  STATUTE = 'statute',
  REGULATION = 'regulation',
  CONSTITUTION = 'constitution',
  TREATISE = 'treatise',
  LAW_REVIEW = 'law_review'
}