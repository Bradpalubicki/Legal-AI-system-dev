'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/Input';
import { API_CONFIG } from '../config/api';
import {
  HelpCircle,
  X,
  Send,
  Minimize2,
  Maximize2,
  Sparkles,
  MessageCircle
} from 'lucide-react';
import { usePathname } from 'next/navigation';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || API_CONFIG.BASE_URL;

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function HelpAgent() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [quickTips, setQuickTips] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get current page name for context
  const getCurrentPage = () => {
    if (pathname === '/') return 'documents';
    if (pathname.includes('credits')) return 'credits';
    if (pathname.includes('pacer')) return 'pacer';
    if (pathname.includes('cases')) return 'cases';
    if (pathname.includes('clients')) return 'clients';
    if (pathname.includes('research')) return 'research';
    if (pathname.includes('dashboard')) return 'dashboard';

    // Check for tab parameter
    const params = new URLSearchParams(window.location.search);
    const tab = params.get('tab');
    if (tab) return tab;

    return 'home';
  };

  // Fetch quick tips when page changes
  useEffect(() => {
    fetchQuickTips();
  }, [pathname]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Add welcome message when first opened
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([{
        role: 'assistant',
        content: "👋 Hi! I'm your AI assistant. I can help you navigate the Legal AI System, answer questions about features, and guide you through any workflows. What would you like to know?",
        timestamp: new Date()
      }]);
    }
  }, [isOpen]);

  // Listen for custom event to open help from toolbar
  useEffect(() => {
    const handleOpenHelp = () => {
      setIsOpen(true);
      setIsMinimized(false);
    };

    window.addEventListener('openHelpAgent', handleOpenHelp);
    return () => window.removeEventListener('openHelpAgent', handleOpenHelp);
  }, []);

  const fetchQuickTips = async () => {
    try {
      const page = getCurrentPage();
      const response = await fetch(`${API_BASE_URL}/api/v1/help/quick-tips?page=${page}`);
      if (response.ok) {
        const data = await response.json();
        setQuickTips(data.tips || []);
      }
    } catch (error) {
      console.error('Error fetching quick tips:', error);
    }
  };

  const sendMessage = async (messageText?: string) => {
    const questionText = messageText || input.trim();
    if (!questionText) return;

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: questionText,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const currentPage = getCurrentPage();
      const token = localStorage.getItem('accessToken') || localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/api/v1/help/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          question: questionText,
          current_page: currentPage,
          context: {
            pathname: pathname,
            url: window.location.href
          },
          chat_history: messages.map(m => ({
            role: m.role,
            content: m.content
          }))
        })
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.answer,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error('Failed to get response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: "I'm sorry, I encountered an error. Please try again or contact support if the problem persists.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([{
      role: 'assistant',
      content: "Chat cleared. How can I help you?",
      timestamp: new Date()
    }]);
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-teal-600 hover:bg-teal-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-110 z-50"
        title="Get Help"
      >
        <HelpCircle className="w-6 h-6" />
      </button>
    );
  }

  return (
    <div
      className={`fixed bottom-6 right-6 bg-white rounded-lg shadow-2xl z-50 flex flex-col transition-all ${
        isMinimized ? 'w-80 h-14' : 'w-96 h-[600px]'
      }`}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 rounded-t-lg flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5" />
          <span className="font-semibold">AI Help Assistant</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 hover:bg-white/20 rounded transition-colors"
            title={isMinimized ? 'Maximize' : 'Minimize'}
          >
            {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-white/20 rounded transition-colors"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Quick Tips */}
          {quickTips.length > 0 && messages.length <= 1 && (
            <div className="p-3 bg-teal-50 border-b border-blue-100">
              <div className="text-xs font-medium text-navy-800 mb-2">Quick Tips:</div>
              <div className="space-y-1">
                {quickTips.slice(0, 3).map((tip, idx) => (
                  <div key={idx} className="text-xs text-blue-800">
                    {tip}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message, idx) => (
              <div
                key={idx}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-teal-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                  <div
                    className={`text-xs mt-1 ${
                      message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-gray-600">
                    <MessageCircle className="w-4 h-4 animate-pulse" />
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Questions */}
          {messages.length <= 1 && (
            <div className="px-4 pb-2 space-y-1">
              <div className="text-xs text-gray-500 mb-2">Try asking:</div>
              <button
                onClick={() => sendMessage("How do I upload documents?")}
                className="text-xs text-left w-full p-2 bg-gray-50 hover:bg-gray-100 rounded border border-gray-200 transition-colors"
              >
                "How do I upload documents?"
              </button>
              <button
                onClick={() => sendMessage("What can I do with PACER Search?")}
                className="text-xs text-left w-full p-2 bg-gray-50 hover:bg-gray-100 rounded border border-gray-200 transition-colors"
              >
                "What can I do with PACER Search?"
              </button>
            </div>
          )}

          {/* Input */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything..."
                disabled={isLoading}
                className="flex-1"
              />
              <Button
                onClick={() => sendMessage()}
                disabled={!input.trim() || isLoading}
                size="sm"
                className="bg-teal-600 hover:bg-teal-700"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            {messages.length > 2 && (
              <button
                onClick={clearChat}
                className="text-xs text-gray-500 hover:text-gray-700 mt-2"
              >
                Clear chat
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
