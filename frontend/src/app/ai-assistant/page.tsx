'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/Input';
import { API_CONFIG } from '../../config/api';
import {
  MessageCircle,
  Send,
  Bot,
  User,
  AlertTriangle,
  Loader2,
  BookOpen,
  Sparkles
} from 'lucide-react';
import { toast } from 'sonner';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatResponse {
  answer: string;
  suggested_questions: string[];
  session_id: string;
  message_count: number;
  educational_disclaimer: string;
}

export default function AIAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([
    "What are the different types of bankruptcy?",
    "How does the litigation process work?",
    "What is the difference between criminal and civil law?",
    "What are the key elements of a valid contract?"
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load session from localStorage on mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem('ai_assistant_session_id');
    const savedMessages = localStorage.getItem('ai_assistant_messages');

    if (savedSessionId) {
      setSessionId(savedSessionId);
    }

    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        setMessages(parsed.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp)
        })));
      } catch (error) {
        console.error('Failed to parse saved messages:', error);
      }
    }
  }, []);

  // Save session and messages to localStorage
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('ai_assistant_session_id', sessionId);
    }
    if (messages.length > 0) {
      localStorage.setItem('ai_assistant_messages', JSON.stringify(messages));
    }
  }, [sessionId, messages]);

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content: messageText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/qa/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          session_id: sessionId,
          user_id: 'demo_user' // TODO: Replace with actual user ID from auth
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response from AI assistant');
      }

      const data: ChatResponse = await response.json();

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      setSuggestedQuestions(data.suggested_questions);

      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }

    } catch (error: any) {
      console.error('Failed to send message:', error);
      toast.error('Failed to send message', {
        description: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputMessage);
  };

  const handleSuggestedQuestion = (question: string) => {
    sendMessage(question);
  };

  const clearConversation = () => {
    setMessages([]);
    setSessionId(null);
    setSuggestedQuestions([
      "What are the different types of bankruptcy?",
      "How does the litigation process work?",
      "What is the difference between criminal and civil law?",
      "What are the key elements of a valid contract?"
    ]);
    localStorage.removeItem('ai_assistant_session_id');
    localStorage.removeItem('ai_assistant_messages');
    toast.success('Conversation cleared');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <MessageCircle className="w-8 h-8 text-primary-600" />
                AI Legal Education Assistant
              </h1>
              <p className="text-gray-600 mt-2">
                Ask questions about legal concepts, processes, and topics for educational purposes
              </p>
            </div>
            {messages.length > 0 && (
              <Button
                variant="outline"
                onClick={clearConversation}
                className="text-gray-600 hover:text-gray-900"
              >
                Clear Conversation
              </Button>
            )}
          </div>
        </div>

        {/* Educational Disclaimer */}
        <Alert className="mb-6 bg-amber-50 border-amber-300">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertDescription>
            <strong>Educational Purpose Only:</strong> All information provided is for educational purposes and does not constitute legal advice.
            For specific legal matters, please consult a licensed attorney.
          </AlertDescription>
        </Alert>

        {/* Chat Container */}
        <Card className="mb-6">
          <CardContent className="p-0">
            {/* Messages Area */}
            <div className="h-[500px] overflow-y-auto p-6 space-y-4">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="p-4 bg-primary-50 rounded-full mb-4">
                    <Bot className="w-12 h-12 text-primary-600" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    Welcome to Your AI Legal Education Assistant
                  </h3>
                  <p className="text-gray-600 max-w-md mb-6">
                    Ask me anything about legal concepts, procedures, or topics. I'm here to help you learn!
                  </p>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <BookOpen className="w-4 h-4" />
                    <span>Try asking about bankruptcy types, litigation processes, or contract law</span>
                  </div>
                </div>
              )}

              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex gap-3 ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                        <Bot className="w-5 h-5 text-primary-600" />
                      </div>
                    </div>
                  )}

                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    <p className={`text-xs mt-2 ${
                      message.role === 'user' ? 'text-primary-100' : 'text-gray-500'
                    }`}>
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>

                  {message.role === 'user' && (
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center">
                        <User className="w-5 h-5 text-gray-600" />
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="flex gap-3 justify-start">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                      <Bot className="w-5 h-5 text-primary-600" />
                    </div>
                  </div>
                  <div className="bg-gray-100 rounded-lg px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-primary-600" />
                      <span className="text-sm text-gray-600">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Suggested Questions */}
            {suggestedQuestions.length > 0 && messages.length > 0 && !loading && (
              <div className="px-6 pb-4 border-t border-gray-200 pt-4">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-primary-600" />
                  <span className="text-sm font-medium text-gray-700">Suggested questions:</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {suggestedQuestions.map((question, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestedQuestion(question)}
                      className="text-sm px-3 py-2 bg-primary-50 text-primary-700 rounded-full hover:bg-primary-100 transition-colors border border-primary-200"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input Area */}
            <div className="border-t border-gray-200 p-4">
              <form onSubmit={handleSubmit} className="flex gap-3">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask a legal question for educational purposes..."
                  disabled={loading}
                  className="flex-1"
                />
                <Button
                  type="submit"
                  disabled={loading || !inputMessage.trim()}
                  className="px-6"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Send className="w-4 h-4 mr-2" />
                      Send
                    </>
                  )}
                </Button>
              </form>
            </div>
          </CardContent>
        </Card>

        {/* Example Questions */}
        {messages.length === 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <BookOpen className="w-5 h-5" />
                Example Questions to Get Started
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[
                  "What are the different types of bankruptcy?",
                  "How does the litigation process work?",
                  "What is the difference between criminal and civil law?",
                  "What are the key elements of a valid contract?",
                  "What is the difference between Chapter 7 and Chapter 13 bankruptcy?",
                  "How do I file a small claims case?",
                  "What are my rights during a traffic stop?",
                  "What is the statute of limitations?"
                ].map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestedQuestion(question)}
                    className="text-left p-3 bg-gray-50 hover:bg-primary-50 rounded-lg border border-gray-200 hover:border-primary-300 transition-colors text-sm text-gray-700 hover:text-primary-700"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
