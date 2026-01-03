import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, Send, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';

import { API_CONFIG } from '../config/api';
export interface Message {
  id: string;
  role: 'ai' | 'user';
  content: string;
  timestamp: Date;
}

interface QASectionProps {
  documentContext?: string;
  sessionId: string;
  documentId?: string;  // For linking Q&A to document in database
  messages: Message[];
  onMessagesChange: (messages: Message[]) => void;
}

export function QASection({ documentContext, sessionId, documentId, messages, onMessagesChange }: QASectionProps) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([
    'What is the jurisdictional basis and procedural deadline for filing a responsive pleading?',
    'Analyze the damages calculation: What is the legal basis for the claimed amount and what defenses exist to each component?',
    'Identify each cause of action alleged and assess the elements the plaintiff must prove for each claim.',
    'What documentary evidence has been produced, and what evidentiary gaps or weaknesses exist in the opposing party\'s case?',
    'Analyze the parties\' legal standing: Does the plaintiff have proper authority to bring this action?',
    'What affirmative defenses or procedural challenges are available based on this pleading?'
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const prevMessageCountRef = useRef<number>(0);
  const isInitialMountRef = useRef<boolean>(true);

  // Auto-scroll to bottom only when new messages are added (not on initial load/tab switch)
  useEffect(() => {
    // Skip scroll on initial mount or when loading history
    if (isInitialMountRef.current) {
      isInitialMountRef.current = false;
      prevMessageCountRef.current = messages.length;
      return;
    }

    // Only scroll if message count increased by 1 or 2 (typical for user sending + AI response)
    // This prevents scroll when history loads (which adds many messages at once)
    const messageIncrease = messages.length - prevMessageCountRef.current;
    if (messageIncrease > 0 && messageIncrease <= 2) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    prevMessageCountRef.current = messages.length;
  }, [messages]);

  // Load Q&A history from database on mount
  useEffect(() => {
    const loadHistory = async () => {
      if (historyLoaded || !sessionId) return;

      try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/qa/conversation/${sessionId}`);
        if (response.ok) {
          const data = await response.json();
          if (data.conversation && data.conversation.length > 0) {
            const loadedMessages: Message[] = data.conversation.map((qa: any) => [
              {
                id: crypto.randomUUID(),
                role: 'user' as const,
                content: qa.question,
                timestamp: new Date(qa.timestamp)
              },
              {
                id: crypto.randomUUID(),
                role: 'ai' as const,
                content: qa.answer,
                timestamp: new Date(qa.timestamp)
              }
            ]).flat();

            onMessagesChange(loadedMessages);
            console.log(`Loaded ${data.conversation.length} Q&A exchanges from database`);
          }
        } else if (response.status === 404) {
          // No history found - this is fine for new sessions
          console.log('No previous conversation history found - starting fresh');
        }
      } catch (error) {
        console.error('Error loading Q&A history:', error);
      } finally {
        setHistoryLoaded(true);
      }
    };

    loadHistory();
  }, [sessionId, historyLoaded]);

  // Welcome message on mount (only if no messages exist and history loaded)
  useEffect(() => {
    if (messages.length === 0 && historyLoaded) {
      const welcomeMessage: Message = {
        id: crypto.randomUUID(),
        role: 'ai',
        content: documentContext
          ? `Good day. I've completed a preliminary review of your document. As your legal counsel, I'm prepared to address any questions regarding procedural deadlines, substantive claims, evidentiary issues, or strategic considerations.\n\nI will provide precise legal analysis with citations to specific provisions in your document. Please proceed with your inquiry.`
          : `Good day. I'm Senior Legal Counsel available for consultation. While I recommend uploading relevant legal documents for thorough analysis, I can provide general legal guidance on procedural questions, substantive law, and strategic considerations.\n\nPlease state your legal question or concern.`,
        timestamp: new Date()
      };
      onMessagesChange([welcomeMessage]);
    }
  }, [documentContext, historyLoaded]);

  const askQuestion = async () => {
    if (!question.trim() || loading) return;

    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question.trim(),
      timestamp: new Date()
    };

    onMessagesChange([...messages, userMessage]);
    setQuestion('');
    setLoading(true);

    try {
      // Call Q&A endpoint with document context
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/qa/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_text: documentContext || '',
          document_analysis: {
            document_type: 'Legal Document',
            summary: 'Document analysis'
          },
          question: question.trim(),
          session_id: sessionId,
          document_id: documentId  // For database persistence
        })
      });

      if (response.ok) {
        const data = await response.json();

        // DEBUG: Log what we received
        console.log('=== FRONTEND RECEIVED ===');
        console.log('Answer length:', data.answer?.length || 0, 'chars');
        console.log('Answer preview:', data.answer?.substring(0, 200));
        console.log('Answer end:', data.answer?.substring(data.answer.length - 200));
        console.log('========================');

        // Update suggested questions if provided by backend
        if (data.suggested_questions && Array.isArray(data.suggested_questions) && data.suggested_questions.length > 0) {
          setSuggestedQuestions(data.suggested_questions);
        }

        // Add AI response
        const aiMessage: Message = {
          id: crypto.randomUUID(),
          role: 'ai',
          content: data.answer || data.response || 'I need more information to answer that question.',
          timestamp: new Date()
        };

        const updatedMessages = [...messages, userMessage, aiMessage];
        onMessagesChange(updatedMessages);

        toast.success('Answer received', {
          description: 'AI has analyzed your question',
          duration: 2000,
        });
      } else {
        // Fallback answer
        const errorMessage: Message = {
          id: crypto.randomUUID(),
          role: 'ai',
          content: 'I encountered an issue. Could you rephrase your question or provide more details?',
          timestamp: new Date()
        };
        onMessagesChange([...messages, userMessage, errorMessage]);

        toast.error('Failed to get answer', {
          description: 'Please try rephrasing your question',
          duration: 4000,
        });
      }

    } catch (error) {
      console.error('Q&A Error:', error);
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: 'ai',
        content: 'I apologize, but I encountered an error. Please try asking your question again.',
        timestamp: new Date()
      };
      onMessagesChange([...messages, userMessage, errorMessage]);

      toast.error('Connection error', {
        description: 'Could not reach the AI service. Please try again.',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  };

  return (
    <div className="qa-section space-y-6">
      {/* Conversational Chat Interface */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-navy-800 flex items-center gap-2">
            <MessageSquare className="w-6 h-6 text-teal-600" />
            AI Q&A Assistant
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            Ask questions and get intelligent answers with follow-ups
          </p>
        </div>

        {/* Chat Messages */}
        <div className="bg-slate-50 rounded-lg p-4 mb-4 h-96 overflow-y-auto space-y-4">
          {!historyLoaded && (
            <div className="space-y-4">
              {/* Loading skeleton for messages */}
              <div className="flex justify-start">
                <div className="max-w-[85%] bg-white border border-slate-200 rounded-lg p-4">
                  <Skeleton count={2} />
                </div>
              </div>
              <div className="flex justify-end">
                <div className="max-w-[85%] bg-teal-100 rounded-lg p-4">
                  <Skeleton count={1} />
                </div>
              </div>
              <div className="flex justify-start">
                <div className="max-w-[85%] bg-white border border-slate-200 rounded-lg p-4">
                  <Skeleton count={3} />
                </div>
              </div>
            </div>
          )}

          {historyLoaded && messages.map(message => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'bg-teal-600 text-white'
                    : 'bg-white border border-slate-200 text-navy-800'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-blue-100' : 'text-slate-500'}`}>
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-teal-600" />
                <p className="text-sm text-slate-600">AI is thinking...</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Questions - Always Visible */}
        <div className="suggested-questions mb-4 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <MessageSquare className="w-5 h-5 text-purple-600" />
            <p className="text-sm font-bold text-purple-900">Suggested Questions</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((q, i) => (
              <button
                key={i}
                onClick={() => setQuestion(q)}
                disabled={loading}
                className="px-3 py-2 text-xs bg-white hover:bg-purple-100 disabled:bg-slate-50 text-navy-800 rounded-lg border border-purple-200 transition-all hover:shadow-sm disabled:cursor-not-allowed"
              >
                {q}
              </button>
            ))}
          </div>
          <p className="text-xs text-purple-700 mt-3 italic">
            💡 Click any question to ask it, or type your own below. Questions update based on your conversation.
          </p>
        </div>

        {/* Input Area */}
        <div className="flex gap-2">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type your question here... (Press Enter to send, Shift+Enter for new line)"
            className="flex-1 p-3 border border-slate-300 rounded-lg resize-none focus:ring-2 focus:ring-teal-500 focus:border-transparent disabled:bg-slate-100"
            rows={3}
            disabled={loading}
          />
          <button
            onClick={askQuestion}
            disabled={!question.trim() || loading}
            className="px-6 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send className="w-5 h-5" />
            Send
          </button>
        </div>

        {/* Info Box */}
        <div className="mt-4 bg-teal-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-navy-800">
            💬 <strong>Agent Mode:</strong> The AI will ask follow-up questions to better understand your situation and provide more accurate guidance.
          </p>
        </div>
      </div>
    </div>
  );
}
