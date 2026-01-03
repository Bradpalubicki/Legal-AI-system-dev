'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/Input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertTriangle, Download, Search, Filter, TrendingUp, TrendingDown, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { useAdminDisclaimers, AcknowledgmentRecord as APIAcknowledgmentRecord, AcknowledgmentPattern } from '@/hooks/useAdminDisclaimers';

// Map API record to display record
interface AcknowledgmentRecord {
  id: string;
  userId: string;
  userType: 'attorney' | 'client' | 'staff' | 'user';
  disclaimerType: string;
  acknowledged: boolean;
  acknowledgedAt: string | null;
  viewCount: number;
  timeToAcknowledge: number | null; // seconds
  jurisdiction: string;
  sessionId: string;
  ipAddress: string;
  userAgent: string;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  followUpRequired: boolean;
}

export default function UserAcknowledgments() {
  const { fetchAcknowledgments, fetchAnalytics, loading: apiLoading, error } = useAdminDisclaimers();

  const [acknowledgments, setAcknowledgments] = useState<AcknowledgmentRecord[]>([]);
  const [patterns, setPatterns] = useState<AcknowledgmentPattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterJurisdiction, setFilterJurisdiction] = useState<string>('all');

  useEffect(() => {
    loadAcknowledgmentData();
  }, []);

  const loadAcknowledgmentData = async () => {
    setLoading(true);

    try {
      // Fetch real data from API
      const [acknowledgementsData, analyticsData] = await Promise.all([
        fetchAcknowledgments({ limit: 100 }),
        fetchAnalytics()
      ]);

      // Map API records to display records
      const mappedRecords: AcknowledgmentRecord[] = acknowledgementsData.acknowledgments.map((rec: APIAcknowledgmentRecord) => ({
        id: rec.id,
        userId: rec.user_id,
        userType: rec.user_type as 'attorney' | 'client' | 'staff' | 'user',
        disclaimerType: rec.disclaimer_type,
        acknowledged: rec.acknowledged,
        acknowledgedAt: rec.acknowledged_at,
        viewCount: rec.view_count,
        timeToAcknowledge: rec.time_to_acknowledge,
        jurisdiction: rec.jurisdiction || 'N/A',
        sessionId: rec.session_id,
        ipAddress: rec.ip_address,
        userAgent: rec.user_agent,
        riskLevel: rec.risk_level,
        followUpRequired: rec.follow_up_required
      }));

      setAcknowledgments(mappedRecords);
      setPatterns(analyticsData);
    } catch (err) {
      console.error('Error loading acknowledgment data:', err);
      // Show empty state on error
      setAcknowledgments([]);
      setPatterns([]);
    } finally {
      setLoading(false);
    }
  };


  const filteredAcknowledgments = acknowledgments.filter(ack => {
    if (searchTerm && !ack.userId.toLowerCase().includes(searchTerm.toLowerCase()) && 
        !ack.disclaimerType.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    if (filterStatus !== 'all' && (filterStatus === 'acknowledged' ? !ack.acknowledged : ack.acknowledged)) {
      return false;
    }
    if (filterType !== 'all' && ack.disclaimerType !== filterType) {
      return false;
    }
    if (filterJurisdiction !== 'all' && ack.jurisdiction !== filterJurisdiction) {
      return false;
    }
    return true;
  });

  const exportData = () => {
    const exportData = filteredAcknowledgments.map(ack => ({
      ...ack,
      // Additional PII redaction for export
      userId: 'user_***',
      sessionId: 'sess_***',
      ipAddress: '***.***.***.***',
      userAgent: '[REDACTED]'
    }));

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `acknowledgment-report-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getRiskBadge = (level: string) => {
    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800', 
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    };
    return <Badge className={colors[level as keyof typeof colors]}>{level.toUpperCase()}</Badge>;
  };

  const getStatusIcon = (acknowledged: boolean, followUpRequired: boolean) => {
    if (acknowledged && !followUpRequired) return <CheckCircle className="h-4 w-4 text-green-600" />;
    if (acknowledged && followUpRequired) return <AlertCircle className="h-4 w-4 text-yellow-600" />;
    return <XCircle className="h-4 w-4 text-red-600" />;
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading acknowledgment data...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Professional Responsibility Notice */}
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="pt-6">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-amber-800">Acknowledgment Monitoring Notice</h3>
              <p className="text-sm text-amber-700 mt-1">
                This interface tracks user acknowledgment of critical disclaimers and professional responsibility notices. 
                Non-acknowledgment may indicate inadequate disclosure or user interface issues requiring immediate attention.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Acknowledgment Patterns Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {patterns.map((pattern, index) => (
          <Card key={index}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                {pattern.disclaimerType.replace('_', ' ').toUpperCase()}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Acknowledgment Rate:</span>
                  <span className="font-medium">
                    {((pattern.acknowledged / pattern.totalShown) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Avg. Time:</span>
                  <span className="font-medium">{pattern.averageTimeToAcknowledge}s</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Drop-off Rate:</span>
                  <div className="flex items-center space-x-1">
                    {pattern.dropOffRate > 10 ? 
                      <TrendingUp className="h-3 w-3 text-red-500" /> : 
                      <TrendingDown className="h-3 w-3 text-green-500" />
                    }
                    <span className="font-medium">{pattern.dropOffRate}%</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Risk Level:</span>
                  {getRiskBadge(pattern.riskLevel)}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Filter className="h-5 w-5" />
              <span>Acknowledgment Records</span>
            </div>
            <Button onClick={exportData} size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export (Redacted)
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 mb-6">
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <Input
                  placeholder="Search by user ID or disclaimer type..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="acknowledged">Acknowledged</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="initial_warning">Initial Warning</SelectItem>
                <SelectItem value="advice_limitation">Advice Limitation</SelectItem>
                <SelectItem value="jurisdiction_notice">Jurisdiction Notice</SelectItem>
                <SelectItem value="confidentiality">Confidentiality</SelectItem>
                <SelectItem value="billing_terms">Billing Terms</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterJurisdiction} onValueChange={setFilterJurisdiction}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="State" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All States</SelectItem>
                <SelectItem value="CA">CA</SelectItem>
                <SelectItem value="NY">NY</SelectItem>
                <SelectItem value="TX">TX</SelectItem>
                <SelectItem value="FL">FL</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Acknowledgment Records Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Status</th>
                  <th className="text-left p-2">User</th>
                  <th className="text-left p-2">Type</th>
                  <th className="text-left p-2">Disclaimer</th>
                  <th className="text-left p-2">Views</th>
                  <th className="text-left p-2">Time to Ack</th>
                  <th className="text-left p-2">Risk</th>
                  <th className="text-left p-2">Jurisdiction</th>
                  <th className="text-left p-2">Follow-up</th>
                </tr>
              </thead>
              <tbody>
                {filteredAcknowledgments.map((ack) => (
                  <tr key={ack.id} className="border-b hover:bg-gray-50">
                    <td className="p-2">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(ack.acknowledged, ack.followUpRequired)}
                        <span className="text-sm">
                          {ack.acknowledged ? 'Acknowledged' : 'Pending'}
                        </span>
                      </div>
                    </td>
                    <td className="p-2">
                      <div>
                        <div className="text-sm font-medium">{ack.userId}</div>
                        <div className="text-xs text-gray-500">{ack.userType}</div>
                      </div>
                    </td>
                    <td className="p-2">
                      <Badge variant="outline">{ack.disclaimerType.replace('_', ' ')}</Badge>
                    </td>
                    <td className="p-2 text-sm">
                      {ack.disclaimerType.replace('_', ' ').charAt(0).toUpperCase() + 
                       ack.disclaimerType.replace('_', ' ').slice(1)}
                    </td>
                    <td className="p-2">
                      <div className="flex items-center space-x-1">
                        <span className="text-sm">{ack.viewCount}</span>
                        {ack.viewCount > 2 && <AlertTriangle className="h-3 w-3 text-yellow-500" />}
                      </div>
                    </td>
                    <td className="p-2">
                      <div className="flex items-center space-x-1">
                        <Clock className="h-3 w-3 text-gray-400" />
                        <span className="text-sm">
                          {ack.timeToAcknowledge ? `${ack.timeToAcknowledge}s` : 'N/A'}
                        </span>
                      </div>
                    </td>
                    <td className="p-2">
                      {getRiskBadge(ack.riskLevel)}
                    </td>
                    <td className="p-2 text-sm font-mono">
                      {ack.jurisdiction}
                    </td>
                    <td className="p-2">
                      {ack.followUpRequired && (
                        <Badge variant="outline" className="bg-yellow-50 text-yellow-800">
                          Required
                        </Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredAcknowledgments.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No acknowledgment records match the current filters.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}