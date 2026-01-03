'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Scale,
  Plus,
  Search,
  FileText,
  Calendar,
  User,
  Building,
  Filter
} from 'lucide-react';
import { getCases, formatCaseType, formatCaseStatus, getStatusColor, type LegalCase } from '@/lib/api/cases';
import { toast } from 'sonner';
import CreateCaseModal from '@/components/Cases/CreateCaseModal';

export default function CasesPage() {
  const router = useRouter();
  const [cases, setCases] = useState<LegalCase[]>([]);
  const [filteredCases, setFilteredCases] = useState<LegalCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    loadCases();
  }, []);

  useEffect(() => {
    filterCases();
  }, [searchTerm, statusFilter, typeFilter, cases]);

  const loadCases = async () => {
    try {
      setLoading(true);
      const data = await getCases();
      setCases(data);
      setFilteredCases(data);
    } catch (error: any) {
      console.error('Failed to load cases:', error);
      toast.error('Failed to load cases', {
        description: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const filterCases = () => {
    let filtered = [...cases];

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(c =>
        c.case_name.toLowerCase().includes(term) ||
        c.case_number.toLowerCase().includes(term) ||
        c.court_name?.toLowerCase().includes(term) ||
        c.jurisdiction?.toLowerCase().includes(term)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(c => c.status === statusFilter);
    }

    // Type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter(c => c.case_type === typeFilter);
    }

    setFilteredCases(filtered);
  };

  const getStats = () => {
    return {
      total: cases.length,
      active: cases.filter(c => c.status === 'active').length,
      closed: cases.filter(c => c.status === 'closed' || c.status === 'dismissed' || c.status === 'settled').length,
      pending: cases.filter(c => c.status === 'pending' || c.status === 'intake').length,
    };
  };

  const stats = getStats();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-600">Loading cases...</p>
            </div>
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
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Scale className="w-8 h-8 text-primary-600" />
                Case Management
              </h1>
              <p className="text-gray-600 mt-2">
                Track and manage all legal cases and proceedings
              </p>
            </div>
            <Button
              onClick={() => setShowCreateModal(true)}
              className="bg-primary-600 hover:bg-primary-700 text-white"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Case
            </Button>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Cases</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
                </div>
                <FileText className="w-8 h-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Active Cases</p>
                  <p className="text-2xl font-bold text-green-600">{stats.active}</p>
                </div>
                <Scale className="w-8 h-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Pending</p>
                  <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
                </div>
                <Calendar className="w-8 h-8 text-yellow-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Closed</p>
                  <p className="text-2xl font-bold text-gray-600">{stats.closed}</p>
                </div>
                <FileText className="w-8 h-8 text-gray-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Filters */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search cases..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">All Statuses</option>
                <option value="active">Active</option>
                <option value="pending">Pending</option>
                <option value="intake">Intake</option>
                <option value="closed">Closed</option>
                <option value="settled">Settled</option>
                <option value="dismissed">Dismissed</option>
              </select>

              {/* Type Filter */}
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">All Types</option>
                <option value="bankruptcy_ch7">Bankruptcy Ch 7</option>
                <option value="bankruptcy_ch11">Bankruptcy Ch 11</option>
                <option value="civil_litigation">Civil Litigation</option>
                <option value="debt_collection">Debt Collection</option>
                <option value="contract_dispute">Contract Dispute</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Cases Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Cases ({filteredCases.length})</span>
              {filteredCases.length !== cases.length && (
                <button
                  onClick={() => {
                    setSearchTerm('');
                    setStatusFilter('all');
                    setTypeFilter('all');
                  }}
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  Clear Filters
                </button>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {filteredCases.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 mb-4">
                  {cases.length === 0 ? 'No cases yet' : 'No cases match your filters'}
                </p>
                {cases.length === 0 && (
                  <Button onClick={() => setShowCreateModal(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Your First Case
                  </Button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900">Case Number</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900">Case Name</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900">Type</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900">Status</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900">Court</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900">Filing Date</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-900">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredCases.map((case_) => (
                      <tr
                        key={case_.id}
                        className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
                        onClick={() => router.push(`/cases/${case_.id}`)}
                      >
                        <td className="py-4 px-4">
                          <span className="font-mono text-sm text-gray-900">{case_.case_number}</span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="max-w-xs">
                            <p className="font-medium text-gray-900 truncate">{case_.case_name}</p>
                            {case_.current_phase && (
                              <p className="text-xs text-gray-500 mt-1">{case_.current_phase}</p>
                            )}
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-sm text-gray-700">{formatCaseType(case_.case_type)}</span>
                        </td>
                        <td className="py-4 px-4">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(case_.status)}`}>
                            {formatCaseStatus(case_.status)}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="max-w-xs">
                            <p className="text-sm text-gray-700 truncate">{case_.court_name || '—'}</p>
                            {case_.jurisdiction && (
                              <p className="text-xs text-gray-500">{case_.jurisdiction}</p>
                            )}
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          {case_.filing_date ? (
                            <span className="text-sm text-gray-700">
                              {new Date(case_.filing_date).toLocaleDateString()}
                            </span>
                          ) : (
                            <span className="text-sm text-gray-400">—</span>
                          )}
                        </td>
                        <td className="py-4 px-4 text-right">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/cases/${case_.id}`);
                            }}
                          >
                            View Details
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Create Case Modal */}
        <CreateCaseModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSuccess={loadCases}
        />
      </div>
    </div>
  );
}
