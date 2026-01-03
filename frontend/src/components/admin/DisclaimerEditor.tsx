'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertTriangle, Save, Eye, Edit, Plus, Trash2, Copy, History, Shield } from 'lucide-react';

interface DisclaimerTemplate {
  id: string;
  name: string;
  type: 'initial_warning' | 'advice_limitation' | 'jurisdiction_notice' | 'confidentiality' | 'billing_terms' | 'custom';
  jurisdiction: string;
  content: string;
  isActive: boolean;
  requiredAcknowledgment: boolean;
  displayDuration: number; // seconds
  priority: 'low' | 'medium' | 'high' | 'critical';
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  version: number;
  approvalStatus: 'draft' | 'pending_review' | 'approved' | 'rejected';
  approvedBy?: string;
  approvedAt?: string;
  usageCount: number;
  acknowledgmentRate: number;
}

interface DisclaimerHistory {
  id: string;
  disclaimerId: string;
  version: number;
  content: string;
  changedBy: string;
  changedAt: string;
  changeReason: string;
}

export default function DisclaimerEditor() {
  const [disclaimers, setDisclaimers] = useState<DisclaimerTemplate[]>([]);
  const [history, setHistory] = useState<DisclaimerHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingDisclaimer, setEditingDisclaimer] = useState<DisclaimerTemplate | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');

  useEffect(() => {
    loadDisclaimers();
    loadHistory();
  }, []);

  const loadDisclaimers = async () => {
    setLoading(true);
    
    // Mock data - replace with actual API call
    const mockDisclaimers: DisclaimerTemplate[] = [
      {
        id: '1',
        name: 'California UPL Warning',
        type: 'initial_warning',
        jurisdiction: 'CA',
        content: `IMPORTANT NOTICE: This system provides legal information and document analysis tools, but does not provide legal advice. The use of this system does not create an attorney-client relationship. 

California residents should be aware that the practice of law is regulated by the State Bar of California. Only licensed attorneys may provide legal advice.

For legal advice specific to your situation, please consult with a qualified attorney licensed in California.`,
        isActive: true,
        requiredAcknowledgment: true,
        displayDuration: 30,
        priority: 'critical',
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-10T00:00:00Z',
        createdBy: 'admin@legal-system.com',
        version: 2,
        approvalStatus: 'approved',
        approvedBy: 'legal.counsel@legal-system.com',
        approvedAt: '2024-01-10T08:00:00Z',
        usageCount: 1247,
        acknowledgmentRate: 94.2
      },
      {
        id: '2',
        name: 'New York Advice Limitation',
        type: 'advice_limitation',
        jurisdiction: 'NY',
        content: `LIMITATION OF SERVICE: This platform provides information and analysis tools only. We do not provide legal advice or representation.

New York Rules of Professional Conduct prohibit the unauthorized practice of law. This service does not constitute legal practice and should not be relied upon as a substitute for legal counsel.

Any documents or information provided are for informational purposes only and may not be suitable for your specific legal needs.`,
        isActive: true,
        requiredAcknowledgment: true,
        displayDuration: 25,
        priority: 'high',
        createdAt: '2024-01-05T00:00:00Z',
        updatedAt: '2024-01-12T00:00:00Z',
        createdBy: 'admin@legal-system.com',
        version: 1,
        approvalStatus: 'approved',
        approvedBy: 'legal.counsel@legal-system.com',
        approvedAt: '2024-01-12T10:00:00Z',
        usageCount: 892,
        acknowledgmentRate: 87.6
      },
      {
        id: '3',
        name: 'Texas Attorney Supervision Notice',
        type: 'jurisdiction_notice',
        jurisdiction: 'TX',
        content: `TEXAS NOTICE: Legal services in Texas are regulated by the State Bar of Texas. This system operates under the supervision of licensed Texas attorneys.

All document analysis and legal research conducted through this platform is reviewed by qualified attorneys admitted to practice in Texas.

This notice is provided in compliance with Texas Disciplinary Rules of Professional Conduct.`,
        isActive: false,
        requiredAcknowledgment: true,
        displayDuration: 20,
        priority: 'medium',
        createdAt: '2024-01-08T00:00:00Z',
        updatedAt: '2024-01-13T00:00:00Z',
        createdBy: 'admin@legal-system.com',
        version: 1,
        approvalStatus: 'pending_review',
        usageCount: 634,
        acknowledgmentRate: 72.3
      }
    ];

    const mockHistory: DisclaimerHistory[] = [
      {
        id: '1',
        disclaimerId: '1',
        version: 1,
        content: 'Previous version of CA warning...',
        changedBy: 'legal.counsel@legal-system.com',
        changedAt: '2024-01-10T00:00:00Z',
        changeReason: 'Updated for State Bar requirements'
      }
    ];

    setDisclaimers(mockDisclaimers);
    setHistory(mockHistory);
    setLoading(false);
  };

  const loadHistory = async () => {
    // Mock history loading
  };

  const filteredDisclaimers = disclaimers.filter(disclaimer => {
    if (selectedJurisdiction !== 'all' && disclaimer.jurisdiction !== selectedJurisdiction) {
      return false;
    }
    if (selectedType !== 'all' && disclaimer.type !== selectedType) {
      return false;
    }
    return true;
  });

  const createNewDisclaimer = () => {
    const newDisclaimer: DisclaimerTemplate = {
      id: '',
      name: '',
      type: 'custom',
      jurisdiction: 'CA',
      content: '',
      isActive: false,
      requiredAcknowledgment: true,
      displayDuration: 30,
      priority: 'medium',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      createdBy: 'current.user@legal-system.com',
      version: 1,
      approvalStatus: 'draft',
      usageCount: 0,
      acknowledgmentRate: 0
    };
    setEditingDisclaimer(newDisclaimer);
    setIsCreating(true);
  };

  const saveDisclaimer = async () => {
    if (!editingDisclaimer) return;

    // Here you would make an API call to save the disclaimer
    console.log('Saving disclaimer:', editingDisclaimer);

    if (isCreating) {
      setDisclaimers(prev => [...prev, { ...editingDisclaimer, id: Date.now().toString() }]);
    } else {
      setDisclaimers(prev => prev.map(d => 
        d.id === editingDisclaimer.id ? editingDisclaimer : d
      ));
    }

    setEditingDisclaimer(null);
    setIsCreating(false);
  };

  const duplicateDisclaimer = (disclaimer: DisclaimerTemplate) => {
    const duplicate: DisclaimerTemplate = {
      ...disclaimer,
      id: '',
      name: `${disclaimer.name} (Copy)`,
      isActive: false,
      approvalStatus: 'draft',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      version: 1,
      usageCount: 0,
      acknowledgmentRate: 0
    };
    setEditingDisclaimer(duplicate);
    setIsCreating(true);
  };

  const deleteDisclaimer = async (id: string) => {
    if (confirm('Are you sure you want to delete this disclaimer? This action cannot be undone.')) {
      setDisclaimers(prev => prev.filter(d => d.id !== id));
    }
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      pending_review: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800'
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

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading disclaimers...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Professional Responsibility Notice */}
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="pt-6">
          <div className="flex items-start space-x-3">
            <Shield className="h-5 w-5 text-amber-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-amber-800">Disclaimer Management System</h3>
              <p className="text-sm text-amber-700 mt-1">
                All disclaimer changes require legal review and approval. Modifications to jurisdiction-specific 
                disclaimers must comply with local bar rules and professional responsibility requirements.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Header with Actions */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Disclaimer Management</h2>
        <Button onClick={createNewDisclaimer}>
          <Plus className="h-4 w-4 mr-2" />
          Create New Disclaimer
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <Select value={selectedJurisdiction} onValueChange={setSelectedJurisdiction}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by jurisdiction" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Jurisdictions</SelectItem>
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
                <SelectItem value="initial_warning">Initial Warning</SelectItem>
                <SelectItem value="advice_limitation">Advice Limitation</SelectItem>
                <SelectItem value="jurisdiction_notice">Jurisdiction Notice</SelectItem>
                <SelectItem value="confidentiality">Confidentiality</SelectItem>
                <SelectItem value="billing_terms">Billing Terms</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Disclaimer List */}
      <div className="grid grid-cols-1 gap-4">
        {filteredDisclaimers.map((disclaimer) => (
          <Card key={disclaimer.id} className={!disclaimer.isActive ? 'opacity-60' : ''}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="flex items-center space-x-2">
                    <span>{disclaimer.name}</span>
                    {!disclaimer.isActive && <Badge variant="outline">INACTIVE</Badge>}
                  </CardTitle>
                  <div className="flex items-center space-x-2 mt-2">
                    <Badge variant="outline">{disclaimer.jurisdiction}</Badge>
                    <Badge variant="outline">{disclaimer.type.replace('_', ' ')}</Badge>
                    {getStatusBadge(disclaimer.approvalStatus)}
                    {getPriorityBadge(disclaimer.priority)}
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setEditingDisclaimer(disclaimer)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => duplicateDisclaimer(disclaimer)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => deleteDisclaimer(disclaimer.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="text-sm text-gray-600 line-clamp-3">
                  {disclaimer.content.substring(0, 200)}...
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Usage:</span> {disclaimer.usageCount}
                  </div>
                  <div>
                    <span className="font-medium">Ack Rate:</span> {disclaimer.acknowledgmentRate.toFixed(1)}%
                  </div>
                  <div>
                    <span className="font-medium">Display:</span> {disclaimer.displayDuration}s
                  </div>
                  <div>
                    <span className="font-medium">Version:</span> {disclaimer.version}
                  </div>
                </div>
                {disclaimer.approvedBy && (
                  <div className="text-xs text-gray-500">
                    Approved by {disclaimer.approvedBy} on {new Date(disclaimer.approvedAt!).toLocaleDateString()}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Edit/Create Modal */}
      {editingDisclaimer && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{isCreating ? 'Create New Disclaimer' : 'Edit Disclaimer'}</span>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  onClick={() => setPreviewMode(!previewMode)}
                >
                  <Eye className="h-4 w-4 mr-2" />
                  {previewMode ? 'Edit' : 'Preview'}
                </Button>
                <Button onClick={saveDisclaimer}>
                  <Save className="h-4 w-4 mr-2" />
                  Save
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setEditingDisclaimer(null);
                    setIsCreating(false);
                    setPreviewMode(false);
                  }}
                >
                  Cancel
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {previewMode ? (
              <div className="p-4 border rounded-lg bg-gray-50">
                <h3 className="font-medium mb-2">{editingDisclaimer.name}</h3>
                <div className="whitespace-pre-wrap text-sm">
                  {editingDisclaimer.content}
                </div>
                <div className="mt-4 flex items-center space-x-4 text-xs text-gray-500">
                  <span>Display Duration: {editingDisclaimer.displayDuration}s</span>
                  <span>Required Acknowledgment: {editingDisclaimer.requiredAcknowledgment ? 'Yes' : 'No'}</span>
                  <span>Priority: {editingDisclaimer.priority}</span>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Name</label>
                    <Input
                      value={editingDisclaimer.name}
                      onChange={(e) => setEditingDisclaimer(prev => 
                        prev ? { ...prev, name: e.target.value } : null
                      )}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Type</label>
                    <Select
                      value={editingDisclaimer.type}
                      onValueChange={(value: any) => setEditingDisclaimer(prev => 
                        prev ? { ...prev, type: value } : null
                      )}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="initial_warning">Initial Warning</SelectItem>
                        <SelectItem value="advice_limitation">Advice Limitation</SelectItem>
                        <SelectItem value="jurisdiction_notice">Jurisdiction Notice</SelectItem>
                        <SelectItem value="confidentiality">Confidentiality</SelectItem>
                        <SelectItem value="billing_terms">Billing Terms</SelectItem>
                        <SelectItem value="custom">Custom</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Jurisdiction</label>
                    <Select
                      value={editingDisclaimer.jurisdiction}
                      onValueChange={(value: string) => setEditingDisclaimer(prev =>
                        prev ? { ...prev, jurisdiction: value } : null
                      )}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="CA">California</SelectItem>
                        <SelectItem value="NY">New York</SelectItem>
                        <SelectItem value="TX">Texas</SelectItem>
                        <SelectItem value="FL">Florida</SelectItem>
                        <SelectItem value="ALL">All States</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Priority</label>
                    <Select
                      value={editingDisclaimer.priority}
                      onValueChange={(value: any) => setEditingDisclaimer(prev => 
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
                    <label className="block text-sm font-medium mb-2">Display Duration (seconds)</label>
                    <Input
                      type="number"
                      value={editingDisclaimer.displayDuration}
                      onChange={(e) => setEditingDisclaimer(prev => 
                        prev ? { ...prev, displayDuration: parseInt(e.target.value) || 30 } : null
                      )}
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="requiredAcknowledgment"
                      checked={editingDisclaimer.requiredAcknowledgment}
                      onChange={(e) => setEditingDisclaimer(prev => 
                        prev ? { ...prev, requiredAcknowledgment: e.target.checked } : null
                      )}
                    />
                    <label htmlFor="requiredAcknowledgment" className="text-sm font-medium">
                      Required Acknowledgment
                    </label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="isActive"
                      checked={editingDisclaimer.isActive}
                      onChange={(e) => setEditingDisclaimer(prev => 
                        prev ? { ...prev, isActive: e.target.checked } : null
                      )}
                    />
                    <label htmlFor="isActive" className="text-sm font-medium">
                      Active
                    </label>
                  </div>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium mb-2">Content</label>
                  <Textarea
                    rows={8}
                    value={editingDisclaimer.content}
                    onChange={(e) => setEditingDisclaimer(prev => 
                      prev ? { ...prev, content: e.target.value } : null
                    )}
                    placeholder="Enter disclaimer content..."
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {filteredDisclaimers.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-gray-500">
              No disclaimers match the current filters.
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}