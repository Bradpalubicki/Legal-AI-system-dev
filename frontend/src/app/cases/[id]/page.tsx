'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { API_CONFIG } from '../../../config/api';
import {
  Scale,
  ArrowLeft,
  Edit,
  Trash2,
  FileText,
  Users,
  Calendar,
  DollarSign,
  Building,
  User,
  Phone,
  Mail,
  MapPin,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  Search,
  Filter,
  Square,
  CheckSquare,
  Download,
  Plus,
  Link as LinkIcon,
  ExternalLink
} from 'lucide-react';
import {
  getCase,
  getCaseParties,
  getTimeline,
  getTransactions,
  deleteCase,
  formatCaseType,
  formatCaseStatus,
  getStatusColor,
  type LegalCase,
  type CaseParty,
  type TimelineEvent,
  type FinancialTransaction
} from '@/lib/api/cases';
import { toast } from 'sonner';
import EditCaseModal from '@/components/Cases/EditCaseModal';
import AddPartyModal from '@/components/Cases/AddPartyModal';
import AddTimelineEventModal from '@/components/Cases/AddTimelineEventModal';
import AddTransactionModal from '@/components/Cases/AddTransactionModal';
import EditPartyModal from '@/components/Cases/EditPartyModal';
import EditTimelineEventModal from '@/components/Cases/EditTimelineEventModal';
import EditTransactionModal from '@/components/Cases/EditTransactionModal';
import { exportPartiesToCSV, exportTimelineToCSV, exportTransactionsToCSV } from '@/lib/export';
import { exportTimelineToICal } from '@/lib/calendar';

// TypeScript interface for case documents
interface CaseDocument {
  link_id: string;
  document_id: string;
  file_name: string;
  file_type: string;
  upload_date: string;
  document_role?: string;
  filing_date?: string;
  summary?: string;
  parties?: string[];
  keywords?: string[];
}

