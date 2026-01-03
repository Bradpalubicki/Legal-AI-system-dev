'use client';

import React, { useState } from 'react';
import {
  Clock,
  Calendar,
  AlertTriangle,
  Info,
  Scale,
  CheckCircle,
  XCircle,
  ExternalLink,
  MapPin,
  Calculator,
  Building
} from 'lucide-react';

interface DeadlineData {
  date: string;
  description: string;
  confidence: number;
  sourceLocation: string;
}

interface DeadlineCalculatorProps {
  dates: DeadlineData[];
  documentName: string;
  className?: string;
}

interface CalculatedDeadline {
  originalDate: string;
  description: string;
  calculatedResponses: Array<{
    action: string;
    deadline: string;
    daysToRespond: number;
    calculationMethod: string;
    courtRule: string;
  }>;
  warnings: string[];
}

const DeadlineCalculator: React.FC<DeadlineCalculatorProps> = ({
  dates,
  documentName,
  className = ''
}) => {
  const [calculatedDeadlines, setCalculatedDeadlines] = useState<CalculatedDeadline[]>([]);
  const [selectedJurisdiction, setSelectedJurisdiction] = useState('federal');
  const [showCalculationDetails, setShowCalculationDetails] = useState<Record<number, boolean>>({});

  // Mock calculation function - in real app would use actual court rules
  const calculateDeadlines = (originalDate: string, description: string): CalculatedDeadline => {
    const baseDate = new Date(originalDate);
    const calculations: CalculatedDeadline['calculatedResponses'] = [];

    // Example calculations based on common court rules
    if (description.toLowerCase().includes('service') || description.toLowerCase().includes('complaint')) {
      calculations.push({
        action: 'Answer or Motion to Dismiss',
        deadline: new Date(baseDate.getTime() + (21 * 24 * 60 * 60 * 1000)).toISOString().split('T')[0],
        daysToRespond: 21,
        calculationMethod: 'Count forward 21 days from service date, excluding weekends and holidays',
        courtRule: 'Fed. R. Civ. P. 12(a)(1)(A)'
      });
    }

    if (description.toLowerCase().includes('discovery')) {
      calculations.push({
        action: 'Discovery Response',
        deadline: new Date(baseDate.getTime() + (30 * 24 * 60 * 60 * 1000)).toISOString().split('T')[0],
        daysToRespond: 30,
        calculationMethod: 'Count forward 30 days from service date',
        calculationRule: 'Fed. R. Civ. P. 33, 34'
      });
    }

    if (description.toLowerCase().includes('motion')) {
      calculations.push({
        action: 'Response to Motion',
        deadline: new Date(baseDate.getTime() + (21 * 24 * 60 * 60 * 1000)).toISOString().split('T')[0],
        daysToRespond: 21,
        calculationMethod: 'Count forward 21 days from service of motion',
        courtRule: 'Fed. R. Civ. P. 6(c)'
      });
    }

    const warnings = [
      'Verify actual service date and method',
      'Check local court rules for variations',
      'Consider holidays and court closures',
      'Confirm jurisdiction-specific requirements'
    ];

    return {
      originalDate,
      description,
      calculatedResponses: calculations,
      warnings
    };
  };

  React.useEffect(() => {
    const calculated = dates.map(date => calculateDeadlines(date.date, date.description));
    setCalculatedDeadlines(calculated);
  }, [dates]);

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getDaysUntil = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
      return `${Math.abs(diffDays)} days ago`;
    } else if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Tomorrow';
    } else {
      return `${diffDays} days from now`;
    }
  };

  const isUrgent = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return diffDays <= 7 && diffDays >= 0;
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Critical Warning */}
      <div className="bg-error-50 border border-error-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <AlertTriangle className="h-5 w-5 text-error-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-semibold text-error-900 mb-2">
              VERIFY WITH COURT - Calculations Are Estimates Only
            </h3>
            <ul className="text-sm text-error-800 space-y-1">
              <li>• These calculations are AI-generated estimates based on common rules</li>
              <li>• Actual deadlines depend on specific court rules, local practices, and case circumstances</li>
              <li>• Always verify through official court records and applicable rules</li>
              <li>• Consider service methods, holidays, and jurisdiction-specific requirements</li>
              <li>• Consult local counsel for jurisdiction-specific deadline calculations</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Jurisdiction Selection */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900">Deadline Calculations</h3>
          <div className="flex items-center space-x-2">
            <Building className="h-4 w-4 text-gray-600" />
            <label className="text-sm font-medium text-gray-700">Jurisdiction:</label>
            <select
              value={selectedJurisdiction}
              onChange={(e) => setSelectedJurisdiction(e.target.value)}
              className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="federal">Federal Court</option>
              <option value="state_ca">California State</option>
              <option value="state_ny">New York State</option>
              <option value="state_tx">Texas State</option>
              <option value="other">Other (Verify Rules)</option>
            </select>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded p-3">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> Rules shown are examples for {selectedJurisdiction === 'federal' ? 'Federal Courts' : 'selected jurisdiction'}. 
            Local rules and specific case circumstances may modify these deadlines.
          </p>
        </div>
      </div>

      {/* Calculated Deadlines */}
      {calculatedDeadlines.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <Calculator className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No deadlines available for calculation</p>
        </div>
      ) : (
        <div className="space-y-6">
          {calculatedDeadlines.map((deadline, index) => (
            <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-1">
                    Original Deadline: {deadline.description}
                  </h4>
                  <div className="text-sm text-gray-600">
                    Base Date: {formatDate(deadline.originalDate)}
                  </div>
                </div>

                <button
                  onClick={() => setShowCalculationDetails(prev => ({
                    ...prev,
                    [index]: !prev[index]
                  }))}
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  {showCalculationDetails[index] ? 'Hide' : 'Show'} Details
                </button>
              </div>

              {/* Calculated Response Deadlines */}
              <div className="space-y-3">
                {deadline.calculatedResponses.map((response, responseIndex) => (
                  <div 
                    key={responseIndex}
                    className={`border rounded-lg p-3 ${
                      isUrgent(response.deadline) 
                        ? 'border-error-300 bg-error-50' 
                        : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h5 className="font-medium text-gray-900">{response.action}</h5>
                          {isUrgent(response.deadline) && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-error-100 text-error-800">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              Urgent
                            </span>
                          )}
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Calculated Deadline:</span>
                            <div className="font-semibold text-gray-900">
                              {formatDate(response.deadline)}
                            </div>
                            <div className={`text-sm ${
                              isUrgent(response.deadline) ? 'text-error-600 font-medium' : 'text-gray-600'
                            }`}>
                              {getDaysUntil(response.deadline)}
                            </div>
                          </div>
                          <div>
                            <span className="text-gray-500">Response Time:</span>
                            <div className="font-semibold text-gray-900">
                              {response.daysToRespond} days
                            </div>
                            <div className="text-sm text-gray-600">
                              Based on {response.courtRule}
                            </div>
                          </div>
                        </div>

                        {showCalculationDetails[index] && (
                          <div className="mt-3 p-3 bg-white border border-gray-200 rounded">
                            <h6 className="text-xs font-semibold text-gray-900 mb-2">Calculation Method</h6>
                            <p className="text-xs text-gray-700 mb-2">{response.calculationMethod}</p>
                            <div className="flex items-center space-x-2 text-xs">
                              <span className="text-gray-500">Authority:</span>
                              <span className="font-medium text-gray-700">{response.courtRule}</span>
                              <button className="text-primary-600 hover:text-primary-700 inline-flex items-center">
                                <ExternalLink className="h-3 w-3 mr-1" />
                                View Rule
                              </button>
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-col space-y-2">
                        <button
                          className="p-1 text-success-600 hover:bg-success-100 rounded"
                          title="Verify calculation"
                        >
                          <CheckCircle className="h-4 w-4" />
                        </button>
                        <button
                          className="p-1 text-error-600 hover:bg-error-100 rounded"
                          title="Mark as needs verification"
                        >
                          <XCircle className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Warnings */}
              <div className="mt-4 bg-amber-50 border border-amber-200 rounded p-3">
                <h6 className="text-sm font-semibold text-amber-800 mb-2">Verification Required</h6>
                <ul className="text-sm text-amber-700 space-y-1">
                  {deadline.warnings.map((warning, warningIndex) => (
                    <li key={warningIndex} className="flex items-start space-x-2">
                      <span className="text-amber-600 mt-1">•</span>
                      <span>{warning}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Calculation Methodology */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <Calculator className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-blue-900 mb-2">Calculation Methodology</h4>
            <div className="text-sm text-blue-800 space-y-2">
              <p>
                <strong>AI Calculations:</strong> Based on commonly applicable federal and state court rules
              </p>
              <p>
                <strong>Assumptions:</strong> Standard service methods, no extensions or modifications, typical business days
              </p>
              <p>
                <strong>Exclusions:</strong> Holidays, court closures, and jurisdiction-specific variations may not be reflected
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Court Rules Reference */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Common Deadline Rules Reference</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <h5 className="font-semibold text-gray-800 mb-2">Federal Court</h5>
            <ul className="text-gray-600 space-y-1">
              <li>• Answer to Complaint: 21 days (FRCP 12(a))</li>
              <li>• Response to Motion: 21 days (FRCP 6(c))</li>
              <li>• Discovery Responses: 30 days (FRCP 33, 34)</li>
              <li>• Appeal Notice: 30 days (FRAP 4)</li>
            </ul>
          </div>
          <div>
            <h5 className="font-semibold text-gray-800 mb-2">Common Variations</h5>
            <ul className="text-gray-600 space-y-1">
              <li>• Service by mail: +3 days (FRCP 6(d))</li>
              <li>• Service on United States: 60 days (FRCP 12(a)(2))</li>
              <li>• Local rules may modify timelines</li>
              <li>• Emergency motions: Variable timing</li>
            </ul>
          </div>
        </div>
        <div className="mt-3 flex items-center space-x-4 text-xs">
          <button className="text-blue-600 hover:text-blue-700 font-medium inline-flex items-center">
            <ExternalLink className="h-3 w-3 mr-1" />
            Federal Rules of Civil Procedure
          </button>
          <button className="text-blue-600 hover:text-blue-700 font-medium inline-flex items-center">
            <ExternalLink className="h-3 w-3 mr-1" />
            Local Court Rules
          </button>
        </div>
      </div>

      {/* Professional Responsibility Notice */}
      <div className="bg-legal-50 border border-legal-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-legal-900 mb-1">Professional Responsibility Warning</h4>
            <p className="text-sm text-legal-700 mb-2">
              <strong>Attorney Duty:</strong> You remain professionally responsible for calculating accurate deadlines. 
              These AI calculations are tools to assist your analysis, not replace professional judgment.
            </p>
            <div className="text-sm text-legal-700">
              <strong>Required Verification:</strong>
              <ul className="mt-1 space-y-1 list-disc list-inside">
                <li>Confirm actual service dates and methods</li>
                <li>Check applicable court rules and local practices</li>
                <li>Account for holidays and court scheduling</li>
                <li>Consider any case-specific orders or extensions</li>
                <li>Verify jurisdiction and venue requirements</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeadlineCalculator;