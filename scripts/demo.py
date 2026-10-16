from database.db import initialize_database, connect
from services.ingestion import ingest_scan
from services.search_service import search_scans, get_inode_rows

def main():
    initialize_database()
    with connect() as conn:
        patient_id = conn.execute("SELECT patient_id FROM Patients LIMIT 1").fetchone()["patient_id"]
    try:
        scan_id = ingest_scan(
            patient_id=patient_id,
            scan_type="CT",
            file_name="demo_ct_scan.dcm",
            file_size_kb=512,
            notes="Synthetic report note mentioning abnormal lung finding.",
            allocation_policy="CONTIGUOUS_FIRST"
        )
        print(f"Created synthetic scan {scan_id}")
    except Exception as exc:
        print(f"Ingestion skipped/failed: {exc}")

    print("\nRoutine ranking:")
    for row in search_scans("abnormal lung finding", "ROUTINE"):
        print(row["scan_id"], row["relevance_score"], row["predicted_latency_ms"], row["hybrid_score"])
    print("\nInodes:")
    for row in get_inode_rows():
        print(row)

if __name__ == "__main__":
    main()
