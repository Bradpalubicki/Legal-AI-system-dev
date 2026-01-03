'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Upload, MessageSquare, Shield, FolderOpen, FileText, Scale } from 'lucide-react';
import { Card, Badge } from '@/components/design-system';
import { DocumentProvider, useDocuments } from '@/contexts/DocumentContext';
import { DocumentsTab } from '@/components/Documents/DocumentsTab';
import { ConversationalDefenseBuilder } from '@/components/Defense';
import { QASection } from '@/components/QASection';
import { EnhancedCaseTracker } from '@/components/CaseTracking/EnhancedCaseTracker';
import Toolbar from '@/components/layout/Toolbar';
import { GuidedTour } from '@/components/GuidedTour';
import { TabInfoButton } from '@/components/TabInfoButton';
import dynamic from 'next/dynamic';
import { useSearchParams } from 'next/navigation';

// Dynamically import PACER component to avoid SSR issues
const PACERIntegration = dynamic(() => import('@/components/PACER/PACERIntegration'), { ssr: false });

type MainTab = 'documents' | 'qa' | 'defense' | 'cases' | 'pacer';

interface ChatMessage {
  id: string;
  role: 'ai' | 'user';
  content: string;
  timestamp: Date;
  followUpQuestion?: string;
}

interface DefenseMessage {
  id: string;
  role: 'ai' | 'user';
  content: string;
  timestamp: Date;
}

