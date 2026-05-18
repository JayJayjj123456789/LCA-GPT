import streamlit as st
import json
import os
import logging
import tempfile
from app.config import APP_ID
from app.analyzer import (
    extract_text_from_pdf,
    analyze_enterprise_carbon,
    save_audit_to_memory,
    find_past_audits,
)
from app.database import reset_neo4j_data, ingest_analysis_to_graph, get_graph_data
from app.style import CUSTOM_CSS
from app.analytics import carbon_hotspot_chart, carbon_breakdown_pie, carbon_sankey_diagram
from app.report import generate_pdf_report
from streamlit_agraph import agraph, Config
from backend.graph_rag import ask_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="LCA-GPT Enterprise | Supply Chain Intelligence",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/green-earth.png", width=80)
    st.title("Admin Panel")
    if st.button("🗑️ Clear Data History", use_container_width=True):
        try:
            if reset_neo4j_data():
                st.session_state.clear()
                st.success("Graph Reset Successfully!")
                st.rerun()
        except Exception as e:
            st.error(f"Reset failed: {e}")
            logger.error(f"Reset failed: {e}")
    st.divider()
    st.markdown("### Export")
    if "last_analysis" in st.session_state:
        pdf_bytes = generate_pdf_report(st.session_state["last_analysis"])
        project_name = st.session_state["last_analysis"].get("project_info", {}).get("name", "report")
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name=f"LCA_{project_name}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.caption("Upload a report to enable export.")
    st.divider()
    st.markdown("### Methodology")
    st.caption("Standard: ISO 14067 / IPCC 2019")
    st.latex(r"CO_2e = \sum (Activity \times EF)")

# --- MAIN DASHBOARD ---
st.markdown("<h1 style='color: #58a6ff;'>🏢 LCA-GPT Enterprise</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e;'>AI-Powered Supply Chain Carbon Audit & Visualization</p>", unsafe_allow_html=True)

if "last_analysis" in st.session_state:
    data = st.session_state["last_analysis"]
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Supplier", data["project_info"]["supplier"])
    with m2:
        st.metric("Items Tracked", len(data.get("materials", [])) + len(data.get("energy", [])))
    with m3:
        st.metric("Carbon Footprint", f"{data.get('total_estimated_co2', 0):,.2f} kgCO2e")
    with m4:
        score = data.get("optimization_score", 0)
        st.metric("Optimization Score", f"{score}/100")

st.divider()

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.markdown("### 📤 Data Ingestion")
    uploaded_file = st.file_uploader("Upload Sustainability Report / PO (PDF)", type=["pdf"])

    if uploaded_file:
        if st.button("🚀 Run AI Carbon Audit", use_container_width=True):
            with st.spinner("Analyzing with Owl-Alpha..."):
                tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                tmp_path = tmp.name
                try:
                    tmp.write(uploaded_file.getbuffer())
                    tmp.close()
                    raw_text = extract_text_from_pdf(tmp_path)
                    if not raw_text.strip():
                        st.warning("No text extracted. The PDF may be scanned/image-based.")
                    else:
                        analysis_result = analyze_enterprise_carbon(raw_text)
                        if analysis_result:
                            clean_json = analysis_result.replace("```json", "").replace("```", "").strip()
                            json_data = json.loads(clean_json)
                            st.session_state["last_analysis"] = json_data
                            ingest_analysis_to_graph(json_data)
                            save_audit_to_memory(json_data)
                            st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"AI returned invalid JSON: {e}")
                    logger.error(f"JSON parse error: {e}")
                except RuntimeError as e:
                    st.error(str(e))
                    logger.error(str(e))
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
                    logger.error(f"Unexpected error: {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

    if "last_analysis" in st.session_state:
        st.markdown("### 💡 Strategic Insights")
        for rec in st.session_state["last_analysis"].get("recommendations", []):
            st.markdown(
                f"""<div style='background: #21262d; border-left: 5px solid #58a6ff; padding: 10px; margin-bottom: 10px; border-radius: 0 8px 8px 0;'>
                {rec}</div>""",
                unsafe_allow_html=True,
            )

with col_right:
    st.markdown("### 🕸️ Supply Chain Graph")
    nodes, edges = get_graph_data_streamlit()
    if nodes:
        config = Config(width="100%", height=550, directed=True, physics=True, hierarchical=False)
        agraph(nodes=nodes, edges=edges, config=config)
    else:
        st.info("No graph data available. Upload a report to start.")

st.divider()

# --- ANALYTICS SECTION ---
if "last_analysis" in st.session_state:
    st.markdown("### 📈 Carbon Analytics")
    data = st.session_state["last_analysis"]

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_hotspot = carbon_hotspot_chart(data.get("materials", []))
        st.plotly_chart(fig_hotspot, use_container_width=True)

    with chart_col2:
        fig_pie = carbon_breakdown_pie(data)
        st.plotly_chart(fig_pie, use_container_width=True)

    fig_sankey = carbon_sankey_diagram(data)
    st.plotly_chart(fig_sankey, use_container_width=True)

    # --- PAST AUDITS ---
    current_materials = [m["name"] for m in data.get("materials", [])]
    if current_materials:
        past_audits = find_past_audits(current_materials)
        if past_audits:
            st.markdown("### 🔍 Similar Past Audits")
            for audit in past_audits:
                with st.expander(f"📁 {audit['project_name']} (match: {audit['match_score']:.0%})"):
                    st.write(f"**Summary:** {audit['summary']}")
                    st.write(f"**Total CO₂:** {audit['total_co2']:,.2f} kgCO₂e")
                    st.write(f"**Materials:** {', '.join(audit['materials'])}")

st.divider()

# --- BOTTOM SECTION: DATA TABLES ---
if "last_analysis" in st.session_state:
    st.markdown("### 📊 Detailed Audit Inventory")
    data = st.session_state["last_analysis"]

    t1, t2, t3 = st.tabs(["📋 Materials", "⚡ Energy", "🚚 Logistics"])

    with t1:
        if data.get("materials"):
            import pandas as pd
            df_mat = pd.DataFrame(data["materials"])
            df_mat["Subtotal (kgCO2e)"] = df_mat["amount"] * df_mat["emission_factor"]
            st.dataframe(
                df_mat.style.format(
                    subset=["amount", "emission_factor", "Subtotal (kgCO2e)"],
                    formatter="{:.4f}",
                ),
                use_container_width=True,
                hide_index=True,
            )

    with t2:
        if data.get("energy"):
            import pandas as pd
            st.dataframe(pd.DataFrame(data["energy"]), use_container_width=True, hide_index=True)
        else:
            st.caption("No Energy data found.")

    with t3:
        if data.get("transport"):
            import pandas as pd
            st.dataframe(pd.DataFrame(data["transport"]), use_container_width=True, hide_index=True)
        else:
            st.caption("No Transport data found.")

    # Strategy Chat
    st.divider()
    st.markdown("### 💬 Strategy Consultant Chat")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about the calculation logic..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                res = ask_graph(prompt)
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
            except Exception as e:
                error_msg = "Sorry, I couldn't process your question right now."
                st.markdown(error_msg)
                logger.error(f"Chat error: {e}")
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
