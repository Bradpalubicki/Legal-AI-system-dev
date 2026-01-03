'use client';
import { useState } from 'react';

interface AnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysis: any;
  documentName: string;
}

export default function AnalysisModal({ isOpen, onClose, analysis, documentName }: AnalysisModalProps) {
  if (!isOpen) return null;

  return (
    <div className='fixed inset-0 z-50 overflow-y-auto'>
      {/* Backdrop */}
      <div className='fixed inset-0 bg-black bg-opacity-50' onClick={onClose} />

      {/* Modal */}
      <div className='relative min-h-screen flex items-center justify-center p-4'>
        <div className='relative bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto'>
          {/* Header */}
          <div className='sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center'>
            <h2 className='text-2xl font-bold'>Document Analysis</h2>
            <button
              onClick={onClose}
              className='text-gray-500 hover:text-gray-700 text-2xl'
            >
              ×
            </button>
          </div>

          {/* Content */}
          <div className='p-6'>
            {/* Document Info */}
            <div className='mb-6'>
              <h3 className='font-semibold text-lg mb-2'>Document: {documentName}</h3>
            </div>

            {/* Analysis Sections */}
            {analysis ? (
              <>
                {/* Document Type */}
                <div className='mb-6 p-4 bg-blue-50 rounded-lg'>
                  <h4 className='font-semibold mb-2'>Document Type</h4>
                  <p>{analysis.document_type || 'Unknown'}</p>
                  <p className='text-sm text-gray-600 mt-1'>
                    Confidence: {(analysis.confidence * 100).toFixed(0)}%
                  </p>
                </div>

                {/* Summary */}
                <div className='mb-6 p-4 bg-green-50 rounded-lg'>
                  <h4 className='font-semibold mb-2'>Plain English Summary</h4>
                  <p>{analysis.summary || 'No summary available'}</p>
                </div>

                {/* Key Information */}
                <div className='mb-6 p-4 bg-yellow-50 rounded-lg'>
                  <h4 className='font-semibold mb-2'>Key Information</h4>
                  <ul className='space-y-2'>
                    {(() => {
                      const parties = analysis.all_parties || analysis.parties || [];
                      return Array.isArray(parties) && parties.length > 0 && (
                        <li><strong>Parties:</strong> {parties.map((p: any) =>
                          typeof p === 'string' ? p : (p.name || p.party_name || String(p))
                        ).join(', ')}</li>
                      );
                    })()}
                    {analysis.case_number && (
                      <li><strong>Case Number:</strong> {analysis.case_number}</li>
                    )}
                    {(analysis.amount || analysis.all_financial_amounts?.length > 0 || analysis.financial_amounts?.length > 0) && (
                      <li><strong>Amount:</strong> {
                        analysis.amount ||
                        (analysis.all_financial_amounts?.[0]?.amount || analysis.financial_amounts?.[0]?.amount || 'N/A')
                      }</li>
                    )}
                  </ul>
                </div>

                {/* Deadlines */}
                {analysis.deadlines && analysis.deadlines.length > 0 && (
                  <div className='mb-6 p-4 bg-red-50 rounded-lg'>
                    <h4 className='font-semibold mb-2'>Important Deadlines</h4>
                    <ul className='space-y-2'>
                      {analysis.deadlines.map((deadline: { description: string; date: string }, idx: number) => (
                        <li key={idx}>
                          <strong>{deadline.description}:</strong> {deadline.date}
                        </li>
                      ))}
                    </ul>
                    <p className='text-sm text-red-600 mt-2'>
                      ⚠️ Verify all deadlines with the court
                    </p>
                  </div>
                )}

                {/* Legal Disclaimer */}
                <div className='mt-6 p-4 bg-gray-100 rounded-lg text-sm'>
                  <p className='font-semibold'>⚖️ Legal Disclaimer</p>
                  <p>This analysis is for informational purposes only and does not constitute legal advice.
                     Please consult with a qualified attorney for case-specific guidance.</p>
                </div>
              </>
            ) : (
              <p>No analysis available</p>
            )}
          </div>

          {/* Footer */}
          <div className='border-t px-6 py-4 flex justify-end space-x-3'>
            <button
              onClick={onClose}
              className='px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300'
            >
              Close
            </button>
            <button
              onClick={() => window.print()}
              className='px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700'
            >
              Print Analysis
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}