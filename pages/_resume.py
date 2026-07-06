from __future__ import annotations
import streamlit as st
import tempfile, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from utils.backend import get_skill_gap

SKILL_CATEGORY_ICONS = {
    "languages": "💻", "frameworks": "🧩", "cloud": "☁️",
    "data_engineering": "🔧", "ml_ai": "🤖", "devops": "🐳",
    "web": "🌐", "databases": "🗄️", "tools": "🛠️",
    "enterprise": "🏢", "business_soft": "💼", "other": "📌",
}

def render():
    st.markdown("""
    <div class="cs-section-header">
        <span style="font-size:24px;">📄</span>
        <span class="cs-section-title">Resume Analyzer</span>
    </div>
    """, unsafe_allow_html=True)

    if "resume_data" not in st.session_state:
        st.session_state.resume_data = None
    if "resume_path" not in st.session_state:
        st.session_state.resume_path = None

    upload_col, preview_col = st.columns([5, 5], gap="large")

    with upload_col:
        st.markdown("""
        <div style="background:white;border-radius:16px;padding:24px;
                    border:1px solid #E2E8F0;margin-bottom:16px;">
            <div style="font-size:16px;font-weight:700;color:#0D1B2A;margin-bottom:4px;">
                📤 Upload Resume
            </div>
            <div style="font-size:12px;color:#64748B;margin-bottom:16px;">
                Supports PDF, DOCX, and TXT formats
            </div>
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Drop your resume here",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
        )

        if uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded.name.split('.')[-1]}") as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name

            st.session_state.resume_path = tmp_path
            st.markdown(f"""
            <div style="background:#F0FDF9;border-radius:12px;padding:16px;
                        border:1px solid rgba(0,200,150,0.2);margin-top:12px;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:24px;">✅</span>
                    <div>
                        <div style="font-weight:700;font-size:14px;color:#0D1B2A;">{uploaded.name}</div>
                        <div style="font-size:11px;color:#64748B;">
                            {uploaded.size // 1024:.0f} KB · Ready to analyze
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.spinner("Parsing resume and detecting skills..."):
                jd_text = st.session_state.get("jd_for_resume", "")
                data = get_skill_gap(tmp_path, jd_text)
                st.session_state.resume_data = data

        # JD input for better analysis
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:13px;font-weight:600;color:#475569;margin-bottom:8px;">
            📋 Paste a job description (optional — improves ATS accuracy)
        </div>
        """, unsafe_allow_html=True)
        jd_input = st.text_area(
            "JD", label_visibility="collapsed",
            placeholder="Paste the job description here for a more accurate ATS score and gap analysis...",
            height=120,
        )
        if jd_input:
            st.session_state.jd_for_resume = jd_input

        if st.button("🔍 Re-analyze with JD", type="primary") and st.session_state.resume_path:
            with st.spinner("Running analysis..."):
                data = get_skill_gap(st.session_state.resume_path, jd_input)
                st.session_state.resume_data = data

    with preview_col:
        data = st.session_state.resume_data
        if not data:
            st.markdown("""
            <div style="background:white;border-radius:16px;padding:48px 24px;
                        border:2px dashed #E2E8F0;text-align:center;height:100%;">
                <div style="font-size:48px;margin-bottom:16px;">📄</div>
                <div style="font-size:15px;font-weight:600;color:#64748B;">
                    Upload your resume to see analysis
                </div>
                <div style="font-size:12px;color:#94A3B8;margin-top:6px;">
                    Skills, ATS score, and gap analysis will appear here
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            ats = data.get("ats_score", 0)
            grade = data.get("grade", "C")
            grade_color = {"A": "#00C896", "B": "#1A73E8", "C": "#F59E0B", "D": "#FF6B6B"}.get(grade, "#64748B")

            # ATS Score
            st.markdown(f"""
            <div style="background:white;border-radius:16px;padding:24px;
                        border:1px solid #E2E8F0;text-align:center;margin-bottom:16px;">
                <div style="font-size:13px;color:#64748B;font-weight:500;margin-bottom:8px;">ATS COMPATIBILITY SCORE</div>
                <div style="font-size:56px;font-weight:800;color:{grade_color};font-family:'Space Grotesk',sans-serif;line-height:1;">
                    {ats:.0f}
                </div>
                <div style="font-size:14px;font-weight:700;color:{grade_color};margin-top:4px;">Grade {grade}</div>
                <div style="margin-top:16px;">
                    <div style="height:8px;background:#F1F5F9;border-radius:8px;overflow:hidden;">
                        <div style="height:100%;width:{ats}%;background:linear-gradient(90deg,#1A73E8,{grade_color});
                                    border-radius:8px;transition:width 0.8s ease;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ATS warnings
            warnings = data.get("warnings", [])
            if warnings:
                for w in warnings:
                    st.markdown(f"""
                    <div style="background:#FFFBEB;border-radius:10px;padding:10px 14px;
                                border-left:3px solid #F59E0B;font-size:12px;color:#92400E;
                                margin-bottom:8px;">⚠️ {w}</div>
                    """, unsafe_allow_html=True)

    # Detected skills
    data = st.session_state.resume_data
    if data and not data.get("error"):
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="cs-section-header">
            <span class="cs-section-title">Detected Skills</span>
        </div>
        """, unsafe_allow_html=True)

        # skill_count from data or from detected_skills
        detected = data.get("detected_skills", {})
        # Normalize — could be flat list or dict of categories
        if isinstance(detected, dict):
            categories = detected
        else:
            categories = {"skills": detected}

        if categories:
            cat_cols = st.columns(min(len(categories), 3))
            for i, (cat, skills) in enumerate(categories.items()):
                col = cat_cols[i % len(cat_cols)]
                icon = SKILL_CATEGORY_ICONS.get(cat, "📌")
                pills = "".join(
                    f'<span class="cs-skill-pill matched">✓ {s}</span>'
                    for s in (skills if isinstance(skills, list) else [skills])
                )
                col.markdown(f"""
                <div style="background:white;border-radius:14px;padding:16px;
                            border:1px solid #E2E8F0;margin-bottom:12px;">
                    <div style="font-size:13px;font-weight:700;color:#0D1B2A;margin-bottom:10px;">
                        {icon} {cat.replace('_',' ').title()}
                    </div>
                    <div>{pills}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No skills detected. Try uploading a more detailed resume.")

        # Missing required skills
        missing = data.get("required_missing", [])
        if missing:
            st.markdown("""
            <div class="cs-section-header" style="margin-top:8px;">
                <span class="cs-section-title">Missing Required Skills</span>
            </div>
            """, unsafe_allow_html=True)
            pills = "".join(
                f'<span class="cs-skill-pill missing">✗ {s}</span>'
                for s in missing[:15]
            )
            st.markdown(f"""
            <div style="background:white;border-radius:14px;padding:16px;border:1px solid #E2E8F0;">
                {pills}
            </div>
            """, unsafe_allow_html=True)
