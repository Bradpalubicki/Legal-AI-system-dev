'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/Input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertTriangle, Download, Search, Shield, AlertCircle, CheckCircle, XCircle, Clock } from 'lucide-react';

interface StateComplianceData {
  state: string;
  stateName: string;
  overallStatus: 'compliant' | 'warning' | 'non_compliant' | 'unknown';
  lastUpdated: string;
  requirements: {
    uplPrevention: {
      status: 'compliant' | 'warning' | 'non_compliant';
      lastReview: string;
      violations: number;
    };
    disclaimerRequirements: {
      status: 'compliant' | 'warning' | 'non_compliant';
      requiredText: boolean;
      displayCompliance: boolean;
      acknowledgmentRate: number;
    };
    attorneySupervision: {
      status: 'compliant' | 'warning' | 'non_compliant';
      requiredSupervision: boolean;
      currentSupervision: boolean;
      qualifiedAttorneys: number;
    };
    dataProtection: {
      status: 'compliant' | 'warning' | 'non_compliant';
      encryptionCompliant: boolean;
      retentionCompliant: boolean;
      accessControlCompliant: boolean;
    };
    advertising: {
      status: 'compliant' | 'warning' | 'non_compliant';
      rulesCompliant: boolean;
      disclaimersPresent: boolean;
      approvalRequired: boolean;
    };
  };
  activeUsers: number;
  recentActivity: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  actionItems: string[];
  nextReviewDate: string;
}

