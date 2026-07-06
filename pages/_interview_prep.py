from __future__ import annotations
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from utils.backend import get_interview_prep, get_applications

KNOWN_COMPANIES = ["Turing", "Toptal", "Wellfound", "Deloitte", "Google", "Amazon", "Microsoft", "Meta", "Infosys", "Wipro"]

def render():
    st.markdown("""
    <div class="cs-section-header">
        <span style="font-size:24px;">🎤</span>
        <span class="cs-section-title">Interview Prep</span>
    </div>
    """, unsafe_allow_html=True)

    # Company selector
    apps = get_applications()
    tracked_companies = list({a.get("company","") for a in apps if a.get("company")})
    all_companies = sorted(set(tracked_companies + KNOWN_COMPANIES))

    sel_col, role_col, gen_col = st.columns([4, 4, 2])
    with sel_col:
        company = st.selectbox("Company", all_companies, label_visibility="collapsed")
    with role_col:
        role = st.text_input("Role (optional)", placeholder="Data Engineer, ML Scientist...", label_visibility="collapsed")
    with gen_col:
        generate = st.button("🎯 Generate", type="primary", use_container_width=True)

    if "prep_data" not in st.session_state:
        st.session_state.prep_data = None
        st.session_state.prep_company = ""

    if generate or (company and company != st.session_state.prep_company):
        with st.spinner(f"Generating interview prep for {company}..."):
            data = get_interview_prep(company, role)
            st.session_state.prep_data = data
            st.session_state.prep_company = company

    data = st.session_state.prep_data
    if not data:
        # Landing state
        st.markdown("""
        <div style="text-align:center;padding:48px 24px;background:white;border-radius:20px;
                    border:1px solid #E2E8F0;margin-top:16px;">
            <div style="font-size:56px;margin-bottom:16px;">🎤</div>
            <div style="font-size:18px;font-weight:700;color:#0D1B2A;margin-bottom:8px;">
                Select a company to start prepping
            </div>
            <div style="font-size:13px;color:#64748B;max-width:400px;margin:0 auto;">
                CareerSarthi knows the interview patterns for Turing, Toptal, Wellfound,
                Deloitte, and more. Pick a company and get a tailored prep brief.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Quick company tiles
        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
        cols = st.columns(4)
        quick_cos = [("🔵", "Turing"), ("🟣", "Toptal"), ("🟢", "Wellfound"), ("🔷", "Deloitte")]
        for i, (icon, co) in enumerate(quick_cos):
            with cols[i]:
                if st.button(f"{icon} {co}", use_container_width=True):
                    data = get_interview_prep(co, "")
                    st.session_state.prep_data = data
                    st.session_state.prep_company = co
                    st.rerun()
        return

    company_name = st.session_state.prep_company

    # Header card
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0D1B2A,#1A3356);border-radius:20px;
                padding:32px;color:#FFFFFF !important;margin:16px 0 24px;">
        <div style="font-size:28px;margin-bottom:8px;color:#FFFFFF !important;">🎤</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:700;
                    color:#FFFFFF !important;">
            {company_name} Interview Prep
        </div>
        <div style="font-size:14px;opacity:0.80;margin-top:6px;color:rgba(255,255,255,0.80) !important;">
            {data.get('format','—')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Focus areas + Tips
    top_col, tip_col = st.columns([6, 4], gap="large")

    with top_col:
        st.markdown("""
        <div class="cs-section-header">
            <span class="cs-section-title">Focus Areas</span>
        </div>
        """, unsafe_allow_html=True)
        focus = data.get("focus", [])
        for i, area in enumerate(focus, 1):
            colors = ["#1A73E8", "#00C896", "#F59E0B"]
            color = colors[(i-1) % len(colors)]
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:14px;padding:14px 18px;
                        background:white;border-radius:12px;margin-bottom:10px;
                        border-left:4px solid {color};box-shadow:0 1px 4px rgba(0,0,0,0.05);">
                <div style="width:28px;height:28px;border-radius:8px;background:{color}18;
                            display:flex;align-items:center;justify-content:center;
                            font-weight:800;font-size:14px;color:{color};flex-shrink:0;">{i}</div>
                <div style="font-size:14px;font-weight:600;color:#0D1B2A;">{area}</div>
            </div>
            """, unsafe_allow_html=True)

    with tip_col:
        st.markdown("""
        <div class="cs-section-header">
            <span class="cs-section-title">💡 Insider Tip</span>
        </div>
        """, unsafe_allow_html=True)
        tip = data.get("tips","")
        st.markdown(f"""
        <div style="background:#FFFBEB;border-radius:14px;padding:20px;
                    border:1px solid rgba(245,158,11,0.20);">
            <div style="font-size:32px;margin-bottom:10px;">💡</div>
            <div style="font-size:13px;color:#78350F;line-height:1.6;">{tip}</div>
        </div>
        """, unsafe_allow_html=True)

    # Interview Questions
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="cs-section-header">
        <span class="cs-section-title">Interview Questions</span>
    </div>
    """, unsafe_allow_html=True)

    questions = data.get("questions") or data.get("question_categories", {})
    if questions:
        tab_names = []
        tab_data = []

        tech = questions.get("technical") or questions.get("technical_core", [])
        beh = questions.get("behavioral", [])
        coding = questions.get("coding", [])
        gaps = questions.get("gap_focused", [])

        if tech: tab_names.append("💻 Technical"); tab_data.append(tech)
        if beh: tab_names.append("💬 Behavioral"); tab_data.append(beh)
        if coding: tab_names.append("🖥️ Coding"); tab_data.append(coding)
        if gaps: tab_names.append("🎯 Gap-Focused"); tab_data.append(gaps)

        if tab_names:
            tabs = st.tabs(tab_names)
            icons = {"💻 Technical": "⚙️", "💬 Behavioral": "💬", "🖥️ Coding": "💻", "🎯 Gap-Focused": "🎯"}
            for tab, name, q_list in zip(tabs, tab_names, tab_data):
                with tab:
                    for i, q in enumerate(q_list, 1):
                        st.markdown(f"""
                        <div style="padding:14px 18px;background:white;border-radius:12px;
                                    margin-bottom:8px;border:1px solid #E2E8F0;
                                    display:flex;gap:12px;align-items:flex-start;">
                            <div style="width:24px;height:24px;border-radius:6px;background:#EEF2FF;
                                        display:flex;align-items:center;justify-content:center;
                                        font-size:11px;font-weight:700;color:#1A73E8;flex-shrink:0;">
                                Q{i}
                            </div>
                            <div style="font-size:13px;color:#0D1B2A;line-height:1.6;">{q}</div>
                        </div>
                        """, unsafe_allow_html=True)

    # Resources
    resources = data.get("resources", [])
    if resources:
        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="cs-section-header">
            <span class="cs-section-title">📚 Resources</span>
        </div>
        """, unsafe_allow_html=True)
        res_cols = st.columns(min(len(resources), 3))
        for i, res in enumerate(resources):
            res_cols[i % len(res_cols)].markdown(f"""
            <div style="background:#EEF2FF;border-radius:12px;padding:14px;text-align:center;
                        border:1px solid rgba(26,115,232,0.15);">
                <div style="font-size:20px;margin-bottom:6px;">📖</div>
                <div style="font-size:12px;font-weight:600;color:#1A73E8;">{res}</div>
            </div>
            """, unsafe_allow_html=True)

    # STAR story generator
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    with st.expander("✨ STAR Story Prompt Generator", expanded=False):
        st.markdown("""
        <div style="font-size:13px;color:#475569;margin-bottom:12px;">
            Use this framework to prepare compelling behavioral answers:
        </div>
        """, unsafe_allow_html=True)
        for letter, word, prompt_text in [
            ("S", "Situation", "Set the scene — what was the context, team size, and timeline?"),
            ("T", "Task", "What were you specifically responsible for?"),
            ("A", "Action", "What did YOU do? Focus on your decisions, not the team's."),
            ("R", "Result", "What was the measurable outcome? (%, $, time saved...)"),
        ]:
            st.markdown(f"""
            <div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #F1F5F9;">
                <div style="width:32px;height:32px;border-radius:8px;background:#1A73E8;
                            display:flex;align-items:center;justify-content:center;
                            font-weight:800;font-size:14px;color:white;flex-shrink:0;">{letter}</div>
                <div>
                    <div style="font-weight:700;font-size:13px;color:#0D1B2A;">{word}</div>
                    <div style="font-size:12px;color:#64748B;margin-top:2px;">{prompt_text}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)