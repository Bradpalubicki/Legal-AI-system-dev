'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Upload, MessageSquare, Shield, CheckCircle, FileText } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

import { API_CONFIG } from '../config/api';
interface Message {
  type: 'agent' | 'user' | 'system';
  content: string;
  timestamp: Date;
}

type Tab = 'upload' | 'interview' | 'defense';

export function UnifiedDefenseBuilder() {
  const [sessionId] = useState(() => crypto.randomUUID());
  const [activeTab, setActiveTab] = useState<Tab>('upload');
  const [documentData, setDocumentData] = useState<any>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [textAnswer, setTextAnswer] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [strategy, setStrategy] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [supportingDocs, setSupportingDocs] = useState<any[]>([]);
  const [interviewComplete, setInterviewComplete] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const supportingDocsInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = (type: 'agent' | 'user' | 'system', content: string) => {
    setMessages(prev => [...prev, { type, content, timestamp: new Date() }]);
  };

  const handleMainDocumentUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    addMessage('system', `📎 Uploading ${file.name}...`);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/documents/extract-text`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to upload document');
      }

      const data = await response.json();

      const uploadedDoc = {
        text: data.text || '',
        type: data.document_type || 'legal_document',
        analysis: data,
        fileName: file.name
      };

      setDocumentData(uploadedDoc);
      addMessage('system', `✅ Document "${file.name}" uploaded successfully!`);

      // Clear the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      // Auto-switch to interview tab and start AI interview
      setTimeout(() => {
        setActiveTab('interview');
        startAIInterview(uploadedDoc.text);
      }, 500);

    } catch (error: any) {
      console.error('File upload error:', error);
      addMessage('system', `❌ Failed to upload ${file.name}: ${error.message}`);
      setIsProcessing(false);
    }
  };

  const handleSampleDocument = () => {
    const sampleDoc = {
      text: `IN THE CIRCUIT COURT

MIDLAND CREDIT MANAGEMENT, INC.,
Plaintiff,

vs.

JOHN DOE,
Defendant.

Case No: 2024-CC-12345

COMPLAINT

Plaintiff alleges:
1. Defendant owes $8,542.00 on a credit card account
2. Original creditor was Chase Bank
3. Debt was assigned to Plaintiff on January 15, 2023
4. Defendant has failed to pay despite demand

WHEREFORE, Plaintiff seeks judgment for $8,542.00 plus interest, costs, and attorney fees.`,
      type: 'debt_collection',
      fileName: 'Sample_Debt_Collection_Case.txt'
    };
    setDocumentData(sampleDoc);
    addMessage('system', '✅ Sample document loaded successfully!');

    // Auto-switch to interview tab and start AI interview
    setTimeout(() => {
      setActiveTab('interview');
      startAIInterview(sampleDoc.text);
    }, 500);
  };

  const startAIInterview = async (documentText: string) => {
    setIsProcessing(true);

    addMessage('system', '🤖 AI Agent starting...');
    addMessage('agent', "Hi! I'm your Legal AI Assistant. I'm analyzing your legal document now...");

    console.log('📄 Starting AI Interview with document text length:', documentText?.length);
    console.log('📄 First 200 chars:', documentText?.substring(0, 200));

    try {
      // Call backend defense-flow endpoint
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/defense-flow/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: sessionId,
          documentText: documentText
        })
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();

      // Store analysis data
      setAnalysis({
        case_type: data.document_summary?.case_type || 'legal matter',
        summary: data.message || 'Document analyzed'
      });

      // Set first question
      if (data.current_question) {
        setCurrentQuestion({
          question: data.current_question.text || data.current_question.question,
          options: data.current_question.options,
          why_important: 'This information is critical for building your defense strategy'
        });
      }

      addMessage('agent', `✅ I've analyzed your case. ${data.message || 'Let me ask you some strategic questions.'}`);

      setTimeout(() => {
        if (data.current_question) {
          addMessage('agent', data.current_question.text || data.current_question.question);
        }
      }, 1000);

    } catch (error: any) {
      console.error('Failed to start AI interview:', error);
      addMessage('system', `❌ Error: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const submitAnswer = async (answer: string) => {
    if (!currentQuestion) return;

    addMessage('user', answer);
    setIsProcessing(true);
    setCurrentQuestion(null);
    setTextAnswer('');

    try {
      // Call backend defense-flow answer endpoint
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/defense-flow/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: sessionId,
          answer: answer
        })
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();

      // Show acknowledgment
      setTimeout(() => {
        addMessage('agent', 'Thank you for that information.');
      }, 500);

      // Check if complete or more questions
      if (data.complete || data.action === 'INTERVIEW_COMPLETE') {
        setInterviewComplete(true);
        setTimeout(() => {
          addMessage('agent', "Perfect! I have all the information I need. Click the 'Build Defense Strategy' button below or switch to the Defense tab when you're ready.");
        }, 1000);
      } else if (data.current_question) {
        // Set next question
        setCurrentQuestion({
          question: data.current_question.text || data.current_question.question,
          options: data.current_question.options,
          why_important: 'This information helps strengthen your defense'
        });

        setTimeout(() => {
          addMessage('agent', data.current_question.text || data.current_question.question);
        }, 1000);
      }

    } catch (error: any) {
      console.error('Failed to process answer:', error);
      addMessage('system', `❌ Error: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const buildDefense = async () => {
    setIsProcessing(true);

    if (supportingDocs.length > 0) {
      addMessage('agent', `I'm building your defense strategy with ${supportingDocs.length} supporting document${supportingDocs.length !== 1 ? 's' : ''} you uploaded...`);
    } else {
      addMessage('agent', "I'm building your comprehensive defense strategy...");
    }

    try {
      // Call backend defense-flow build endpoint
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/defense-flow/build`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();

      // Transform backend response to match frontend expected format
      // Handle based_on which can be either an object {document_facts, interview_answers} or a string
      let strategyBasis = 'Based on document analysis and interview responses';
      if (data.based_on) {
        if (typeof data.based_on === 'object') {
          strategyBasis = `Based on ${data.based_on.document_facts || 0} document facts and ${data.based_on.interview_answers || 0} interview answers`;
        } else {
          strategyBasis = data.based_on;
        }
      }

      const transformedStrategy = {
        primary_defenses: data.defenses || [],
        immediate_actions: data.immediate_actions || [],
        evidence_needed: data.evidence_needed || [],
        strategy_basis: strategyBasis
      };

      setStrategy(transformedStrategy);

      addMessage('agent', `✅ Defense Strategy Complete! I've identified ${transformedStrategy.primary_defenses.length} strong defense${transformedStrategy.primary_defenses.length !== 1 ? 's' : ''} for your case. Switch to the Defense tab to see the full analysis.`);

      // Auto-switch to defense tab
      setTimeout(() => {
        setActiveTab('defense');
      }, 1000);

    } catch (error: any) {
      console.error('Failed to build defense:', error);
      addMessage('system', `❌ Error: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    // Notify about multiple files
    if (files.length > 1) {
      addMessage('system', `📎 Uploading ${files.length} supporting documents...`);
    }

    // Process each file
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (files.length === 1) {
        addMessage('system', `📎 Uploading ${file.name}...`);
      }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/documents/extract-text`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to upload document');
      }

      const data = await response.json();

      const uploadedDoc = {
        name: file.name,
        text: data.text || '',
        size: file.size,
        uploadedAt: new Date()
      };

      setSupportingDocs(prev => [...prev, uploadedDoc]);
      if (files.length === 1 || i === files.length - 1) {
        addMessage('agent', `✅ Document${files.length > 1 ? 's' : ''} "${file.name}"${files.length > 1 && i < files.length - 1 ? ' and others' : ''} uploaded successfully! ${files.length > 1 ? 'All documents' : 'This'} will be included in your defense strategy.`);
      }

    } catch (error: any) {
      console.error('File upload error:', error);
      addMessage('system', `❌ Failed to upload ${file.name}: ${error.message}`);
    }
    }

    // Clear the file input after processing all files
    if (supportingDocsInputRef.current) {
      supportingDocsInputRef.current.value = '';
    }
  };

  const resetBuilder = () => {
    setActiveTab('upload');
    setDocumentData(null);
    setMessages([]);
    setCurrentQuestion(null);
    setTextAnswer('');
    setStrategy(null);
    setAnalysis(null);
    setSupportingDocs([]);
    setInterviewComplete(false);
  };

  const canSwitchToInterview = documentData !== null;
  const canSwitchToDefense = strategy !== null;

  return (
    <div className="unified-defense-builder max-w-6xl mx-auto p-4">
      {/* Three-Tab Navigation System */}
      <div className="tabs-navigation bg-white rounded-lg shadow-lg mb-6">
        <div className="flex border-b border-gray-200">
          {/* Upload Tab */}
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex-1 flex items-center justify-center gap-3 px-6 py-4 font-semibold transition-all ${
              activeTab === 'upload'
                ? 'bg-blue-500 text-white border-b-4 border-blue-700'
                : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Upload className="w-5 h-5" />
            <span>Upload</span>
            {documentData && activeTab !== 'upload' && (
              <CheckCircle className="w-4 h-4 text-green-500" />
            )}
          </button>

          {/* Interview Tab */}
          <button
            onClick={() => canSwitchToInterview && setActiveTab('interview')}
            disabled={!canSwitchToInterview}
            className={`flex-1 flex items-center justify-center gap-3 px-6 py-4 font-semibold transition-all ${
              activeTab === 'interview'
                ? 'bg-blue-500 text-white border-b-4 border-blue-700'
                : canSwitchToInterview
                ? 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                : 'bg-gray-50 text-gray-300 cursor-not-allowed'
            }`}
          >
            <MessageSquare className="w-5 h-5" />
            <span>Interview</span>
            {interviewComplete && activeTab !== 'interview' && (
              <CheckCircle className="w-4 h-4 text-green-500" />
            )}
          </button>

          {/* Defense Tab */}
          <button
            onClick={() => canSwitchToDefense && setActiveTab('defense')}
            disabled={!canSwitchToDefense}
            className={`flex-1 flex items-center justify-center gap-3 px-6 py-4 font-semibold transition-all ${
              activeTab === 'defense'
                ? 'bg-blue-500 text-white border-b-4 border-blue-700'
                : canSwitchToDefense
                ? 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                : 'bg-gray-50 text-gray-300 cursor-not-allowed'
            }`}
          >
            <Shield className="w-5 h-5" />
            <span>Defense</span>
            {strategy && (
              <CheckCircle className="w-4 h-4 text-green-500" />
            )}
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <Card className="main-content">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-center">
            {activeTab === 'upload' && 'Upload Legal Document'}
            {activeTab === 'interview' && 'AI Interview & Analysis'}
            {activeTab === 'defense' && 'Defense Strategy'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Upload Tab Content */}
          {activeTab === 'upload' && (
            <div className="upload-stage space-y-4">
              <p className="text-center text-gray-600 mb-6">
                Upload your legal document to begin the AI-powered defense analysis.
              </p>

              {documentData && (
                <div className="mb-6 p-4 bg-green-50 rounded-lg border-l-4 border-green-400">
                  <div className="flex items-center gap-3">
                    <FileText className="w-6 h-6 text-green-600" />
                    <div>
                      <p className="text-green-800 font-medium">
                        ✅ Document Loaded: {documentData.fileName || 'Legal Document'}
                      </p>
                      {documentData.type && (
                        <p className="text-green-700 text-sm mt-1">
                          Type: {documentData.type}
                        </p>
                      )}
                    </div>
                  </div>
                  <Button
                    onClick={() => setActiveTab('interview')}
                    className="w-full mt-4 bg-green-600 hover:bg-green-700"
                  >
                    Continue to Interview →
                  </Button>
                </div>
              )}

              {/* Main Document Upload Button */}
              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={handleMainDocumentUpload}
                  accept=".pdf,.doc,.docx,.txt"
                  className="hidden"
                  id="main-document-upload"
                  disabled={isProcessing}
                />
                <label
                  htmlFor="main-document-upload"
                  className={`block w-full h-32 border-4 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all ${
                    isProcessing
                      ? 'bg-gray-100 border-gray-300 cursor-not-allowed'
                      : 'bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-400 hover:border-blue-600 hover:bg-gradient-to-br hover:from-blue-100 hover:to-indigo-100'
                  }`}
                >
                  <Upload className={`w-12 h-12 mb-3 ${isProcessing ? 'text-gray-400' : 'text-blue-600'}`} />
                  <span className={`text-lg font-semibold ${isProcessing ? 'text-gray-500' : 'text-blue-900'}`}>
                    {isProcessing ? 'Uploading...' : 'Click to Upload Legal Document'}
                  </span>
                  <span className="text-sm text-gray-600 mt-1">
                    PDF, DOC, DOCX, or TXT files
                  </span>
                </label>
              </div>

              {/* Divider */}
              <div className="flex items-center gap-4 my-6">
                <div className="flex-1 h-px bg-gray-300"></div>
                <span className="text-gray-500 text-sm font-medium">OR</span>
                <div className="flex-1 h-px bg-gray-300"></div>
              </div>

              {/* Sample Document Button */}
              <Button
                onClick={handleSampleDocument}
                disabled={isProcessing}
                className="w-full h-16 text-lg"
              >
                📄 Use Sample Debt Collection Case
              </Button>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                <h3 className="font-medium text-blue-900 mb-2">How it works:</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Upload your legal document (complaint, summons, etc.)</li>
                  <li>• AI analyzes and asks strategic questions</li>
                  <li>• Answer questions to build your defense</li>
                  <li>• Receive comprehensive defense strategy</li>
                  <li>• Navigate between tabs at any time!</li>
                </ul>
              </div>
            </div>
          )}

          {/* Interview Tab Content */}
          {activeTab === 'interview' && (
            <div className="interview-stage">
              {!documentData ? (
                <div className="text-center py-12">
                  <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 text-lg mb-4">No document uploaded yet</p>
                  <Button onClick={() => setActiveTab('upload')}>
                    Go to Upload Tab
                  </Button>
                </div>
              ) : (
                <>
                  <div className="chat-container bg-gray-50 rounded-lg p-6 mb-4 min-h-[500px] max-h-[600px] overflow-y-auto">
                    <div className="space-y-4">
                      {messages.map((msg, index) => (
                        <div
                          key={index}
                          className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                          {msg.type === 'system' && (
                            <div className="w-full text-center">
                              <span className="inline-block bg-gray-100 text-gray-600 text-sm px-4 py-2 rounded-full">
                                {msg.content}
                              </span>
                            </div>
                          )}

                          {msg.type === 'agent' && (
                            <div className="flex items-start gap-3 max-w-[80%]">
                              <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold shadow-lg">
                                AI
                              </div>
                              <div className="flex-1">
                                <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4 shadow-sm">
                                  <p className="text-gray-800 whitespace-pre-wrap">{msg.content}</p>
                                </div>
                              </div>
                            </div>
                          )}

                          {msg.type === 'user' && (
                            <div className="flex items-start gap-3 max-w-[80%] justify-end">
                              <div className="bg-green-500 text-white rounded-lg p-4 shadow-sm">
                                <p>{msg.content}</p>
                              </div>
                              <div className="flex-shrink-0 w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-white font-bold shadow-lg">
                                U
                              </div>
                            </div>
                          )}
                        </div>
                      ))}

                      {/* Options for current question */}
                      {currentQuestion && currentQuestion.options && !isProcessing && (
                        <div className="flex justify-start">
                          <div className="flex items-start gap-3 max-w-[80%]">
                            <div className="flex-shrink-0 w-10 h-10" />
                            <div className="flex-1 grid grid-cols-1 gap-2">
                              {currentQuestion.options.map((option: string, index: number) => (
                                <button
                                  key={index}
                                  onClick={() => submitAnswer(option)}
                                  className="text-left p-3 bg-white border-2 border-blue-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all shadow-sm hover:shadow-md"
                                >
                                  {option}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Text input for open-ended questions */}
                      {currentQuestion && !currentQuestion.options && !isProcessing && (
                        <div className="flex justify-start">
                          <div className="flex items-start gap-3 max-w-[80%] w-full">
                            <div className="flex-shrink-0 w-10 h-10" />
                            <div className="flex-1 flex gap-2">
                              <input
                                type="text"
                                value={textAnswer}
                                onChange={(e) => setTextAnswer(e.target.value)}
                                onKeyPress={(e) => {
                                  if (e.key === 'Enter' && textAnswer.trim()) {
                                    submitAnswer(textAnswer);
                                  }
                                }}
                                placeholder="Type your answer..."
                                className="flex-1 px-4 py-3 border-2 border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              />
                              <button
                                onClick={() => textAnswer.trim() && submitAnswer(textAnswer)}
                                disabled={!textAnswer.trim()}
                                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
                              >
                                Send
                              </button>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Typing indicator */}
                      {isProcessing && (
                        <div className="flex justify-start">
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold shadow-lg">
                              AI
                            </div>
                            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4 shadow-sm">
                              <div className="flex gap-2">
                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      <div ref={messagesEndRef} />
                    </div>
                  </div>

                  {/* Supporting Documents Upload Section */}
                  <div className="mt-6 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 border-2 border-purple-200">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Upload className="w-5 h-5 text-purple-600" />
                        <h3 className="font-semibold text-purple-900">Upload Supporting Documents</h3>
                      </div>
                      {supportingDocs.length > 0 && (
                        <span className="text-sm bg-purple-100 text-purple-800 px-3 py-1 rounded-full font-medium">
                          {supportingDocs.length} uploaded
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-purple-700 mb-3">
                      Upload evidence, contracts, receipts, or other documents to strengthen your defense
                    </p>
                    <input
                      ref={supportingDocsInputRef}
                      type="file"
                      multiple
                      onChange={handleFileUpload}
                      accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
                      className="hidden"
                      id="supporting-docs-upload"
                    />
                    <label
                      htmlFor="supporting-docs-upload"
                      className="inline-block cursor-pointer px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors shadow-md"
                    >
                      📎 Choose File to Upload
                    </label>
                    {supportingDocs.length > 0 && (
                      <div className="mt-3 space-y-1">
                        {supportingDocs.map((doc, index) => (
                          <div key={index} className="text-sm bg-white rounded px-3 py-2 flex items-center gap-2">
                            <span className="text-green-600">✓</span>
                            <span className="flex-1 text-gray-800">{doc.name}</span>
                            <span className="text-gray-500 text-xs">{(doc.size / 1024).toFixed(1)} KB</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Build Defense Button */}
                  {interviewComplete && (
                    <div className="mt-6 text-center">
                      <Button
                        onClick={buildDefense}
                        disabled={isProcessing}
                        className="px-8 py-4 bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 text-white text-lg font-semibold shadow-lg"
                      >
                        ✅ Build Defense Strategy
                      </Button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Defense Tab Content */}
          {activeTab === 'defense' && (
            <div className="defense-stage">
              {!strategy ? (
                <div className="text-center py-12">
                  <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 text-lg mb-4">No defense strategy generated yet</p>
                  <p className="text-gray-400 mb-4">Complete the interview and click "Build Defense Strategy"</p>
                  <Button onClick={() => setActiveTab('interview')}>
                    Go to Interview Tab
                  </Button>
                </div>
              ) : (
                <div className="complete-stage">
                  {/* Defense Strategy Display */}
                  {strategy.primary_defenses && (
                    <div className="defense-strategy">
                      <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                        <span className="text-4xl">🛡️</span>
                        Your Defense Strategy
                      </h2>

                      {strategy.strategy_basis && (
                        <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border-2 border-blue-300">
                          <h3 className="font-bold text-blue-900 mb-3 flex items-center gap-2">
                            <span className="text-xl">🎯</span>
                            Strategy Foundation
                          </h3>
                          <p className="text-gray-800 leading-relaxed">{strategy.strategy_basis}</p>
                        </div>
                      )}

                      {strategy.primary_defenses.map((defense: any, index: number) => (
                        <div key={index} className="defense-card bg-white rounded-xl shadow-2xl border-2 border-gray-200 p-8 mb-6 hover:shadow-3xl transition-shadow">
                          <div className="flex justify-between items-start mb-6">
                            <div className="flex-1">
                              <h3 className="text-2xl font-bold text-gray-900 mb-2">{defense.name}</h3>
                              <p className="text-gray-600 text-lg">{defense.description}</p>
                            </div>
                            <div className="text-right ml-6">
                              <div className="text-5xl font-bold text-green-600">{defense.strength}%</div>
                              {defense.strength_level && (
                                <div className={`text-sm font-bold px-4 py-2 rounded-full inline-block mt-2 ${
                                  defense.strength_level === 'VERY STRONG' || defense.strength_level === 'STRONG' ? 'bg-green-100 text-green-800' :
                                  defense.strength_level === 'MODERATE' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-red-100 text-red-800'
                                }`}>
                                  {defense.strength_level}
                                </div>
                              )}
                            </div>
                          </div>

                          {defense.why_recommended && (
                            <div className="mb-6 p-6 bg-amber-50 rounded-lg border-l-4 border-amber-500">
                              <h4 className="font-bold text-amber-900 mb-3">💡 Why This Defense is Recommended</h4>
                              <div className="text-gray-800 whitespace-pre-wrap leading-relaxed">{defense.why_recommended}</div>
                            </div>
                          )}

                          {defense.document_evidence && (
                            <div className="mb-6 p-6 bg-indigo-50 rounded-lg border-l-4 border-indigo-500">
                              <h4 className="font-bold text-indigo-900 mb-3">📄 Document-Based Evidence</h4>

                              {defense.document_evidence.plaintiff_claims && (
                                <div className="mb-4">
                                  <h5 className="font-semibold text-indigo-800 mb-2">Plaintiff's Claims:</h5>
                                  <p className="text-gray-800">{defense.document_evidence.plaintiff_claims}</p>
                                </div>
                              )}

                              {defense.document_evidence.missing_from_complaint && defense.document_evidence.missing_from_complaint.length > 0 && (
                                <div className="mb-4">
                                  <h5 className="font-semibold text-indigo-800 mb-2">Missing from Complaint:</h5>
                                  <ul className="list-disc list-inside space-y-1 text-gray-800">
                                    {defense.document_evidence.missing_from_complaint.map((item: string, i: number) => (
                                      <li key={i}>{item}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {defense.document_evidence.defendant_answers_support && (
                                <div className="mb-4">
                                  <h5 className="font-semibold text-indigo-800 mb-2">How Your Answers Support This:</h5>
                                  <p className="text-gray-800">{defense.document_evidence.defendant_answers_support}</p>
                                </div>
                              )}

                              {defense.document_evidence.specific_facts && defense.document_evidence.specific_facts.length > 0 && (
                                <div>
                                  <h5 className="font-semibold text-indigo-800 mb-2">Key Facts:</h5>
                                  <ul className="list-disc list-inside space-y-1 text-gray-800">
                                    {defense.document_evidence.specific_facts.map((fact: string, i: number) => (
                                      <li key={i}>{fact}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}

                          {defense.detailed_explanation && (
                            <div className="mb-6 p-6 bg-blue-50 rounded-lg border-l-4 border-blue-500">
                              <h4 className="font-bold text-blue-900 mb-3">📋 Legal Explanation</h4>
                              <div className="text-gray-800 whitespace-pre-wrap">{defense.detailed_explanation}</div>
                            </div>
                          )}

                          {defense.how_to_assert && (
                            <div className="mb-6 p-6 bg-green-50 rounded-lg border-l-4 border-green-500">
                              <h4 className="font-bold text-green-900 mb-3">⚖️ How to Assert This Defense</h4>
                              <div className="text-gray-800 whitespace-pre-wrap">{defense.how_to_assert}</div>
                            </div>
                          )}

                          {defense.winning_scenarios && defense.winning_scenarios.length > 0 && (
                            <div className="mb-6 p-6 bg-purple-50 rounded-lg border-l-4 border-purple-500">
                              <h4 className="font-bold text-purple-900 mb-3">✅ Winning Scenarios</h4>
                              <ul className="list-disc list-inside space-y-2 text-gray-800">
                                {defense.winning_scenarios.map((scenario: string, i: number) => (
                                  <li key={i}>{scenario}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {defense.risks_to_avoid && defense.risks_to_avoid.length > 0 && (
                            <div className="p-6 bg-red-50 rounded-lg border-l-4 border-red-500">
                              <h4 className="font-bold text-red-900 mb-3">⚠️ Risks to Avoid</h4>
                              <ul className="list-disc list-inside space-y-2 text-red-800">
                                {defense.risks_to_avoid.map((risk: string, i: number) => (
                                  <li key={i}>{risk}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      ))}

                      {strategy.immediate_actions && strategy.immediate_actions.length > 0 && (
                        <div className="actions-card bg-yellow-50 border-2 border-yellow-300 rounded-xl p-6 mb-6">
                          <h3 className="text-xl font-bold text-yellow-900 mb-4">📋 Immediate Actions Required</h3>
                          <div className="space-y-3">
                            {strategy.immediate_actions.map((action: any, index: number) => (
                              <div key={index} className="flex items-start gap-4 p-4 bg-white rounded-lg">
                                <div className={`px-3 py-1 rounded-full text-xs font-bold ${
                                  action.priority === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                                  action.priority === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                                  'bg-blue-100 text-blue-800'
                                }`}>
                                  {action.priority}
                                </div>
                                <div className="flex-1">
                                  <div className="font-bold text-gray-900">{action.action}</div>
                                  <div className="text-sm text-gray-600 mt-1">{action.details}</div>
                                  {action.why_important && (
                                    <div className="text-sm text-blue-700 mt-2 italic">
                                      <strong>Why:</strong> {action.why_important}
                                    </div>
                                  )}
                                  {action.deadline && (
                                    <div className="text-sm text-red-600 font-medium mt-1">⏰ Deadline: {action.deadline}</div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="text-center mt-8">
                        <Button
                          onClick={resetBuilder}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 text-lg"
                        >
                          🔄 Analyze Another Document
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
