import streamlit as st
from database.db import initialize_database, connect
from services.ingestion import ingest_scan, list_scans
from services.search_service import search_scans, get_disk_state, get_inode_rows
from services.feedback import record_feedback

st.set_page_config(page_title="MedLink PBL", page_icon="💾", layout="wide")
st.title("MedLink — OS + DBMS Intelligent Scan Retrieval")
st.caption("PBL phase 1 prototype · Synthetic data only · OS storage is simulated")

with st.sidebar:
    st.header("Database")
    if st.button("Initialize / verify database", use_container_width=True):
        initialize_database()
        st.success("Database initialized.")
    st.info("First run: click Initialize / verify database.")

try:
    initialize_database()
except Exception as exc:
    st.error(f"Database initialization failed: {exc}")
    st.stop()

tab_ingest, tab_search, tab_disk, tab_feedback = st.tabs(
    ["Ingest scan", "Search", "Virtual disk & inodes", "RAG feedback"]
)

with tab_ingest:
    st.subheader("Add a synthetic scan record")
    with st.form("ingest_form"):
        with connect() as conn:
            patients = conn.execute("SELECT patient_id, patient_code, display_name FROM Patients").fetchall()
        patient_options = {f"{p['patient_code']} — {p['display_name']}": p["patient_id"] for p in patients}
        selected_patient = st.selectbox("Synthetic patient", list(patient_options))
        scan_type = st.selectbox("Scan type", ["CT", "X-RAY", "MRI", "ULTRASOUND"])
        file_name = st.text_input("File name", "sample_scan_001.dcm")
        file_size_kb = st.number_input("File size (KB)", min_value=1, max_value=100000, value=512, step=64)
        notes = st.text_area("Synthetic report notes", "Example note: abnormal lung finding mentioned in report.")
        policy = st.selectbox("OS allocation policy", ["CONTIGUOUS_FIRST", "SPACE_EFFICIENT", "CONTIGUOUS_ONLY"])
        preference = st.selectbox("Storage preference", ["SPACE_EFFICIENT", "CONTIGUOUS_FIRST"])
        submitted = st.form_submit_button("Ingest scan")
    if submitted:
        try:
            scan_id = ingest_scan(
                patient_options[selected_patient], scan_type, file_name,
                int(file_size_kb), notes, policy, preference
            )
            st.success(f"Scan ingested successfully. Scan ID: {scan_id}")
        except Exception as exc:
            st.error(f"Ingestion failed; transaction rolled back: {exc}")

with tab_search:
    st.subheader("Search scan notes")
    query = st.text_input("Search phrase", "abnormal lung finding")
    urgency = st.radio("Retrieval urgency", ["ROUTINE", "EMERGENCY"], horizontal=True)
    if st.button("Search scans"):
        results = search_scans(query, urgency)
        if not results:
            st.warning("No scan records found. Add a synthetic scan first.")
        else:
            st.caption("Phase 1 uses keyword overlap as a placeholder for semantic embeddings.")
            for item in results:
                with st.container(border=True):
                    st.markdown(f"**Scan #{item['scan_id']} — {item['scan_type']}**")
                    st.write(item["file_name"])
                    st.write(item["notes"])
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Relevance", f"{item['relevance_score']:.2f}")
                    c2.metric("Predicted cost", f"{item['predicted_latency_ms']:.2f} ms")
                    c3.metric("Hybrid score", f"{item['hybrid_score']:.3f}")
                    st.caption(
                        f"Allocation: {item['allocation_strategy']} · "
                        f"Fragmentation: {item['fragmentation_ratio']:.2f}"
                    )
                    if item["retrieval_warning"]:
                        st.warning("High simulated retrieval cost. Check for an authorized cached copy.")
                    if item["relevance_score"] == 0:
                        st.caption("No query tokens matched this note in the baseline search.")

with tab_disk:
    st.subheader("Virtual disk block map")
    blocks = get_disk_state()
    used = sum(1 for b in blocks if b["is_allocated"])
    m1, m2, m3 = st.columns(3)
    m1.metric("Total blocks", len(blocks))
    m2.metric("Allocated blocks", used)
    m3.metric("Free blocks", len(blocks) - used)
    if blocks:
        cols = st.columns(10)
        for idx, block in enumerate(blocks):
            with cols[idx % 10]:
                label = f"{block['block_id']}"
                st.markdown(
                    f"<div title='File {block['file_id']}' style='text-align:center;"
                    f"padding:6px 2px;margin:2px;border-radius:5px;"
                    f"background:{'#0D9488' if block['is_allocated'] else '#E5E7EB'};"
                    f"color:{'white' if block['is_allocated'] else '#111827'}'>{label}</div>",
                    unsafe_allow_html=True
                )
    st.subheader("Inodes table")
    inode_rows = get_inode_rows()
    st.dataframe(inode_rows, use_container_width=True, hide_index=True)

with tab_feedback:
    st.subheader("Record a simulated RAG priority signal")
    scans = list_scans()
    if not scans:
        st.info("Ingest a synthetic scan first.")
    else:
        labels = {f"#{s['scan_id']} — {s['file_name']}": s['scan_id'] for s in scans}
        with st.form("feedback_form"):
            selected = st.selectbox("Scan", list(labels))
            confidence = st.slider("Demo confidence score", 0.0, 1.0, 0.90, 0.01)
            priority = st.selectbox("Assessed priority", ["HIGH", "ROUTINE"])
            save_feedback = st.form_submit_button("Save feedback")
        if save_feedback:
            try:
                preference = record_feedback(labels[selected], confidence, priority)
                st.success(f"Feedback saved. Future preference: {preference}")
                st.caption("This updates the preference for a future allocation/re-storage operation; it does not relocate existing blocks.")
            except Exception as exc:
                st.error(str(exc))

st.divider()
st.caption("Educational simulator only. No real clinical decisions, patient data, or physical disk allocation.")
