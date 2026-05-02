-- ═══════════════════════════════════════════════════
-- FinYaar Database Schema (SQLite)
-- Group CSD138 | Banasthali Vidyapith
-- ═══════════════════════════════════════════════════

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(100)  NOT NULL,
    email       VARCHAR(150)  NOT NULL UNIQUE,      -- MUST be @banasthali.in
    student_id  VARCHAR(50)   NOT NULL,             -- e.g. BTBTI12345
    course      VARCHAR(80)   NOT NULL,             -- B.Tech-CS / BCA / MCA etc.
    year        VARCHAR(20)   NOT NULL,             -- 1st Year / 2nd Year ...
    password    VARCHAR(256)  NOT NULL,             -- bcrypt hash
    role        VARCHAR(20)   DEFAULT 'student',
    budget      FLOAT         DEFAULT 55000.0,      -- monthly budget (₹)
    paper_cash  FLOAT         DEFAULT 100000.0,     -- virtual trading cash (₹)
    is_verified BOOLEAN       DEFAULT 0,            -- email OTP verified
    created_at  DATETIME      DEFAULT CURRENT_TIMESTAMP
);

-- 2. EXPENSES TABLE
CREATE TABLE IF NOT EXISTS expenses (
    expense_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER   NOT NULL REFERENCES users(user_id),
    title       VARCHAR(200) NOT NULL,              -- Zomato, Uber, Stationary...
    amount      FLOAT     NOT NULL,
    category    VARCHAR(50)  NOT NULL,              -- Food|Travel|Study|Leisure|Health|Shopping
    date        DATE      NOT NULL,
    notes       TEXT      DEFAULT '',
    created_at  DATETIME  DEFAULT CURRENT_TIMESTAMP
);

-- 3. SAVINGS GOALS TABLE
CREATE TABLE IF NOT EXISTS savings_goals (
    goal_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(user_id),
    name           VARCHAR(100) NOT NULL,           -- Europe Trip, New Laptop...
    icon           VARCHAR(10)  DEFAULT '✈️',
    target_amount  FLOAT NOT NULL,
    current_amount FLOAT DEFAULT 0.0,
    deadline       DATE  NOT NULL,
    is_done        BOOLEAN DEFAULT 0,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 4. PORTFOLIO TABLE (current holdings)
CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(user_id),
    stock_symbol VARCHAR(20) NOT NULL,             -- RELIANCE, TCS, HDFCBANK...
    quantity     INTEGER DEFAULT 0,
    avg_price    FLOAT   NOT NULL,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, stock_symbol)
);

-- 5. STOCK TRADES TABLE (all buy/sell history)
CREATE TABLE IF NOT EXISTS stock_trades (
    trade_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(user_id),
    stock_symbol VARCHAR(20)  NOT NULL,
    trade_type   VARCHAR(10)  NOT NULL,            -- BUY | SELL
    quantity     INTEGER NOT NULL,
    price        FLOAT   NOT NULL,                 -- price per share at execution
    total_amount FLOAT   NOT NULL,                 -- quantity * price
    traded_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 6. NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS notifications (
    notif_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(user_id),
    message    TEXT    NOT NULL,
    type       VARCHAR(30) DEFAULT 'info',         -- info|goal|trade|budget_alert
    is_read    BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. FINBOT LOGS TABLE
CREATE TABLE IF NOT EXISTS finbot_logs (
    log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(user_id),
    query      TEXT NOT NULL,
    response   TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 8. PASSWORD RESETS TABLE
CREATE TABLE IF NOT EXISTS password_resets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    email      VARCHAR(150) NOT NULL,
    otp        VARCHAR(6)   NOT NULL,
    expires_at DATETIME     NOT NULL,
    used       BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════
-- INDEXES (for performance)
-- ═══════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_expenses_user     ON expenses(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_savings_user      ON savings_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_user       ON stock_trades(user_id, traded_at DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_user    ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_notifs_user       ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_finbot_user       ON finbot_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email       ON users(email);
