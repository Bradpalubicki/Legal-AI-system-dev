'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertTriangle, Save, Plus, Edit, Trash2, FileText, Shield, Clock, CheckCircle, XCircle } from 'lucide-react';

interface StateRule {
  id: string;
  state: string;
  stateName: string;
  ruleType: 'upl_prevention' | 'attorney_supervision' | 'advertising' | 'data_protection' | 'client_communication' | 'fee_disclosure';
  title: string;
  description: string;
  requirements: string[];
  penalties: string;
  effectiveDate: string;
  lastReviewed: string;
  reviewBy: string;
  complianceStatus: 'compliant' | 'partial' | 'non_compliant' | 'unknown';
  automationLevel: 'manual' | 'semi_automated' | 'fully_automated';
  monitoringEnabled: boolean;
  citations: string[];
  relatedRules: string[];
  implementationNotes: string;
  createdAt: string;
  updatedAt: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
}

interface RuleViolation {
  id: string;
  ruleId: string;
  violationDate: string;
  description: string;
  severity: 'minor' | 'moderate' | 'severe' | 'critical';
  status: 'open' | 'investigating' | 'resolved';
  assignedTo: string;
  dueDate: string;
}

export default function StateRulesManager() {
  const [rules, setRules] = useState<StateRule[]>([]);
  const [violations, setViolations] = useState<RuleViolation[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingRule, setEditingRule] = useState<StateRule | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedState, setSelectedState] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');

  useEffect(() => {
    loadStateRules();
    loadViolations();
  }, []);

  const loadStateRules = async () => {
    setLoading(true);
    
    // Mock data - replace with actual API call
    const mockRules: StateRule[] = [
      {
        id: '1',
        state: 'CA',
        stateName: 'California',
        ruleType: 'upl_prevention',
        title: 'Unauthorized Practice of Law Prevention',
        description: 'Rules governing the prevention of unauthorized practice of law by non-attorneys',
        requirements: [
          'Clear disclaimers on all legal information',
          'No attorney-client relationship formation',
          'Referral system for legal advice requests',
          'Attorney supervision of all legal content'
        ],
        penalties: 'Civil penalties up to $10,000, potential criminal charges',
        effectiveDate: '2023-01-01T00:00:00Z',
        lastReviewed: '2024-01-10T00:00:00Z',
        reviewBy: 'legal.counsel@legal-system.com',
        complianceStatus: 'compliant',
        automationLevel: 'semi_automated',
        monitoringEnabled: true,
        citations: ['California Business and Professions Code Section 6125', 'Cal Bar Rule 5.5'],
        relatedRules: ['attorney_supervision', 'advertising'],
        implementationNotes: 'Automated disclaimer system implemented. Manual review of flagged content.',
        createdAt: '2023-12-01T00:00:00Z',
        updatedAt: '2024-01-10T00:00:00Z',
        priority: 'critical'
      },
      {
        id: '2',
        state: 'NY',
        stateName: 'New York',
        ruleType: 'attorney_supervision',
        title: 'Attorney Supervision Requirements',
        description: 'Requirements for attorney supervision of legal technology services',
        requirements: [
          'Licensed NY attorney must review all legal outputs',
          'Direct supervision for client communications',
          'Regular training for non-attorney staff',
          'Quarterly compliance reviews'
        ],
        penalties: 'Professional discipline, fines, suspension of operations',
        effectiveDate: '2023-06-01T00:00:00Z',
        lastReviewed: '2024-01-12T00:00:00Z',
        reviewBy: 'ny.counsel@legal-system.com',
        complianceStatus: 'partial',
        automationLevel: 'manual',
        monitoringEnabled: true,
        citations: ['NY Rules of Professional Conduct Rule 5.3', '22 NYCRR Part 1200'],
        relatedRules: ['upl_prevention', 'client_communication'],
        implementationNotes: 'Need to increase attorney staffing. Currently understaffed for volume.',
        createdAt: '2023-11-15T00:00:00Z',
        updatedAt: '2024-01-12T00:00:00Z',
        priority: 'high'
      },
      {
        id: '3',
        state: 'TX',
        stateName: 'Texas',
        ruleType: 'advertising',
        title: 'Legal Service Advertising Rules',
        description: 'Regulations governing advertising of legal technology services',
        requirements: [
          'All advertising must include required disclaimers',
          'No false or misleading statements about services',
          'Proper identification of supervising attorneys',
          'Pre-approval of marketing materials'
        ],
        penalties: 'Bar disciplinary action, advertising restrictions, fines',
        effectiveDate: '2023-03-01T00:00:00Z',
        lastReviewed: '2024-01-05T00:00:00Z',
        reviewBy: 'tx.counsel@legal-system.com',
        complianceStatus: 'non_compliant',
        automationLevel: 'manual',
        monitoringEnabled: false,
        citations: ['Texas Disciplinary Rules of Professional Conduct Rule 7.02', 'State Bar Act'],
        relatedRules: ['upl_prevention'],
        implementationNotes: 'Marketing materials need review and approval. Non-compliant ads detected.',
        createdAt: '2023-10-20T00:00:00Z',
        updatedAt: '2024-01-05T00:00:00Z',
        priority: 'critical'
      }
    ];

    const mockViolations: RuleViolation[] = [
      {
        id: '1',
        ruleId: '2',
        violationDate: '2024-01-14T00:00:00Z',
        description: 'Insufficient attorney supervision detected in document review process',
        severity: 'moderate',
        status: 'investigating',
        assignedTo: 'compliance.team@legal-system.com',
        dueDate: '2024-01-21T00:00:00Z'
      },
      {
        id: '2',
        ruleId: '3',
        violationDate: '2024-01-13T00:00:00Z',
        description: 'Marketing email sent without required disclaimers',
        severity: 'severe',
        status: 'open',
        assignedTo: 'marketing.compliance@legal-system.com',
        dueDate: '2024-01-18T00:00:00Z'
      }
    ];

    setRules(mockRules);
    setViolations(mockViolations);
    setLoading(false);
  };

  const loadViolations = async () => {
    // Mock violation loading
  };

  const filteredRules = rules.filter(rule => {
    if (selectedState !== 'all' && rule.state !== selectedState) {
      return false;
    }
    if (selectedType !== 'all' && rule.ruleType !== selectedType) {
      return false;
    }
    if (selectedStatus !== 'all' && rule.complianceStatus !== selectedStatus) {
      return false;
    }
    return true;
  });

  const createNewRule = () => {
    const newRule: StateRule = {
      id: '',
      state: 'CA',
      stateName: 'California',
      ruleType: 'upl_prevention',
      title: '',
      description: '',
      requirements: [],
      penalties: '',
      effectiveDate: new Date().toISOString(),
      lastReviewed: new Date().toISOString(),
      reviewBy: 'current.user@legal-system.com',
      complianceStatus: 'unknown',
      automationLevel: 'manual',
      monitoringEnabled: false,
      citations: [],
      relatedRules: [],
      implementationNotes: '',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      priority: 'medium'
    };
    setEditingRule(newRule);
    setIsCreating(true);
  };

  const saveRule = async () => {
    if (!editingRule) return;

    // Here you would make an API call to save the rule
    console.log('Saving rule:', editingRule);

    if (isCreating) {
      setRules(prev => [...prev, { ...editingRule, id: Date.now().toString() }]);
    } else {
      setRules(prev => prev.map(r => 
        r.id === editingRule.id ? editingRule : r
      ));
    }

    setEditingRule(null);
    setIsCreating(false);
  };

  const deleteRule = async (id: string) => {
    if (confirm('Are you sure you want to delete this rule? This action cannot be undone.')) {
      setRules(prev => prev.filter(r => r.id !== id));
    }
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      compliant: 'bg-green-100 text-green-800',
      partial: 'bg-yellow-100 text-yellow-800',
      non_compliant: 'bg-red-100 text-red-800',
      unknown: 'bg-gray-100 text-gray-800'
    };
    return <Badge className={colors[status as keyof typeof colors]}>{status.replace('_', ' ').toUpperCase()}</Badge>;
  };

  const getPriorityBadge = (priority: string) => {
    const colors = {
      low: 'bg-blue-100 text-blue-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    };
    return <Badge className={colors[priority as keyof typeof colors]}>{priority.toUpperCase()}</Badge>;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'partial':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'non_compliant':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-600" />;
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading state rules...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Professional Responsibility Notice */}
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="pt-6">
          <div className="flex items-start space-x-3">
            <Shield className="h-5 w-5 text-amber-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-amber-800">State Rules Management System</h3>
              <p className="text-sm text-amber-700 mt-1">
                This system manages jurisdiction-specific legal rules and compliance requirements. 
                Changes to state rules require attorney review and may trigger compliance audits. 
                Ensure all modifications comply with local bar regulations.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Header with Actions */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">State Rules Manager</h2>
        <Button onClick={createNewRule}>
          <Plus className="h-4 w-4 mr-2" />
          Add New Rule
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Rules</p>
                <p className="text-2xl font-bold">{rules.length}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Compliant</p>
                <p className="text-2xl font-bold text-green-600">
                  {rules.filter(r => r.complianceStatus === 'compliant').length}
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
                <p className="text-sm font-medium text-gray-600">Violations</p>
                <p className="text-2xl font-bold text-red-600">{violations.length}</p>
              </div>
              <XCircle className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Automated</p>
                <p className="text-2xl font-bold text-blue-600">
                  {rules.filter(r => r.automationLevel !== 'manual').length}
                </p>
              </div>
              <Shield className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <Select value={selectedState} onValueChange={setSelectedState}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by state" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All States</SelectItem>
                <SelectItem value="CA">California</SelectItem>
                <SelectItem value="NY">New York</SelectItem>
                <SelectItem value="TX">Texas</SelectItem>
                <SelectItem value="FL">Florida</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="upl_prevention">UPL Prevention</SelectItem>
                <SelectItem value="attorney_supervision">Attorney Supervision</SelectItem>
                <SelectItem value="advertising">Advertising</SelectItem>
                <SelectItem value="data_protection">Data Protection</SelectItem>
                <SelectItem value="client_communication">Client Communication</SelectItem>
                <SelectItem value="fee_disclosure">Fee Disclosure</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedStatus} onValueChange={setSelectedStatus}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by compliance" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="compliant">Compliant</SelectItem>
                <SelectItem value="partial">Partial Compliance</SelectItem>
                <SelectItem value="non_compliant">Non-Compliant</SelectItem>
                <SelectItem value="unknown">Unknown</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Active Violations Alert */}
      {violations.filter(v => v.status === 'open').length > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">Active Compliance Violations</h3>
                <p className="text-sm text-red-700 mt-1">
                  {violations.filter(v => v.status === 'open').length} active violations require immediate attention.
                </p>
                <div className="mt-2 space-y-1">
                  {violations.filter(v => v.status === 'open').map(violation => (
                    <div key={violation.id} className="text-xs text-red-700">
                      • {violation.description} (Due: {new Date(violation.dueDate).toLocaleDateString()})
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Rules List */}
      <div className="grid grid-cols-1 gap-4">
        {filteredRules.map((rule) => (
          <Card key={rule.id} className={rule.complianceStatus === 'non_compliant' ? 'border-red-200' : ''}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="flex items-center space-x-2">
                    {getStatusIcon(rule.complianceStatus)}
                    <span>{rule.title}</span>
                  </CardTitle>
                  <div className="flex items-center space-x-2 mt-2">
                    <Badge variant="outline">{rule.state}</Badge>
                    <Badge variant="outline">{rule.ruleType.replace('_', ' ')}</Badge>
                    {getStatusBadge(rule.complianceStatus)}
                    {getPriorityBadge(rule.priority)}
                    {rule.monitoringEnabled && (
                      <Badge className="bg-blue-100 text-blue-800">MONITORED</Badge>
                    )}
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setEditingRule(rule)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => deleteRule(rule.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <p className="text-sm text-gray-600">{rule.description}</p>
                
                <div>
                  <h4 className="font-medium text-sm mb-2">Requirements:</h4>
                  <ul className="text-xs space-y-1 text-gray-600">
                    {rule.requirements.map((req, index) => (
                      <li key={index}>• {req}</li>
                    ))}
                  </ul>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                  <div>
                    <span className="font-medium">Effective:</span> {new Date(rule.effectiveDate).toLocaleDateString()}
                  </div>
                  <div>
                    <span className="font-medium">Last Reviewed:</span> {new Date(rule.lastReviewed).toLocaleDateString()}
                  </div>
                  <div>
                    <span className="font-medium">Automation:</span> {rule.automationLevel.replace('_', ' ')}
                  </div>
                </div>

                {rule.implementationNotes && (
                  <div className="text-xs text-gray-600 p-2 bg-gray-50 rounded">
                    <strong>Notes:</strong> {rule.implementationNotes}
                  </div>
                )}

                {rule.citations.length > 0 && (
                  <div className="text-xs">
                    <strong>Citations:</strong> {rule.citations.join(', ')}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Edit/Create Modal */}
      {editingRule && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{isCreating ? 'Create New Rule' : 'Edit Rule'}</span>
              <div className="flex space-x-2">
                <Button onClick={saveRule}>
                  <Save className="h-4 w-4 mr-2" />
                  Save
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setEditingRule(null);
                    setIsCreating(false);
                  }}
                >
                  Cancel
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Title</label>
                  <Input
                    value={editingRule.title}
                    onChange={(e) => setEditingRule(prev => 
                      prev ? { ...prev, title: e.target.value } : null
                    )}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">State</label>
                  <Select
                    value={editingRule.state}
                    onValueChange={(value: string) => {
                      const stateNames: Record<string, string> = {
                        CA: 'California',
                        NY: 'New York',
                        TX: 'Texas',
                        FL: 'Florida'
                      };
                      setEditingRule(prev => 
                        prev ? { ...prev, state: value, stateName: stateNames[value] || value } : null
                      );
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CA">California</SelectItem>
                      <SelectItem value="NY">New York</SelectItem>
                      <SelectItem value="TX">Texas</SelectItem>
                      <SelectItem value="FL">Florida</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Rule Type</label>
                  <Select
                    value={editingRule.ruleType}
                    onValueChange={(value: any) => setEditingRule(prev => 
                      prev ? { ...prev, ruleType: value } : null
                    )}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="upl_prevention">UPL Prevention</SelectItem>
                      <SelectItem value="attorney_supervision">Attorney Supervision</SelectItem>
                      <SelectItem value="advertising">Advertising</SelectItem>
                      <SelectItem value="data_protection">Data Protection</SelectItem>
                      <SelectItem value="client_communication">Client Communication</SelectItem>
                      <SelectItem value="fee_disclosure">Fee Disclosure</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Priority</label>
                  <Select
                    value={editingRule.priority}
                    onValueChange={(value: any) => setEditingRule(prev => 
                      prev ? { ...prev, priority: value } : null
                    )}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Compliance Status</label>
                  <Select
                    value={editingRule.complianceStatus}
                    onValueChange={(value: any) => setEditingRule(prev => 
                      prev ? { ...prev, complianceStatus: value } : null
                    )}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="compliant">Compliant</SelectItem>
                      <SelectItem value="partial">Partial Compliance</SelectItem>
                      <SelectItem value="non_compliant">Non-Compliant</SelectItem>
                      <SelectItem value="unknown">Unknown</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Automation Level</label>
                  <Select
                    value={editingRule.automationLevel}
                    onValueChange={(value: any) => setEditingRule(prev => 
                      prev ? { ...prev, automationLevel: value } : null
                    )}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="manual">Manual</SelectItem>
                      <SelectItem value="semi_automated">Semi-Automated</SelectItem>
                      <SelectItem value="fully_automated">Fully Automated</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="monitoringEnabled"
                    checked={editingRule.monitoringEnabled}
                    onChange={(e) => setEditingRule(prev => 
                      prev ? { ...prev, monitoringEnabled: e.target.checked } : null
                    )}
                  />
                  <label htmlFor="monitoringEnabled" className="text-sm font-medium">
                    Enable Monitoring
                  </label>
                </div>
              </div>

              <div className="md:col-span-2 space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Description</label>
                  <Textarea
                    rows={3}
                    value={editingRule.description}
                    onChange={(e) => setEditingRule(prev => 
                      prev ? { ...prev, description: e.target.value } : null
                    )}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Requirements (one per line)</label>
                  <Textarea
                    rows={4}
                    value={editingRule.requirements.join('\n')}
                    onChange={(e) => setEditingRule(prev => 
                      prev ? { ...prev, requirements: e.target.value.split('\n').filter(r => r.trim()) } : null
                    )}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Penalties</label>
                  <Textarea
                    rows={2}
                    value={editingRule.penalties}
                    onChange={(e) => setEditingRule(prev => 
                      prev ? { ...prev, penalties: e.target.value } : null
                    )}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Implementation Notes</label>
                  <Textarea
                    rows={3}
                    value={editingRule.implementationNotes}
                    onChange={(e) => setEditingRule(prev => 
                      prev ? { ...prev, implementationNotes: e.target.value } : null
                    )}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Citations (comma-separated)</label>
                  <Textarea
                    rows={2}
                    value={editingRule.citations.join(', ')}
                    onChange={(e) => setEditingRule(prev => 
                      prev ? { ...prev, citations: e.target.value.split(',').map(c => c.trim()).filter(c => c) } : null
                    )}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {filteredRules.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-gray-500">
              No rules match the current filters.
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}