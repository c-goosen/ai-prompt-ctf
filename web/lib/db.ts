import "server-only";

import { databaseUrl, sqlitePath } from "./config";

/**
 * Leaderboard/identity storage shared with the Python agent
 * (ctf/leaderboard.py writes completions from submit_answer_func).
 *
 * Two drivers behind one tiny interface:
 * - Postgres (postgres.js) when POSTGRES_DB_URI is set: Docker and Workers.
 * - node:sqlite otherwise: local Node dev, on the same file as the agent.
 *
 * SQL is written with $1-style placeholders; the SQLite driver rewrites them.
 */
export interface Db {
  readonly dialect: "postgres" | "sqlite";
  query<T = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<T[]>;
  close(): Promise<void>;
}

// Same tables as the SQLAlchemy models, so either side can create them first.
const SCHEMA: Record<Db["dialect"], string[]> = {
  postgres: [
    `CREATE TABLE IF NOT EXISTS leaderboard_entries (
       username VARCHAR NOT NULL,
       level INTEGER NOT NULL,
       completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
       PRIMARY KEY (username, level))`,
    `CREATE INDEX IF NOT EXISTS ix_leaderboard_entries_completed_at
       ON leaderboard_entries (completed_at)`,
    `CREATE TABLE IF NOT EXISTS player_identities (
       username VARCHAR NOT NULL PRIMARY KEY,
       token_hash VARCHAR NOT NULL,
       created_at TIMESTAMP WITH TIME ZONE NOT NULL)`,
  ],
  sqlite: [
    `CREATE TABLE IF NOT EXISTS leaderboard_entries (
       username VARCHAR NOT NULL,
       level INTEGER NOT NULL,
       completed_at DATETIME NOT NULL,
       PRIMARY KEY (username, level))`,
    `CREATE INDEX IF NOT EXISTS ix_leaderboard_entries_completed_at
       ON leaderboard_entries (completed_at)`,
    `CREATE TABLE IF NOT EXISTS player_identities (
       username VARCHAR NOT NULL PRIMARY KEY,
       token_hash VARCHAR NOT NULL,
       created_at DATETIME NOT NULL)`,
  ],
};

/**
 * Timestamp parameter for the current dialect. SQLAlchemy stores SQLite
 * DateTime values as naive UTC "YYYY-MM-DD HH:MM:SS.ffffff"; matching that
 * keeps ordering consistent with rows the agent writes.
 */
export function timestampParam(db: Db, date: Date): Date | string {
  if (db.dialect === "postgres") {
    return date;
  }
  const iso = date.toISOString(); // 2026-10-21T12:00:00.123Z
  return `${iso.slice(0, 10)} ${iso.slice(11, 23)}000`;
}

/** Normalise a timestamp column from either driver to a Date. */
export function toDate(value: unknown): Date | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (value instanceof Date) {
    return value;
  }
  const text = String(value);
  // Naive SQLite values are UTC; make that explicit before parsing.
  const hasZone = /[zZ]|[+-]\d\d:?\d\d$/.test(text);
  return new Date(hasZone ? text : `${text.replace(" ", "T")}Z`);
}

async function createPostgres(url: string): Promise<Db> {
  const { default: postgres } = await import("postgres");
  const sql = postgres(url, { max: 5, idle_timeout: 20, onnotice: () => {} });
  return {
    dialect: "postgres",
    async query<T>(text: string, params: unknown[] = []) {
      return (await sql.unsafe(text, params as never[])) as unknown as T[];
    },
    async close() {
      await sql.end({ timeout: 5 });
    },
  };
}

async function createSqlite(path: string): Promise<Db> {
  const { DatabaseSync } = await import("node:sqlite");
  const db = new DatabaseSync(path);
  db.exec("PRAGMA busy_timeout = 5000");
  return {
    dialect: "sqlite",
    async query<T>(text: string, params: unknown[] = []) {
      const statement = db.prepare(text.replace(/\$\d+/g, "?"));
      const values = params.map((p) => (p instanceof Date ? p.toISOString() : p));
      return statement.all(...(values as never[])) as T[];
    },
    async close() {
      db.close();
    },
  };
}

export async function openDb(url?: string): Promise<Db> {
  const db = url ? await createPostgres(url) : await createSqlite(sqlitePath());
  for (const statement of SCHEMA[db.dialect]) {
    await db.query(statement);
  }
  return db;
}

let shared: Promise<Db> | null = null;

/** Process-wide connection, opened on first use. */
export function getDb(): Promise<Db> {
  if (!shared) {
    shared = openDb(databaseUrl()).catch((error) => {
      shared = null;
      throw error;
    });
  }
  return shared;
}

/** Test hook: swap in a specific database (e.g. an in-memory SQLite one). */
export function setDbForTesting(db: Db | null): void {
  shared = db ? Promise.resolve(db) : null;
}

export async function openSqliteForTesting(path = ":memory:"): Promise<Db> {
  const db = await createSqlite(path);
  for (const statement of SCHEMA.sqlite) {
    await db.query(statement);
  }
  return db;
}
