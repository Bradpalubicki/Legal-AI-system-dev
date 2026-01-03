'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/Input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertTriangle, Download, FileText, Calendar, Filter, Shield, TrendingUp, BarChart3, PieChart } from 'lucide-react';

interface ComplianceReport {
  id: string;
  title: string;
  type: 'monthly' | 'quarterly' | 'annual' | 'incident' | 'audit' | 'custom';
  status: 'generating' | 'ready' | 'error' | 'archived';
  period: {
    start: string;
    end: string;
  };
  jurisdiction: string[];
  generatedAt: string;
  generatedBy: string;
  fileSize: number;
  summary: {
    totalViolations: number;
    criticalIssues: number;
    complianceScore: number;
    recommendations: number;
  };
  sections: string[];
  redactionLevel: 'none' | 'partial' | 'full';
  downloadCount: number;
  expirationDate?: string;
}

interface ReportTemplate {
  id: string;
  name: string;
  type: 'monthly' | 'quarterly' | 'annual' | 'incident' | 'audit' | 'custom';
  sections: string[];
  jurisdictions: string[];
  schedule?: string; // cron expression
  autoGenerate: boolean;
  recipients: string[];
  redactionLevel: 'none' | 'partial' | 'full';
  isActive: boolean;
}

export default function ComplianceReports() {
  const [reports, setReports] = useState<ComplianceReport[]>([]);
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [customReportConfig, setCustomReportConfig] = useState<{
    title: string;
    type: string;
    startDate: string;
    endDate: string;
    jurisdictions: string[];
    sections: string[];
    redactionLevel: string;
  }>({
    title: '',
    type: 'custom',
    startDate: '',
    endDate: '',
    jurisdictions: [],
    sections: [],
    redactionLevel: 'partial'
  });

  useEffect(() => {
    loadReports();
    loadTemplates();
  }, []);

  const loadReports = async () => {
    setLoading(true);
    
    // Mock data - replace with actual API call
    const mockReports: ComplianceReport[] = [
      {
        id: '1',
        title: 'January 2024 Monthly Compliance Report',
        type: 'monthly',
        status: 'ready',
        period: {
          start: '2024-01-01T00:00:00Z',
          end: '2024-01-31T23:59:59Z'
        },
        jurisdiction: ['CA', 'NY', 'TX'],
        generatedAt: '2024-02-01T09:00:00Z',
        generatedBy: 'system.admin@legal-system.com',
        fileSize: 2547892,
        summary: {
          totalViolations: 12,
          criticalIssues: 3,
          complianceScore: 87.4,
          recommendations: 8
        },
        sections: [
          'Executive Summary',
          'UPL Compliance Analysis',
          'Attorney Supervision Review',
          'Disclaimer Effectiveness',
          'State-Specific Compliance',
          'Violation Reports',
          'Recommendations'
        ],
        redactionLevel: 'partial',
        downloadCount: 15,
        expirationDate: '2024-08-01T00:00:00Z'
      },
      {
        id: '2',
        title: 'Q4 2023 Quarterly Audit Report',
        type: 'quarterly',
        status: 'ready',
        period: {
          start: '2023-10-01T00:00:00Z',
          end: '2023-12-31T23:59:59Z'
        },
        jurisdiction: ['CA', 'NY', 'TX', 'FL'],
        generatedAt: '2024-01-15T14:30:00Z',
        generatedBy: 'legal.counsel@legal-system.com',
        fileSize: 4892341,
        summary: {
          totalViolations: 34,
          criticalIssues: 7,
          complianceScore: 82.1,
          recommendations: 18
        },
        sections: [
          'Quarterly Overview',
          'Compliance Metrics Trends',
          'Attorney Verification Status',
          'State Rule Changes',
          'Risk Assessment',
          'Client Feedback Analysis',
          'Action Items'
        ],
        redactionLevel: 'partial',
        downloadCount: 8,
        expirationDate: '2024-07-15T00:00:00Z'
      },
      {
        id: '3',
        title: 'UPL Violation Incident Report - TX-2024-001',
        type: 'incident',
        status: 'ready',
        period: {
          start: '2024-01-10T00:00:00Z',
          end: '2024-01-15T00:00:00Z'
        },
        jurisdiction: ['TX'],
        generatedAt: '2024-01-16T10:15:00Z',
        generatedBy: 'compliance.team@legal-system.com',
        fileSize: 892456,
        summary: {
          totalViolations: 7,
          criticalIssues: 7,
          complianceScore: 45.2,
          recommendations: 12
        },
        sections: [
          'Incident Summary',
          'Timeline of Events',
          'Root Cause Analysis',
          'Immediate Actions Taken',
          'Corrective Measures',
          'Prevention Recommendations'
        ],
        redactionLevel: 'full',
        downloadCount: 3
      },
      {
        id: '4',
        title: 'February 2024 Monthly Report',
        type: 'monthly',
        status: 'generating',
        period: {
          start: '2024-02-01T00:00:00Z',
          end: '2024-02-29T23:59:59Z'
        },
        jurisdiction: ['CA', 'NY', 'TX'],
        generatedAt: '2024-03-01T08:00:00Z',
        generatedBy: 'system.admin@legal-system.com',
        fileSize: 0,
        summary: {
          totalViolations: 0,
          criticalIssues: 0,
          complianceScore: 0,
          recommendations: 0
        },
        sections: [],
        redactionLevel: 'partial',
        downloadCount: 0
      }
    ];

    const mockTemplates: ReportTemplate[] = [
      {
        id: '1',
        name: 'Standard Monthly Report',
        type: 'monthly',
        sections: [
          'Executive Summary',
          'UPL Compliance Analysis', 
          'Attorney Supervision Review',
          'Disclaimer Effectiveness',
          'State-Specific Compliance',
          'Recommendations'
        ],
        jurisdictions: ['CA', 'NY', 'TX'],
        schedule: '0 9 1 * *', // First day of month at 9 AM
        autoGenerate: true,
        recipients: [
          'legal.counsel@legal-system.com',
          'compliance.team@legal-system.com'
        ],
        redactionLevel: 'partial',
        isActive: true
      }
    ];

    setReports(mockReports);
    setTemplates(mockTemplates);
    setLoading(false);
  };

  const loadTemplates = async () => {
    // Mock template loading
  };

  const filteredReports = reports.filter(report => {
    if (selectedType !== 'all' && report.type !== selectedType) {
      return false;
    }
    if (selectedJurisdiction !== 'all' && !report.jurisdiction.includes(selectedJurisdiction)) {
      return false;
    }
    if (selectedStatus !== 'all' && report.status !== selectedStatus) {
      return false;
    }
    return true;
  });

  const generateCustomReport = async () => {
    if (!customReportConfig.title || !customReportConfig.startDate || !customReportConfig.endDate) {
      alert('Please fill in all required fields');
      return;
    }

    const reportId = Date.now().toString();
    setGenerating(reportId);

    // Mock report generation
    setTimeout(() => {
      const newReport: ComplianceReport = {
        id: reportId,
        title: customReportConfig.title,
        type: customReportConfig.type as any,
        status: 'ready',
        period: {
          start: customReportConfig.startDate,
          end: customReportConfig.endDate
        },
        jurisdiction: customReportConfig.jurisdictions,
        generatedAt: new Date().toISOString(),
        generatedBy: 'current.user@legal-system.com',
        fileSize: Math.floor(Math.random() * 5000000) + 1000000,
        summary: {
          totalViolations: Math.floor(Math.random() * 20),
          criticalIssues: Math.floor(Math.random() * 5),
          complianceScore: Math.floor(Math.random() * 30) + 70,
          recommendations: Math.floor(Math.random() * 10) + 5
        },
        sections: customReportConfig.sections,
        redactionLevel: customReportConfig.redactionLevel as any,
        downloadCount: 0
      };

      setReports(prev => [newReport, ...prev]);
      setGenerating(null);
      
      // Reset form
      setCustomReportConfig({
        title: '',
        type: 'custom',
        startDate: '',
        endDate: '',
        jurisdictions: [],
        sections: [],
        redactionLevel: 'partial'
      });
    }, 3000);
  };

  const downloadReport = (reportId: string) => {
    const report = reports.find(r => r.id === reportId);
    if (!report || report.status !== 'ready') return;

    // Mock file download
    const mockContent = {
      reportId: report.id,
      title: report.title,
      type: report.type,
      period: report.period,
      jurisdiction: report.jurisdiction,
      summary: report.summary,
      generatedAt: report.generatedAt,
      redactionLevel: report.redactionLevel,
      sections: report.sections.map(section => ({
        title: section,
        content: '[REDACTED CONTENT FOR EXPORT]'
      })),
      disclaimer: 'This report contains sensitive legal compliance information. Distribution is restricted to authorized personnel only.',
      watermark: `Generated by Legal AI System on ${new Date().toISOString()}`
    };

    const blob = new Blob([JSON.stringify(mockContent, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${report.title.replace(/[^a-zA-Z0-9]/g, '_')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    // Update download count
    setReports(prev => prev.map(r => 
      r.id === reportId ? { ...r, downloadCount: r.downloadCount + 1 } : r
    ));
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      generating: 'bg-blue-100 text-blue-800',
      ready: 'bg-green-100 text-green-800',
      error: 'bg-red-100 text-red-800',
      archived: 'bg-gray-100 text-gray-800'
    };
    return <Badge className={colors[status as keyof typeof colors]}>{status.toUpperCase()}</Badge>;
  };

  const getTypeBadge = (type: string) => {
    const colors = {
      monthly: 'bg-blue-100 text-blue-800',
      quarterly: 'bg-purple-100 text-purple-800',
      annual: 'bg-green-100 text-green-800',
      incident: 'bg-red-100 text-red-800',
      audit: 'bg-yellow-100 text-yellow-800',
      custom: 'bg-gray-100 text-gray-800'
    };
    return <Badge className={colors[type as keyof typeof colors]}>{type.toUpperCase()}</Badge>;
  };

  const getRedactionBadge = (level: string) => {
    const colors = {
      none: 'bg-red-100 text-red-800',
      partial: 'bg-yellow-100 text-yellow-800',
      full: 'bg-green-100 text-green-800'
    };
    return <Badge className={colors[level as keyof typeof colors]}>{level.toUpperCase()}</Badge>;
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getComplianceScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-yellow-600';
    if (score >= 70) return 'text-orange-600';
    return 'text-red-600';
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading compliance reports...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Professional Responsibility Notice */}
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="pt-6">
          <div className="flex items-start space-x-3">
            <Shield className="h-5 w-5 text-amber-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-amber-800">Compliance Reporting System</h3>
              <p className="text-sm text-amber-700 mt-1">
                This system generates comprehensive compliance reports for legal review and regulatory purposes. 
                All reports contain sensitive information and must be handled according to data protection policies. 
                Distribution is restricted to authorized personnel only.
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
                <p className="text-sm font-medium text-gray-600">Total Reports</p>
                <p className="text-2xl font-bold">{reports.length}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Ready Reports</p>
                <p className="text-2xl font-bold text-green-600">
                  {reports.filter(r => r.status === 'ready').length}
                </p>
              </div>
              <BarChart3 className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Compliance Score</p>
                <p className={`text-2xl font-bold ${getComplianceScoreColor(
                  reports.filter(r => r.status === 'ready').reduce((acc, r) => acc + r.summary.complianceScore, 0) / 
                  Math.max(reports.filter(r => r.status === 'ready').length, 1)
                )}`}>
                  {Math.round(
                    reports.filter(r => r.status === 'ready').reduce((acc, r) => acc + r.summary.complianceScore, 0) / 
                    Math.max(reports.filter(r => r.status === 'ready').length, 1)
                  )}%
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Critical Issues</p>
                <p className="text-2xl font-bold text-red-600">
                  {reports.filter(r => r.status === 'ready').reduce((acc, r) => acc + r.summary.criticalIssues, 0)}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Custom Report Generator */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <PieChart className="h-5 w-5" />
            <span>Generate Custom Report</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Report Title</label>
              <Input
                placeholder="Enter report title"
                value={customReportConfig.title}
                onChange={(e) => setCustomReportConfig(prev => ({ ...prev, title: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Start Date</label>
              <Input
                type="date"
                value={customReportConfig.startDate.split('T')[0]}
                onChange={(e) => setCustomReportConfig(prev => ({ ...prev, startDate: e.target.value + 'T00:00:00Z' }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">End Date</label>
              <Input
                type="date"
                value={customReportConfig.endDate.split('T')[0]}
                onChange={(e) => setCustomReportConfig(prev => ({ ...prev, endDate: e.target.value + 'T23:59:59Z' }))}
              />
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <Button 
              onClick={generateCustomReport}
              disabled={generating !== null}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {generating ? 'Generating...' : 'Generate Report'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Reports List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span>Compliance Reports</span>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex flex-wrap gap-4 mb-6">
            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
                <SelectItem value="quarterly">Quarterly</SelectItem>
                <SelectItem value="annual">Annual</SelectItem>
                <SelectItem value="incident">Incident</SelectItem>
                <SelectItem value="audit">Audit</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedJurisdiction} onValueChange={setSelectedJurisdiction}>
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
            <Select value={selectedStatus} onValueChange={setSelectedStatus}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="ready">Ready</SelectItem>
                <SelectItem value="generating">Generating</SelectItem>
                <SelectItem value="error">Error</SelectItem>
                <SelectItem value="archived">Archived</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Reports Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Report</th>
                  <th className="text-left p-2">Type</th>
                  <th className="text-left p-2">Status</th>
                  <th className="text-left p-2">Period</th>
                  <th className="text-left p-2">Compliance Score</th>
                  <th className="text-left p-2">Issues</th>
                  <th className="text-left p-2">Size</th>
                  <th className="text-left p-2">Downloads</th>
                  <th className="text-left p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.map((report) => (
                  <tr key={report.id} className="border-b hover:bg-gray-50">
                    <td className="p-2">
                      <div>
                        <div className="text-sm font-medium">{report.title}</div>
                        <div className="text-xs text-gray-500">
                          Generated {new Date(report.generatedAt).toLocaleDateString()}
                        </div>
                        <div className="flex items-center space-x-1 mt-1">
                          {report.jurisdiction.map(j => (
                            <Badge key={j} variant="outline" className="text-xs">{j}</Badge>
                          ))}
                          {getRedactionBadge(report.redactionLevel)}
                        </div>
                      </div>
                    </td>
                    <td className="p-2">
                      {getTypeBadge(report.type)}
                    </td>
                    <td className="p-2">
                      {getStatusBadge(report.status)}
                    </td>
                    <td className="p-2 text-sm">
                      <div>{new Date(report.period.start).toLocaleDateString()}</div>
                      <div>to {new Date(report.period.end).toLocaleDateString()}</div>
                    </td>
                    <td className="p-2">
                      {report.status === 'ready' && (
                        <div className={`text-sm font-medium ${getComplianceScoreColor(report.summary.complianceScore)}`}>
                          {report.summary.complianceScore.toFixed(1)}%
                        </div>
                      )}
                    </td>
                    <td className="p-2">
                      {report.status === 'ready' && (
                        <div className="text-sm space-y-1">
                          <div>Total: {report.summary.totalViolations}</div>
                          <div className="text-red-600">Critical: {report.summary.criticalIssues}</div>
                        </div>
                      )}
                    </td>
                    <td className="p-2 text-sm">
                      {report.fileSize > 0 ? formatFileSize(report.fileSize) : '-'}
                    </td>
                    <td className="p-2 text-sm">
                      {report.downloadCount}
                    </td>
                    <td className="p-2">
                      <div className="flex space-x-2">
                        {report.status === 'ready' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => downloadReport(report.id)}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                        )}
                        {report.status === 'generating' && generating === report.id && (
                          <div className="text-xs text-blue-600 animate-pulse">
                            Generating...
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredReports.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No reports match the current filters.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}