function LegalAIHubContent() {
  const searchParams = useSearchParams();
  const tabParam = searchParams.get('tab') as MainTab | null;

  // Set initial tab from URL parameter, default to 'documents'
  const [activeTab, setActiveTab] = useState<MainTab>(
    tabParam && ['documents', 'qa', 'defense', 'cases', 'pacer'].includes(tabParam)
      ? tabParam
      : 'documents'
  );

  // Update tab when URL parameter changes
  useEffect(() => {
    if (tabParam && ['documents', 'qa', 'defense', 'cases', 'pacer'].includes(tabParam)) {
      setActiveTab(tabParam);
    }
  }, [tabParam]);
  const [sessionId] = useState(() => crypto.randomUUID());
  const { currentDocument, documents } = useDocuments();

  // Persist Q&A chat history
  const [qaMessages, setQaMessages] = useState<ChatMessage[]>([]);

  // Persist Defense Builder chat history
  const [defenseMessages, setDefenseMessages] = useState<DefenseMessage[]>([]);
  const [defenseCollectedAnswers, setDefenseCollectedAnswers] = useState<string[]>([]);
  const [defenseConversationPhase, setDefenseConversationPhase] = useState<'intro' | 'questions' | 'analysis' | 'complete'>('intro');
  const [defenseAnalysis, setDefenseAnalysis] = useState<any | null>(null);

  // Guided tour state
  const [showTour, setShowTour] = useState(false);

  // Check if user has seen the tour (auto-show on first login)
  useEffect(() => {
    const hasSeenTour = localStorage.getItem('hasSeenGuidedTour');
    if (!hasSeenTour) {
      // Small delay to let the UI render first
      const timer = setTimeout(() => {
        setShowTour(true);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, []);

  // Listen for manual tour restart from Toolbar
  useEffect(() => {
    const handleRestartTour = () => {
      setShowTour(true);
    };
    window.addEventListener('restartGuidedTour', handleRestartTour);
    return () => window.removeEventListener('restartGuidedTour', handleRestartTour);
  }, []);

  // Handle tour tab changes
  const handleTourTabChange = useCallback((tabId: string) => {
    if (['documents', 'qa', 'defense', 'cases', 'pacer'].includes(tabId)) {
      setActiveTab(tabId as MainTab);
    }
  }, []);

  // Handle tour completion
  const handleTourComplete = useCallback(() => {
    localStorage.setItem('hasSeenGuidedTour', 'true');
  }, []);

  // Handle tour close (also marks as seen)
  const handleTourClose = useCallback(() => {
    setShowTour(false);
    localStorage.setItem('hasSeenGuidedTour', 'true');
  }, []);

  return (
    <div className="legal-ai-hub min-h-screen" style={{ backgroundColor: '#f1f5f9' }}>
      {/* Header */}
      <div style={{ backgroundColor: '#1a365d' }} className="shadow-lg">
        {/* Top Toolbar */}
        <div style={{ backgroundColor: '#0f172a', borderBottom: '1px solid #334155' }}>
          <div className="max-w-content mx-auto px-6 py-2">
            <div className="flex items-center justify-end">
              <Toolbar />
            </div>
          </div>
        </div>

        {/* Main Header */}
        <div className="max-w-content mx-auto px-6 py-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
                <div style={{ backgroundColor: '#0d9488' }} className="p-2 rounded-lg">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                Legal AI Defense System
              </h1>
              <p style={{ color: '#cbd5e1' }}>
                AI-powered legal document analysis, defense building, and case management
              </p>
              {currentDocument && (
                <div className="mt-3">
                  <Badge variant="success" size="sm">
                    <FileText className="w-3 h-3" />
                    Active: {currentDocument.fileName}
                  </Badge>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

      {/* Navigation Tabs - White background below dark header */}
      <div className="bg-white dark:bg-slate-800 shadow-md border-b border-slate-200 dark:border-slate-700">
        <div className="max-w-content mx-auto px-6">
          <div className="flex space-x-1">
            <button
              data-tour="documents-tab"
              onClick={() => setActiveTab('documents')}
              className={`flex items-center gap-2 px-5 py-4 font-medium transition-all duration-200 border-b-[3px] ${
                activeTab === 'documents'
                  ? 'text-navy-800 dark:text-teal-300 bg-teal-50 dark:bg-teal-900/30 border-teal-500 dark:border-teal-400'
                  : 'text-slate-500 dark:text-slate-400 bg-transparent border-transparent hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>Documents</span>
              {documents.length > 0 && (
                <span className="ml-1 px-2 py-0.5 text-white text-xs rounded-full bg-navy-800 dark:bg-teal-600">
                  {documents.length}
                </span>
              )}
            </button>

            <button
              data-tour="qa-tab"
              onClick={() => setActiveTab('qa')}
              className={`flex items-center gap-2 px-5 py-4 font-medium transition-all duration-200 border-b-[3px] ${
                activeTab === 'qa'
                  ? 'text-navy-800 dark:text-teal-300 bg-teal-50 dark:bg-teal-900/30 border-teal-500 dark:border-teal-400'
                  : 'text-slate-500 dark:text-slate-400 bg-transparent border-transparent hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>Q&A Assistant</span>
            </button>

            <button
              data-tour="defense-tab"
              onClick={() => setActiveTab('defense')}
              className={`flex items-center gap-2 px-5 py-4 font-medium transition-all duration-200 border-b-[3px] ${!currentDocument ? 'opacity-50' : ''} ${
                activeTab === 'defense'
                  ? 'text-navy-800 dark:text-teal-300 bg-teal-50 dark:bg-teal-900/30 border-teal-500 dark:border-teal-400'
                  : 'text-slate-500 dark:text-slate-400 bg-transparent border-transparent hover:text-slate-700 dark:hover:text-slate-300'
              }`}
              disabled={!currentDocument}
            >
              <Shield className="w-4 h-4" />
              <span>Defense Builder</span>
              {!currentDocument && (
                <span className="ml-2 text-xs text-slate-400 dark:text-slate-500">(Upload doc first)</span>
              )}
            </button>

            <button
              data-tour="cases-tab"
              onClick={() => setActiveTab('cases')}
              className={`flex items-center gap-2 px-5 py-4 font-medium transition-all duration-200 border-b-[3px] ${
                activeTab === 'cases'
                  ? 'text-navy-800 dark:text-teal-300 bg-teal-50 dark:bg-teal-900/30 border-teal-500 dark:border-teal-400'
                  : 'text-slate-500 dark:text-slate-400 bg-transparent border-transparent hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <FolderOpen className="w-4 h-4" />
              <span>Case Tracking</span>
            </button>

            <button
              data-tour="pacer-tab"
              onClick={() => setActiveTab('pacer')}
              className={`flex items-center gap-2 px-5 py-4 font-medium transition-all duration-200 border-b-[3px] ${
                activeTab === 'pacer'
                  ? 'text-navy-800 dark:text-teal-300 bg-teal-50 dark:bg-teal-900/30 border-teal-500 dark:border-teal-400'
                  : 'text-slate-500 dark:text-slate-400 bg-transparent border-transparent hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <Scale className="w-4 h-4" />
              <span>PACER Search</span>
            </button>
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-content mx-auto px-6 py-8">
        {activeTab === 'documents' && (
          <div className="documents-tab">
            <div className="mb-6 p-4 rounded-lg relative" style={{ backgroundColor: '#f8fafc', borderLeft: '4px solid #0d9488' }}>
              <TabInfoButton tabId="documents" className="absolute top-2 right-2" />
              <h3 className="font-semibold mb-1" style={{ color: '#1a365d' }}>Document Upload & Analysis</h3>
              <p className="text-sm" style={{ color: '#475569' }}>
                Upload your legal documents to analyze them. The system will extract parties, dates, key figures,
                and keywords. Documents are saved and can be used in Q&A and Defense Builder.
              </p>
            </div>
            <DocumentsTab />
          </div>
        )}

        {activeTab === 'qa' && (
          <div className="qa-tab">
            <div className="mb-6 p-4 rounded-lg relative" style={{ backgroundColor: '#f0fdfa', borderLeft: '4px solid #0d9488' }}>
              <TabInfoButton tabId="qa" className="absolute top-2 right-2" />
              <h3 className="font-semibold mb-1" style={{ color: '#1a365d' }}>Interactive Q&A</h3>
              <p className="text-sm" style={{ color: '#475569' }}>
                {currentDocument
                  ? 'Ask questions about your legal situation and get immediate AI-powered answers based on your uploaded document.'
                  : 'Ask general legal questions and get AI-powered guidance. For document-specific analysis, upload a document first.'}
              </p>
            </div>
            <QASection
              documentContext={currentDocument?.text}
              sessionId={sessionId}
              documentId={currentDocument?.id}
              messages={qaMessages}
              onMessagesChange={setQaMessages}
            />
          </div>
        )}

        {activeTab === 'defense' && (
          <div className="defense-tab">
            {currentDocument ? (
              <>
                <div className="mb-6 p-4 rounded-lg relative" style={{ backgroundColor: '#f8fafc', borderLeft: '4px solid #0d9488' }}>
                  <TabInfoButton tabId="defense" className="absolute top-2 right-2" />
                  <h3 className="font-semibold mb-1" style={{ color: '#1a365d' }}>AI Defense Builder</h3>
                  <p className="text-sm" style={{ color: '#475569' }}>
                    Our AI will have a conversation with you about your case, asking relevant questions
                    based on your document. Then it will build a comprehensive defense strategy.
                  </p>
                </div>
                <ConversationalDefenseBuilder
                  document={currentDocument}
                  sessionId={sessionId}
                  messages={defenseMessages}
                  onMessagesChange={setDefenseMessages}
                  collectedAnswers={defenseCollectedAnswers}
                  onCollectedAnswersChange={setDefenseCollectedAnswers}
                  conversationPhase={defenseConversationPhase}
                  onConversationPhaseChange={setDefenseConversationPhase}
                  defenseAnalysis={defenseAnalysis}
                  onDefenseAnalysisChange={setDefenseAnalysis}
                />
              </>
            ) : (
              <Card className="p-12 text-center">
                <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-8 h-8 text-slate-400" />
                </div>
                <p className="text-navy-800 text-lg font-semibold mb-2">No document selected</p>
                <p className="text-slate-500 text-sm mb-6">
                  Upload a document in the Documents tab first
                </p>
                <button
                  onClick={() => setActiveTab('documents')}
                  className="px-6 py-3 text-white rounded-lg transition-colors duration-200 font-medium"
                  style={{ backgroundColor: '#1a365d' }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#0f172a'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#1a365d'}
                >
                  Go to Documents
                </button>
              </Card>
            )}
          </div>
        )}

        {activeTab === 'cases' && (
          <div className="cases-tab">
            <div className="mb-6 p-4 rounded-lg shadow-sm relative" style={{ backgroundColor: '#f8fafc', borderLeft: '4px solid #1a365d' }}>
              <TabInfoButton tabId="cases" className="absolute top-2 right-2" />
              <h3 className="font-semibold mb-1" style={{ color: '#1a365d' }}>Case Tracking & Management</h3>
              <p className="text-sm" style={{ color: '#475569' }}>
                Track all your legal cases in one place. Monitor case progress, deadlines, and documents.
              </p>
            </div>
            <EnhancedCaseTracker />
          </div>
        )}

        {activeTab === 'pacer' && (
          <div className="pacer-tab">
            <div className="mb-6 p-4 rounded-lg shadow-sm relative" style={{ backgroundColor: '#f8fafc', borderLeft: '4px solid #1a365d' }}>
              <TabInfoButton tabId="pacer" className="absolute top-2 right-2" />
              <h3 className="font-semibold mb-1" style={{ color: '#1a365d' }}>PACER Federal Court Access</h3>
              <p className="text-sm" style={{ color: '#475569' }}>
                Connect to PACER (Public Access to Court Electronic Records) to search federal court cases,
                download documents, and track federal court filings across all bankruptcy, district, and circuit courts.
              </p>
            </div>
            <PACERIntegration />
          </div>
        )}
      </div>

      {/* Educational Footer */}
      <div className="max-w-content mx-auto px-6 pb-8">
        <div className="rounded-lg p-4" style={{ backgroundColor: '#fef3c7', border: '1px solid #fcd34d' }}>
          <p className="text-sm" style={{ color: '#92400e' }}>
            <strong>EDUCATIONAL CONTENT DISCLAIMER:</strong> All information provided by this system is for
            educational purposes only and does not constitute legal advice. This platform is designed for
            informational purposes and learning about legal processes, not for providing professional legal counsel.
            Always consult with a qualified attorney for legal advice specific to your situation.
          </p>
        </div>
      </div>

      {/* Guided Tour */}
      <GuidedTour
        isOpen={showTour}
        onClose={handleTourClose}
        onComplete={handleTourComplete}
        onTabChange={handleTourTabChange}
      />
    </div>
  );
}

export function LegalAIHub() {
  return (
    <DocumentProvider>
      <LegalAIHubContent />
    </DocumentProvider>
  );
}
