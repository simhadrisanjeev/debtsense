-- =============================================================================
-- DebtSense — Initial Database Schema
-- =============================================================================
--
-- This script creates the complete relational schema for the DebtSense
-- application.  It is designed for PostgreSQL 14+ and uses:
--
--   * UUID primary keys via gen_random_uuid()
--   * TIMESTAMPTZ for all temporal columns
--   * Appropriate indexes for query patterns used by the API
--   * ON DELETE CASCADE for child tables referencing users
--
-- Run against a fresh database:
--   psql -U debtsense_user -d debtsense -f 001_initial.sql
-- =============================================================================

-- Enable pgcrypto if gen_random_uuid() is not available (PG < 14)
-- CREATE EXTENSION IF NOT EXISTS pgcrypto;

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. users
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email             VARCHAR(320) NOT NULL,
    hashed_password   VARCHAR(1024) NOT NULL,
    first_name        VARCHAR(150) NOT NULL DEFAULT '',
    last_name         VARCHAR(150) NOT NULL DEFAULT '',
    is_active         BOOLEAN      NOT NULL DEFAULT TRUE,
    is_verified       BOOLEAN      NOT NULL DEFAULT FALSE,
    subscription_tier VARCHAR(20)  NOT NULL DEFAULT 'free',
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_is_active ON users (is_active) WHERE is_active = TRUE;

-- ---------------------------------------------------------------------------
-- 2. refresh_tokens
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL,
    token       VARCHAR(512) NOT NULL,
    expires_at  TIMESTAMPTZ  NOT NULL,
    revoked     BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT fk_refresh_tokens_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT uq_refresh_tokens_token UNIQUE (token)
);

CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens (user_id);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token ON refresh_tokens (token);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_active
    ON refresh_tokens (user_id, revoked) WHERE revoked = FALSE;

-- ---------------------------------------------------------------------------
-- 3. debts
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS debts (
    id                UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID          NOT NULL,
    name              VARCHAR(255)  NOT NULL,
    debt_type         VARCHAR(50)   NOT NULL,
    principal_balance NUMERIC(12,2) NOT NULL,
    current_balance   NUMERIC(12,2) NOT NULL,
    interest_rate     NUMERIC(5,4)  NOT NULL,
    minimum_payment   NUMERIC(10,2) NOT NULL,
    due_date          INTEGER       NOT NULL CHECK (due_date BETWEEN 1 AND 31),
    start_date        DATE          NOT NULL,
    is_active         BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT fk_debts_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT ck_debts_debt_type
        CHECK (debt_type IN (
            'credit_card', 'student_loan', 'mortgage',
            'auto_loan', 'personal_loan', 'medical', 'other'
        )),
    CONSTRAINT ck_debts_balance_positive
        CHECK (current_balance >= 0),
    CONSTRAINT ck_debts_rate_positive
        CHECK (interest_rate >= 0)
);

CREATE INDEX IF NOT EXISTS ix_debts_user_id ON debts (user_id);
CREATE INDEX IF NOT EXISTS ix_debts_user_active ON debts (user_id, is_active);
CREATE INDEX IF NOT EXISTS ix_debts_debt_type ON debts (debt_type);

-- ---------------------------------------------------------------------------
-- 4. income
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS income (
    id         UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID          NOT NULL,
    source     VARCHAR(50)   NOT NULL,
    amount     NUMERIC(12,2) NOT NULL,
    frequency  VARCHAR(20)   NOT NULL,
    is_active  BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT fk_income_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT ck_income_frequency
        CHECK (frequency IN (
            'weekly', 'biweekly', 'monthly', 'annually', 'one_time'
        )),
    CONSTRAINT ck_income_amount_positive
        CHECK (amount >= 0)
);

CREATE INDEX IF NOT EXISTS ix_income_user_id ON income (user_id);

-- ---------------------------------------------------------------------------
-- 5. expenses
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS expenses (
    id           UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID          NOT NULL,
    category     VARCHAR(50)   NOT NULL,
    description  VARCHAR(255)  NOT NULL,
    amount       NUMERIC(10,2) NOT NULL,
    frequency    VARCHAR(20)   NOT NULL DEFAULT 'monthly',
    is_recurring BOOLEAN       NOT NULL DEFAULT TRUE,
    is_active    BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT fk_expenses_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT ck_expenses_category
        CHECK (category IN (
            'housing', 'transportation', 'food', 'utilities',
            'insurance', 'healthcare', 'entertainment',
            'subscriptions', 'other'
        )),
    CONSTRAINT ck_expenses_frequency
        CHECK (frequency IN (
            'one_time', 'weekly', 'biweekly', 'monthly', 'annually'
        )),
    CONSTRAINT ck_expenses_amount_positive
        CHECK (amount >= 0)
);

CREATE INDEX IF NOT EXISTS ix_expenses_user_id ON expenses (user_id);
CREATE INDEX IF NOT EXISTS ix_expenses_user_category ON expenses (user_id, category);

-- ---------------------------------------------------------------------------
-- 6. analytics_events
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS analytics_events (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID,
    event_type  VARCHAR(100) NOT NULL,
    event_data  JSONB        NOT NULL DEFAULT '{}',
    ip_address  INET,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT fk_analytics_events_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_analytics_events_user_id ON analytics_events (user_id);
CREATE INDEX IF NOT EXISTS ix_analytics_events_type ON analytics_events (event_type);
CREATE INDEX IF NOT EXISTS ix_analytics_events_created ON analytics_events (created_at);
-- GIN index for fast JSONB containment queries
CREATE INDEX IF NOT EXISTS ix_analytics_events_data ON analytics_events USING GIN (event_data);

-- ---------------------------------------------------------------------------
-- 7. monthly_snapshots
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS monthly_snapshots (
    id                      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID          NOT NULL,
    snapshot_date           DATE          NOT NULL,
    total_debt              NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_minimum_payments  NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_income            NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_expenses          NUMERIC(14,2) NOT NULL DEFAULT 0,
    disposable_income       NUMERIC(14,2) NOT NULL DEFAULT 0,
    debt_count              INTEGER       NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT fk_monthly_snapshots_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT uq_monthly_snapshots_user_date
        UNIQUE (user_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS ix_monthly_snapshots_user_id ON monthly_snapshots (user_id);
CREATE INDEX IF NOT EXISTS ix_monthly_snapshots_date ON monthly_snapshots (snapshot_date);

-- ---------------------------------------------------------------------------
-- 8. notifications
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS notifications (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID         NOT NULL,
    title       VARCHAR(255) NOT NULL,
    body        TEXT         NOT NULL DEFAULT '',
    channel     VARCHAR(20)  NOT NULL DEFAULT 'in_app',
    is_read     BOOLEAN      NOT NULL DEFAULT FALSE,
    read_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT fk_notifications_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT ck_notifications_channel
        CHECK (channel IN ('in_app', 'email', 'push'))
);

CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id);
CREATE INDEX IF NOT EXISTS ix_notifications_unread
    ON notifications (user_id, is_read) WHERE is_read = FALSE;

-- ---------------------------------------------------------------------------
-- Trigger: auto-update updated_at on row modification
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply the trigger to every table that has an updated_at column.
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_name = 'updated_at'
    LOOP
        EXECUTE format(
            'CREATE OR REPLACE TRIGGER trg_%I_updated_at
             BEFORE UPDATE ON %I
             FOR EACH ROW
             EXECUTE FUNCTION trigger_set_updated_at();',
            tbl, tbl
        );
    END LOOP;
END;
$$;

COMMIT;
