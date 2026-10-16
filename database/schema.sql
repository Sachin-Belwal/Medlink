PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Patients (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_code TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Scans (
    scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    scan_type TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size_kb INTEGER NOT NULL CHECK(file_size_kb > 0),
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES Patients(patient_id)
);

CREATE TABLE IF NOT EXISTS Inodes (
    inode_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL UNIQUE,
    start_block INTEGER,
    block_count INTEGER NOT NULL CHECK(block_count > 0),
    allocation_strategy TEXT NOT NULL,
    fragmentation_ratio REAL NOT NULL DEFAULT 0,
    predicted_latency_ms REAL NOT NULL DEFAULT 0,
    storage_preference TEXT NOT NULL DEFAULT 'SPACE_EFFICIENT',
    FOREIGN KEY(file_id) REFERENCES Scans(scan_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS DiskBlocks (
    block_id INTEGER PRIMARY KEY,
    file_id INTEGER,
    next_block_id INTEGER,
    is_allocated INTEGER NOT NULL DEFAULT 0 CHECK(is_allocated IN (0,1)),
    FOREIGN KEY(file_id) REFERENCES Scans(scan_id) ON DELETE CASCADE,
    FOREIGN KEY(next_block_id) REFERENCES DiskBlocks(block_id)
);

CREATE TABLE IF NOT EXISTS QueryLogs (
    query_id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    urgency TEXT NOT NULL CHECK(urgency IN ('ROUTINE','EMERGENCY')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS RAGFeedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    urgency TEXT NOT NULL CHECK(urgency IN ('ROUTINE','HIGH')),
    storage_preference TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(file_id) REFERENCES Scans(scan_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scans_patient ON Scans(patient_id);
CREATE INDEX IF NOT EXISTS idx_scans_type ON Scans(scan_type);
CREATE INDEX IF NOT EXISTS idx_inodes_latency ON Inodes(predicted_latency_ms);
CREATE INDEX IF NOT EXISTS idx_blocks_file ON DiskBlocks(file_id);
