// Frontend database client
// Connects to PostgreSQL database via connection pool

import { Pool, QueryResult } from 'pg';

class DatabaseClient {
  private pool: Pool;

  constructor() {
    this.pool = new Pool({
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT || '5432'),
      database: process.env.DB_NAME || 'legal_ai',
      user: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD,
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });
  }

  async query(text: string, params?: any[]): Promise<QueryResult> {
    const start = Date.now();
    try {
      const result = await this.pool.query(text, params);
      const duration = Date.now() - start;
      console.log('[DB] Query executed', { text, duration, rows: result.rowCount });
      return result;
    } catch (error) {
      console.error('[DB] Query error', { text, error });
      throw error;
    }
  }

  async getClient() {
    return await this.pool.connect();
  }

  async end() {
    await this.pool.end();
  }
}

export const db = new DatabaseClient();
