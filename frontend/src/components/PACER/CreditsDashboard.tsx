'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import { API_CONFIG } from '../../config/api';
import {
  DollarSign,
  Plus,
  Download,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  CreditCard,
  FileText,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
} from 'lucide-react';
import { UserCredits, CreditTransaction, DocumentPurchase, CreditStats } from '@/types/credits';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || API_CONFIG.BASE_URL;

interface CreditsDashboardProps {
  userId: number;
  username: string;
}

export default function CreditsDashboard({ userId, username }: CreditsDashboardProps) {
  const [credits, setCredits] = useState<UserCredits | null>(null);
  const [stats, setStats] = useState<CreditStats | null>(null);
  const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
  const [purchases, setPurchases] = useState<DocumentPurchase[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddCredits, setShowAddCredits] = useState(false);
  const [addAmount, setAddAmount] = useState('100');
  const [addingCredits, setAddingCredits] = useState(false);

  // Fetch credit balance and stats
  const fetchCredits = async () => {
    try {
      const [balanceRes, statsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/credits/balance/${userId}`),
        fetch(`${API_BASE_URL}/api/v1/credits/stats/${userId}`),
      ]);

      if (balanceRes.ok) {
        const data = await balanceRes.json();
        setCredits(data);
      }

      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching credits:', error);
    }
  };

  // Fetch transaction history
  const fetchTransactions = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/credits/transactions/${userId}?limit=10`
      );
      if (response.ok) {
        const data = await response.json();
        setTransactions(data);
      }
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  };

  // Fetch purchase history
  const fetchPurchases = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/credits/purchases/${userId}?limit=10`
      );
      if (response.ok) {
        const data = await response.json();
        setPurchases(data);
      }
    } catch (error) {
      console.error('Error fetching purchases:', error);
    }
  };

  // Load all data
  const loadData = async () => {
    setLoading(true);
    await Promise.all([fetchCredits(), fetchTransactions(), fetchPurchases()]);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [userId]);

  // Handle add credits (placeholder - needs payment integration)
  const handleAddCredits = async () => {
    setAddingCredits(true);
    try {
      // TODO: Integrate with payment provider (Stripe, PayPal, etc.)
      // For now, this is a placeholder that calls the add credits endpoint
      const response = await fetch(`${API_BASE_URL}/api/v1/credits/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          username: username,
          amount: parseFloat(addAmount),
          payment_method: 'manual',
          payment_id: `manual_${Date.now()}`,
        }),
      });

      if (response.ok) {
        await loadData();
        setShowAddCredits(false);
        setAddAmount('100');
      } else {
        alert('Failed to add credits. Please try again.');
      }
    } catch (error) {
      console.error('Error adding credits:', error);
      alert('Error adding credits. Please try again.');
    } finally {
      setAddingCredits(false);
    }
  };

  // Format transaction type for display
  const formatTransactionType = (type: string): string => {
    return type
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Get status badge color and icon
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return { color: 'bg-green-100 text-green-800', icon: <CheckCircle className="h-3 w-3" /> };
      case 'processing':
        return { color: 'bg-teal-100 text-navy-700', icon: <Clock className="h-3 w-3" /> };
      case 'pending':
        return { color: 'bg-yellow-100 text-yellow-800', icon: <Clock className="h-3 w-3" /> };
      case 'failed':
        return { color: 'bg-red-100 text-red-800', icon: <XCircle className="h-3 w-3" /> };
      default:
        return { color: 'bg-gray-100 text-gray-800', icon: <AlertCircle className="h-3 w-3" /> };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-teal-600" />
        <span className="ml-2 text-gray-600">Loading credits...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Credits Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Current Balance */}
        <Card className="p-6 bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium opacity-90">Current Balance</h3>
            <DollarSign className="h-5 w-5 opacity-90" />
          </div>
          <p className="text-3xl font-bold">${credits?.balance.toFixed(2) || '0.00'}</p>
          <p className="text-xs opacity-75 mt-1">1 credit = $1.00 USD</p>
        </Card>

        {/* Total Purchased */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Total Purchased</h3>
            <TrendingUp className="h-5 w-5 text-green-600" />
          </div>
          <p className="text-3xl font-bold text-gray-900">
            ${credits?.total_purchased.toFixed(2) || '0.00'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {stats?.transaction_count || 0} transactions
          </p>
        </Card>

        {/* Total Spent */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Total Spent</h3>
            <TrendingDown className="h-5 w-5 text-orange-600" />
          </div>
          <p className="text-3xl font-bold text-gray-900">
            ${credits?.total_spent.toFixed(2) || '0.00'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {stats?.purchase_count || 0} purchases
          </p>
        </Card>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <Button
          onClick={() => setShowAddCredits(true)}
          className="bg-green-600 hover:bg-green-700 text-white"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Credits
        </Button>
        <Button onClick={loadData} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Transaction History */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Recent Transactions
          </h3>
        </div>

        {transactions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <CreditCard className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No transactions yet</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Date
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Description
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                    Amount
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                    Balance
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {transactions.map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(transaction.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {formatTransactionType(transaction.transaction_type)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {transaction.description || '-'}
                    </td>
                    <td
                      className={`px-4 py-3 text-sm text-right font-medium ${
                        transaction.amount >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {transaction.amount >= 0 ? '+' : ''}${transaction.amount.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">
                      ${transaction.balance_after.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Purchase History */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Document Purchases
          </h3>
        </div>

        {purchases.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No purchases yet</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Date
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Case
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Document
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                    Cost
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {purchases.map((purchase) => {
                  const statusBadge = getStatusBadge(purchase.status);
                  return (
                    <tr key={purchase.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {new Date(purchase.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {purchase.case_number || '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        Doc #{purchase.document_number || '-'}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusBadge.color}`}
                        >
                          {statusBadge.icon}
                          {purchase.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-medium text-gray-900">
                        ${purchase.cost_credits.toFixed(2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Add Credits Modal */}
      <Modal isOpen={showAddCredits} onClose={() => setShowAddCredits(false)}>
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-4">Add Credits</h2>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Amount (USD)
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">
                $
              </span>
              <input
                type="number"
                min="10"
                step="10"
                value={addAmount}
                onChange={(e) => setAddAmount(e.target.value)}
                className="w-full pl-8 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-teal-500"
                placeholder="100.00"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              You will receive {addAmount} credits (1 credit = $1.00)
            </p>
          </div>

          <div className="bg-teal-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-teal-600 mt-0.5" />
              <div className="text-sm text-navy-800">
                <p className="font-medium mb-1">Payment Integration Required</p>
                <p className="text-blue-700">
                  This is a placeholder. In production, integrate with Stripe, PayPal, or another
                  payment provider to process actual payments.
                </p>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <Button
              onClick={handleAddCredits}
              disabled={addingCredits || !addAmount || parseFloat(addAmount) < 10}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white"
            >
              {addingCredits ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-2" />
                  Add ${addAmount} Credits
                </>
              )}
            </Button>
            <Button onClick={() => setShowAddCredits(false)} variant="outline">
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
