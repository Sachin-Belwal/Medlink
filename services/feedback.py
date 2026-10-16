from database.db import connect

def record_feedback(file_id: int, confidence: float, urgency: str,
                    db_path: str | None = None) -> str:
    """Store RAG feedback and set a future preference; does not move existing blocks."""
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("Confidence must be between 0 and 1.")
    urgency = urgency.upper()
    if urgency not in {"HIGH", "ROUTINE"}:
        raise ValueError("Urgency must be HIGH or ROUTINE.")
    preference = "CONTIGUOUS_FIRST" if urgency == "HIGH" and confidence >= 0.85 else "SPACE_EFFICIENT"

    with connect(db_path) as conn:
        exists = conn.execute("SELECT 1 FROM Scans WHERE scan_id = ?", (file_id,)).fetchone()
        if not exists:
            raise ValueError("Scan does not exist.")
        conn.execute(
            """INSERT INTO RAGFeedback(file_id, confidence, urgency, storage_preference)
               VALUES (?, ?, ?, ?)""",
            (file_id, confidence, urgency, preference)
        )
        conn.execute(
            "UPDATE Inodes SET storage_preference = ? WHERE file_id = ?",
            (preference, file_id)
        )
    return preference
