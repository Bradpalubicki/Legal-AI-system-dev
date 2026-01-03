'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import { createCase, type CaseCreateData } from '@/lib/api/cases';
import { toast } from 'sonner';

interface CreateCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function CreateCaseModal({ isOpen, onClose, onSuccess }: CreateCaseModalProps) {
  const [formData, setFormData] = useState<CaseCreateData>({
    case_number: '',
    case_name: '',
    case_type: 'civil_litigation',
    court_name: '',
    jurisdiction: '',
    judge_name: '',
    filing_date: '',
    description: '',
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.case_number.trim()) {
      newErrors.case_number = 'Case number is required';
    }

    if (!formData.case_name.trim()) {
      newErrors.case_name = 'Case name is required';
    }

    if (!formData.case_type) {
      newErrors.case_type = 'Case type is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);

      // Prepare data for submission
      const submitData: CaseCreateData = {
        case_number: formData.case_number.trim(),
        case_name: formData.case_name.trim(),
        case_type: formData.case_type,
      };

      // Add optional fields if provided
      if (formData.court_name?.trim()) {
        submitData.court_name = formData.court_name.trim();
      }
      if (formData.jurisdiction?.trim()) {
        submitData.jurisdiction = formData.jurisdiction.trim();
      }
      if (formData.judge_name?.trim()) {
        submitData.judge_name = formData.judge_name.trim();
      }
      if (formData.filing_date) {
        submitData.filing_date = formData.filing_date;
      }
      if (formData.description?.trim()) {
        submitData.description = formData.description.trim();
      }

      await createCase(submitData);

      toast.success('Case created successfully', {
        description: `${formData.case_number} - ${formData.case_name}`
      });

      // Reset form
      setFormData({
        case_number: '',
        case_name: '',
        case_type: 'civil_litigation',
        court_name: '',
        jurisdiction: '',
        judge_name: '',
        filing_date: '',
        description: '',
      });

      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Failed to create case:', error);
      toast.error('Failed to create case', {
        description: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof CaseCreateData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Create New Case</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={loading}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-6">
            {/* Case Number & Name */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Case Number <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.case_number}
                  onChange={(e) => handleChange('case_number', e.target.value)}
                  placeholder="e.g., 24-CV-12345"
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                    errors.case_number ? 'border-red-500' : 'border-gray-300'
                  }`}
                  disabled={loading}
                />
                {errors.case_number && (
                  <p className="mt-1 text-sm text-red-500">{errors.case_number}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Case Type <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.case_type}
                  onChange={(e) => handleChange('case_type', e.target.value)}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                    errors.case_type ? 'border-red-500' : 'border-gray-300'
                  }`}
                  disabled={loading}
                >
                  <option value="bankruptcy_ch7">Bankruptcy Chapter 7</option>
                  <option value="bankruptcy_ch11">Bankruptcy Chapter 11</option>
                  <option value="bankruptcy_ch13">Bankruptcy Chapter 13</option>
                  <option value="civil_litigation">Civil Litigation</option>
                  <option value="debt_collection">Debt Collection</option>
                  <option value="foreclosure">Foreclosure</option>
                  <option value="eviction">Eviction</option>
                  <option value="criminal">Criminal</option>
                  <option value="employment">Employment</option>
                  <option value="contract_dispute">Contract Dispute</option>
                  <option value="other">Other</option>
                </select>
                {errors.case_type && (
                  <p className="mt-1 text-sm text-red-500">{errors.case_type}</p>
                )}
              </div>
            </div>

            {/* Case Name */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Case Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.case_name}
                onChange={(e) => handleChange('case_name', e.target.value)}
                placeholder="e.g., Smith v. Jones"
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.case_name ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={loading}
              />
              {errors.case_name && (
                <p className="mt-1 text-sm text-red-500">{errors.case_name}</p>
              )}
            </div>

            {/* Court Information */}
            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Court Information</h3>

              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Court Name
                    </label>
                    <input
                      type="text"
                      value={formData.court_name || ''}
                      onChange={(e) => handleChange('court_name', e.target.value)}
                      placeholder="e.g., Superior Court of California"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      disabled={loading}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Jurisdiction
                    </label>
                    <input
                      type="text"
                      value={formData.jurisdiction || ''}
                      onChange={(e) => handleChange('jurisdiction', e.target.value)}
                      placeholder="e.g., Los Angeles County"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      disabled={loading}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Judge Name
                    </label>
                    <input
                      type="text"
                      value={formData.judge_name || ''}
                      onChange={(e) => handleChange('judge_name', e.target.value)}
                      placeholder="e.g., Hon. Jane Smith"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      disabled={loading}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Filing Date
                    </label>
                    <input
                      type="date"
                      value={formData.filing_date || ''}
                      onChange={(e) => handleChange('filing_date', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      disabled={loading}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Description */}
            <div className="border-t border-gray-200 pt-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => handleChange('description', e.target.value)}
                placeholder="Enter case description, summary, or notes..."
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={loading}
              />
            </div>
          </div>

          {/* Footer */}
          <div className="flex gap-3 justify-end mt-6 pt-6 border-t border-gray-200">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="bg-primary-600 hover:bg-primary-700 text-white"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Creating...
                </>
              ) : (
                'Create Case'
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
