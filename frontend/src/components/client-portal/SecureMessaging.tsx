'use client';

import React, { useState, useRef } from 'react';
import {
  MessageSquare,
  Send,
  AlertTriangle,
  Shield,
  Clock,
  Info,
  Scale,
  Lock,
  FileText,
  Paperclip,
  X,
  CheckCircle,
  ExternalLink,
  Calendar
} from 'lucide-react';

interface Message {
  id: string;
  sender: 'client' | 'attorney' | 'staff';
  senderName: string;
  content: string;
  timestamp: string;
  attachments?: Array<{
    id: string;
    name: string;
    size: string;
    type: string;
  }>;
  isPrivileged: boolean;
  status: 'sent' | 'delivered' | 'read';
}

interface SecureMessagingProps {
  className?: string;
}

const SecureMessaging: React.FC<SecureMessagingProps> = ({ className = '' }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: 'attorney',
      senderName: 'Sarah Johnson, Esq.',
      content: 'Thank you for your message. I\'ve reviewed the documents you provided. We\'ll discuss the next steps during our upcoming appointment.',
      timestamp: '2024-01-15T14:30:00Z',
      isPrivileged: true,
      status: 'read'
    },
    {
      id: '2',
      sender: 'staff',
      senderName: 'Legal Assistant - Maria',
      content: 'Hi John, this is a reminder that your deposition is scheduled for next Tuesday at 2:00 PM. Please arrive 15 minutes early. General information only.',
      timestamp: '2024-01-14T10:15:00Z',
      isPrivileged: false,
      status: 'read'
    }
  ]);

  const [newMessage, setNewMessage] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [showPrivilegeWarning, setShowPrivilegeWarning] = useState(true);
  const [messageType, setMessageType] = useState<'general' | 'urgent' | 'question'>('general');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSendMessage = () => {
    if (!newMessage.trim() && attachments.length === 0) return;

    const message: Message = {
      id: Date.now().toString(),
      sender: 'client',
      senderName: 'John Smith',
      content: newMessage,
      timestamp: new Date().toISOString(),
      attachments: attachments.map(file => ({
        id: Date.now().toString(),
        name: file.name,
        size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
        type: file.type
      })),
      isPrivileged: false,
      status: 'sent'
    };

    setMessages(prev => [...prev, message]);
    setNewMessage('');
    setAttachments([]);
  };

  const handleFileAttach = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setAttachments(prev => [...prev, ...files]);
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'sent':
        return <Clock className="h-3 w-3 text-gray-400" />;
      case 'delivered':
        return <CheckCircle className="h-3 w-3 text-blue-500" />;
      case 'read':
        return <CheckCircle className="h-3 w-3 text-success-500" />;
      default:
        return <Clock className="h-3 w-3 text-gray-400" />;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <MessageSquare className="h-5 w-5 text-primary-600" />
          <h3 className="text-lg font-medium text-gray-900">Secure Messaging</h3>
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <Shield className="h-3 w-3 mr-1" />
            Encrypted
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <Info className="h-3 w-3 mr-1" />
            Information Only
          </span>
        </div>
      </div>

      {/* Privilege Warning Banner */}
      {showPrivilegeWarning && (
        <div className="p-4 bg-error-50 border-b border-error-200">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-error-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-error-900 mb-1">
                Attorney-Client Privilege Notice - Read Carefully
              </h4>
              <div className="text-sm text-error-800 space-y-1">
                <p>
                  <strong>Important:</strong> Communications through this portal may NOT create or maintain attorney-client privilege 
                  unless you already have a signed representation agreement with this law firm.
                </p>
                <p>
                  <strong>For Privileged Communications:</strong> Contact your attorney directly by phone or schedule an in-person meeting.
                </p>
                <p>
                  <strong>Emergency Situations:</strong> Do not use this messaging system for urgent legal matters. Call the office directly.
                </p>
              </div>
              <button
                onClick={() => setShowPrivilegeWarning(false)}
                className="mt-2 text-xs text-error-700 hover:text-error-800 font-medium underline"
              >
                I understand - Continue with non-privileged messaging
              </button>
            </div>
            <button
              onClick={() => setShowPrivilegeWarning(false)}
              className="text-error-400 hover:text-error-600"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="h-96 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'client' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-xs lg:max-w-md ${
              message.sender === 'client' 
                ? 'bg-primary-600 text-white' 
                : 'bg-gray-100 text-gray-900'
            } rounded-lg p-3`}>
              
              {/* Message Header */}
              <div className={`flex items-center justify-between mb-1 ${
                message.sender === 'client' ? 'text-primary-200' : 'text-gray-600'
              }`}>
                <span className="text-xs font-medium">{message.senderName}</span>
                <div className="flex items-center space-x-1">
                  {message.isPrivileged && (
                    <span title="Privileged Communication">
                      <Lock className="h-3 w-3" />
                    </span>
                  )}
                  {getStatusIcon(message.status)}
                </div>
              </div>
              
              {/* Message Content */}
              <p className="text-sm">{message.content}</p>
              
              {/* Attachments */}
              {message.attachments && message.attachments.length > 0 && (
                <div className="mt-2 space-y-1">
                  {message.attachments.map((attachment) => (
                    <div key={attachment.id} className={`flex items-center space-x-2 text-xs ${
                      message.sender === 'client' ? 'text-primary-200' : 'text-gray-600'
                    }`}>
                      <Paperclip className="h-3 w-3" />
                      <span>{attachment.name} ({attachment.size})</span>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Timestamp */}
              <div className={`text-xs mt-2 ${
                message.sender === 'client' ? 'text-primary-200' : 'text-gray-500'
              }`}>
                {formatTimestamp(message.timestamp)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Message Input Area */}
      <div className="border-t border-gray-200 p-4">
        {/* Message Type Selector */}
        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-2">Message Type</label>
          <div className="flex space-x-3">
            {[
              { key: 'general', label: 'General Question', icon: MessageSquare },
              { key: 'question', label: 'Case Question', icon: FileText },
              { key: 'urgent', label: 'Time-Sensitive', icon: AlertTriangle }
            ].map((type) => (
              <button
                key={type.key}
                onClick={() => setMessageType(type.key as any)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  messageType === type.key
                    ? 'bg-primary-100 text-primary-800 border border-primary-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <type.icon className="h-4 w-4" />
                <span>{type.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Attachments Preview */}
        {attachments.length > 0 && (
          <div className="mb-3 space-y-2">
            <label className="block text-sm font-medium text-gray-700">Attachments</label>
            {attachments.map((file, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded border">
                <div className="flex items-center space-x-2">
                  <Paperclip className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-700">{file.name}</span>
                  <span className="text-xs text-gray-500">({(file.size / 1024 / 1024).toFixed(1)} MB)</span>
                </div>
                <button
                  onClick={() => removeAttachment(index)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Message Input */}
        <div className="flex items-end space-x-2">
          <div className="flex-1">
            <textarea
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Type your non-privileged message here..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              rows={3}
            />
          </div>
          
          <div className="flex flex-col space-y-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2 text-gray-500 hover:text-gray-700 border border-gray-300 rounded-lg"
              title="Attach file"
            >
              <Paperclip className="h-4 w-4" />
            </button>
            
            <button
              onClick={handleSendMessage}
              disabled={!newMessage.trim() && attachments.length === 0}
              className="p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileAttach}
          className="hidden"
          accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.txt"
        />

        {/* Message Guidelines */}
        <div className="mt-3 space-y-2">
          {messageType === 'urgent' && (
            <div className="bg-error-50 border border-error-200 rounded-lg p-3">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="h-4 w-4 text-error-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm font-semibold text-error-900 mb-1">Urgent Matters</h5>
                  <p className="text-sm text-error-700">
                    For truly urgent legal matters, please call the office directly rather than using this messaging system. 
                    This system is not monitored 24/7.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-start space-x-2">
              <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <div>
                <h5 className="text-sm font-semibold text-blue-900 mb-1">Messaging Guidelines</h5>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Use this for non-urgent questions and general communication</li>
                  <li>• Response time is typically 1-2 business days</li>
                  <li>• Do not include sensitive personal information</li>
                  <li>• For legal advice, schedule a consultation</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer with Links */}
      <div className="border-t border-gray-200 p-4 bg-gray-50">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-4">
            <a 
              href="/client-portal/scheduling" 
              className="text-primary-600 hover:text-primary-700 font-medium flex items-center"
            >
              <Calendar className="h-4 w-4 mr-1" />
              Schedule Consultation
            </a>
            <a 
              href="/emergency-contact" 
              className="text-error-600 hover:text-error-700 font-medium flex items-center"
            >
              <AlertTriangle className="h-4 w-4 mr-1" />
              Emergency Contact
            </a>
          </div>
          
          <div className="text-gray-500">
            <Lock className="h-4 w-4 inline mr-1" />
            Messages are encrypted
          </div>
        </div>
      </div>

      {/* Legal Disclaimer */}
      <div className="border-t border-legal-200 p-4 bg-legal-50">
        <div className="flex items-start space-x-2">
          <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
          <div>
            <h5 className="text-sm font-semibold text-legal-900 mb-1">Communication Disclaimer</h5>
            <p className="text-xs text-legal-700">
              This messaging system is for general communication only. Messages may not be protected by attorney-client privilege 
              unless you have a signed representation agreement. Do not send confidential information through this system. 
              For privileged communications, contact your attorney directly.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SecureMessaging;