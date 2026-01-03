'use client';

import React, { useState } from 'react';
import {
  Calendar,
  Clock,
  User,
  AlertTriangle,
  Info,
  Scale,
  Phone,
  Video,
  MapPin,
  Send,
  CheckCircle,
  X,
  Shield
} from 'lucide-react';

interface TimeSlot {
  id: string;
  date: string;
  time: string;
  duration: string;
  available: boolean;
  type: 'in-person' | 'phone' | 'video';
  attorney: string;
}

interface AppointmentRequest {
  type: 'consultation' | 'case-review' | 'document-signing' | 'mediation' | 'other';
  preferredMethod: 'in-person' | 'phone' | 'video' | 'any';
  urgency: 'routine' | 'important' | 'urgent';
  duration: '30-minutes' | '1-hour' | '2-hours' | 'half-day';
  description: string;
  preferredDates: string[];
  specialAccommodations: string;
}

interface AppointmentSchedulerProps {
  className?: string;
}

const AppointmentScheduler: React.FC<AppointmentSchedulerProps> = ({ className = '' }) => {
  const [activeTab, setActiveTab] = useState<'schedule' | 'upcoming'>('schedule');
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [showRequestForm, setShowRequestForm] = useState(false);
  const [appointmentRequest, setAppointmentRequest] = useState<AppointmentRequest>({
    type: 'consultation',
    preferredMethod: 'any',
    urgency: 'routine',
    duration: '1-hour',
    description: '',
    preferredDates: [],
    specialAccommodations: ''
  });

  // Mock data - would come from API
  const availableSlots: TimeSlot[] = [
    {
      id: '1',
      date: '2024-01-25',
      time: '10:00 AM',
      duration: '1 hour',
      available: true,
      type: 'in-person',
      attorney: 'Sarah Johnson, Esq.'
    },
    {
      id: '2',
      date: '2024-01-25',
      time: '2:00 PM',
      duration: '30 minutes',
      available: true,
      type: 'phone',
      attorney: 'Sarah Johnson, Esq.'
    },
    {
      id: '3',
      date: '2024-01-26',
      time: '9:00 AM',
      duration: '1 hour',
      available: true,
      type: 'video',
      attorney: 'Sarah Johnson, Esq.'
    }
  ];

  const upcomingAppointments = [
    {
      id: '1',
      date: '2024-01-22',
      time: '2:00 PM',
      type: 'Case Review Meeting',
      method: 'in-person',
      attorney: 'Sarah Johnson, Esq.',
      location: '123 Main St, Suite 200',
      duration: '1 hour',
      description: 'Review case progress and discuss settlement options'
    }
  ];

  const appointmentTypes = [
    {
      value: 'consultation',
      label: 'Initial Consultation',
      description: 'First meeting to discuss your legal matter',
      typicalDuration: '1-2 hours'
    },
    {
      value: 'case-review',
      label: 'Case Review Meeting',
      description: 'Update on case progress and strategy discussion',
      typicalDuration: '30-60 minutes'
    },
    {
      value: 'document-signing',
      label: 'Document Signing',
      description: 'Sign legal documents and agreements',
      typicalDuration: '30 minutes'
    },
    {
      value: 'mediation',
      label: 'Mediation Preparation',
      description: 'Prepare for mediation or settlement conference',
      typicalDuration: '1-2 hours'
    },
    {
      value: 'other',
      label: 'Other',
      description: 'Specify your needs in the description',
      typicalDuration: 'Variable'
    }
  ];

  const getMethodIcon = (method: string) => {
    switch (method) {
      case 'in-person':
        return <MapPin className="h-4 w-4" />;
      case 'phone':
        return <Phone className="h-4 w-4" />;
      case 'video':
        return <Video className="h-4 w-4" />;
      default:
        return <Calendar className="h-4 w-4" />;
    }
  };

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'in-person':
        return 'bg-blue-100 text-blue-800';
      case 'phone':
        return 'bg-green-100 text-green-800';
      case 'video':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleScheduleRequest = () => {
    console.log('Scheduling appointment request:', appointmentRequest);
    alert('Appointment request submitted successfully. Our office will contact you within 24 hours to confirm scheduling.');
    setShowRequestForm(false);
    setAppointmentRequest({
      type: 'consultation',
      preferredMethod: 'any',
      urgency: 'routine',
      duration: '1-hour',
      description: '',
      preferredDates: [],
      specialAccommodations: ''
    });
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center space-x-2 mb-4">
        <Calendar className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-medium text-gray-900">Schedule Appointment</h3>
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          <Info className="h-3 w-3 mr-1" />
          Coordination Only
        </span>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('schedule')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'schedule'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Calendar className="h-4 w-4" />
            <span>Schedule New</span>
          </button>
          <button
            onClick={() => setActiveTab('upcoming')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'upcoming'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Clock className="h-4 w-4" />
            <span>Upcoming</span>
          </button>
        </div>
      </div>

      {/* Schedule New Tab */}
      {activeTab === 'schedule' && (
        <div>
          {/* Important Notice */}
          <div className="mb-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-semibold text-amber-800 mb-2">Appointment Scheduling Notice</h4>
                <ul className="text-sm text-amber-700 space-y-1">
                  <li>• This scheduling system is for coordination purposes only</li>
                  <li>• Appointments do not create attorney-client relationships</li>
                  <li>• All appointments are subject to attorney availability and confirmation</li>
                  <li>• Legal advice is only provided during confirmed appointments</li>
                  <li>• Emergency legal matters should not wait for scheduled appointments</li>
                </ul>
              </div>
            </div>
          </div>

          {!showRequestForm ? (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold text-gray-900">Available Time Slots</h4>
                <button
                  onClick={() => setShowRequestForm(true)}
                  className="inline-flex items-center px-3 py-2 border border-primary-600 text-sm font-medium rounded-md text-primary-600 bg-white hover:bg-primary-50"
                >
                  Request Custom Time
                </button>
              </div>

              {availableSlots.length === 0 ? (
                <div className="text-center py-8">
                  <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 mb-2">No available slots at this time</p>
                  <button
                    onClick={() => setShowRequestForm(true)}
                    className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                  >
                    Request appointment availability
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {availableSlots.map((slot) => (
                    <div key={slot.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div>
                            <div className="font-medium text-gray-900">
                              {new Date(slot.date).toLocaleDateString('en-US', { 
                                weekday: 'long', 
                                year: 'numeric', 
                                month: 'long', 
                                day: 'numeric' 
                              })}
                            </div>
                            <div className="text-sm text-gray-600">{slot.time} ({slot.duration})</div>
                            <div className="text-sm text-gray-500">with {slot.attorney}</div>
                          </div>
                          
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getMethodColor(slot.type)}`}>
                            {getMethodIcon(slot.type)}
                            <span className="ml-1 capitalize">{slot.type.replace('-', ' ')}</span>
                          </span>
                        </div>
                        
                        <button
                          onClick={() => setSelectedSlot(slot)}
                          className="inline-flex items-center px-3 py-2 border border-primary-600 text-sm font-medium rounded-md text-primary-600 bg-white hover:bg-primary-50"
                        >
                          Select
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Request Form */
            <div>
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold text-gray-900">Request Appointment</h4>
                <button
                  onClick={() => setShowRequestForm(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={(e) => { e.preventDefault(); handleScheduleRequest(); }} className="space-y-4">
                {/* Appointment Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Appointment Type
                  </label>
                  <div className="space-y-2">
                    {appointmentTypes.map((type) => (
                      <label key={type.value} className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                        <input
                          type="radio"
                          name="appointmentType"
                          value={type.value}
                          checked={appointmentRequest.type === type.value}
                          onChange={(e) => setAppointmentRequest({...appointmentRequest, type: e.target.value as any})}
                          className="mt-1"
                        />
                        <div className="flex-1">
                          <div className="text-sm font-medium text-gray-900">{type.label}</div>
                          <div className="text-xs text-gray-600">{type.description}</div>
                          <div className="text-xs text-gray-500 mt-1">Typical duration: {type.typicalDuration}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Preferred Method */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Preferred Meeting Method
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      { value: 'any', label: 'Any Method', icon: CheckCircle },
                      { value: 'in-person', label: 'In-Person', icon: MapPin },
                      { value: 'phone', label: 'Phone Call', icon: Phone },
                      { value: 'video', label: 'Video Call', icon: Video }
                    ].map((method) => (
                      <label key={method.value} className="flex items-center space-x-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                        <input
                          type="radio"
                          name="preferredMethod"
                          value={method.value}
                          checked={appointmentRequest.preferredMethod === method.value}
                          onChange={(e) => setAppointmentRequest({...appointmentRequest, preferredMethod: e.target.value as any})}
                        />
                        <method.icon className="h-4 w-4 text-gray-600" />
                        <span className="text-sm">{method.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    What would you like to discuss?
                  </label>
                  <textarea
                    value={appointmentRequest.description}
                    onChange={(e) => setAppointmentRequest({...appointmentRequest, description: e.target.value})}
                    placeholder="Brief description of what you'd like to cover in this appointment..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                    rows={3}
                    required
                  />
                </div>

                {/* Urgency */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Urgency Level
                  </label>
                  <div className="space-y-2">
                    {[
                      { value: 'routine', label: 'Routine - Next 2 weeks', desc: 'General discussion, no immediate deadline' },
                      { value: 'important', label: 'Important - This week', desc: 'Time-sensitive matter that affects case progress' },
                      { value: 'urgent', label: 'Urgent - Within 2 days', desc: 'Critical deadline or emergency situation' }
                    ].map((urgency) => (
                      <label key={urgency.value} className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                        <input
                          type="radio"
                          name="urgency"
                          value={urgency.value}
                          checked={appointmentRequest.urgency === urgency.value}
                          onChange={(e) => setAppointmentRequest({...appointmentRequest, urgency: e.target.value as any})}
                          className="mt-1"
                        />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{urgency.label}</div>
                          <div className="text-xs text-gray-600">{urgency.desc}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Special Accommodations */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Special Accommodations (Optional)
                  </label>
                  <textarea
                    value={appointmentRequest.specialAccommodations}
                    onChange={(e) => setAppointmentRequest({...appointmentRequest, specialAccommodations: e.target.value})}
                    placeholder="Any accessibility needs, language interpretation, or other special requirements..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                    rows={2}
                  />
                </div>

                {/* Submit Button */}
                <div className="pt-4">
                  <button
                    type="submit"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={!appointmentRequest.description}
                  >
                    <Send className="h-4 w-4 mr-2" />
                    Request Appointment
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      )}

      {/* Upcoming Appointments Tab */}
      {activeTab === 'upcoming' && (
        <div>
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              Your confirmed appointments are listed below. Please arrive on time and bring any requested documents.
            </p>
          </div>

          {upcomingAppointments.length === 0 ? (
            <div className="text-center py-8">
              <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No upcoming appointments scheduled</p>
            </div>
          ) : (
            <div className="space-y-4">
              {upcomingAppointments.map((appointment) => (
                <div key={appointment.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="font-medium text-gray-900">{appointment.type}</h4>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getMethodColor(appointment.method)}`}>
                          {getMethodIcon(appointment.method)}
                          <span className="ml-1 capitalize">{appointment.method.replace('-', ' ')}</span>
                        </span>
                      </div>
                      
                      <div className="space-y-1 text-sm text-gray-600">
                        <div className="flex items-center space-x-2">
                          <Calendar className="h-4 w-4" />
                          <span>{new Date(appointment.date).toLocaleDateString('en-US', { 
                            weekday: 'long', 
                            year: 'numeric', 
                            month: 'long', 
                            day: 'numeric' 
                          })}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Clock className="h-4 w-4" />
                          <span>{appointment.time} ({appointment.duration})</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <User className="h-4 w-4" />
                          <span>with {appointment.attorney}</span>
                        </div>
                        {appointment.method === 'in-person' && (
                          <div className="flex items-center space-x-2">
                            <MapPin className="h-4 w-4" />
                            <span>{appointment.location}</span>
                          </div>
                        )}
                      </div>
                      
                      {appointment.description && (
                        <div className="mt-2 p-2 bg-gray-50 rounded text-sm text-gray-700">
                          {appointment.description}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex flex-col space-y-2">
                      <button className="px-3 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50">
                        Reschedule
                      </button>
                      <button className="px-3 py-1 text-xs font-medium text-error-600 bg-white border border-error-300 rounded hover:bg-error-50">
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Appointment Confirmation Modal */}
      {selectedSlot && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Confirm Appointment</h3>
              <button
                onClick={() => setSelectedSlot(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-3 mb-6">
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm font-medium text-gray-900">
                  {new Date(selectedSlot.date).toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </div>
                <div className="text-sm text-gray-600">{selectedSlot.time}</div>
                <div className="text-sm text-gray-600">Duration: {selectedSlot.duration}</div>
                <div className="text-sm text-gray-600">with {selectedSlot.attorney}</div>
                <div className="flex items-center space-x-1 mt-1">
                  {getMethodIcon(selectedSlot.type)}
                  <span className="text-sm text-gray-600 capitalize">{selectedSlot.type.replace('-', ' ')} meeting</span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <button
                onClick={() => setSelectedSlot(null)}
                className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  console.log('Confirming appointment:', selectedSlot);
                  alert('Appointment request sent! Our office will contact you within 2 hours to confirm.');
                  setSelectedSlot(null);
                }}
                className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                Confirm Appointment
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Important Disclaimers */}
      <div className="mt-6 space-y-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <Info className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-sm font-semibold text-blue-900 mb-2">Appointment Guidelines</h5>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Arrive 15 minutes early for in-person appointments</li>
                <li>• Bring photo ID and any requested documents</li>
                <li>• Phone and video appointments require prior technology setup</li>
                <li>• Reschedule at least 24 hours in advance when possible</li>
                <li>• Emergency legal matters should not wait for scheduled appointments</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="bg-legal-50 border border-legal-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <Scale className="h-5 w-5 text-legal-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-sm font-semibold text-legal-900 mb-2">Appointment Scheduling Disclaimer</h5>
              <ul className="text-sm text-legal-700 space-y-1">
                <li>• Appointment scheduling is for coordination purposes only</li>
                <li>• No attorney-client relationship is created by scheduling</li>
                <li>• Legal advice is only provided during confirmed consultations</li>
                <li>• All appointments are subject to attorney availability and confirmation</li>
                <li>• Confidentiality protections begin only with confirmed representation</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AppointmentScheduler;