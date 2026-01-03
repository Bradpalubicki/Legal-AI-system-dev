// src/services/pacer-monitor.ts
// PACER/CourtListener monitoring service for automatic case updates

import { db } from '@/lib/database';
import { SecureUnifiedSessionManager } from '@/lib/core/secure-session-manager';

interface PacerUpdate {
  newFilings: Filing[];
  statusChanges: StatusChange[];
  docketEntries: DocketEntry[];
}

interface Filing {
  id: string;
  documentNumber: string;
  documentUrl: string;
  filingDate: string;
  description: string;
  filedBy: string;
  documentType: string;
}

interface StatusChange {
  field: string;
  oldValue: string;
  newValue: string;
  changedAt: string;
}

interface DocketEntry {
  entryNumber: number;
  date: string;
  description: string;
  documentUrl?: string;
}

export class PacerMonitor {
  private sessionManager = SecureUnifiedSessionManager.getInstance();
  private intervals: Map<string, NodeJS.Timeout> = new Map();
  private isMonitoring: Map<string, boolean> = new Map();

  /**
   * Start monitoring a case for PACER updates
   */
  async startMonitoring(caseId: string, userId: string) {
    // Prevent duplicate monitoring
    if (this.isMonitoring.get(caseId)) {
      console.log(`[PACER Monitor] Already monitoring case ${caseId}`);
      return;
    }

    // Check PACER every 15 minutes
    const interval = setInterval(async () => {
      await this.checkForUpdates(caseId, userId);
    }, 15 * 60 * 1000);

    this.intervals.set(caseId, interval);
    this.isMonitoring.set(caseId, true);

    console.log(`[PACER Monitor] Started monitoring case ${caseId}`);

    // Do immediate check
    await this.checkForUpdates(caseId, userId);
  }

  /**
   * Stop monitoring a case
   */
  stopMonitoring(caseId: string) {
    const interval = this.intervals.get(caseId);
    if (interval) {
      clearInterval(interval);
      this.intervals.delete(caseId);
      this.isMonitoring.delete(caseId);
      console.log(`[PACER Monitor] Stopped monitoring case ${caseId}`);
    }
  }

  /**
   * Check for updates from PACER/CourtListener
   */
  async checkForUpdates(caseId: string, userId: string) {
    try {
      console.log(`[PACER Monitor] Checking for updates: ${caseId}`);

      // Fetch from PACER/CourtListener
      const updates = await this.fetchPacerData(caseId);

      if (updates.newFilings.length > 0) {
        console.log(`[PACER Monitor] Found ${updates.newFilings.length} new filings`);

        // Process each filing
        for (const filing of updates.newFilings) {
          await this.processFiling(caseId, userId, filing);
        }
      }

      // Handle status changes
      if (updates.statusChanges.length > 0) {
        await this.processStatusChanges(caseId, updates.statusChanges);
      }

      // Store docket entries
      if (updates.docketEntries.length > 0) {
        await this.storeDocketEntries(caseId, updates.docketEntries);
      }
    } catch (error) {
      console.error(`[PACER Monitor] Error checking updates for case ${caseId}:`, error);
    }
  }

  /**
   * Process a new filing
   */
  private async processFiling(caseId: string, userId: string, filing: Filing) {
    try {
      // Download document
      const documentText = await this.downloadDocument(filing);

      // Create session for this case
      const metadata = {
        ipAddress: 'pacer-monitor',
        userAgent: 'automated-system',
      };
      const session = await this.sessionManager.createSession(userId, caseId, metadata);

      // Analyze document using AI
      const analysis = await this.sessionManager.processDocument(
        session.sessionId,
        session.sessionToken,
        documentText,
        caseId
      );

      // Store filing in database
      await db.query(
        `INSERT INTO court_filings (
          case_id, document_number, document_url, filing_date,
          description, filed_by, document_type, analysis, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())`,
        [
          caseId,
          filing.documentNumber,
          filing.documentUrl,
          filing.filingDate,
          filing.description,
          filing.filedBy,
          filing.documentType,
          JSON.stringify(analysis),
        ]
      );

      // Check if filing requires urgent response
      if (this.isUrgentFiling(filing, analysis)) {
        await this.createAlert(caseId, userId, filing, analysis);
      }

      console.log(`[PACER Monitor] Processed filing ${filing.documentNumber} for case ${caseId}`);
    } catch (error) {
      console.error(`[PACER Monitor] Error processing filing ${filing.id}:`, error);
    }
  }

