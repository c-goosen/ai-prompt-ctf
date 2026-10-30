import { describe, expect, it } from "vitest";

import { type Db, timestampParam, toDate } from "./db";

describe("db timestamps", () => {
  const date = new Date("2026-10-21T12:00:00.123Z");

  it("formats SQLite timestamps like SQLAlchemy and passes Dates to Postgres", () => {
    expect(timestampParam({ dialect: "sqlite" } as Db, date)).toBe("2026-10-21 12:00:00.123000");
    expect(timestampParam({ dialect: "postgres" } as Db, date)).toBe(date);
  });

  it("reads naive SQLite values as UTC", () => {
    expect(toDate("2026-10-21 12:00:00.123000")).toEqual(date);
    expect(toDate(timestampParam({ dialect: "sqlite" } as Db, date))).toEqual(date);
  });

  it("keeps explicit zones, Dates and nulls", () => {
    expect(toDate("2026-10-21T14:00:00.123+02:00")).toEqual(date);
    expect(toDate("2026-10-21T12:00:00.123Z")).toEqual(date);
    expect(toDate(date)).toBe(date);
    expect(toDate(null)).toBeNull();
    expect(toDate(undefined)).toBeNull();
  });
});
