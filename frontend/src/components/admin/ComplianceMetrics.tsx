'use client';

import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Users,
  Clock,
  Shield,
  Scale,
  BarChart3,
  PieChart,
  Calendar,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';

interface MetricData {
  label: string;
  value: number;
  change: number;
  trend: 'up' | 'down' | 'stable';
  target?: number;
}

interface ChartDataPoint {
  date: string;
  value: number;
  category?: string;
}

interface ComplianceMetricsProps {
  timeRange?: '24h' | '7d' | '30d' | '90d';
  jurisdiction?: string;
  onMetricClick?: (metric: string) => void;
  className?: string;
}

const ComplianceMetrics: React.FC<ComplianceMetricsProps> = ({
  timeRange = '7d',
  jurisdiction = 'all',
  onMetricClick,
  className = ''
}) => {
  const [metrics, setMetrics] = useState<Record<string, MetricData>>({});
  const [uplTrendData, setUplTrendData] = useState<ChartDataPoint[]>([]);
  const [disclaimerTrendData, setDisclaimerTrendData] = useState<ChartDataPoint[]>([]);
  const [jurisdictionBreakdown, setJurisdictionBreakdown] = useState<ChartDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  useEffect(() => {
    loadMetricsData();
  }, [timeRange, jurisdiction]);

  const loadMetricsData = async () => {
    setIsLoading(true);
    
    // Simulate API call to load metrics
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock data based on timeRange and jurisdiction
    setMetrics({
      uplWarnings: {
        label: 'UPL Warnings',
        value: timeRange === '24h' ? 3 : timeRange === '7d' ? 12 : 47,
        change: timeRange === '24h' ? 50 : 15.8,
        trend: 'up',
        target: timeRange === '7d' ? 8 : 35
      },
      disclaimerRate: {
        label: 'Disclaimer Acknowledgment Rate',
        value: 91.5,
        change: 2.3,
        trend: 'up',
        target: 95
      },
      attorneyReviews: {
        label: 'Avg Attorney Review Time (hours)',
        value: 2.4,
        change: -0.6,
        trend: 'down',
        target: 4
      },
      stateCompliance: {
        label: 'State Compliance Rate',
        value: 94,
        change: 1.2,
        trend: 'up',
        target: 98
      },
      riskDetections: {
        label: 'High-Risk AI Outputs',
        value: timeRange === '24h' ? 1 : timeRange === '7d' ? 5 : 23,
        change: -12.5,
        trend: 'down',
        target: 10
      },
      sessionQuality: {
        label: 'Session Compliance Score',
        value: 87.3,
        change: 4.1,
        trend: 'up',
        target: 90
      }
    });

    // Mock trend data
    const generateTrendData = (baseValue: number, days: number) => {
      const data: ChartDataPoint[] = [];
      for (let i = days; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        data.push({
          date: date.toISOString().split('T')[0],
          value: baseValue + Math.random() * 10 - 5
        });
      }
      return data;
    };

    const days = timeRange === '24h' ? 1 : timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
    setUplTrendData(generateTrendData(12, days));
    setDisclaimerTrendData(generateTrendData(92, days));
    
    setJurisdictionBreakdown([
      { date: 'CA', value: 28, category: 'California' },
      { date: 'NY', value: 15, category: 'New York' },
      { date: 'TX', value: 12, category: 'Texas' },
      { date: 'FL', value: 8, category: 'Florida' },
      { date: 'Other', value: 37, category: 'Other States' }
    ]);

    setIsLoading(false);
  };

  const formatChange = (change: number, isPercentage = true) => {
    const sign = change >= 0 ? '+' : '';
    const suffix = isPercentage ? '%' : '';
    return `${sign}${change.toFixed(1)}${suffix}`;
  };

  const getTrendColor = (trend: 'up' | 'down' | 'stable', isGoodTrend = true) => {
    if (trend === 'stable') return 'text-gray-500';
    const isPositive = (trend === 'up' && isGoodTrend) || (trend === 'down' && !isGoodTrend);
    return isPositive ? 'text-green-600' : 'text-red-600';
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4" />;
      case 'down':
        return <TrendingDown className="h-4 w-4" />;
      default:
        return <div className="h-4 w-4" />;
    }
  };

  const getMetricStatus = (metric: MetricData) => {
    if (!metric.target) return 'neutral';
    
    if (metric.label.includes('Time') || metric.label.includes('Warning')) {
      // Lower is better for these metrics
      return metric.value <= metric.target ? 'good' : 'needs-attention';
    } else {
      // Higher is better for rate metrics
      return metric.value >= metric.target ? 'good' : 'needs-attention';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good':
        return 'border-green-200 bg-green-50';
      case 'needs-attention':
        return 'border-amber-200 bg-amber-50';
      default:
        return 'border-gray-200 bg-white';
    }
  };

  const SimpleBarChart: React.FC<{ data: ChartDataPoint[]; height?: number }> = ({ 
    data, 
    height = 60 
  }) => {
    const maxValue = Math.max(...data.map(d => d.value));
    const minValue = Math.min(...data.map(d => d.value));
    const range = maxValue - minValue || 1;
    
    return (
      <div className="flex items-end justify-between" style={{ height }}>
        {data.map((point, index) => {
          const barHeight = ((point.value - minValue) / range) * (height - 10) + 5;
          return (
            <div
              key={index}
              className="bg-primary-500 rounded-sm flex-1 mx-0.5 transition-all hover:bg-primary-600"
              style={{ height: barHeight }}
              title={`${point.date}: ${point.value}`}
            />
          );
        })}
      </div>
    );
  };

  const SimplePieChart: React.FC<{ data: ChartDataPoint[] }> = ({ data }) => {
    const total = data.reduce((sum, item) => sum + item.value, 0);
    
    return (
      <div className="space-y-2">
        {data.map((item, index) => {
          const percentage = (item.value / total) * 100;
          const colors = ['bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500', 'bg-purple-500'];
          
          return (
            <div key={index} className="flex items-center space-x-2 text-sm">
              <div className={`w-3 h-3 rounded-full ${colors[index % colors.length]}`} />
              <span className="flex-1">{item.category || item.date}</span>
              <span className="font-medium">{percentage.toFixed(1)}%</span>
              <span className="text-gray-500">({item.value})</span>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-6 w-6 text-legal-600" />
          <h2 className="text-xl font-semibold text-gray-900">Compliance Metrics</h2>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={loadMetricsData}
            disabled={isLoading}
            className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          
          <button className="flex items-center space-x-1 px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50">
            <Download className="h-4 w-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {Object.entries(metrics).map(([key, metric]) => {
          const status = getMetricStatus(metric);
          const isGoodTrend = !key.includes('warning') && !key.includes('time');
          
          return (
            <div
              key={key}
              className={`rounded-lg border-2 p-6 cursor-pointer transition-all hover:shadow-md ${getStatusColor(status)}`}
              onClick={() => {
                setSelectedMetric(selectedMetric === key ? null : key);
                onMetricClick?.(key);
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600 mb-1">{metric.label}</p>
                  <p className="text-3xl font-bold text-gray-900 mb-2">
                    {metric.label.includes('Rate') || metric.label.includes('Score') 
                      ? `${metric.value}%` 
                      : metric.value
                    }
                  </p>
                  
                  <div className="flex items-center space-x-2">
                    <div className={`flex items-center space-x-1 ${getTrendColor(metric.trend, isGoodTrend)}`}>
                      {getTrendIcon(metric.trend)}
                      <span className="text-sm font-medium">
                        {formatChange(metric.change)}
                      </span>
                    </div>
                    
                    {metric.target && (
                      <div className="text-xs text-gray-500">
                        Target: {metric.target}{metric.label.includes('Rate') ? '%' : ''}
                      </div>
                    )}
                  </div>
                </div>

                <div className="ml-4">
                  {status === 'good' ? (
                    <CheckCircle className="h-8 w-8 text-green-500" />
                  ) : status === 'needs-attention' ? (
                    <AlertTriangle className="h-8 w-8 text-amber-500" />
                  ) : (
                    <BarChart3 className="h-8 w-8 text-gray-400" />
                  )}
                </div>
              </div>

              {/* Mini chart for selected metric */}
              {selectedMetric === key && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="text-xs text-gray-500 mb-2">Trend ({timeRange})</div>
                  {key === 'uplWarnings' && (
                    <SimpleBarChart data={uplTrendData} />
                  )}
                  {key === 'disclaimerRate' && (
                    <SimpleBarChart data={disclaimerTrendData} />
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Detailed Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* UPL Warnings Trend */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
              UPL Warnings Trend
            </h3>
            <select className="text-sm border border-gray-300 rounded px-2 py-1">
              <option>Daily</option>
              <option>Weekly</option>
              <option>Monthly</option>
            </select>
          </div>
          
          <div className="h-32 mb-4">
            <SimpleBarChart data={uplTrendData} height={128} />
          </div>
          
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>Past {timeRange}</span>
            <span>
              Avg: {(uplTrendData.reduce((sum, d) => sum + d.value, 0) / uplTrendData.length).toFixed(1)}
            </span>
          </div>
        </div>

        {/* Jurisdiction Breakdown */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Scale className="h-5 w-5 text-legal-600 mr-2" />
              Compliance by Jurisdiction
            </h3>
            <button className="text-sm text-legal-600 hover:text-legal-800">
              View All States
            </button>
          </div>
          
          <SimplePieChart data={jurisdictionBreakdown} />
        </div>

        {/* Disclaimer Acknowledgment Rates */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
              Disclaimer Acknowledgment
            </h3>
            <div className="flex items-center space-x-2 text-sm">
              <span className="text-gray-500">Current Rate:</span>
              <span className="font-semibold text-green-600">
                {metrics.disclaimerRate?.value}%
              </span>
            </div>
          </div>
          
          <div className="h-32 mb-4">
            <SimpleBarChart data={disclaimerTrendData} height={128} />
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Target Rate</span>
              <span className="font-medium">95%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all"
                style={{ width: `${Math.min((metrics.disclaimerRate?.value || 0) / 95 * 100, 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Attorney Review Performance */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Users className="h-5 w-5 text-blue-500 mr-2" />
              Attorney Review Performance
            </h3>
            <span className="text-sm text-gray-500">
              Target: ≤4 hours
            </span>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Average Review Time</span>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-gray-900">
                  {metrics.attorneyReviews?.value}h
                </span>
                <div className="flex items-center text-green-600">
                  <TrendingDown className="h-4 w-4" />
                  <span className="text-sm">
                    {formatChange(metrics.attorneyReviews?.change || 0)}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-3 bg-green-50 rounded">
                <div className="text-lg font-semibold text-green-700">78%</div>
                <div className="text-xs text-green-600">Under 4h</div>
              </div>
              <div className="p-3 bg-amber-50 rounded">
                <div className="text-lg font-semibold text-amber-700">15%</div>
                <div className="text-xs text-amber-600">4-24h</div>
              </div>
              <div className="p-3 bg-red-50 rounded">
                <div className="text-lg font-semibold text-red-700">7%</div>
                <div className="text-xs text-red-600">Over 24h</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Assessment Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Shield className="h-5 w-5 text-purple-500 mr-2" />
            Risk Assessment Summary
          </h3>
          <div className="flex items-center space-x-2">
            <Calendar className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-500">Updated {new Date().toLocaleDateString()}</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-red-50 rounded-lg border border-red-200">
            <div className="text-2xl font-bold text-red-600">
              {Math.round((metrics.riskDetections?.value || 0) * 0.15)}
            </div>
            <div className="text-sm text-red-700">Critical Risk</div>
          </div>
          
          <div className="text-center p-4 bg-amber-50 rounded-lg border border-amber-200">
            <div className="text-2xl font-bold text-amber-600">
              {Math.round((metrics.riskDetections?.value || 0) * 0.35)}
            </div>
            <div className="text-sm text-amber-700">High Risk</div>
          </div>
          
          <div className="text-center p-4 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="text-2xl font-bold text-yellow-600">
              {Math.round((metrics.riskDetections?.value || 0) * 0.30)}
            </div>
            <div className="text-sm text-yellow-700">Medium Risk</div>
          </div>
          
          <div className="text-center p-4 bg-green-50 rounded-lg border border-green-200">
            <div className="text-2xl font-bold text-green-600">
              {Math.round((metrics.riskDetections?.value || 0) * 0.20)}
            </div>
            <div className="text-sm text-green-700">Low Risk</div>
          </div>
        </div>
      </div>

      {/* Compliance Score Card */}
      <div className="bg-legal-50 border border-legal-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-legal-900">Overall Compliance Score</h3>
          <div className="text-3xl font-bold text-legal-700">
            {metrics.sessionQuality?.value || 87}%
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <h4 className="font-semibold text-legal-900 mb-2">Strengths:</h4>
            <ul className="space-y-1 text-legal-700">
              <li>• High disclaimer acknowledgment rates</li>
              <li>• Effective UPL warning detection</li>
              <li>• Good attorney review compliance</li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold text-legal-900 mb-2">Areas for Improvement:</h4>
            <ul className="space-y-1 text-legal-700">
              <li>• Reduce high-risk AI output frequency</li>
              <li>• Improve state compliance coverage</li>
              <li>• Faster attorney review turnaround</li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold text-legal-900 mb-2">Recommendations:</h4>
            <ul className="space-y-1 text-legal-700">
              <li>• Enhanced AI training for UPL detection</li>
              <li>• Automated compliance monitoring</li>
              <li>• Regular reviewer training updates</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplianceMetrics;