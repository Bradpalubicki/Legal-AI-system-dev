/**
 * Transaction Details Component
 * Shows financial transactions with bidding history, approvals, and associated documents
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { FinancialTransaction, BiddingProcess } from '@/types/case-management';
import { caseManagementAPI } from '@/lib/api/case-management-api';

interface TransactionDetailsProps {
  caseId: string;
}

export default function TransactionDetails({ caseId }: TransactionDetailsProps) {
  const [transactions, setTransactions] = useState<FinancialTransaction[]>([]);
  const [biddingProcesses, setBiddingProcesses] = useState<BiddingProcess[]>([]);
  const [selectedTransaction, setSelectedTransaction] = useState<FinancialTransaction | null>(null);
  const [selectedBidding, setSelectedBidding] = useState<BiddingProcess | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'transactions' | 'bidding'>('transactions');

  useEffect(() => {
    loadData();
  }, [caseId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [transactionsData, biddingData] = await Promise.all([
        caseManagementAPI.transactions.list(caseId),
        caseManagementAPI.bidding.list(caseId),
      ]);

      setTransactions(transactionsData);
      setBiddingProcesses(biddingData);
      setLoading(false);
    } catch (err) {
      console.error('Error loading transaction data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load transaction data');
      setLoading(false);
    }
  };

  const getTransactionTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      payment: 'bg-green-100 text-green-800',
      distribution: 'bg-blue-100 text-blue-800',
      fee: 'bg-yellow-100 text-yellow-800',
      deposit: 'bg-purple-100 text-purple-800',
      refund: 'bg-red-100 text-red-800',
      bid: 'bg-pink-100 text-pink-800',
      transfer: 'bg-indigo-100 text-indigo-800',
      escrow: 'bg-teal-100 text-teal-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const getApprovalStatusColor = (status?: string): string => {
    if (!status) return 'bg-gray-100 text-gray-800';
    const colors: Record<string, string> = {
      approved: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      denied: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getTotalTransactionAmount = (): number => {
    return transactions.reduce((sum, t) => sum + t.amount, 0);
  };

  const getTotalBiddingAmount = (): number => {
    return biddingProcesses.reduce((sum, b) => sum + (b.highest_bid_amount || 0), 0);
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
          onClick={loadData}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Transaction Details</h1>
            <p className="text-gray-600 mt-1">
              Financial transactions and bidding activity
            </p>
          </div>

          {/* Tab Selector */}
          <div className="flex space-x-2 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab('transactions')}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                activeTab === 'transactions'
                  ? 'bg-white text-blue-600 shadow'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Transactions ({transactions.length})
            </button>
            <button
              onClick={() => setActiveTab('bidding')}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                activeTab === 'bidding'
                  ? 'bg-white text-blue-600 shadow'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Bidding ({biddingProcesses.length})
            </button>
          </div>
        </div>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6 bg-gradient-to-br from-green-50 to-green-100">
          <p className="text-sm text-green-600 font-medium">Total Transactions</p>
          <p className="text-3xl font-bold text-green-900">
            ${getTotalTransactionAmount().toLocaleString()}
          </p>
          <p className="text-sm text-green-700 mt-1">{transactions.length} transactions</p>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-blue-50 to-blue-100">
          <p className="text-sm text-blue-600 font-medium">Total Bidding</p>
          <p className="text-3xl font-bold text-blue-900">
            ${getTotalBiddingAmount().toLocaleString()}
          </p>
          <p className="text-sm text-blue-700 mt-1">{biddingProcesses.length} processes</p>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-purple-50 to-purple-100">
          <p className="text-sm text-purple-600 font-medium">Pending Approvals</p>
          <p className="text-3xl font-bold text-purple-900">
            {transactions.filter((t) => t.approval_status === 'pending').length}
          </p>
          <p className="text-sm text-purple-700 mt-1">Require action</p>
        </Card>
      </div>

      {/* Transactions Tab */}
      {activeTab === 'transactions' && (
        <div className="space-y-4">
          {transactions.map((transaction) => (
            <Card
              key={transaction.id}
              onClick={() => setSelectedTransaction(transaction)}
              className="p-6 cursor-pointer hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between">
                {/* Transaction Info */}
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span
                      className={`px-3 py-1 rounded text-xs font-medium ${getTransactionTypeColor(
                        transaction.transaction_type
                      )}`}
                    >
                      {transaction.transaction_type.toUpperCase()}
                    </span>
                    {transaction.requires_approval && (
                      <span
                        className={`px-3 py-1 rounded text-xs font-medium ${getApprovalStatusColor(
                          transaction.approval_status
                        )}`}
                      >
                        {transaction.approval_status || 'PENDING'} APPROVAL
                      </span>
                    )}
                  </div>

                  <h3 className="font-semibold text-gray-900 text-lg">
                    {transaction.description || `${transaction.transaction_type} Transaction`}
                  </h3>

                  <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Date</p>
                      <p className="text-gray-900 font-medium">
                        {new Date(transaction.transaction_date).toLocaleDateString()}
                      </p>
                    </div>
                    {transaction.category && (
                      <div>
                        <p className="text-gray-600">Category</p>
                        <p className="text-gray-900 font-medium capitalize">{transaction.category}</p>
                      </div>
                    )}
                    {transaction.payment_method && (
                      <div>
                        <p className="text-gray-600">Payment Method</p>
                        <p className="text-gray-900 font-medium capitalize">
                          {transaction.payment_method}
                        </p>
                      </div>
                    )}
                    {transaction.payment_status && (
                      <div>
                        <p className="text-gray-600">Payment Status</p>
                        <p className="text-gray-900 font-medium capitalize">
                          {transaction.payment_status}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Amount */}
                <div className="text-right ml-4">
                  <p className="text-3xl font-bold text-gray-900">
                    ${transaction.amount.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600">{transaction.currency || 'USD'}</p>
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedTransaction(transaction);
                }}
                className="mt-4 text-blue-600 hover:text-blue-700 font-medium text-sm"
              >
                View Full Details →
              </button>
            </Card>
          ))}

          {transactions.length === 0 && (
            <Card className="p-12 text-center">
              <p className="text-gray-500 text-lg">No transactions found</p>
            </Card>
          )}
        </div>
      )}

      {/* Bidding Tab */}
      {activeTab === 'bidding' && (
        <div className="space-y-4">
          {biddingProcesses.map((bidding) => (
            <Card
              key={bidding.id}
              onClick={() => setSelectedBidding(bidding)}
              className="p-6 cursor-pointer hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between">
                {/* Bidding Info */}
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span
                      className={`px-3 py-1 rounded text-xs font-medium ${
                        bidding.status === 'open'
                          ? 'bg-green-100 text-green-800'
                          : bidding.status === 'closed'
                          ? 'bg-gray-100 text-gray-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {bidding.status?.toUpperCase() || 'OPEN'}
                    </span>
                    {bidding.sale_approved && (
                      <span className="px-3 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                        SALE APPROVED
                      </span>
                    )}
                  </div>

                  <h3 className="font-semibold text-gray-900 text-lg">
                    {bidding.process_name || `Bidding Process for Asset ${bidding.asset_id}`}
                  </h3>

                  <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Start Date</p>
                      <p className="text-gray-900 font-medium">
                        {new Date(bidding.bidding_start_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600">End Date</p>
                      <p className="text-gray-900 font-medium">
                        {new Date(bidding.bidding_end_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600">Minimum Bid</p>
                      <p className="text-gray-900 font-medium">
                        ${bidding.minimum_bid?.toLocaleString() || 'TBD'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600">Total Bids</p>
                      <p className="text-gray-900 font-medium">{bidding.bids?.length || 0}</p>
                    </div>
                  </div>

                  {/* Bidding History */}
                  {bidding.bids && bidding.bids.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <p className="text-sm font-medium text-gray-700 mb-2">Recent Bids:</p>
                      <div className="space-y-1">
                        {bidding.bids.slice(-3).reverse().map((bid, idx) => (
                          <div key={idx} className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">
                              {new Date(bid.timestamp).toLocaleString()}
                            </span>
                            <span className="font-bold text-green-600">
                              ${bid.amount.toLocaleString()}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Current Terms (Highest Bid) */}
                <div className="text-right ml-4">
                  <p className="text-sm text-gray-600">Current High Bid</p>
                  <p className="text-3xl font-bold text-green-600">
                    ${bidding.highest_bid_amount?.toLocaleString() || '0'}
                  </p>
                  {bidding.reserve_price && (
                    <p className="text-sm text-gray-600 mt-1">
                      Reserve: ${bidding.reserve_price.toLocaleString()}
                    </p>
                  )}
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedBidding(bidding);
                }}
                className="mt-4 text-blue-600 hover:text-blue-700 font-medium text-sm"
              >
                View Bidding History →
              </button>
            </Card>
          ))}

          {biddingProcesses.length === 0 && (
            <Card className="p-12 text-center">
              <p className="text-gray-500 text-lg">No bidding processes found</p>
            </Card>
          )}
        </div>
      )}

      {/* Transaction Detail Modal */}
      {selectedTransaction && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedTransaction(null)}
        >
          <Card
            className="max-w-3xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Transaction Details</h2>
                  <p className="text-gray-600 mt-1">
                    {selectedTransaction.description || 'Transaction Record'}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedTransaction(null)}
                  className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
                >
                  ×
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Basic Information</h3>
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="text-gray-600 font-medium">Amount</p>
                      <p className="text-gray-900 text-2xl font-bold">
                        ${selectedTransaction.amount.toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600 font-medium">Transaction Type</p>
                      <p className="text-gray-900 capitalize">{selectedTransaction.transaction_type}</p>
                    </div>
                    <div>
                      <p className="text-gray-600 font-medium">Transaction Date</p>
                      <p className="text-gray-900">
                        {new Date(selectedTransaction.transaction_date).toLocaleString()}
                      </p>
                    </div>
                    {selectedTransaction.reference_number && (
                      <div>
                        <p className="text-gray-600 font-medium">Reference Number</p>
                        <p className="text-gray-900">{selectedTransaction.reference_number}</p>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Approval Status</h3>
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="text-gray-600 font-medium">Requires Approval</p>
                      <p className="text-gray-900">
                        {selectedTransaction.requires_approval ? 'Yes' : 'No'}
                      </p>
                    </div>
                    {selectedTransaction.approval_status && (
                      <div>
                        <p className="text-gray-600 font-medium">Status</p>
                        <span
                          className={`inline-block px-3 py-1 rounded text-sm font-medium ${getApprovalStatusColor(
                            selectedTransaction.approval_status
                          )}`}
                        >
                          {selectedTransaction.approval_status.toUpperCase()}
                        </span>
                      </div>
                    )}
                    {selectedTransaction.approval_date && (
                      <div>
                        <p className="text-gray-600 font-medium">Approval Date</p>
                        <p className="text-gray-900">
                          {new Date(selectedTransaction.approval_date).toLocaleDateString()}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {selectedTransaction.payment_method && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Payment Details</h3>
                    <div className="space-y-3 text-sm">
                      <div>
                        <p className="text-gray-600 font-medium">Payment Method</p>
                        <p className="text-gray-900 capitalize">{selectedTransaction.payment_method}</p>
                      </div>
                      {selectedTransaction.payment_status && (
                        <div>
                          <p className="text-gray-600 font-medium">Payment Status</p>
                          <p className="text-gray-900 capitalize">{selectedTransaction.payment_status}</p>
                        </div>
                      )}
                      {selectedTransaction.check_number && (
                        <div>
                          <p className="text-gray-600 font-medium">Check Number</p>
                          <p className="text-gray-900">{selectedTransaction.check_number}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {selectedTransaction.notes && (
                  <div className="md:col-span-2">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Associated Documents & Notes</h3>
                    <p className="text-sm text-gray-900">{selectedTransaction.notes}</p>
                  </div>
                )}
              </div>

              <button
                onClick={() => setSelectedTransaction(null)}
                className="mt-6 w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                Close
              </button>
            </div>
          </Card>
        </div>
      )}

      {/* Bidding Detail Modal */}
      {selectedBidding && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedBidding(null)}
        >
          <Card
            className="max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {selectedBidding.process_name || 'Bidding Process'}
                  </h2>
                  <p className="text-gray-600 mt-1">Asset ID: {selectedBidding.asset_id}</p>
                </div>
                <button
                  onClick={() => setSelectedBidding(null)}
                  className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
                >
                  ×
                </button>
              </div>

              <div className="space-y-6">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Minimum Bid</p>
                    <p className="text-xl font-bold text-gray-900">
                      ${selectedBidding.minimum_bid?.toLocaleString() || 'TBD'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Current High Bid</p>
                    <p className="text-xl font-bold text-green-600">
                      ${selectedBidding.highest_bid_amount?.toLocaleString() || '0'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Total Bids</p>
                    <p className="text-xl font-bold text-blue-600">{selectedBidding.bids?.length || 0}</p>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Bidding History</h3>
                  <div className="space-y-2">
                    {selectedBidding.bids && selectedBidding.bids.length > 0 ? (
                      selectedBidding.bids.map((bid, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                        >
                          <div>
                            <p className="font-medium text-gray-900">Bid #{selectedBidding.bids!.length - idx}</p>
                            <p className="text-sm text-gray-600">
                              {new Date(bid.timestamp).toLocaleString()}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-xl font-bold text-green-600">
                              ${bid.amount.toLocaleString()}
                            </p>
                            {idx === selectedBidding.bids!.length - 1 && (
                              <span className="text-xs text-green-600 font-medium">HIGHEST BID</span>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-gray-500 text-center py-4">No bids yet</p>
                    )}
                  </div>
                </div>

                {selectedBidding.approved_bidders && selectedBidding.approved_bidders.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Required Approvals</h3>
                    <p className="text-sm text-gray-600">
                      {selectedBidding.approved_bidders.length} bidders approved
                    </p>
                  </div>
                )}
              </div>

              <button
                onClick={() => setSelectedBidding(null)}
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
