'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  DocumentSession, 
  SessionParticipant, 
  PermissionRole,
  CursorPosition 
} from '../../types/document'
import { Button } from '../ui'
import {
  UserGroupIcon,
  UserCircleIcon,
  EyeIcon,
  PencilIcon,
  ShareIcon,
  ClockIcon,
  WiFiIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'

interface CollaborationPanelProps {
  documentId: string
  session?: DocumentSession
  currentUserId: string
  onParticipantClick?: (participant: SessionParticipant) => void
  onShareDocument?: () => void
  onClose?: () => void
  className?: string
}

const PARTICIPANT_COLORS = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57',
  '#FF9FF3', '#54A0FF', '#5F27CD', '#00D2D3', '#FF9F43'
]

export default function CollaborationPanel({
  documentId,
  session,
  currentUserId,
  onParticipantClick,
  onShareDocument,
  onClose,
  className = ''
}: CollaborationPanelProps) {
  const [showInviteDialog, setShowInviteDialog] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<PermissionRole>(PermissionRole.VIEWER)

  const getParticipantColor = (userId: string) => {
    const index = session?.participants.findIndex(p => p.userId === userId) || 0
    return PARTICIPANT_COLORS[index % PARTICIPANT_COLORS.length]
  }

  const getRoleIcon = (role: PermissionRole) => {
    switch (role) {
      case PermissionRole.OWNER:
      case PermissionRole.EDITOR:
        return PencilIcon
      case PermissionRole.REVIEWER:
      case PermissionRole.VIEWER:
        return EyeIcon
      default:
        return UserCircleIcon
    }
  }

  const getRoleColor = (role: PermissionRole) => {
    switch (role) {
      case PermissionRole.OWNER:
        return 'text-purple-600 bg-purple-100'
      case PermissionRole.EDITOR:
        return 'text-blue-600 bg-blue-100'
      case PermissionRole.REVIEWER:
        return 'text-orange-600 bg-orange-100'
      case PermissionRole.VIEWER:
        return 'text-gray-600 bg-gray-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const formatLastSeen = (lastSeen: string) => {
    const date = new Date(lastSeen)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
    
    return date.toLocaleDateString()
  }

  const handleInviteUser = () => {
    if (!inviteEmail.trim()) return
    
    // Here you would typically call an API to invite the user
    console.log('Inviting user:', inviteEmail, 'with role:', inviteRole)
    
    setInviteEmail('')
    setShowInviteDialog(false)
  }

  if (!session) {
    return (
      <div className={`w-64 bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
        <div className="text-center text-gray-500">
          <UserGroupIcon className="w-8 h-8 mx-auto mb-2" />
          <p className="text-sm">No active collaboration session</p>
          <Button 
            variant="primary" 
            size="sm" 
            className="mt-3"
            onClick={onShareDocument}
          >
            Start Collaboration
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className={`w-64 bg-white border border-gray-200 rounded-lg ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-gray-900 flex items-center">
            <UserGroupIcon className="w-4 h-4 mr-2" />
            Collaboration
          </h3>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              <XMarkIcon className="w-4 h-4" />
            </Button>
          )}
        </div>
        
        <div className="flex items-center space-x-2 text-xs text-gray-500">
          <div className="flex items-center">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
            {session.participants.filter(p => p.isOnline).length} online
          </div>
          <span>•</span>
          <span>{session.participants.length} total</span>
        </div>
      </div>

      {/* Participants List */}
      <div className="max-h-64 overflow-y-auto">
        <AnimatePresence>
          {session.participants.map((participant) => {
            const RoleIcon = getRoleIcon(participant.role)
            const isCurrentUser = participant.userId === currentUserId
            
            return (
              <motion.div
                key={participant.userId}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={`p-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                  isCurrentUser ? 'bg-blue-50' : ''
                }`}
                onClick={() => onParticipantClick?.(participant)}
              >
                <div className="flex items-center space-x-3">
                  {/* Avatar with Online Status */}
                  <div className="relative">
                    {participant.userAvatar ? (
                      <img
                        src={participant.userAvatar}
                        alt={participant.userName}
                        className="w-8 h-8 rounded-full"
                      />
                    ) : (
                      <div 
                        className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium"
                        style={{ backgroundColor: getParticipantColor(participant.userId) }}
                      >
                        {participant.userName.charAt(0).toUpperCase()}
                      </div>
                    )}
                    
                    {/* Online Status Indicator */}
                    <div className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white ${
                      participant.isOnline ? 'bg-green-500' : 'bg-gray-400'
                    }`} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {participant.userName}
                        {isCurrentUser && <span className="text-gray-500 ml-1">(You)</span>}
                      </p>
                      
                      {/* Role Badge */}
                      <div className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${getRoleColor(participant.role)}`}>
                        <RoleIcon className="w-3 h-3 mr-1" />
                        {participant.role}
                      </div>
                    </div>
                    
                    {/* Last Seen */}
                    <div className="flex items-center text-xs text-gray-500 mt-1">
                      <ClockIcon className="w-3 h-3 mr-1" />
                      {participant.isOnline ? (
                        <span className="text-green-600">Active now</span>
                      ) : (
                        formatLastSeen(participant.lastSeen)
                      )}
                    </div>
                  </div>
                </div>

                {/* Cursor Position Indicator */}
                {participant.isOnline && participant.cursor && (
                  <div className="mt-2 text-xs text-gray-500">
                    Viewing page {participant.cursor.page}
                  </div>
                )}
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>

      {/* Actions */}
      <div className="p-4 border-t border-gray-200 space-y-2">
        <Button
          variant="primary"
          size="sm"
          onClick={() => setShowInviteDialog(true)}
          className="w-full"
        >
          <ShareIcon className="w-4 h-4 mr-2" />
          Invite People
        </Button>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={onShareDocument}
          className="w-full"
        >
          Share Document
        </Button>
      </div>

      {/* Invite Dialog */}
      <AnimatePresence>
        {showInviteDialog && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setShowInviteDialog(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-lg p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Invite Collaborator
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="Enter email address"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Role
                  </label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as PermissionRole)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value={PermissionRole.VIEWER}>Viewer - Can view only</option>
                    <option value={PermissionRole.REVIEWER}>Reviewer - Can view and comment</option>
                    <option value={PermissionRole.EDITOR}>Editor - Can view, comment, and annotate</option>
                  </select>
                </div>
              </div>
              
              <div className="flex justify-end space-x-3 mt-6">
                <Button
                  variant="ghost"
                  onClick={() => setShowInviteDialog(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={handleInviteUser}
                  disabled={!inviteEmail.trim()}
                >
                  Send Invite
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Cursor component for showing other participants' cursors
export function ParticipantCursor({ 
  participant, 
  position 
}: { 
  participant: SessionParticipant
  position: CursorPosition 
}) {
  return (
    <div
      className="absolute pointer-events-none z-50"
      style={{
        left: position.x,
        top: position.y,
        transform: 'translate(-2px, -2px)'
      }}
    >
      <svg
        width="12"
        height="16"
        viewBox="0 0 12 16"
        fill="none"
        className="drop-shadow-md"
      >
        <path
          d="M0 0L0 10.5L3.5 7.5L5.5 11.5L7.5 10.5L5.5 6.5L9 5L0 0Z"
          fill={position.color}
          stroke="white"
          strokeWidth="0.5"
        />
      </svg>
      
      {/* User name label */}
      <div
        className="absolute top-4 left-2 text-xs text-white px-2 py-1 rounded whitespace-nowrap shadow-md"
        style={{ backgroundColor: position.color }}
      >
        {participant.userName}
      </div>
    </div>
  )
}