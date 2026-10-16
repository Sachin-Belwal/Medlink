import sqlite3
from pathlib import Path
from config import DB_PATH, DEFAULT_DISK_BLOCKS

def connect(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database(db_path: str | None = None, disk_blocks: int = DEFAULT_DISK_BLOCKS) -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    with connect(db_path) as conn:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        existing = conn.execute("SELECT COUNT(*) AS n FROM DiskBlocks").fetchone()["n"]
        if existing == 0:
            conn.executemany(
                "INSERT INTO DiskBlocks(block_id, file_id, next_block_id, is_allocated) VALUES (?, NULL, NULL, 0)",
                [(i,) for i in range(disk_blocks)]
            )
        # Add a harmless synthetic demo patient if the table is empty.
        n_patients = conn.execute("SELECT COUNT(*) AS n FROM Patients").fetchone()["n"]
        if n_patients == 0:
            conn.execute(
                "INSERT INTO Patients(patient_code, display_name) VALUES (?, ?)",
                ("SYN-001", "Synthetic Demo Patient")
            )

def database_path() -> str:
    return DB_PATH
