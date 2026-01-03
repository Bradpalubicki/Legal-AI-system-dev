/**
 * Export utilities for case data (CSV format)
 */

import { CaseParty, TimelineEvent, FinancialTransaction } from './api/cases';

/**
 * Convert array of objects to CSV string
 */
function arrayToCSV(data: any[], headers: string[]): string {
  const headerRow = headers.join(',');
  const dataRows = data.map(row => {
    return headers.map(header => {
      const value = row[header];
      // Escape commas and quotes in CSV
      if (value === null || value === undefined) return '';
      const stringValue = String(value);
      if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
        return `"${stringValue.replace(/"/g, '""')}"`;
      }
      return stringValue;
    }).join(',');
  });

  return [headerRow, ...dataRows].join('\n');
}

/**
 * Download CSV file
 */
function downloadCSV(filename: string, csvContent: string): void {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Export parties to CSV
 */
export function exportPartiesToCSV(parties: CaseParty[], caseName: string): void {
  const headers = ['name', 'legal_name', 'role', 'email', 'phone', 'address', 'represented_by', 'notes'];
  const csvContent = arrayToCSV(parties, headers);
  const filename = `${caseName.replace(/[^a-z0-9]/gi, '_')}_parties_${new Date().toISOString().split('T')[0]}.csv`;
  downloadCSV(filename, csvContent);
}

/**
 * Export timeline events to CSV
 */
export function exportTimelineToCSV(events: TimelineEvent[], caseName: string): void {
  const headers = ['title', 'event_type', 'event_date', 'status', 'location', 'description', 'outcome', 'is_critical_path'];

  // Format dates for better readability
  const formattedEvents = events.map(event => ({
    ...event,
    event_date: new Date(event.event_date).toLocaleString(),
    is_critical_path: event.is_critical_path ? 'Yes' : 'No'
  }));

  const csvContent = arrayToCSV(formattedEvents, headers);
  const filename = `${caseName.replace(/[^a-z0-9]/gi, '_')}_timeline_${new Date().toISOString().split('T')[0]}.csv`;
  downloadCSV(filename, csvContent);
}

/**
 * Export transactions to CSV
 */
export function exportTransactionsToCSV(transactions: FinancialTransaction[], caseName: string): void {
  const headers = ['transaction_date', 'transaction_type', 'amount', 'currency', 'description', 'payment_status', 'approval_status'];

  // Format dates and amounts for better readability
  const formattedTransactions = transactions.map(transaction => ({
    ...transaction,
    transaction_date: new Date(transaction.transaction_date).toLocaleDateString(),
    amount: `${transaction.currency} ${transaction.amount.toLocaleString()}`
  }));

  const csvContent = arrayToCSV(formattedTransactions, headers);
  const filename = `${caseName.replace(/[^a-z0-9]/gi, '_')}_transactions_${new Date().toISOString().split('T')[0]}.csv`;
  downloadCSV(filename, csvContent);
}

/**
 * Export all case data to CSV (combines all tabs)
 */
export function exportAllCaseData(
  parties: CaseParty[],
  events: TimelineEvent[],
  transactions: FinancialTransaction[],
  caseName: string
): void {
  exportPartiesToCSV(parties, caseName);
  setTimeout(() => exportTimelineToCSV(events, caseName), 100);
  setTimeout(() => exportTransactionsToCSV(transactions, caseName), 200);
}
