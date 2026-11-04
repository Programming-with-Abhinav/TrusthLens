-- Version 002: Retire raw-content history persistence.
DROP INDEX IF EXISTS trustlens_history_created_at_idx;
DROP TABLE IF EXISTS trustlens_history;
