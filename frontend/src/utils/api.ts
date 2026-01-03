import { API_CONFIG } from '../config/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || API_CONFIG.BASE_URL;

// TEMPORARY - Use test endpoint to bypass AI issues
const USE_TEST_ENDPOINT = process.env.NODE_ENV === 'development';

export const api = {
  // Q&A endpoint - with optional test mode
  sendMessage: async (message: string, documentText?: string, documentAnalysis?: any) => {
    const endpoint = USE_TEST_ENDPOINT
      ? `${API_BASE_URL}/api/v1/test/correct-behavior`  // Hardcoded responses - instant
      : `${API_BASE_URL}/api/v1/qa/ask`;  // AI-powered responses

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(USE_TEST_ENDPOINT ? {
        message  // Test endpoint uses "message"
      } : {
        question: message,  // AI endpoint uses "question"
        document_text: documentText || '',
        document_analysis: documentAnalysis || {}
      })
    });

    if (!response.ok) throw new Error('Request failed');

    const data = await response.json();

    // Log to verify it's working
    console.log('Response received:', data);
    console.log('Word count:', data.word_count);
    console.log('Processing time:', data.processing_time || 'N/A');
    console.log('Source:', data.source || data.model_used);

    return data;
  },

  // Document endpoints
  uploadDocument: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/document-processing/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) throw new Error('Upload failed');
    return response.json();
  },

  // Health check
  checkHealth: async () => {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  }
};