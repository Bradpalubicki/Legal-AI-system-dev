'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import { updateCase, type LegalCase, type CaseUpdateData } from '@/lib/api/cases';
import { toast } from 'sonner';

interface EditCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  caseData: LegalCase;
}

export default function EditCaseModal({ isOpen, onClose, onSuccess, caseData }: EditCaseModalProps) {
  const [formData, setFormData] = useState<CaseUpdateData>({
    case_name: '',
    status: undefined,
    current_phase: '',
    description: '',
    notes: '',
    tags: [],
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (caseData) {
      setFormData({
        case_name: caseData.case_name,
        status: caseData.status,
        current_phase: caseData.current_phase || '',
        description: caseData.description || '',
        notes: caseData.notes || '',
        tags: caseData.tags || [],
      });
    }
  }, [caseData]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.case_name?.trim()) {
      newErrors.case_name = 'Case name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      toast.error('Please fix validation errors');
      return;
    }

    try {
      setLoading(true);

      // Prepare data for submission
      const submitData: CaseUpdateData = {};

      if (formData.case_name?.trim()) {
        submitData.case_name = formData.case_name.trim();
      }
      if (formData.status) {
        submitData.status = formData.status;
      }
      if (formData.current_phase?.trim()) {
        submitData.current_phase = formData.current_phase.trim();
      }
      if (formData.description?.trim()) {
        submitData.description = formData.description.trim();
      }
      if (formData.notes?.trim()) {
        submitData.notes = formData.notes.trim();
      }
      if (formData.tags && formData.tags.length > 0) {
        submitData.tags = formData.tags;
      }

      await updateCase(caseData.id, submitData);

      toast.success('Case updated successfully', {
        description: `${formData.case_name}`
      });

      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Failed to update case:', error);
      toast.error('Failed to update case', {
        description: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof CaseUpdateData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleTagsChange = (value: string) => {
    // Split by comma and trim
    const tags = value.split(',').map(t => t.trim()).filter(t => t.length > 0);
    handleChange('tags', tags);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Edit Case</h2>
            <p className="text-sm text-gray-600 mt-1">{caseData.case_number}</p>
          </div>
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
            {/* Case Name */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Case Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.case_name || ''}
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

            {/* Status & Current Phase */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Status
                </label>
                <select
                  value={formData.status || ''}
                  onChange={(e) => handleChange('status', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={loading}
                >
                  <option value="intake">Intake</option>
                  <option value="active">Active</option>
                  <option value="pending">Pending</option>
                  <option value="stayed">Stayed</option>
                  <option value="closed">Closed</option>
                  <option value="dismissed">Dismissed</option>
                  <option value="settled">Settled</option>
                  <option value="appealed">Appealed</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Current Phase
                </label>
                <input
                  type="text"
                  value={formData.current_phase || ''}
                  onChange={(e) => handleChange('current_phase', e.target.value)}
                  placeholder="e.g., Discovery, Trial Preparation"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => handleChange('description', e.target.value)}
                placeholder="Enter case description, summary, or background..."
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={loading}
              />
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Notes
              </label>
              <textarea
                value={formData.notes || ''}
                onChange={(e) => handleChange('notes', e.target.value)}
                placeholder="Internal notes, reminders, or important information..."
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={loading}
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Tags
              </label>
              <input
                type="text"
                value={formData.tags?.join(', ') || ''}
                onChange={(e) => handleTagsChange(e.target.value)}
                placeholder="e.g., urgent, complex, settlement-candidate (comma separated)"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={loading}
              />
              <p className="mt-1 text-xs text-gray-500">
                Separate tags with commas
              </p>
            </div>

            {/* Current Tags Display */}
            {formData.tags && formData.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {formData.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
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
                  Updating...
                </>
              ) : (
                'Save Changes'
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
