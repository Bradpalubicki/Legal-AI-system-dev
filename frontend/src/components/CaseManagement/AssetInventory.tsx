/**
 * Asset Inventory Component
 * Tracks all assets with categories, inclusion/exclusion status, liens, and contracts
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Asset, AssetStatus, CreateAssetRequest } from '@/types/case-management';
import { caseManagementAPI } from '@/lib/api/case-management-api';

interface AssetInventoryProps {
  caseId: string;
}

export default function AssetInventory({ caseId }: AssetInventoryProps) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [filteredAssets, setFilteredAssets] = useState<Asset[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<AssetStatus | 'all'>('all');
  const [filterCategory, setFilterCategory] = useState<string>('all');

  useEffect(() => {
    loadAssets();
  }, [caseId]);

  useEffect(() => {
    let filtered = [...assets];

    if (filterStatus !== 'all') {
      filtered = filtered.filter((a) => a.status === filterStatus);
    }

    if (filterCategory !== 'all') {
      filtered = filtered.filter((a) => a.category === filterCategory);
    }

    setFilteredAssets(filtered);
  }, [filterStatus, filterCategory, assets]);

  const loadAssets = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await caseManagementAPI.assets.list(caseId);
      setAssets(data);
      setFilteredAssets(data);
      setLoading(false);
    } catch (err) {
      console.error('Error loading assets:', err);
      setError(err instanceof Error ? err.message : 'Failed to load assets');
      setLoading(false);
    }
  };

  const getStatusColor = (status: AssetStatus): string => {
    const colors = {
      included: 'bg-green-100 text-green-800 border-green-300',
      excluded: 'bg-red-100 text-red-800 border-red-300',
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      sold: 'bg-blue-100 text-blue-800 border-blue-300',
      abandoned: 'bg-gray-100 text-gray-800 border-gray-300',
      exempt: 'bg-purple-100 text-purple-800 border-purple-300',
    };
    return colors[status] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getAssetTypeIcon = (type: string): string => {
    const icons: Record<string, string> = {
      real_estate: '🏠',
      vehicle: '🚗',
      account: '💰',
      equipment: '🔧',
      inventory: '📦',
      intellectual_property: '💡',
      investment: '📈',
      other: '📄',
    };
    return icons[type] || '📄';
  };

  const getTotalValue = (): number => {
    return filteredAssets.reduce((sum, asset) => sum + (asset.estimated_value || 0), 0);
  };

  const getCategories = (): string[] => {
    const categories = new Set(assets.map((a) => a.category).filter(Boolean) as string[]);
    return Array.from(categories);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
        <button
          onClick={loadAssets}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Summary */}
      <Card className="p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Asset Inventory</h1>
            <p className="text-gray-600 mt-1">
              {filteredAssets.length} assets • Total Value: ${getTotalValue().toLocaleString()}
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            {/* Category Filter */}
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Categories</option>
              {getCategories().map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>

            {/* Status Filter */}
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as AssetStatus | 'all')}
              className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value={AssetStatus.INCLUDED}>Included</option>
              <option value={AssetStatus.EXCLUDED}>Excluded</option>
              <option value={AssetStatus.PENDING}>Pending</option>
              <option value={AssetStatus.SOLD}>Sold</option>
              <option value={AssetStatus.ABANDONED}>Abandoned</option>
              <option value={AssetStatus.EXEMPT}>Exempt</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 bg-green-50 border-green-200">
          <p className="text-sm text-green-600 font-medium">Included</p>
          <p className="text-2xl font-bold text-green-900">
            {assets.filter((a) => a.status === AssetStatus.INCLUDED).length}
          </p>
        </Card>
        <Card className="p-4 bg-yellow-50 border-yellow-200">
          <p className="text-sm text-yellow-600 font-medium">Pending</p>
          <p className="text-2xl font-bold text-yellow-900">
            {assets.filter((a) => a.status === AssetStatus.PENDING).length}
          </p>
        </Card>
        <Card className="p-4 bg-blue-50 border-blue-200">
          <p className="text-sm text-blue-600 font-medium">Sold</p>
          <p className="text-2xl font-bold text-blue-900">
            {assets.filter((a) => a.status === AssetStatus.SOLD).length}
          </p>
        </Card>
        <Card className="p-4 bg-red-50 border-red-200">
          <p className="text-sm text-red-600 font-medium">Excluded</p>
          <p className="text-2xl font-bold text-red-900">
            {assets.filter((a) => a.status === AssetStatus.EXCLUDED).length}
          </p>
        </Card>
      </div>

      {/* Asset Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredAssets.map((asset) => (
          <Card
            key={asset.id}
            onClick={() => setSelectedAsset(asset)}
            className="p-6 cursor-pointer hover:shadow-lg transition-shadow"
          >
            {/* Asset Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <span className="text-3xl">{getAssetTypeIcon(asset.asset_type)}</span>
                <div>
                  <h3 className="font-bold text-gray-900">{asset.name}</h3>
                  <p className="text-sm text-gray-600">{asset.asset_type.replace('_', ' ')}</p>
                </div>
              </div>
              <span className={`px-3 py-1 rounded border text-xs font-medium ${getStatusColor(asset.status)}`}>
                {asset.status.toUpperCase()}
              </span>
            </div>

            {/* Valuation */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-xs text-gray-600">Estimated Value</p>
                <p className="text-lg font-bold text-gray-900">
                  {asset.estimated_value ? `$${asset.estimated_value.toLocaleString()}` : 'TBD'}
                </p>
              </div>
              {asset.appraised_value && (
                <div>
                  <p className="text-xs text-gray-600">Appraised Value</p>
                  <p className="text-lg font-bold text-gray-900">
                    ${asset.appraised_value.toLocaleString()}
                  </p>
                </div>
              )}
            </div>

            {/* Key Details */}
            <div className="space-y-2 text-sm">
              {asset.category && (
                <div className="flex items-center text-gray-600">
                  <span className="mr-2">📁</span>
                  <span>Category: {asset.category}</span>
                </div>
              )}
              {asset.location && (
                <div className="flex items-center text-gray-600">
                  <span className="mr-2">📍</span>
                  <span className="truncate">{asset.location}</span>
                </div>
              )}
              {asset.has_liens && (
                <div className="flex items-center text-red-600">
                  <span className="mr-2">⚠️</span>
                  <span>
                    Liens: ${asset.lien_amount?.toLocaleString() || 'Unknown'}
                  </span>
                </div>
              )}
              {asset.has_contracts && (
                <div className="flex items-center text-blue-600">
                  <span className="mr-2">📋</span>
                  <span>Has associated contracts</span>
                </div>
              )}
            </div>

            {/* Bidding Info */}
            {asset.minimum_bid && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-600">Minimum Bid</p>
                    <p className="text-sm font-bold text-gray-900">
                      ${asset.minimum_bid.toLocaleString()}
                    </p>
                  </div>
                  {asset.current_high_bid && (
                    <div>
                      <p className="text-xs text-gray-600">Current Bid</p>
                      <p className="text-sm font-bold text-green-600">
                        ${asset.current_high_bid.toLocaleString()}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedAsset(asset);
              }}
              className="mt-4 w-full py-2 text-blue-600 hover:text-blue-700 font-medium text-sm"
            >
              View Full Details →
            </button>
          </Card>
        ))}
      </div>

      {filteredAssets.length === 0 && (
        <Card className="p-12 text-center">
          <p className="text-gray-500 text-lg">No assets match the current filters</p>
          <button
            onClick={() => {
              setFilterStatus('all');
              setFilterCategory('all');
            }}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Clear Filters
          </button>
        </Card>
      )}

      {/* Asset Detail Modal */}
      {selectedAsset && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedAsset(null)}
        >
          <Card
            className="max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-6">
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="text-4xl">{getAssetTypeIcon(selectedAsset.asset_type)}</span>
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">{selectedAsset.name}</h2>
                      <p className="text-gray-600 capitalize">
                        {selectedAsset.asset_type.replace('_', ' ')}
                      </p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded border text-sm font-medium ${getStatusColor(selectedAsset.status)}`}>
                    {selectedAsset.status.toUpperCase()}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedAsset(null)}
                  className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
                >
                  ×
                </button>
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Basic Information */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Basic Information</h3>
                  <div className="space-y-3 text-sm">
                    {selectedAsset.description && (
                      <div>
                        <p className="text-gray-600 font-medium">Description</p>
                        <p className="text-gray-900">{selectedAsset.description}</p>
                      </div>
                    )}
                    {selectedAsset.category && (
                      <div>
                        <p className="text-gray-600 font-medium">Category</p>
                        <p className="text-gray-900">{selectedAsset.category}</p>
                      </div>
                    )}
                    {selectedAsset.location && (
                      <div>
                        <p className="text-gray-600 font-medium">Location</p>
                        <p className="text-gray-900">{selectedAsset.location}</p>
                      </div>
                    )}
                    {selectedAsset.identification_number && (
                      <div>
                        <p className="text-gray-600 font-medium">ID Number</p>
                        <p className="text-gray-900">{selectedAsset.identification_number}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Valuation */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Valuation</h3>
                  <div className="space-y-3 text-sm">
                    {selectedAsset.estimated_value && (
                      <div>
                        <p className="text-gray-600 font-medium">Estimated Value</p>
                        <p className="text-gray-900 text-xl font-bold">
                          ${selectedAsset.estimated_value.toLocaleString()}
                        </p>
                      </div>
                    )}
                    {selectedAsset.appraised_value && (
                      <div>
                        <p className="text-gray-600 font-medium">Appraised Value</p>
                        <p className="text-gray-900 text-xl font-bold">
                          ${selectedAsset.appraised_value.toLocaleString()}
                        </p>
                      </div>
                    )}
                    {selectedAsset.market_value && (
                      <div>
                        <p className="text-gray-600 font-medium">Market Value</p>
                        <p className="text-gray-900 text-xl font-bold">
                          ${selectedAsset.market_value.toLocaleString()}
                        </p>
                      </div>
                    )}
                    {selectedAsset.valuation_date && (
                      <div>
                        <p className="text-gray-600 font-medium">Valuation Date</p>
                        <p className="text-gray-900">
                          {new Date(selectedAsset.valuation_date).toLocaleDateString()}
                        </p>
                      </div>
                    )}
                    {selectedAsset.valuation_method && (
                      <div>
                        <p className="text-gray-600 font-medium">Valuation Method</p>
                        <p className="text-gray-900">{selectedAsset.valuation_method}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Liens & Encumbrances */}
                {selectedAsset.has_liens && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Liens & Encumbrances
                    </h3>
                    <div className="space-y-3 text-sm">
                      {selectedAsset.lien_amount && (
                        <div>
                          <p className="text-gray-600 font-medium">Total Lien Amount</p>
                          <p className="text-red-600 text-xl font-bold">
                            ${selectedAsset.lien_amount.toLocaleString()}
                          </p>
                        </div>
                      )}
                      {selectedAsset.lien_holders && selectedAsset.lien_holders.length > 0 && (
                        <div>
                          <p className="text-gray-600 font-medium mb-2">Lien Holders</p>
                          <div className="space-y-1">
                            {selectedAsset.lien_holders.map((holder, idx) => (
                              <div key={idx} className="p-2 bg-gray-50 rounded">
                                {typeof holder === 'string' ? holder : JSON.stringify(holder)}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {selectedAsset.encumbrances && selectedAsset.encumbrances.length > 0 && (
                        <div>
                          <p className="text-gray-600 font-medium mb-2">Encumbrances</p>
                          <div className="space-y-1">
                            {selectedAsset.encumbrances.map((enc, idx) => (
                              <div key={idx} className="p-2 bg-gray-50 rounded">
                                {typeof enc === 'string' ? enc : JSON.stringify(enc)}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Associated Contracts */}
                {selectedAsset.has_contracts && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Associated Contracts
                    </h3>
                    <div className="space-y-3 text-sm">
                      {selectedAsset.contract_details && selectedAsset.contract_details.length > 0 && (
                        <div>
                          <p className="text-gray-600 font-medium mb-2">Contract Details</p>
                          <div className="space-y-1">
                            {selectedAsset.contract_details.map((contract, idx) => (
                              <div key={idx} className="p-2 bg-blue-50 rounded">
                                {typeof contract === 'string' ? contract : JSON.stringify(contract)}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {selectedAsset.ongoing_obligations && selectedAsset.ongoing_obligations.length > 0 && (
                        <div>
                          <p className="text-gray-600 font-medium mb-2">Ongoing Obligations</p>
                          <div className="space-y-1">
                            {selectedAsset.ongoing_obligations.map((obligation, idx) => (
                              <div key={idx} className="p-2 bg-yellow-50 rounded">
                                {typeof obligation === 'string' ? obligation : JSON.stringify(obligation)}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Inclusion/Exclusion Status */}
                <div className="md:col-span-2">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Inclusion/Exclusion Status
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600 font-medium">Current Status</p>
                      <span className={`inline-block px-3 py-1 rounded border text-sm font-medium mt-1 ${getStatusColor(selectedAsset.status)}`}>
                        {selectedAsset.status.toUpperCase()}
                      </span>
                    </div>
                    {selectedAsset.inclusion_reason && (
                      <div>
                        <p className="text-gray-600 font-medium">Inclusion Reason</p>
                        <p className="text-gray-900 mt-1">{selectedAsset.inclusion_reason}</p>
                      </div>
                    )}
                    {selectedAsset.exclusion_reason && (
                      <div>
                        <p className="text-gray-600 font-medium">Exclusion Reason</p>
                        <p className="text-gray-900 mt-1">{selectedAsset.exclusion_reason}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Bidding Information */}
                {(selectedAsset.minimum_bid || selectedAsset.current_high_bid || selectedAsset.reserve_price) && (
                  <div className="md:col-span-2">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Bidding Information</h3>
                    <div className="grid grid-cols-3 gap-4">
                      {selectedAsset.minimum_bid && (
                        <div>
                          <p className="text-gray-600 font-medium text-sm">Minimum Bid</p>
                          <p className="text-gray-900 text-lg font-bold">
                            ${selectedAsset.minimum_bid.toLocaleString()}
                          </p>
                        </div>
                      )}
                      {selectedAsset.current_high_bid && (
                        <div>
                          <p className="text-gray-600 font-medium text-sm">Current High Bid</p>
                          <p className="text-green-600 text-lg font-bold">
                            ${selectedAsset.current_high_bid.toLocaleString()}
                          </p>
                        </div>
                      )}
                      {selectedAsset.reserve_price && (
                        <div>
                          <p className="text-gray-600 font-medium text-sm">Reserve Price</p>
                          <p className="text-blue-600 text-lg font-bold">
                            ${selectedAsset.reserve_price.toLocaleString()}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Notes */}
              {selectedAsset.notes && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Notes</h3>
                  <p className="text-sm text-gray-900">{selectedAsset.notes}</p>
                </div>
              )}

              {/* Close Button */}
              <button
                onClick={() => setSelectedAsset(null)}
                className="mt-6 w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                Close
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
