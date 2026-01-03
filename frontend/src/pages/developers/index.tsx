/**
 * Legal AI System - Developer Portal
 * Comprehensive developer portal with API documentation and tools
 */

import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  CodeBracketIcon,
  KeyIcon,
  DocumentTextIcon,
  ChartBarIcon,
  CogIcon,
  ShieldCheckIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowTopRightOnSquareIcon,
  CopyIcon
} from '@heroicons/react/24/outline';

interface APIKey {
  id: number;
  key_id: string;
  name: string;
  scopes: string[];
  status: string;
  created_at: string;
  last_used_at?: string;
  expires_at?: string;
}

interface UsageStats {
  requests_today: number;
  requests_this_month: number;
  rate_limit_exceeded: number;
  most_used_endpoint?: string;
}

const DeveloperPortal: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [newKeyForm, setNewKeyForm] = useState({
    name: '',
    scopes: [] as string[],
    expires_in_days: ''
  });

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // Show toast notification
  };

  const handleCreateAPIKey = async () => {
    // API call to create new key
  };

  const availableScopes = [
    { value: 'read', label: 'Read Access', description: 'Read documents and analysis results' },
    { value: 'write', label: 'Write Access', description: 'Create and modify documents' },
    { value: 'webhook', label: 'Webhook Access', description: 'Receive webhook notifications' }
  ];

  const codeExamples = {
    curl: `curl -X POST "https://api.legal-ai.com/v1/documents/analyze" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "document_content": "Your legal document text here",
    "analysis_type": "contract_review"
  }'`,

    python: `import requests

url = "https://api.legal-ai.com/v1/documents/analyze"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
data = {
    "document_content": "Your legal document text here",
    "analysis_type": "contract_review"
}

response = requests.post(url, headers=headers, json=data)
result = response.json()`,

    javascript: `const response = await fetch('https://api.legal-ai.com/v1/documents/analyze', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    document_content: 'Your legal document text here',
    analysis_type: 'contract_review'
  })
});

const result = await response.json();`,

    php: `<?php
$url = 'https://api.legal-ai.com/v1/documents/analyze';
$data = array(
    'document_content' => 'Your legal document text here',
    'analysis_type' => 'contract_review'
);

$options = array(
    'http' => array(
        'header' => "Authorization: Bearer YOUR_API_KEY\\r\\n" .
                   "Content-Type: application/json\\r\\n",
        'method' => 'POST',
        'content' => json_encode($data)
    )
);

$context = stream_context_create($options);
$result = file_get_contents($url, false, $context);
$response = json_decode($result, true);
?>`
  };

  return (
    <>
      <Head>
        <title>Developer Portal - Legal AI API Documentation</title>
        <meta name="description" content="Integrate Legal AI into your applications with our comprehensive API. Documentation, SDKs, and developer tools." />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-8">
                <Link href="/" className="text-2xl font-bold text-blue-600">
                  Legal AI
                </Link>
                <Badge variant="outline">Developer Portal</Badge>
              </div>
              <div className="flex items-center space-x-4">
                <Link href="/docs" className="text-gray-600 hover:text-blue-600">
                  API Docs
                </Link>
                <Link href="/support" className="text-gray-600 hover:text-blue-600">
                  Support
                </Link>
                <Button>Dashboard</Button>
              </div>
            </div>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Developer Portal</h1>
            <p className="text-gray-600">
              Integrate Legal AI's powerful document analysis and legal research capabilities into your applications.
            </p>
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="api-keys">API Keys</TabsTrigger>
              <TabsTrigger value="usage">Usage</TabsTrigger>
              <TabsTrigger value="webhooks">Webhooks</TabsTrigger>
              <TabsTrigger value="examples">Examples</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              {/* Quick Stats */}
              <div className="grid md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-2">
                      <KeyIcon className="h-5 w-5 text-blue-600" />
                      <div>
                        <div className="text-sm text-gray-600">API Keys</div>
                        <div className="text-2xl font-bold">{apiKeys.length}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-2">
                      <ChartBarIcon className="h-5 w-5 text-green-600" />
                      <div>
                        <div className="text-sm text-gray-600">Requests Today</div>
                        <div className="text-2xl font-bold">{usageStats?.requests_today || 0}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-2">
                      <ClockIcon className="h-5 w-5 text-orange-600" />
                      <div>
                        <div className="text-sm text-gray-600">This Month</div>
                        <div className="text-2xl font-bold">{usageStats?.requests_this_month || 0}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-2">
                      <ShieldCheckIcon className="h-5 w-5 text-purple-600" />
                      <div>
                        <div className="text-sm text-gray-600">Rate Limits</div>
                        <div className="text-2xl font-bold text-green-600">OK</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Getting Started */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <CodeBracketIcon className="h-6 w-6" />
                    <span>Getting Started</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid md:grid-cols-3 gap-6">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold">1</div>
                        <h3 className="font-semibold">Create API Key</h3>
                      </div>
                      <p className="text-sm text-gray-600">
                        Generate your API key to authenticate requests to the Legal AI API.
                      </p>
                      <Link href="#api-keys">
                        <Button size="sm" variant="outline">Create Key</Button>
                      </Link>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold">2</div>
                        <h3 className="font-semibold">Read Documentation</h3>
                      </div>
                      <p className="text-sm text-gray-600">
                        Explore our comprehensive API documentation and integration guides.
                      </p>
                      <Link href="/docs">
                        <Button size="sm" variant="outline">View Docs</Button>
                      </Link>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold">3</div>
                        <h3 className="font-semibold">Start Building</h3>
                      </div>
                      <p className="text-sm text-gray-600">
                        Use our SDKs and code examples to integrate Legal AI into your application.
                      </p>
                      <Link href="#examples">
                        <Button size="sm" variant="outline">See Examples</Button>
                      </Link>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* API Features */}
              <Card>
                <CardHeader>
                  <CardTitle>API Capabilities</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="p-4 border rounded-lg">
                      <DocumentTextIcon className="h-8 w-8 text-blue-600 mb-2" />
                      <h3 className="font-semibold mb-2">Document Analysis</h3>
                      <p className="text-sm text-gray-600">
                        Analyze contracts, legal briefs, and other documents with AI-powered insights.
                      </p>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <CodeBracketIcon className="h-8 w-8 text-green-600 mb-2" />
                      <h3 className="font-semibold mb-2">Legal Research</h3>
                      <p className="text-sm text-gray-600">
                        Access comprehensive legal research capabilities including case law and statutes.
                      </p>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <ShieldCheckIcon className="h-8 w-8 text-purple-600 mb-2" />
                      <h3 className="font-semibold mb-2">Compliance Check</h3>
                      <p className="text-sm text-gray-600">
                        Verify document compliance with relevant regulations and standards.
                      </p>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <CogIcon className="h-8 w-8 text-orange-600 mb-2" />
                      <h3 className="font-semibold mb-2">Workflow Automation</h3>
                      <p className="text-sm text-gray-600">
                        Automate legal workflows and document processing tasks.
                      </p>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <ChartBarIcon className="h-8 w-8 text-red-600 mb-2" />
                      <h3 className="font-semibold mb-2">Analytics & Reporting</h3>
                      <p className="text-sm text-gray-600">
                        Generate insights and reports from your legal document analysis.
                      </p>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <ClockIcon className="h-8 w-8 text-indigo-600 mb-2" />
                      <h3 className="font-semibold mb-2">Real-time Processing</h3>
                      <p className="text-sm text-gray-600">
                        Process documents in real-time with webhook notifications.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* API Keys Tab */}
            <TabsContent value="api-keys" className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold">API Keys</h2>
                  <p className="text-gray-600">Manage your API keys and access tokens</p>
                </div>
                <Button>Create New API Key</Button>
              </div>

              {/* Create API Key Form */}
              <Card>
                <CardHeader>
                  <CardTitle>Create New API Key</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="key-name">Key Name</Label>
                      <Input
                        id="key-name"
                        placeholder="e.g., Production API Key"
                        value={newKeyForm.name}
                        onChange={(e) => setNewKeyForm({...newKeyForm, name: e.target.value})}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="expires">Expires In</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Never" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="never">Never</SelectItem>
                          <SelectItem value="30">30 days</SelectItem>
                          <SelectItem value="90">90 days</SelectItem>
                          <SelectItem value="365">1 year</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Scopes</Label>
                    <div className="grid md:grid-cols-3 gap-4">
                      {availableScopes.map((scope) => (
                        <div key={scope.value} className="flex items-start space-x-2 p-3 border rounded-lg">
                          <input
                            type="checkbox"
                            id={scope.value}
                            className="mt-1"
                            checked={newKeyForm.scopes.includes(scope.value)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setNewKeyForm({
                                  ...newKeyForm,
                                  scopes: [...newKeyForm.scopes, scope.value]
                                });
                              } else {
                                setNewKeyForm({
                                  ...newKeyForm,
                                  scopes: newKeyForm.scopes.filter(s => s !== scope.value)
                                });
                              }
                            }}
                          />
                          <div>
                            <label htmlFor={scope.value} className="font-medium text-sm">
                              {scope.label}
                            </label>
                            <p className="text-xs text-gray-600">{scope.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <Button onClick={handleCreateAPIKey}>Create API Key</Button>
                </CardContent>
              </Card>

              {/* Existing API Keys */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Your API Keys</h3>
                {apiKeys.length === 0 ? (
                  <Card>
                    <CardContent className="p-8 text-center">
                      <KeyIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold mb-2">No API Keys</h3>
                      <p className="text-gray-600 mb-4">Create your first API key to get started with the Legal AI API.</p>
                      <Button>Create API Key</Button>
                    </CardContent>
                  </Card>
                ) : (
                  apiKeys.map((key) => (
                    <Card key={key.id}>
                      <CardContent className="p-6">
                        <div className="flex justify-between items-start">
                          <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                              <h3 className="font-semibold">{key.name}</h3>
                              <Badge variant={key.status === 'active' ? 'default' : 'destructive'}>
                                {key.status}
                              </Badge>
                            </div>
                            <div className="flex items-center space-x-4 text-sm text-gray-600">
                              <span>Key ID: {key.key_id}</span>
                              <button
                                onClick={() => copyToClipboard(key.key_id)}
                                className="hover:text-blue-600"
                              >
                                <CopyIcon className="h-4 w-4" />
                              </button>
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {key.scopes.map((scope) => (
                                <Badge key={scope} variant="outline" className="text-xs">
                                  {scope}
                                </Badge>
                              ))}
                            </div>
                            <div className="text-sm text-gray-600">
                              Created: {new Date(key.created_at).toLocaleDateString()}
                              {key.last_used_at && (
                                <span className="ml-4">
                                  Last used: {new Date(key.last_used_at).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="space-x-2">
                            <Button variant="outline" size="sm">Edit</Button>
                            <Button variant="destructive" size="sm">Revoke</Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </TabsContent>

            {/* Usage Tab */}
            <TabsContent value="usage" className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold">API Usage</h2>
                <p className="text-gray-600">Monitor your API usage and performance</p>
              </div>

              {/* Usage Charts and Stats would go here */}
              <Card>
                <CardHeader>
                  <CardTitle>Usage Statistics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8">
                    <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">Usage analytics will appear here</p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Webhooks Tab */}
            <TabsContent value="webhooks" className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold">Webhooks</h2>
                  <p className="text-gray-600">Configure webhook endpoints for real-time notifications</p>
                </div>
                <Button>Add Webhook</Button>
              </div>

              <Card>
                <CardContent className="p-8 text-center">
                  <CogIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Webhooks Configured</h3>
                  <p className="text-gray-600 mb-4">Set up webhooks to receive real-time notifications about document processing and analysis completion.</p>
                  <Button>Configure Webhook</Button>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Examples Tab */}
            <TabsContent value="examples" className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold">Code Examples</h2>
                <p className="text-gray-600">Get started quickly with these code examples</p>
              </div>

              <Tabs defaultValue="curl" className="space-y-4">
                <TabsList>
                  <TabsTrigger value="curl">cURL</TabsTrigger>
                  <TabsTrigger value="python">Python</TabsTrigger>
                  <TabsTrigger value="javascript">JavaScript</TabsTrigger>
                  <TabsTrigger value="php">PHP</TabsTrigger>
                </TabsList>

                {Object.entries(codeExamples).map(([language, code]) => (
                  <TabsContent key={language} value={language}>
                    <Card>
                      <CardHeader>
                        <div className="flex justify-between items-center">
                          <CardTitle className="capitalize">{language} Example</CardTitle>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => copyToClipboard(code)}
                          >
                            <CopyIcon className="h-4 w-4 mr-2" />
                            Copy
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                          <code>{code}</code>
                        </pre>
                      </CardContent>
                    </Card>
                  </TabsContent>
                ))}
              </Tabs>

              {/* SDKs */}
              <Card>
                <CardHeader>
                  <CardTitle>Official SDKs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="p-4 border rounded-lg text-center">
                      <div className="text-3xl mb-2">🐍</div>
                      <h3 className="font-semibold mb-2">Python SDK</h3>
                      <Button variant="outline" size="sm">
                        <ArrowTopRightOnSquareIcon className="h-4 w-4 mr-2" />
                        Install
                      </Button>
                    </div>

                    <div className="p-4 border rounded-lg text-center">
                      <div className="text-3xl mb-2">⚡</div>
                      <h3 className="font-semibold mb-2">Node.js SDK</h3>
                      <Button variant="outline" size="sm">
                        <ArrowTopRightOnSquareIcon className="h-4 w-4 mr-2" />
                        Install
                      </Button>
                    </div>

                    <div className="p-4 border rounded-lg text-center">
                      <div className="text-3xl mb-2">🐘</div>
                      <h3 className="font-semibold mb-2">PHP SDK</h3>
                      <Button variant="outline" size="sm">
                        <ArrowTopRightOnSquareIcon className="h-4 w-4 mr-2" />
                        Install
                      </Button>
                    </div>

                    <div className="p-4 border rounded-lg text-center">
                      <div className="text-3xl mb-2">☕</div>
                      <h3 className="font-semibold mb-2">Java SDK</h3>
                      <Button variant="outline" size="sm">
                        <ArrowTopRightOnSquareIcon className="h-4 w-4 mr-2" />
                        Install
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </>
  );
};

export default DeveloperPortal;