export default function CaseDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const caseId = params.id as string;

  const [activeTab, setActiveTab] = useState<'overview' | 'parties' | 'timeline' | 'documents' | 'financials'>('overview');
  const [caseData, setCaseData] = useState<LegalCase | null>(null);
  const [parties, setParties] = useState<CaseParty[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [transactions, setTransactions] = useState<FinancialTransaction[]>([]);
  const [documents, setDocuments] = useState<CaseDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showAddPartyModal, setShowAddPartyModal] = useState(false);
  const [showAddEventModal, setShowAddEventModal] = useState(false);
  const [showAddTransactionModal, setShowAddTransactionModal] = useState(false);

  // Edit modal states
  const [showEditPartyModal, setShowEditPartyModal] = useState(false);
  const [showEditEventModal, setShowEditEventModal] = useState(false);
  const [showEditTransactionModal, setShowEditTransactionModal] = useState(false);
  const [selectedParty, setSelectedParty] = useState<CaseParty | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [selectedTransaction, setSelectedTransaction] = useState<FinancialTransaction | null>(null);

  // Delete confirmation states
  const [deleteItemType, setDeleteItemType] = useState<'party' | 'event' | 'transaction' | null>(null);
  const [deleteItemId, setDeleteItemId] = useState<string | null>(null);

  // Filter states
  const [partyRoleFilter, setPartyRoleFilter] = useState<string>('all');
  const [partySearchQuery, setPartySearchQuery] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('all');
  const [eventStatusFilter, setEventStatusFilter] = useState<string>('all');
  const [eventSearchQuery, setEventSearchQuery] = useState('');
  const [transactionTypeFilter, setTransactionTypeFilter] = useState<string>('all');
  const [transactionStatusFilter, setTransactionStatusFilter] = useState<string>('all');
  const [transactionSearchQuery, setTransactionSearchQuery] = useState('');

  // Bulk selection states
  const [selectedPartyIds, setSelectedPartyIds] = useState<Set<string>>(new Set());
  const [selectedEventIds, setSelectedEventIds] = useState<Set<string>>(new Set());
  const [selectedTransactionIds, setSelectedTransactionIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadCaseData();
  }, [caseId]);

  useEffect(() => {
    // Load additional data based on active tab
    if (activeTab === 'parties' && parties.length === 0) {
      loadParties();
    } else if (activeTab === 'timeline' && timeline.length === 0) {
      loadTimeline();
    } else if (activeTab === 'documents' && documents.length === 0) {
      loadDocuments();
    } else if (activeTab === 'financials' && transactions.length === 0) {
      loadTransactions();
    }
  }, [activeTab]);

  const loadCaseData = async () => {
    try {
      setLoading(true);
      const data = await getCase(caseId);
      setCaseData(data);
    } catch (error: any) {
      console.error('Failed to load case:', error);
      toast.error('Failed to load case details', {
        description: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const loadParties = async () => {
    try {
      const data = await getCaseParties(caseId);
      setParties(data);
    } catch (error: any) {
      console.error('Failed to load parties:', error);
      toast.error('Failed to load parties', {
        description: error.message
      });
    }
  };

  const loadTimeline = async () => {
    try {
      const data = await getTimeline(caseId);
      setTimeline(data);
    } catch (error: any) {
      console.error('Failed to load timeline:', error);
      toast.error('Failed to load timeline', {
        description: error.message
      });
    }
  };

  const loadTransactions = async () => {
    try {
      const data = await getTransactions(caseId);
      setTransactions(data);
    } catch (error: any) {
      console.error('Failed to load transactions:', error);
      toast.error('Failed to load transactions', {
        description: error.message
      });
    }
  };

  const loadDocuments = async () => {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/cases/${caseId}/documents`);
      if (!response.ok) {
        throw new Error('Failed to fetch documents');
      }
      const data = await response.json();
      setDocuments(data);
    } catch (error: any) {
      console.error('Failed to load documents:', error);
      toast.error('Failed to load documents', {
        description: error.message
      });
    }
  };

  const unlinkDocument = async (linkId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/cases/${caseId}/documents/${linkId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to unlink document');
      }

      toast.success('Document unlinked successfully');
      await loadDocuments();
    } catch (error: any) {
      console.error('Failed to unlink document:', error);
      toast.error('Failed to unlink document', {
        description: error.message
      });
    }
  };

  const handleDelete = async () => {
    try {
      await deleteCase(caseId);
      toast.success('Case deleted successfully');
      router.push('/cases');
    } catch (error: any) {
      console.error('Failed to delete case:', error);
      toast.error('Failed to delete case', {
        description: error.message
      });
    }
  };

  const handleDeleteItem = async () => {
    if (!deleteItemType || !deleteItemId) return;

    try {
      const endpoint = deleteItemType === 'party'
        ? `${API_CONFIG.BASE_URL}/api/v1/cases/${caseId}/parties/${deleteItemId}`
        : deleteItemType === 'event'
        ? `${API_CONFIG.BASE_URL}/api/v1/cases/${caseId}/events/${deleteItemId}`
        : `${API_CONFIG.BASE_URL}/api/v1/cases/${caseId}/transactions/${deleteItemId}`;

      const response = await fetch(endpoint, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete ${deleteItemType}`);
      }

      toast.success(`${deleteItemType.charAt(0).toUpperCase() + deleteItemType.slice(1)} deleted successfully`);

      // Refresh the appropriate list
      if (deleteItemType === 'party') {
        loadParties();
      } else if (deleteItemType === 'event') {
        loadTimeline();
      } else {
        loadTransactions();
      }

      // Close delete confirmation
      setDeleteItemType(null);
      setDeleteItemId(null);
    } catch (error: any) {
      console.error(`Failed to delete ${deleteItemType}:`, error);
      toast.error(`Failed to delete ${deleteItemType}`, {
        description: error.message
      });
    }
  };

  const openEditParty = (party: CaseParty) => {
    setSelectedParty(party);
    setShowEditPartyModal(true);
  };

  const openEditEvent = (event: TimelineEvent) => {
    setSelectedEvent(event);
    setShowEditEventModal(true);
  };

  const openEditTransaction = (transaction: FinancialTransaction) => {
    setSelectedTransaction(transaction);
    setShowEditTransactionModal(true);
  };

  const openDeleteConfirmation = (type: 'party' | 'event' | 'transaction', id: string) => {
    setDeleteItemType(type);
    setDeleteItemId(id);
  };

  // Bulk selection handlers
  const togglePartySelection = (id: string) => {
    const newSet = new Set(selectedPartyIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelectedPartyIds(newSet);
  };

  const toggleEventSelection = (id: string) => {
    const newSet = new Set(selectedEventIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelectedEventIds(newSet);
  };

  const toggleTransactionSelection = (id: string) => {
    const newSet = new Set(selectedTransactionIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelectedTransactionIds(newSet);
  };

  const selectAllParties = () => {
    if (selectedPartyIds.size === filteredParties.length) {
      setSelectedPartyIds(new Set());
    } else {
      setSelectedPartyIds(new Set(filteredParties.map(p => p.id)));
    }
  };

  const selectAllEvents = () => {
    if (selectedEventIds.size === filteredEvents.length) {
      setSelectedEventIds(new Set());
    } else {
      setSelectedEventIds(new Set(filteredEvents.map(e => e.id)));
    }
  };

  const selectAllTransactions = () => {
    if (selectedTransactionIds.size === filteredTransactions.length) {
      setSelectedTransactionIds(new Set());
    } else {
      setSelectedTransactionIds(new Set(filteredTransactions.map(t => t.id)));
    }
  };

  const handleBulkDelete = async (type: 'party' | 'event' | 'transaction') => {
    const selectedIds = type === 'party'
      ? selectedPartyIds
      : type === 'event'
      ? selectedEventIds
      : selectedTransactionIds;

    if (selectedIds.size === 0) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete ${selectedIds.size} ${type}${selectedIds.size > 1 ? (type === 'party' ? 'ies' : 's') : ''}? This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
      const baseEndpoint = type === 'party'
        ? `${API_CONFIG.BASE_URL}/api/v1/cases/${caseId}/parties`
        : type === 'event'
        ? `${API_CONFIG.BASE_URL}/api/v1/cases/${caseId}/events`
        : `${API_CONFIG.BASE_URL}/api/v1/cases/${caseId}/transactions`;

      // Delete all selected items in parallel
      await Promise.all(
        Array.from(selectedIds).map(id =>
          fetch(`${baseEndpoint}/${id}`, { method: 'DELETE' })
        )
      );

      toast.success(`Successfully deleted ${selectedIds.size} ${type}${selectedIds.size > 1 ? (type === 'party' ? 'ies' : 's') : ''}`);

      // Clear selection
      if (type === 'party') {
        setSelectedPartyIds(new Set());
        loadParties();
      } else if (type === 'event') {
        setSelectedEventIds(new Set());
        loadTimeline();
      } else {
        setSelectedTransactionIds(new Set());
        loadTransactions();
      }
    } catch (error: any) {
      console.error(`Failed to delete ${type}s:`, error);
      toast.error(`Failed to delete ${type}s`, {
        description: error.message
      });
    }
  };

  // Filter functions
  const filteredParties = parties.filter((party) => {
    const matchesRole = partyRoleFilter === 'all' || party.role === partyRoleFilter;
    const matchesSearch = partySearchQuery === '' ||
      party.name.toLowerCase().includes(partySearchQuery.toLowerCase()) ||
      party.legal_name?.toLowerCase().includes(partySearchQuery.toLowerCase()) ||
      party.email?.toLowerCase().includes(partySearchQuery.toLowerCase());
    return matchesRole && matchesSearch;
  });

  const filteredEvents = timeline.filter((event) => {
    const matchesType = eventTypeFilter === 'all' || event.event_type === eventTypeFilter;
    const matchesStatus = eventStatusFilter === 'all' || event.status === eventStatusFilter;
    const matchesSearch = eventSearchQuery === '' ||
      event.title.toLowerCase().includes(eventSearchQuery.toLowerCase()) ||
      event.description?.toLowerCase().includes(eventSearchQuery.toLowerCase());
    return matchesType && matchesStatus && matchesSearch;
  });

  const filteredTransactions = transactions.filter((transaction) => {
    const matchesType = transactionTypeFilter === 'all' || transaction.transaction_type === transactionTypeFilter;
    const matchesStatus = transactionStatusFilter === 'all' || transaction.payment_status === transactionStatusFilter;
    const matchesSearch = transactionSearchQuery === '' ||
      transaction.description?.toLowerCase().includes(transactionSearchQuery.toLowerCase()) ||
      transaction.amount.toString().includes(transactionSearchQuery);
    return matchesType && matchesStatus && matchesSearch;
  });

  const getEventStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'cancelled':
      case 'missed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'in_progress':
        return <Clock className="w-4 h-4 text-blue-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-yellow-600" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-600">Loading case details...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Case Not Found</h2>
            <p className="text-gray-600 mb-6">The case you're looking for doesn't exist.</p>
            <Button onClick={() => router.push('/cases')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Cases
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="outline"
            onClick={() => router.push('/cases')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Cases
          </Button>

          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <Scale className="w-8 h-8 text-primary-600" />
                <h1 className="text-3xl font-bold text-gray-900">{caseData.case_name}</h1>
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span className="font-mono">{caseData.case_number}</span>
                <span>•</span>
                <span>{formatCaseType(caseData.case_type)}</span>
                <span>•</span>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(caseData.status)}`}>
                  {formatCaseStatus(caseData.status)}
                </span>
              </div>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowEditModal(true)}>
                <Edit className="w-4 h-4 mr-2" />
                Edit
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowDeleteConfirm(true)}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </Button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="flex gap-6">
            {[
              { id: 'overview', label: 'Overview', icon: FileText },
              { id: 'parties', label: 'Parties', icon: Users },
              { id: 'timeline', label: 'Timeline', icon: Calendar },
              { id: 'documents', label: 'Documents', icon: FileText },
              { id: 'financials', label: 'Financials', icon: DollarSign },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-1 py-3 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="text-sm font-semibold text-gray-700">Case Number</label>
                    <p className="mt-1 font-mono text-gray-900">{caseData.case_number}</p>
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-gray-700">Case Type</label>
                    <p className="mt-1 text-gray-900">{formatCaseType(caseData.case_type)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-gray-700">Status</label>
                    <p className="mt-1">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(caseData.status)}`}>
                        {formatCaseStatus(caseData.status)}
                      </span>
                    </p>
                  </div>
                  {caseData.current_phase && (
                    <div>
                      <label className="text-sm font-semibold text-gray-700">Current Phase</label>
                      <p className="mt-1 text-gray-900">{caseData.current_phase}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Court Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building className="w-5 h-5" />
                  Court Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {caseData.court_name && (
                    <div>
                      <label className="text-sm font-semibold text-gray-700">Court Name</label>
                      <p className="mt-1 text-gray-900">{caseData.court_name}</p>
                    </div>
                  )}
                  {caseData.jurisdiction && (
                    <div>
                      <label className="text-sm font-semibold text-gray-700">Jurisdiction</label>
                      <p className="mt-1 text-gray-900">{caseData.jurisdiction}</p>
                    </div>
                  )}
                  {caseData.judge_name && (
                    <div>
                      <label className="text-sm font-semibold text-gray-700">Judge</label>
                      <p className="mt-1 text-gray-900">{caseData.judge_name}</p>
                    </div>
                  )}
                  {caseData.court_division && (
                    <div>
                      <label className="text-sm font-semibold text-gray-700">Court Division</label>
                      <p className="mt-1 text-gray-900">{caseData.court_division}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Important Dates */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  Important Dates
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {caseData.filing_date && (
                    <div>
                      <label className="text-sm font-semibold text-gray-700">Filing Date</label>
                      <p className="mt-1 text-gray-900">{new Date(caseData.filing_date).toLocaleDateString()}</p>
                    </div>
                  )}
                  {caseData.status_date && (
                    <div>
                      <label className="text-sm font-semibold text-gray-700">Status Date</label>
                      <p className="mt-1 text-gray-900">{new Date(caseData.status_date).toLocaleDateString()}</p>
                    </div>
                  )}
                  {caseData.estimated_completion_date && (
                    <div>
                      <label className="text-sm font-semibold text-gray-700">Estimated Completion</label>
                      <p className="mt-1 text-gray-900">{new Date(caseData.estimated_completion_date).toLocaleDateString()}</p>
                    </div>
                  )}
                  {caseData.close_date && (
                    <div>
                      <label className="text-sm font-semibold text-gray-700">Close Date</label>
                      <p className="mt-1 text-gray-900">{new Date(caseData.close_date).toLocaleDateString()}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Description */}
            {caseData.description && (
              <Card>
                <CardHeader>
                  <CardTitle>Description</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700 whitespace-pre-wrap">{caseData.description}</p>
                </CardContent>
              </Card>
            )}

            {/* Notes */}
            {caseData.notes && (
              <Card>
                <CardHeader>
                  <CardTitle>Notes</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700 whitespace-pre-wrap">{caseData.notes}</p>
                </CardContent>
              </Card>
            )}

            {/* Tags */}
            {caseData.tags && caseData.tags.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Tags</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {caseData.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {activeTab === 'parties' && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Parties ({filteredParties.length}{parties.length !== filteredParties.length && ` of ${parties.length}`})
                </CardTitle>
                <div className="flex items-center gap-2">
                  {filteredParties.length > 0 && (
                    <Button
                      variant="outline"
                      onClick={() => exportPartiesToCSV(filteredParties, caseData?.case_name || 'case')}
                      title="Export filtered parties to CSV"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Export CSV
                    </Button>
                  )}
                  <Button onClick={() => setShowAddPartyModal(true)}>
                    <Users className="w-4 h-4 mr-2" />
                    Add Party
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Filters */}
              {parties.length > 0 && (
                <div className="mb-4 flex flex-col sm:flex-row gap-3">
                  {/* Role Filter */}
                  <div className="flex items-center gap-2 flex-1">
                    <Filter className="w-4 h-4 text-gray-500" />
                    <select
                      value={partyRoleFilter}
                      onChange={(e) => setPartyRoleFilter(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="all">All Roles</option>
                      <option value="plaintiff">Plaintiff</option>
                      <option value="defendant">Defendant</option>
                      <option value="debtor">Debtor</option>
                      <option value="creditor">Creditor</option>
                      <option value="trustee">Trustee</option>
                      <option value="attorney">Attorney</option>
                      <option value="witness">Witness</option>
                      <option value="expert">Expert Witness</option>
                      <option value="judge">Judge</option>
                      <option value="mediator">Mediator</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  {/* Search */}
                  <div className="flex items-center gap-2 flex-1">
                    <Search className="w-4 h-4 text-gray-500" />
                    <input
                      type="text"
                      value={partySearchQuery}
                      onChange={(e) => setPartySearchQuery(e.target.value)}
                      placeholder="Search parties by name, email..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    {partySearchQuery && (
                      <button
                        onClick={() => setPartySearchQuery('')}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Bulk Action Bar - Parties */}
              {selectedPartyIds.size > 0 && (
                <div className="mb-4 bg-primary-50 border border-primary-200 rounded-lg p-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckSquare className="w-5 h-5 text-primary-600" />
                    <span className="font-medium text-primary-900">
                      {selectedPartyIds.size} part{selectedPartyIds.size === 1 ? 'y' : 'ies'} selected
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedPartyIds(new Set())}
                    >
                      Clear Selection
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleBulkDelete('party')}
                      className="bg-red-600 hover:bg-red-700 text-white"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete Selected
                    </Button>
                  </div>
                </div>
              )}

              {parties.length === 0 ? (
                <div className="text-center py-12">
                  <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 mb-4">No parties added yet</p>
                  <Button onClick={() => setShowAddPartyModal(true)}>
                    <Users className="w-4 h-4 mr-2" />
                    Add First Party
                  </Button>
                </div>
              ) : filteredParties.length === 0 ? (
                <div className="text-center py-12">
                  <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 mb-2">No parties match your filters</p>
                  <button
                    onClick={() => {
                      setPartyRoleFilter('all');
                      setPartySearchQuery('');
                    }}
                    className="text-sm text-primary-600 hover:text-primary-700"
                  >
                    Clear all filters
                  </button>
                </div>
              ) : (
                <>
                  {/* Select All */}
                  {filteredParties.length > 0 && (
                    <div className="mb-3 pb-3 border-b border-gray-200">
                      <button
                        onClick={selectAllParties}
                        className="flex items-center gap-2 text-sm text-gray-700 hover:text-primary-600 transition-colors"
                      >
                        {selectedPartyIds.size === filteredParties.length ? (
                          <CheckSquare className="w-4 h-4" />
                        ) : (
                          <Square className="w-4 h-4" />
                        )}
                        <span>Select All ({filteredParties.length})</span>
                      </button>
                    </div>
                  )}

                  <div className="space-y-4">
                    {filteredParties.map((party) => (
                      <div
                        key={party.id}
                        className={`border rounded-lg p-4 transition-colors ${
                          selectedPartyIds.has(party.id)
                            ? 'border-primary-500 bg-primary-50'
                            : 'border-gray-200 hover:border-primary-300'
                        }`}
                      >
                        <div className="flex items-start gap-3 mb-3">
                          {/* Checkbox */}
                          <button
                            onClick={() => togglePartySelection(party.id)}
                            className="mt-1 text-gray-400 hover:text-primary-600 transition-colors flex-shrink-0"
                          >
                            {selectedPartyIds.has(party.id) ? (
                              <CheckSquare className="w-5 h-5 text-primary-600" />
                            ) : (
                              <Square className="w-5 h-5" />
                            )}
                          </button>

                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900">{party.name}</h3>
                            {party.legal_name && party.legal_name !== party.name && (
                              <p className="text-sm text-gray-600">{party.legal_name}</p>
                            )}
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-xs font-medium">
                              {party.role}
                            </span>
                            <button
                              onClick={() => openEditParty(party)}
                              className="p-1 text-gray-400 hover:text-primary-600 transition-colors"
                              title="Edit party"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => openDeleteConfirmation('party', party.id)}
                              className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                              title="Delete party"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                        {party.email && (
                          <div className="flex items-center gap-2 text-gray-600">
                            <Mail className="w-4 h-4" />
                            <a href={`mailto:${party.email}`} className="hover:text-primary-600">
                              {party.email}
                            </a>
                          </div>
                        )}
                        {party.phone && (
                          <div className="flex items-center gap-2 text-gray-600">
                            <Phone className="w-4 h-4" />
                            <a href={`tel:${party.phone}`} className="hover:text-primary-600">
                              {party.phone}
                            </a>
                          </div>
                        )}
                        {party.address && (
                          <div className="flex items-center gap-2 text-gray-600">
                            <MapPin className="w-4 h-4" />
                            <span>{party.address}</span>
                          </div>
                        )}
                        {party.represented_by && (
                          <div className="flex items-center gap-2 text-gray-600">
                            <User className="w-4 h-4" />
                            <span>Represented by: {party.represented_by}</span>
                          </div>
                        )}
                      </div>

                        {party.notes && (
                          <p className="mt-3 text-sm text-gray-600 border-t border-gray-100 pt-3">
                            {party.notes}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        )}

        {activeTab === 'timeline' && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  Timeline ({filteredEvents.length}{timeline.length !== filteredEvents.length && ` of ${timeline.length}`})
                </CardTitle>
                <div className="flex items-center gap-2">
                  {filteredEvents.length > 0 && (
                    <>
                      <Button
                        variant="outline"
                        onClick={() => exportTimelineToICal(filteredEvents, caseData?.case_name || 'case')}
                        title="Export to calendar (iCal format)"
                      >
                        <Calendar className="w-4 h-4 mr-2" />
                        Export Calendar
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => exportTimelineToCSV(filteredEvents, caseData?.case_name || 'case')}
                        title="Export filtered timeline to CSV"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Export CSV
                      </Button>
                    </>
                  )}
                  <Button onClick={() => setShowAddEventModal(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Event
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Filters */}
              {timeline.length > 0 && (
                <div className="mb-4 flex flex-col sm:flex-row gap-3">
                  {/* Type Filter */}
                  <div className="flex items-center gap-2 flex-1">
                    <Filter className="w-4 h-4 text-gray-500" />
                    <select
                      value={eventTypeFilter}
                      onChange={(e) => setEventTypeFilter(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="all">All Types</option>
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
                  </div>

                  {/* Status Filter */}
                  <div className="flex items-center gap-2 flex-1">
                    <Filter className="w-4 h-4 text-gray-500" />
                    <select
                      value={eventStatusFilter}
                      onChange={(e) => setEventStatusFilter(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="all">All Statuses</option>
                      <option value="scheduled">Scheduled</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Completed</option>
                      <option value="cancelled">Cancelled</option>
                      <option value="postponed">Postponed</option>
                      <option value="missed">Missed</option>
                    </select>
                  </div>

                  {/* Search */}
                  <div className="flex items-center gap-2 flex-1">
                    <Search className="w-4 h-4 text-gray-500" />
                    <input
                      type="text"
                      value={eventSearchQuery}
                      onChange={(e) => setEventSearchQuery(e.target.value)}
                      placeholder="Search events..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    {eventSearchQuery && (
                      <button
                        onClick={() => setEventSearchQuery('')}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Bulk Action Bar - Events */}
              {selectedEventIds.size > 0 && (
                <div className="mb-4 bg-primary-50 border border-primary-200 rounded-lg p-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckSquare className="w-5 h-5 text-primary-600" />
                    <span className="font-medium text-primary-900">
                      {selectedEventIds.size} event{selectedEventIds.size === 1 ? '' : 's'} selected
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedEventIds(new Set())}
                    >
                      Clear Selection
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleBulkDelete('event')}
                      className="bg-red-600 hover:bg-red-700 text-white"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete Selected
                    </Button>
                  </div>
                </div>
              )}

              {timeline.length === 0 ? (
                <div className="text-center py-12">
                  <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 mb-4">No timeline events yet</p>
                  <Button onClick={() => setShowAddEventModal(true)}>
                    <Calendar className="w-4 h-4 mr-2" />
                    Add First Event
                  </Button>
                </div>
              ) : filteredEvents.length === 0 ? (
                <div className="text-center py-12">
                  <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 mb-2">No events match your filters</p>
                  <button
                    onClick={() => {
                      setEventTypeFilter('all');
                      setEventStatusFilter('all');
                      setEventSearchQuery('');
                    }}
                    className="text-sm text-primary-600 hover:text-primary-700"
                  >
                    Clear all filters
                  </button>
                </div>
              ) : (
                <>
                  {/* Select All */}
                  {filteredEvents.length > 0 && (
                    <div className="mb-3 pb-3 border-b border-gray-200">
                      <button
                        onClick={selectAllEvents}
                        className="flex items-center gap-2 text-sm text-gray-700 hover:text-primary-600 transition-colors"
                      >
                        {selectedEventIds.size === filteredEvents.length ? (
                          <CheckSquare className="w-4 h-4" />
                        ) : (
                          <Square className="w-4 h-4" />
                        )}
                        <span>Select All ({filteredEvents.length})</span>
                      </button>
                    </div>
                  )}

                  <div className="space-y-4">
                    {filteredEvents.sort((a, b) => new Date(b.event_date).getTime() - new Date(a.event_date).getTime()).map((event, index) => (
                      <div
                        key={event.id}
                        className="relative pl-8 pb-4 border-l-2 border-gray-200 last:border-l-0"
                      >
                        <div className="absolute left-0 top-0 -translate-x-1/2 bg-white">
                          {getEventStatusIcon(event.status)}
                        </div>

                        <div className={`rounded-lg p-4 ${
                          selectedEventIds.has(event.id)
                            ? 'bg-primary-50 border border-primary-500'
                            : 'bg-gray-50'
                        }`}>
                          <div className="flex items-start gap-3 mb-2">
                            {/* Checkbox */}
                            <button
                              onClick={() => toggleEventSelection(event.id)}
                              className="mt-1 text-gray-400 hover:text-primary-600 transition-colors flex-shrink-0"
                            >
                              {selectedEventIds.has(event.id) ? (
                                <CheckSquare className="w-5 h-5 text-primary-600" />
                              ) : (
                                <Square className="w-5 h-5" />
                              )}
                            </button>

                            <div className="flex-1">
                              <h3 className="font-semibold text-gray-900">{event.title}</h3>
                              <p className="text-sm text-gray-600">
                                {new Date(event.event_date).toLocaleDateString()} at {new Date(event.event_date).toLocaleTimeString()}
                              </p>
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                                {event.event_type}
                              </span>
                              <button
                                onClick={() => openEditEvent(event)}
                                className="p-1 text-gray-400 hover:text-primary-600 transition-colors"
                                title="Edit event"
                              >
                                <Edit className="w-3 h-3" />
                              </button>
                              <button
                                onClick={() => openDeleteConfirmation('event', event.id)}
                                className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                                title="Delete event"
                              >
                                <Trash2 className="w-3 h-3" />
                              </button>
                            </div>
                          </div>

                        {event.description && (
                          <p className="text-sm text-gray-700 mb-2">{event.description}</p>
                        )}

                        {event.location && (
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <MapPin className="w-4 h-4" />
                            <span>{event.location}</span>
                          </div>
                        )}

                        {event.outcome && (
                          <div className="mt-3 p-3 bg-white rounded border border-gray-200">
                            <p className="text-sm font-semibold text-gray-700 mb-1">Outcome:</p>
                            <p className="text-sm text-gray-600">{event.outcome}</p>
                          </div>
                        )}

                        {event.is_critical_path && (
                          <div className="mt-2">
                            <span className="inline-flex items-center px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium">
                              Critical Path
                            </span>
                          </div>
                        )}
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        )}

        {activeTab === 'documents' && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Documents ({documents.length})
                </CardTitle>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      loadDocuments();
                      toast.info('Refreshing documents...');
                    }}
                  >
                    Refresh
                  </Button>
                  <Button onClick={() => router.push(`/documents?caseId=${caseId}`)}>
                    <LinkIcon className="w-4 h-4 mr-2" />
                    Link Document
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {documents.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 mb-4">
                    No documents linked to this case yet
                  </p>
                  <Button onClick={() => router.push(`/documents?caseId=${caseId}`)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Link First Document
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {documents.map((doc) => (
                    <div
                      key={doc.link_id}
                      className="flex items-start justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <FileText className="w-5 h-5 text-primary-600" />
                          <div>
                            <h4 className="font-medium text-gray-900">{doc.file_name}</h4>
                            <p className="text-sm text-gray-500">
                              {doc.file_type?.toUpperCase() || 'Unknown type'} • Uploaded {new Date(doc.upload_date).toLocaleDateString()}
                            </p>
                          </div>
                        </div>

                        {doc.document_role && (
                          <div className="ml-8 mb-2">
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {doc.document_role}
                            </span>
                          </div>
                        )}

                        {doc.summary && (
                          <div className="ml-8 mb-2">
                            <p className="text-sm text-gray-600 line-clamp-2">{doc.summary}</p>
                          </div>
                        )}

                        {doc.keywords && doc.keywords.length > 0 && (
                          <div className="ml-8 flex flex-wrap gap-1">
                            {doc.keywords.slice(0, 5).map((keyword, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700"
                              >
                                {keyword}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/documents/${doc.document_id}`)}
                          title="View document"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            if (confirm('Are you sure you want to unlink this document from the case?')) {
                              unlinkDocument(doc.link_id);
                            }
                          }}
                          className="text-red-600 hover:text-red-700"
                          title="Unlink document"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {activeTab === 'financials' && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5" />
                  Financial Transactions ({filteredTransactions.length}{transactions.length !== filteredTransactions.length && ` of ${transactions.length}`})
                </CardTitle>
                <div className="flex items-center gap-2">
                  {filteredTransactions.length > 0 && (
                    <Button
                      variant="outline"
                      onClick={() => exportTransactionsToCSV(filteredTransactions, caseData?.case_name || 'case')}
                      title="Export filtered transactions to CSV"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Export CSV
                    </Button>
                  )}
                  <Button onClick={() => setShowAddTransactionModal(true)}>
                    <DollarSign className="w-4 h-4 mr-2" />
                    Add Transaction
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Filters */}
              {transactions.length > 0 && (
                <div className="mb-4 flex flex-col sm:flex-row gap-3">
                  {/* Type Filter */}
                  <div className="flex items-center gap-2 flex-1">
                    <Filter className="w-4 h-4 text-gray-500" />
                    <select
                      value={transactionTypeFilter}
                      onChange={(e) => setTransactionTypeFilter(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="all">All Types</option>
                      <option value="payment">Payment</option>
                      <option value="distribution">Distribution</option>
                      <option value="fee">Fee</option>
                      <option value="deposit">Deposit</option>
                      <option value="refund">Refund</option>
                      <option value="bid">Bid</option>
                      <option value="transfer">Transfer</option>
                      <option value="settlement">Settlement</option>
                      <option value="reimbursement">Reimbursement</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  {/* Status Filter */}
                  <div className="flex items-center gap-2 flex-1">
                    <Filter className="w-4 h-4 text-gray-500" />
                    <select
                      value={transactionStatusFilter}
                      onChange={(e) => setTransactionStatusFilter(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="all">All Statuses</option>
                      <option value="pending">Pending</option>
                      <option value="processing">Processing</option>
                      <option value="completed">Completed</option>
                      <option value="failed">Failed</option>
                      <option value="cancelled">Cancelled</option>
                      <option value="refunded">Refunded</option>
                    </select>
                  </div>

                  {/* Search */}
                  <div className="flex items-center gap-2 flex-1">
                    <Search className="w-4 h-4 text-gray-500" />
                    <input
                      type="text"
                      value={transactionSearchQuery}
                      onChange={(e) => setTransactionSearchQuery(e.target.value)}
                      placeholder="Search transactions..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    {transactionSearchQuery && (
                      <button
                        onClick={() => setTransactionSearchQuery('')}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Bulk Action Bar - Transactions */}
              {selectedTransactionIds.size > 0 && (
                <div className="mb-4 bg-primary-50 border border-primary-200 rounded-lg p-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckSquare className="w-5 h-5 text-primary-600" />
                    <span className="font-medium text-primary-900">
                      {selectedTransactionIds.size} transaction{selectedTransactionIds.size === 1 ? '' : 's'} selected
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedTransactionIds(new Set())}
                    >
                      Clear Selection
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleBulkDelete('transaction')}
                      className="bg-red-600 hover:bg-red-700 text-white"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete Selected
                    </Button>
                  </div>
                </div>
              )}

              {transactions.length === 0 ? (
                <div className="text-center py-12">
                  <DollarSign className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 mb-4">No transactions recorded yet</p>
                  <Button onClick={() => setShowAddTransactionModal(true)}>
                    <DollarSign className="w-4 h-4 mr-2" />
                    Add First Transaction
                  </Button>
                </div>
              ) : filteredTransactions.length === 0 ? (
                <div className="text-center py-12">
                  <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 mb-2">No transactions match your filters</p>
                  <button
                    onClick={() => {
                      setTransactionTypeFilter('all');
                      setTransactionStatusFilter('all');
                      setTransactionSearchQuery('');
                    }}
                    className="text-sm text-primary-600 hover:text-primary-700"
                  >
                    Clear all filters
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900 w-12">
                          <button
                            onClick={selectAllTransactions}
                            className="text-gray-500 hover:text-primary-600 transition-colors"
                          >
                            {selectedTransactionIds.size === filteredTransactions.length ? (
                              <CheckSquare className="w-4 h-4" />
                            ) : (
                              <Square className="w-4 h-4" />
                            )}
                          </button>
                        </th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900">Date</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900">Type</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900">Description</th>
                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-900">Amount</th>
                        <th className="text-center py-3 px-4 text-sm font-semibold text-gray-900">Status</th>
                        <th className="text-center py-3 px-4 text-sm font-semibold text-gray-900">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTransactions.map((transaction) => (
                        <tr
                          key={transaction.id}
                          className={`border-b border-gray-100 ${
                            selectedTransactionIds.has(transaction.id) ? 'bg-primary-50' : ''
                          }`}
                        >
                          <td className="py-3 px-4">
                            <button
                              onClick={() => toggleTransactionSelection(transaction.id)}
                              className="text-gray-400 hover:text-primary-600 transition-colors"
                            >
                              {selectedTransactionIds.has(transaction.id) ? (
                                <CheckSquare className="w-5 h-5 text-primary-600" />
                              ) : (
                                <Square className="w-5 h-5" />
                              )}
                            </button>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-900">
                            {new Date(transaction.transaction_date).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4">
                            <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium">
                              {transaction.transaction_type}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-700">
                            {transaction.description || '—'}
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-900 text-right font-medium">
                            ${transaction.amount.toLocaleString()}
                          </td>
                          <td className="py-3 px-4 text-center">
                            {transaction.payment_status && (
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                transaction.payment_status === 'completed'
                                  ? 'bg-green-100 text-green-800'
                                  : transaction.payment_status === 'pending'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}>
                                {transaction.payment_status}
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <div className="flex items-center justify-center gap-2">
                              <button
                                onClick={() => openEditTransaction(transaction)}
                                className="p-1 text-gray-400 hover:text-primary-600 transition-colors"
                                title="Edit transaction"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => openDeleteConfirmation('transaction', transaction.id)}
                                className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                                title="Delete transaction"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {/* Total */}
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-semibold text-gray-700">
                        {filteredTransactions.length !== transactions.length ? 'Filtered Total' : 'Total'}
                      </span>
                      <span className="text-lg font-bold text-gray-900">
                        ${filteredTransactions.reduce((sum, t) => sum + t.amount, 0).toLocaleString()}
                      </span>
                    </div>
                    {filteredTransactions.length !== transactions.length && (
                      <div className="flex justify-between items-center mt-2">
                        <span className="text-sm text-gray-500">Overall Total</span>
                        <span className="text-sm text-gray-600">
                          ${transactions.reduce((sum, t) => sum + t.amount, 0).toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Add Party Modal */}
        <AddPartyModal
          isOpen={showAddPartyModal}
          onClose={() => setShowAddPartyModal(false)}
          onSuccess={loadParties}
          caseId={caseId}
        />

        {/* Add Timeline Event Modal */}
        <AddTimelineEventModal
          isOpen={showAddEventModal}
          onClose={() => setShowAddEventModal(false)}
          onSuccess={loadTimeline}
          caseId={caseId}
        />

        {/* Add Transaction Modal */}
        <AddTransactionModal
          isOpen={showAddTransactionModal}
          onClose={() => setShowAddTransactionModal(false)}
          onSuccess={loadTransactions}
          caseId={caseId}
        />

        {/* Edit Case Modal */}
        {caseData && (
          <EditCaseModal
            isOpen={showEditModal}
            onClose={() => setShowEditModal(false)}
            onSuccess={loadCaseData}
            caseData={caseData}
          />
        )}

        {/* Edit Party Modal */}
        {selectedParty && (
          <EditPartyModal
            isOpen={showEditPartyModal}
            onClose={() => {
              setShowEditPartyModal(false);
              setSelectedParty(null);
            }}
            onSuccess={loadParties}
            caseId={caseId}
            party={selectedParty}
          />
        )}

        {/* Edit Timeline Event Modal */}
        {selectedEvent && (
          <EditTimelineEventModal
            isOpen={showEditEventModal}
            onClose={() => {
              setShowEditEventModal(false);
              setSelectedEvent(null);
            }}
            onSuccess={loadTimeline}
            caseId={caseId}
            event={selectedEvent}
          />
        )}

        {/* Edit Transaction Modal */}
        {selectedTransaction && (
          <EditTransactionModal
            isOpen={showEditTransactionModal}
            onClose={() => {
              setShowEditTransactionModal(false);
              setSelectedTransaction(null);
            }}
            onSuccess={loadTransactions}
            caseId={caseId}
            transaction={selectedTransaction}
          />
        )}

        {/* Delete Case Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Delete Case</h2>
              <p className="text-gray-600 mb-6">
                Are you sure you want to delete this case? This action cannot be undone and will delete all associated parties, timeline events, and transactions.
              </p>
              <div className="flex gap-3 justify-end">
                <Button
                  variant="outline"
                  onClick={() => setShowDeleteConfirm(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleDelete}
                  className="bg-red-600 hover:bg-red-700 text-white"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Case
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Item Confirmation Modal */}
        {deleteItemType && deleteItemId && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Delete {deleteItemType.charAt(0).toUpperCase() + deleteItemType.slice(1)}
              </h2>
              <p className="text-gray-600 mb-6">
                Are you sure you want to delete this {deleteItemType}? This action cannot be undone.
              </p>
              <div className="flex gap-3 justify-end">
                <Button
                  variant="outline"
                  onClick={() => {
                    setDeleteItemType(null);
                    setDeleteItemId(null);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleDeleteItem}
                  className="bg-red-600 hover:bg-red-700 text-white"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete {deleteItemType.charAt(0).toUpperCase() + deleteItemType.slice(1)}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
