from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from utils.backend import get_skill_gap

def render():
    st.markdown("""
    <div class="cs-section-header">
        <span style="font-size:24px;">🎯</span>
        <span class="cs-section-title">Skill Gap Analyzer</span>
    </div>
    """, unsafe_allow_html=True)

    col_input, col_action = st.columns([7, 3])
    with col_input:
        company_input = st.text_input("Company", placeholder="Turing, Deloitte, Google...", label_visibility="collapsed")
    with col_action:
        analyze = st.button("🔍 Analyze Gaps", type="primary", use_container_width=True)

    jd_text = st.text_area("Job Description", height=100, label_visibility="collapsed",
                            placeholder="Paste the job description to run a precise gap analysis...")

    data = get_skill_gap(jd_text=jd_text) if (analyze and jd_text) else get_skill_gap()

    ats = data.get("ats_score", 68)
    match = data.get("match_score", 62.5)
    grade = data.get("grade", "B")
    grade_color = {"A": "#00C896", "B": "#1A73E8", "C": "#F59E0B", "D": "#FF6B6B"}.get(grade, "#64748B")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Score cards
    s1, s2, s3 = st.columns(3)

    # ATS Gauge
    with s1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=ats,
            title={"text": "ATS Score", "font": {"size": 14, "family": "Inter", "color": "black"}},
            number={"suffix": "/100", "font": {"size": 28, "family": "Space Grotesk", "color": grade_color}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#E2E8F0"},
                "bar": {"color": grade_color, "thickness": 0.3},
                "bgcolor": "#F8FAFD",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "#FFF1F2"},
                    {"range": [50, 65], "color": "#FFFBEB"},
                    {"range": [65, 80], "color": "#EEF2FF"},
                    {"range": [80, 100], "color": "#F0FDF9"},
                ],
                "threshold": {"line": {"color": grade_color, "width": 3}, "thickness": 0.8, "value": ats},
            },
        ))
        fig.update_layout(height=200, margin=dict(l=20,r=20,t=40,b=0),
                         paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"))
        s1.plotly_chart(fig, use_container_width=True)

    # Match score
    with s2:
        fig2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=match,
            title={"text": "JD Match Score", "font": {"size": 14, "family": "Inter"}},
            number={"suffix": "%", "font": {"size": 28, "family": "Space Grotesk", "color": "#1A73E8"}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#1A73E8", "thickness": 0.3},
                "bgcolor": "#F8FAFD",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "#FFF1F2"},
                    {"range": [40, 70], "color": "#FFFBEB"},
                    {"range": [70, 100], "color": "#F0FDF9"},
                ],
            },
        ))
        fig2.update_layout(height=200, margin=dict(l=20,r=20,t=40,b=0),
                          paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"))
        s2.plotly_chart(fig2, use_container_width=True)

    with s3:
        matched_count = len(data.get("matched", []))
        missing_count = len(data.get("required_missing", []))
        total = matched_count + missing_count or 1

        fig3 = go.Figure(data=[go.Pie(
            labels=["Matched", "Missing Required", "Nice-to-Have Gap"],
            values=[matched_count, missing_count, len(data.get("nice_missing",[]))],
            hole=0.55,
            marker=dict(colors=["#00C896", "#FF6B6B", "#F59E0B"],
                       line=dict(color="white", width=2)),
            textinfo="percent",
        )])
        fig3.update_layout(
            height=200, showlegend=False,
            margin=dict(l=0,r=0,t=20,b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(text=f"<b>{matched_count}/{matched_count+missing_count}</b><br>matched",
                            x=0.5, y=0.5, font=dict(size=12, family="Space Grotesk"), showarrow=False)],
        )
        s3.plotly_chart(fig3, use_container_width=True)
        s3.markdown(f'<div style="text-align:center;font-size:12px;color:#64748B;margin-top:-12px;">Grade <b style="color:{grade_color}">{grade}</b></div>', unsafe_allow_html=True)

    # Skills columns
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("""
        <div class="cs-section-header">
            <span style="font-size:18px;">✅</span>
            <span class="cs-section-title" style="font-size:16px;">Matched Skills</span>
        </div>
        """, unsafe_allow_html=True)
        matched = data.get("matched", [])
        if matched:
            pills = " ".join(f'<span class="cs-skill-pill matched">✓ {s}</span>' for s in matched)
            st.markdown(f'<div style="line-height:2.2;">{pills}</div>', unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="cs-section-header">
            <span style="font-size:18px;">❌</span>
            <span class="cs-section-title" style="font-size:16px;">Missing Required Skills</span>
        </div>
        """, unsafe_allow_html=True)
        missing = data.get("required_missing", [])
        if missing:
            pills = " ".join(f'<span class="cs-skill-pill missing">✗ {s}</span>' for s in missing)
            st.markdown(f'<div style="line-height:2.2;">{pills}</div>', unsafe_allow_html=True)

    # Learning Roadmap
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="cs-section-header">
        <span style="font-size:24px;">🗺️</span>
        <span class="cs-section-title">Learning Roadmap</span>
    </div>
    """, unsafe_allow_html=True)

    recommendations = data.get("recommendations", [])
    if recommendations:
        week_skills = recommendations[:3]
        month_skills = recommendations[3:6]
        nice_skills = data.get("nice_missing", [])[:3]

        r1, r2, r3 = st.columns(3)
        roadmap_data = [
            (r1, "🔴", "This Week", "Critical — required by most JDs", week_skills, "#FF6B6B", "#FFF1F2"),
            (r2, "🟡", "This Month", "Required but less urgent", month_skills, "#F59E0B", "#FFFBEB"),
            (r3, "🟢", "Nice to Have", "Strengthen your profile", nice_skills, "#00C896", "#F0FDF9"),
        ]
        for col, emoji, title, subtitle, skills, color, bg in roadmap_data:
            skill_items = "".join(
                f'<div style="padding:8px 10px;background:white;border-radius:8px;'
                f'font-size:12px;font-weight:600;color:#0D1B2A;margin:4px 0;'
                f'border-left:3px solid {color};">{s}</div>'
                for s in skills
            ) if skills else f'<div style="color:#94A3B8;font-size:12px;font-style:italic;">None identified</div>'

            col.markdown(f"""
            <div style="background:{bg};border-radius:16px;padding:20px;
                        border:1px solid {color}22;height:100%;">
                <div style="font-size:22px;margin-bottom:4px;">{emoji}</div>
                <div style="font-weight:700;font-size:15px;color:#0D1B2A;">{title}</div>
                <div style="font-size:11px;color:#64748B;margin-bottom:12px;">{subtitle}</div>
                {skill_items}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Upload a resume and paste a job description to generate your personalized learning roadmap.")

    # Warnings
    warnings = data.get("warnings", [])
    if warnings:
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="cs-section-header">
            <span class="cs-section-title">Resume Formatting Tips</span>
        </div>
        """, unsafe_allow_html=True)
        for w in warnings:
            st.markdown(f"""
            <div style="background:#FFFBEB;border-radius:10px;padding:12px 16px;
                        border-left:3px solid #F59E0B;font-size:13px;color:#92400E;
                        margin-bottom:8px;">⚠️ {w}</div>
            """, unsafe_allow_html=True)
