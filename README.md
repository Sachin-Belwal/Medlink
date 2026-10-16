# MedLink — PBL Phase 1 (approximately 50% implementation)

This is a runnable, structured foundation for the MedLink OS + DBMS + intelligent retrieval project.

## Implemented in this phase
- SQLite schema with `Patients`, `Scans`, `Inodes`, `DiskBlocks`, `QueryLogs`, and `RAGFeedback`
- Virtual disk represented as rows in SQLite
- Contiguous-first and linked allocation policies
- C-SCAN-style disk-head movement estimate and a simple retrieval-cost estimate
- Transactional ingestion: scan, inode, and block mappings are written in one SQL transaction
- Hybrid ranking using text-match relevance and predicted storage cost
- Feedback records that can influence future allocation preferences
- Streamlit dashboard for ingesting synthetic scan records, searching, and viewing the virtual disk

## Not yet implemented (intentionally left for later phase)
- Actual Sentence Transformers embeddings and ChromaDB vector search
- LLM summaries through Ollama
- Authentication/authorization and production-grade medical-data security
- Real DICOM/PACS integration, real clinical urgency rules, and physical disk control
- Background compaction/re-storage worker and comprehensive automated tests

The initial semantic relevance score is a **keyword-overlap placeholder**, not a medical NLP model. All sample records are synthetic. Do not use real patient information.

## Requirements
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

If Streamlit is not installed in your environment, you can still test core functionality with:
```bash
python scripts/demo.py
```

## Project structure
```text
MedLink/
├── app.py
├── config.py
├── requirements.txt
├── database/
│   ├── __init__.py
│   ├── db.py
│   └── schema.sql
├── os_simulator/
│   ├── __init__.py
│   ├── allocator.py
│   └── cscan.py
├── retrieval/
│   ├── __init__.py
│   └── hybrid_ranker.py
├── services/
│   ├── __init__.py
│   ├── ingestion.py
│   ├── search_service.py
│   └── feedback.py
├── scripts/
│   └── demo.py
└── tests/
    └── test_core.py
```

## Demo flow
1. Open the Streamlit app.
2. Initialize the database from the sidebar.
3. Add synthetic scan records. Try `CONTIGUOUS_FIRST` and `SPACE_EFFICIENT`.
4. Search notes using a phrase found in the sample notes.
5. Toggle urgency between `ROUTINE` and `EMERGENCY` and compare result ordering.
6. Inspect the virtual disk and the `Inodes` metadata.

## Design note
The virtual disk is simulated in SQLite. The OS allocator makes decisions about block placement; the DBMS persists those decisions. A single database transaction makes the scan, inode, and block mappings consistent. This is a simulator, not a real OS filesystem driver.
