import tempfile
import unittest
from pathlib import Path

from database.db import initialize_database, connect
from services.ingestion import ingest_scan
from services.search_service import search_scans
from services.feedback import record_feedback
from os_simulator.cscan import cscan_head_movement

class MedLinkCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.db")
        initialize_database(self.db_path, disk_blocks=20)
        with connect(self.db_path) as conn:
            self.patient_id = conn.execute("SELECT patient_id FROM Patients LIMIT 1").fetchone()["patient_id"]

    def tearDown(self):
        self.tmp.cleanup()

    def test_ingestion_creates_scan_inode_and_blocks(self):
        scan_id = ingest_scan(self.patient_id, "CT", "a.dcm", 128,
                              "abnormal lung finding", db_path=self.db_path)
        with connect(self.db_path) as conn:
            self.assertIsNotNone(conn.execute("SELECT 1 FROM Scans WHERE scan_id=?", (scan_id,)).fetchone())
            self.assertIsNotNone(conn.execute("SELECT 1 FROM Inodes WHERE file_id=?", (scan_id,)).fetchone())
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM DiskBlocks WHERE file_id=?", (scan_id,)).fetchone()[0], 2)

    def test_search_returns_relevance(self):
        ingest_scan(self.patient_id, "CT", "a.dcm", 128, "abnormal lung finding", db_path=self.db_path)
        results = search_scans("lung finding", "ROUTINE", db_path=self.db_path)
        self.assertTrue(results)
        self.assertGreater(results[0]["relevance_score"], 0)

    def test_feedback_updates_future_preference(self):
        scan_id = ingest_scan(self.patient_id, "CT", "a.dcm", 128, "synthetic note", db_path=self.db_path)
        preference = record_feedback(scan_id, 0.92, "HIGH", db_path=self.db_path)
        self.assertEqual(preference, "CONTIGUOUS_FIRST")

    def test_cscan_movement(self):
        movement = cscan_head_movement([10, 30, 70, 90], 50, 100)
        self.assertGreater(movement, 0)

if __name__ == "__main__":
    unittest.main()
