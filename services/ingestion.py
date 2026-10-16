import math
from database.db import connect
from os_simulator.allocator import allocate_blocks, AllocationError
from config import BLOCK_SIZE_KB

def ingest_scan(patient_id: int, scan_type: str, file_name: str, file_size_kb: int,
                notes: str, allocation_policy: str = "CONTIGUOUS_FIRST",
                storage_preference: str = "SPACE_EFFICIENT",
                db_path: str | None = None) -> int:
    """Create scan + virtual allocation atomically in one SQLite transaction."""
    if file_size_kb <= 0:
        raise ValueError("File size must be positive.")
    blocks_needed = max(1, math.ceil(file_size_kb / BLOCK_SIZE_KB))
    conn = connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        patient = conn.execute(
            "SELECT patient_id FROM Patients WHERE patient_id = ?", (patient_id,)
        ).fetchone()
        if patient is None:
            raise ValueError("Patient does not exist.")

        cur = conn.execute(
            """INSERT INTO Scans(patient_id, scan_type, file_name, file_size_kb, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (patient_id, scan_type.strip().upper(), file_name.strip(), file_size_kb, notes.strip())
        )
        file_id = int(cur.lastrowid)

        allocation = allocate_blocks(
            conn, file_id, blocks_needed, allocation_policy,
            storage_preference=storage_preference
        )
        conn.execute(
            """INSERT INTO Inodes
               (file_id, start_block, block_count, allocation_strategy,
                fragmentation_ratio, predicted_latency_ms, storage_preference)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (file_id, allocation.blocks[0], len(allocation.blocks), allocation.strategy,
             allocation.fragmentation_ratio, allocation.predicted_latency_ms,
             allocation.storage_preference)
        )
        conn.commit()
        return file_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def list_scans(db_path: str | None = None) -> list[dict]:
    with connect(db_path) as conn:
        rows = conn.execute("""
            SELECT s.scan_id, s.patient_id, s.scan_type, s.file_name, s.file_size_kb,
                   s.notes, s.created_at, i.start_block, i.block_count,
                   i.allocation_strategy, i.fragmentation_ratio,
                   i.predicted_latency_ms, i.storage_preference
            FROM Scans s JOIN Inodes i ON i.file_id = s.scan_id
            ORDER BY s.scan_id DESC
        """).fetchall()
        return [dict(r) for r in rows]