export default function StateComplianceMatrix() {
  const [stateData, setStateData] = useState<StateComplianceData[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterRisk, setFilterRisk] = useState<string>('all');
  const [selectedState, setSelectedState] = useState<StateComplianceData | null>(null);

  useEffect(() => {
    loadStateComplianceData();
  }, []);

  const loadStateComplianceData = async () => {
    setLoading(true);
    
    // Mock data - replace with actual API call
    const mockStateData: StateComplianceData[] = [
      {
        state: 'CA',
        stateName: 'California',
        overallStatus: 'compliant',
        lastUpdated: '2024-01-15T08:00:00Z',
        requirements: {
          uplPrevention: {
            status: 'compliant',
            lastReview: '2024-01-10T00:00:00Z',
            violations: 0
          },
          disclaimerRequirements: {
            status: 'compliant',
            requiredText: true,
            displayCompliance: true,
            acknowledgmentRate: 94.2
          },
          attorneySupervision: {
            status: 'compliant',
            requiredSupervision: true,
            currentSupervision: true,
            qualifiedAttorneys: 12
          },
          dataProtection: {
            status: 'compliant',
            encryptionCompliant: true,
            retentionCompliant: true,
            accessControlCompliant: true
          },
          advertising: {
            status: 'compliant',
            rulesCompliant: true,
            disclaimersPresent: true,
            approvalRequired: false
          }
        },
        activeUsers: 1247,
        recentActivity: 342,
        riskLevel: 'low',
        actionItems: [],
        nextReviewDate: '2024-02-15T00:00:00Z'
      },
      {
        state: 'NY',
        stateName: 'New York',
        overallStatus: 'warning',
        lastUpdated: '2024-01-14T16:30:00Z',
        requirements: {
          uplPrevention: {
            status: 'warning',
            lastReview: '2024-01-12T00:00:00Z',
            violations: 3
          },
          disclaimerRequirements: {
            status: 'compliant',
            requiredText: true,
            displayCompliance: true,
            acknowledgmentRate: 87.6
          },
          attorneySupervision: {
            status: 'compliant',
            requiredSupervision: true,
            currentSupervision: true,
            qualifiedAttorneys: 8
          },
          dataProtection: {
            status: 'warning',
            encryptionCompliant: true,
            retentionCompliant: false,
            accessControlCompliant: true
          },
          advertising: {
            status: 'compliant',
            rulesCompliant: true,
            disclaimersPresent: true,
            approvalRequired: true
          }
        },
        activeUsers: 892,
        recentActivity: 187,
        riskLevel: 'medium',
        actionItems: [
          'Review UPL violation incidents from past week',
          'Update data retention policies to meet NY requirements',
          'Schedule compliance training for client-facing staff'
        ],
        nextReviewDate: '2024-01-20T00:00:00Z'
      },
      {
        state: 'TX',
        stateName: 'Texas',
        overallStatus: 'non_compliant',
        lastUpdated: '2024-01-13T12:00:00Z',
        requirements: {
          uplPrevention: {
            status: 'non_compliant',
            lastReview: '2024-01-08T00:00:00Z',
            violations: 7
          },
          disclaimerRequirements: {
            status: 'warning',
            requiredText: true,
            displayCompliance: false,
            acknowledgmentRate: 72.3
          },
          attorneySupervision: {
            status: 'non_compliant',
            requiredSupervision: true,
            currentSupervision: false,
            qualifiedAttorneys: 2
          },
          dataProtection: {
            status: 'compliant',
            encryptionCompliant: true,
            retentionCompliant: true,
            accessControlCompliant: true
          },
          advertising: {
            status: 'warning',
            rulesCompliant: false,
            disclaimersPresent: true,
            approvalRequired: true
          }
        },
        activeUsers: 634,
        recentActivity: 145,
        riskLevel: 'critical',
        actionItems: [
          'URGENT: Address 7 UPL violations immediately',
          'Hire qualified supervising attorney for TX operations',
          'Update disclaimer display system',
          'Review and update advertising materials for TX compliance',
          'Implement enhanced supervision protocols'
        ],
        nextReviewDate: '2024-01-16T00:00:00Z'
      }
    ];

    setStateData(mockStateData);
    setLoading(false);
  };

  const filteredStates = stateData.filter(state => {
    if (searchTerm && !state.stateName.toLowerCase().includes(searchTerm.toLowerCase()) && 
        !state.state.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    if (filterStatus !== 'all' && state.overallStatus !== filterStatus) {
      return false;
    }
    if (filterRisk !== 'all' && state.riskLevel !== filterRisk) {
      return false;
    }
    return true;
  });

  const exportData = () => {
    const exportData = {
      generatedAt: new Date().toISOString(),
      summary: {
        totalStates: stateData.length,
        compliant: stateData.filter(s => s.overallStatus === 'compliant').length,
        warnings: stateData.filter(s => s.overallStatus === 'warning').length,
        nonCompliant: stateData.filter(s => s.overallStatus === 'non_compliant').length
      },
      stateDetails: filteredStates.map(state => ({
        ...state,
        // Redact sensitive information for export
        activeUsers: state.activeUsers > 100 ? '100+' : state.activeUsers.toString(),
        recentActivity: '[REDACTED]'
      }))
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `state-compliance-matrix-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      compliant: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      non_compliant: 'bg-red-100 text-red-800',
      unknown: 'bg-gray-100 text-gray-800'
    };
    return <Badge className={colors[status as keyof typeof colors]}>{status.replace('_', ' ').toUpperCase()}</Badge>;
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />;
      case 'non_compliant':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading state compliance data...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Professional Responsibility Notice */}
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="pt-6">
          <div className="flex items-start space-x-3">
            <Shield className="h-5 w-5 text-amber-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-amber-800">State-by-State Compliance Monitoring</h3>
              <p className="text-sm text-amber-700 mt-1">
                This matrix provides jurisdiction-specific compliance status for professional responsibility rules, 
                UPL prevention, and regulatory requirements. Critical non-compliance issues require immediate attention.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Jurisdictions</p>
                <p className="text-2xl font-bold">{stateData.length}</p>
              </div>
              <Shield className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Compliant States</p>
                <p className="text-2xl font-bold text-green-600">
                  {stateData.filter(s => s.overallStatus === 'compliant').length}
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Warning States</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {stateData.filter(s => s.overallStatus === 'warning').length}
                </p>
              </div>
              <AlertCircle className="h-8 w-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Non-Compliant</p>
                <p className="text-2xl font-bold text-red-600">
                  {stateData.filter(s => s.overallStatus === 'non_compliant').length}
                </p>
              </div>
              <XCircle className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Shield className="h-5 w-5" />
              <span>State Compliance Matrix</span>
            </div>
            <Button onClick={exportData} size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export Matrix
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 mb-6">
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <Input
                  placeholder="Search by state name or code..."
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
                <SelectItem value="compliant">Compliant</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
                <SelectItem value="non_compliant">Non-Compliant</SelectItem>
                <SelectItem value="unknown">Unknown</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterRisk} onValueChange={setFilterRisk}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by risk" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Risk Levels</SelectItem>
                <SelectItem value="low">Low Risk</SelectItem>
                <SelectItem value="medium">Medium Risk</SelectItem>
                <SelectItem value="high">High Risk</SelectItem>
                <SelectItem value="critical">Critical Risk</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* State Compliance Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">State</th>
                  <th className="text-left p-2">Overall Status</th>
                  <th className="text-left p-2">UPL Prevention</th>
                  <th className="text-left p-2">Disclaimers</th>
                  <th className="text-left p-2">Attorney Supervision</th>
                  <th className="text-left p-2">Data Protection</th>
                  <th className="text-left p-2">Risk Level</th>
                  <th className="text-left p-2">Action Items</th>
                  <th className="text-left p-2">Next Review</th>
                </tr>
              </thead>
              <tbody>
                {filteredStates.map((state) => (
                  <tr 
                    key={state.state} 
                    className="border-b hover:bg-gray-50 cursor-pointer"
                    onClick={() => setSelectedState(state)}
                  >
                    <td className="p-2">
                      <div>
                        <div className="text-sm font-medium">{state.stateName}</div>
                        <div className="text-xs text-gray-500 font-mono">{state.state}</div>
                      </div>
                    </td>
                    <td className="p-2">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(state.overallStatus)}
                        {getStatusBadge(state.overallStatus)}
                      </div>
                    </td>
                    <td className="p-2">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(state.requirements.uplPrevention.status)}
                        <span className="text-sm">
                          {state.requirements.uplPrevention.violations > 0 && 
                            `${state.requirements.uplPrevention.violations} violations`
                          }
                        </span>
                      </div>
                    </td>
                    <td className="p-2">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(state.requirements.disclaimerRequirements.status)}
                        <span className="text-sm">
                          {state.requirements.disclaimerRequirements.acknowledgmentRate.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="p-2">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(state.requirements.attorneySupervision.status)}
                        <span className="text-sm">
                          {state.requirements.attorneySupervision.qualifiedAttorneys} attorneys
                        </span>
                      </div>
                    </td>
                    <td className="p-2">
                      {getStatusIcon(state.requirements.dataProtection.status)}
                    </td>
                    <td className="p-2">
                      {getRiskBadge(state.riskLevel)}
                    </td>
                    <td className="p-2">
                      <div className="flex items-center space-x-1">
                        {state.actionItems.length > 0 && (
                          <>
                            <AlertTriangle className="h-3 w-3 text-yellow-500" />
                            <Badge variant="outline" className="text-xs">
                              {state.actionItems.length}
                            </Badge>
                          </>
                        )}
                      </div>
                    </td>
                    <td className="p-2 text-sm text-gray-500">
                      {new Date(state.nextReviewDate).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredStates.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No states match the current filters.
            </div>
          )}
        </CardContent>
      </Card>

      {/* State Detail Modal */}
      {selectedState && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{selectedState.stateName} Compliance Detail</span>
              <Button variant="outline" onClick={() => setSelectedState(null)}>
                Close
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">Compliance Requirements</h4>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">UPL Prevention:</span>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(selectedState.requirements.uplPrevention.status)}
                      <span className="text-sm">{selectedState.requirements.uplPrevention.violations} violations</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Disclaimer Requirements:</span>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(selectedState.requirements.disclaimerRequirements.status)}
                      <span className="text-sm">{selectedState.requirements.disclaimerRequirements.acknowledgmentRate.toFixed(1)}% ack</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Attorney Supervision:</span>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(selectedState.requirements.attorneySupervision.status)}
                      <span className="text-sm">{selectedState.requirements.attorneySupervision.qualifiedAttorneys} qualified</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Data Protection:</span>
                    {getStatusIcon(selectedState.requirements.dataProtection.status)}
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Advertising Rules:</span>
                    {getStatusIcon(selectedState.requirements.advertising.status)}
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-3">Action Items</h4>
                {selectedState.actionItems.length > 0 ? (
                  <ul className="space-y-2">
                    {selectedState.actionItems.map((item, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5" />
                        <span className="text-sm">{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500">No outstanding action items.</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}