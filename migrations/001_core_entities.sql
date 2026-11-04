-- Version 001: TrustLens local persistence entities.
-- Applied once by the migration runner transaction.
CREATE TABLE trustlens_cache (
    "key" TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE TABLE trustlens_history (
    id INTEGER PRIMARY KEY,
    item_type TEXT NOT NULL CHECK (length(trim(item_type)) > 0),
    input_preview TEXT NOT NULL,
    result TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE INDEX trustlens_history_created_at_idx
    ON trustlens_history(created_at DESC);
