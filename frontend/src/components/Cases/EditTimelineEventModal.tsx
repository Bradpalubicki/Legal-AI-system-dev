'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import { toast } from 'sonner';

import { API_CONFIG } from '../../config/api';
interface TimelineEvent {
  id: string;
  event_type: string;
  title: string;
  description?: string;
  event_date: string;
  end_date?: string;
  location?: string;
  status: string;
  is_critical_path?: boolean;
  priority_level?: number;
  outcome?: string;
}

interface EditTimelineEventModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  caseId: string;
  event: TimelineEvent;
}

export default function EditTimelineEventModal({ isOpen, onClose, onSuccess, caseId, event }: EditTimelineEventModalProps) {
  const [formData, setFormData] = useState({
    event_type: 'hearing',
    title: '',
    description: '',
    event_date: '',
    end_date: '',
    location: '',
    status: 'scheduled',
    is_critical_path: false,
    priority_level: 2,
    outcome: '',
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Pre-populate form when event changes
  useEffect(() => {
    if (event) {
      // Convert ISO datetime to datetime-local format (YYYY-MM-DDTHH:mm)
      const formatDateTimeLocal = (isoDate: string | undefined) => {
        if (!isoDate) return '';
        const date = new Date(isoDate);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}`;
      };

      setFormData({
        event_type: event.event_type || 'hearing',
        title: event.title || '',
        description: event.description || '',
        event_date: formatDateTimeLocal(event.event_date),
        end_date: formatDateTimeLocal(event.end_date),
        location: event.location || '',
        status: event.status || 'scheduled',
        is_critical_path: event.is_critical_path || false,
        priority_level: event.priority_level || 2,
        outcome: event.outcome || '',
      });
    }
  }, [event]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!formData.event_date) {
      newErrors.event_date = 'Event date is required';
    }

    if (!formData.event_type) {
      newErrors.event_type = 'Event type is required';
    }

    // Enhanced validation: end date must be after event date
    if (formData.end_date && formData.event_date) {
      const startDate = new Date(formData.event_date);
      const endDate = new Date(formData.end_date);
      if (endDate <= startDate) {
        newErrors.end_date = 'End date must be after event date';
      }
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

      const submitData: any = {
        event_type: formData.event_type,
        title: formData.title.trim(),
        event_date: new Date(formData.event_date).toISOString(),
        status: formData.status,
        is_critical_path: formData.is_critical_path,
        priority_level: formData.priority_level,
      };

      if (formData.description?.trim()) {
        submitData.description = formData.description.trim();
      }
      if (formData.end_date) {
        submitData.end_date = new Date(formData.end_date).toISOString();
      }
      if (formData.location?.trim()) {
        submitData.location = formData.location.trim();
      }
      if (formData.outcome?.trim()) {
        submitData.outcome = formData.outcome.trim();
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/cases/${caseId}/events/${event.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(submitData),
      });

      if (!response.ok) {
        throw new Error('Failed to update timeline event');
      }

      toast.success('Timeline event updated successfully', {
        description: formData.title
      });

      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Failed to update timeline event:', error);
      toast.error('Failed to update timeline event', {
        description: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

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
          <h2 className="text-xl font-bold text-gray-900">Edit Timeline Event</h2>
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
            {/* Event Type & Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Event Type <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.event_type}
                  onChange={(e) => handleChange('event_type', e.target.value)}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                    errors.event_type ? 'border-red-500' : 'border-gray-300'
                  }`}
                  disabled={loading}
                >
                  <option value="filing">Filing</option>
                  <option value="hearing">Hearing</option>
                  <option value="deadline">Deadline</option>
                  <option value="meeting">Meeting</option>
                  <option value="objection">Objection</option>
                  <option value="motion">Motion</option>
                  <option value="order">Order</option>
                  <option value="payment">Payment</option>
                  <option value="auction">Auction</option>
                  <option value="discovery">Discovery</option>
                  <option value="trial">Trial</option>
                  <option value="settlement">Settlement</option>
                  <option value="other">Other</option>
                </select>
                {errors.event_type && (
                  <p className="mt-1 text-sm text-red-500">{errors.event_type}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Status
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => handleChange('status', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={loading}
                >
                  <option value="scheduled">Scheduled</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                  <option value="postponed">Postponed</option>
                  <option value="missed">Missed</option>
                </select>
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => handleChange('title', e.target.value)}
                placeholder="e.g., Initial Hearing, Response Deadline"
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.title ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={loading}
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-500">{errors.title}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                placeholder="Event details, purpose, or notes..."
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={loading}
              />
            </div>

            {/* Dates & Location */}
            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Date & Location</h3>

              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Event Date & Time <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="datetime-local"
                      value={formData.event_date}
                      onChange={(e) => handleChange('event_date', e.target.value)}
                      className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                        errors.event_date ? 'border-red-500' : 'border-gray-300'
                      }`}
                      disabled={loading}
                    />
                    {errors.event_date && (
                      <p className="mt-1 text-sm text-red-500">{errors.event_date}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      End Date & Time
                    </label>
                    <input
                      type="datetime-local"
                      value={formData.end_date}
                      onChange={(e) => handleChange('end_date', e.target.value)}
                      className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                        errors.end_date ? 'border-red-500' : 'border-gray-300'
                      }`}
                      disabled={loading}
                    />
                    {errors.end_date && (
                      <p className="mt-1 text-sm text-red-500">{errors.end_date}</p>
                    )}
                    <p className="mt-1 text-xs text-gray-500">Optional for multi-day events</p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Location
                  </label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => handleChange('location', e.target.value)}
                    placeholder="e.g., Courtroom 5A, Conference Room, Virtual"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={loading}
                  />
                </div>
              </div>
            </div>

            {/* Priority & Flags */}
            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Priority & Flags</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Priority Level
                  </label>
                  <select
                    value={formData.priority_level}
                    onChange={(e) => handleChange('priority_level', parseInt(e.target.value))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={loading}
                  >
                    <option value="1">1 - Low</option>
                    <option value="2">2 - Medium</option>
                    <option value="3">3 - High</option>
                    <option value="4">4 - Critical</option>
                    <option value="5">5 - Emergency</option>
                  </select>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="critical_path"
                    checked={formData.is_critical_path}
                    onChange={(e) => handleChange('is_critical_path', e.target.checked)}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                    disabled={loading}
                  />
                  <label htmlFor="critical_path" className="ml-2 text-sm text-gray-700">
                    Mark as Critical Path (affects case timeline if delayed)
                  </label>
                </div>
              </div>
            </div>

            {/* Outcome */}
            <div className="border-t border-gray-200 pt-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Outcome
              </label>
              <textarea
                value={formData.outcome}
                onChange={(e) => handleChange('outcome', e.target.value)}
                placeholder="Record the outcome after the event completes..."
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={loading}
              />
              <p className="mt-1 text-xs text-gray-500">
                Leave empty until event is complete
              </p>
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