  /**
   * Fetch data from PACER/CourtListener API
   */
  private async fetchPacerData(caseId: string): Promise<PacerUpdate> {
    // Get case details from database
    const caseResult = await db.query(
      'SELECT case_number, court, last_pacer_check FROM cases WHERE id = $1',
      [caseId]
    );

    if (caseResult.rows.length === 0) {
      throw new Error(`Case ${caseId} not found`);
    }

    const caseData = caseResult.rows[0];

    // Fetch from CourtListener API
    // Note: In production, use actual CourtListener API credentials
    const response = await fetch(
      `https://www.courtlistener.com/api/rest/v3/dockets/?pacer_case_id=${caseData.case_number}`,
      {
        headers: {
          Authorization: `Token ${process.env.COURTLISTENER_API_KEY}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`CourtListener API error: ${response.statusText}`);
    }

    const data = await response.json();

    // Parse response and identify new filings
    const newFilings = this.parseFilings(data, caseData.last_pacer_check);
    const statusChanges = this.parseStatusChanges(data);
    const docketEntries = this.parseDocketEntries(data);

    // Update last check timestamp
    await db.query(
      'UPDATE cases SET last_pacer_check = NOW() WHERE id = $1',
      [caseId]
    );

    return { newFilings, statusChanges, docketEntries };
  }

  /**
   * Download document from PACER
   */
  private async downloadDocument(filing: Filing): Promise<string> {
    // In production, use PACER credentials to download actual documents
    // For now, return description as placeholder
    try {
      const response = await fetch(filing.documentUrl, {
        headers: {
          Authorization: `Bearer ${process.env.PACER_API_KEY}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to download document: ${response.statusText}`);
      }

      // Extract text from PDF or other format
      const blob = await response.blob();
      // TODO: Use PDF extraction library to get text
      // For now, return filing description
      return filing.description;
    } catch (error) {
      console.error(`[PACER Monitor] Error downloading document:`, error);
      return filing.description;
    }
  }

  /**
   * Parse filings from API response
   */
  private parseFilings(data: any, lastCheck: string): Filing[] {
    const filings: Filing[] = [];
    const lastCheckDate = new Date(lastCheck);

    if (data.results && data.results[0]?.docket_entries) {
      for (const entry of data.results[0].docket_entries) {
        const filingDate = new Date(entry.date_filed);

        if (filingDate > lastCheckDate) {
          filings.push({
            id: entry.id,
            documentNumber: entry.entry_number?.toString() || '',
            documentUrl: entry.recap_documents?.[0]?.filepath_local || '',
            filingDate: entry.date_filed,
            description: entry.description || '',
            filedBy: entry.party || 'Unknown',
            documentType: entry.recap_documents?.[0]?.document_type || 'Other',
          });
        }
      }
    }

    return filings;
  }

  /**
   * Parse status changes from API response
   */
  private parseStatusChanges(data: any): StatusChange[] {
    const changes: StatusChange[] = [];
    // Implementation depends on API structure
    // This is a placeholder
    return changes;
  }

  /**
   * Parse docket entries from API response
   */
  private parseDocketEntries(data: any): DocketEntry[] {
    const entries: DocketEntry[] = [];

    if (data.results && data.results[0]?.docket_entries) {
      for (const entry of data.results[0].docket_entries) {
        entries.push({
          entryNumber: entry.entry_number || 0,
          date: entry.date_filed,
          description: entry.description || '',
          documentUrl: entry.recap_documents?.[0]?.filepath_local,
        });
      }
    }

    return entries;
  }

  /**
   * Process status changes
   */
  private async processStatusChanges(caseId: string, changes: StatusChange[]) {
    for (const change of changes) {
      await db.query(
        `INSERT INTO case_status_history (
          case_id, field, old_value, new_value, changed_at
        ) VALUES ($1, $2, $3, $4, $5)`,
        [caseId, change.field, change.oldValue, change.newValue, change.changedAt]
      );
    }
  }

  /**
   * Store docket entries
   */
  private async storeDocketEntries(caseId: string, entries: DocketEntry[]) {
    for (const entry of entries) {
      await db.query(
        `INSERT INTO docket_entries (
          case_id, entry_number, date, description, document_url, created_at
        ) VALUES ($1, $2, $3, $4, $5, NOW())
        ON CONFLICT (case_id, entry_number) DO NOTHING`,
        [caseId, entry.entryNumber, entry.date, entry.description, entry.documentUrl]
      );
    }
  }

  /**
   * Determine if filing requires urgent attention
   */
  private isUrgentFiling(filing: Filing, analysis: any): boolean {
    const urgentKeywords = [
      'motion to dismiss',
      'summary judgment',
      'default judgment',
      'contempt',
      'sanctions',
      'emergency',
      'expedited',
      'ex parte',
    ];

    const description = filing.description.toLowerCase();
    return urgentKeywords.some(keyword => description.includes(keyword));
  }

  /**
   * Create alert for urgent filing
   */
  private async createAlert(caseId: string, userId: string, filing: Filing, analysis: any) {
    await db.query(
      `INSERT INTO alerts (
        user_id, case_id, alert_type, title, message,
        severity, document_id, created_at, is_read
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), false)`,
      [
        userId,
        caseId,
        'urgent_filing',
        `Urgent Filing: ${filing.description}`,
        `A new urgent filing has been detected in your case. Document #${filing.documentNumber} requires immediate attention.`,
        'high',
        filing.id,
      ]
    );

    console.log(`[PACER Monitor] Created alert for urgent filing ${filing.documentNumber}`);
  }

  /**
   * Stop all monitoring
   */
  stopAll() {
    this.intervals.forEach((interval, caseId) => {
      clearInterval(interval);
      console.log(`[PACER Monitor] Stopped monitoring case ${caseId}`);
    });
    this.intervals.clear();
    this.isMonitoring.clear();
  }
}

// Export singleton instance
export const pacerMonitor = new PacerMonitor();
