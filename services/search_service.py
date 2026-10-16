from database.db import connect
from retrieval.hybrid_ranker import rank_candidates

def search_scans(query: str, urgency: str = "ROUTINE", db_path: str | None = None) -> list[dict]:
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO QueryLogs(query_text, urgency) VALUES (?, ?)",
            (query, urgency.upper())
        )
        rows = conn.execute("""
            SELECT s.scan_id, s.scan_type, s.file_name, s.file_size_kb, s.notes,
                   i.allocation_strategy, i.fragmentation_ratio,
                   i.predicted_latency_ms, i.storage_preference
            FROM Scans s
            JOIN Inodes i ON i.file_id = s.scan_id
        """).fetchall()
        candidates = [dict(r) for r in rows]
        return rank_candidates(query, candidates, urgency)

def get_disk_state(db_path: str | None = None) -> list[dict]:
    with connect(db_path) as conn:
        rows = conn.execute("""
            SELECT block_id, file_id, next_block_id, is_allocated
            FROM DiskBlocks ORDER BY block_id
        """).fetchall()
        return [dict(r) for r in rows]

def get_inode_rows(db_path: str | None = None) -> list[dict]:
    with connect(db_path) as conn:
        rows = conn.execute("""
            SELECT i.*, s.file_name, s.scan_type
            FROM Inodes i JOIN Scans s ON s.scan_id = i.file_id
            ORDER BY i.inode_id
        """).fetchall()
        return [dict(r) for r in rows]
