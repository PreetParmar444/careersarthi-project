from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from utils.backend import get_applications, run_agent_pipeline

STATUS_COLORS = {
    "applied":     ("#1A73E8", "#EEF2FF"),
    "assessment":  ("#F59E0B", "#FFFBEB"),
    "shortlisted": ("#8B5CF6", "#F5F3FF"),
    "interview":   ("#00C896", "#F0FDF9"),
    "offer":       ("#10B981", "#ECFDF5"),
    "rejected":    ("#FF6B6B", "#FFF1F2"),
}

def status_badge(status: str) -> str:
    color, bg = STATUS_COLORS.get(status, ("#64748B", "#F1F5F9"))
    label = status.title()
    return f'<span style="background:{bg};color:{color};padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;">{label}</span>'

def render():
    st.markdown("""
    <div class="cs-section-header">
        <span style="font-size:24px;">📧</span>
        <span class="cs-section-title">Applications</span>
    </div>
    """, unsafe_allow_html=True)

    apps = get_applications()

    # Filters
    filter_col, search_col, sort_col = st.columns([3, 4, 3])
    with filter_col:
        all_statuses = sorted({a.get("status","") for a in apps if a.get("status")})
        status_filter = st.multiselect("Status", all_statuses, placeholder="All statuses")
    with search_col:
        search_q = st.text_input("Search", placeholder="Search company or role...", label_visibility="collapsed")
    with sort_col:
        sort_by = st.selectbox("Sort by", ["Updated (newest)", "Company A-Z", "Deadline"], label_visibility="collapsed")

    # Apply filters
    filtered = apps
    if status_filter:
        filtered = [a for a in filtered if a.get("status") in status_filter]
    if search_q:
        q = search_q.lower()
        filtered = [a for a in filtered if q in a.get("company","").lower() or q in a.get("role","").lower()]
    if sort_by == "Company A-Z":
        filtered = sorted(filtered, key=lambda x: x.get("company",""))
    elif sort_by == "Deadline":
        filtered = sorted(filtered, key=lambda x: x.get("deadline","") or "9999")

    # Summary pills
    st.markdown("<div style='margin:12px 0 20px;'>", unsafe_allow_html=True)
    pill_cols = st.columns(len(STATUS_COLORS))
    status_counts = {s: len([a for a in apps if a.get("status") == s]) for s in STATUS_COLORS}
    for i, (status, (color, bg)) in enumerate(STATUS_COLORS.items()):
        count = status_counts.get(status, 0)
        pill_cols[i].markdown(f"""
        <div style="background:{bg};border-radius:12px;padding:12px;text-align:center;">
            <div style="font-size:22px;font-weight:800;color:{color};">{count}</div>
            <div style="font-size:11px;color:{color};font-weight:600;margin-top:2px;">{status.title()}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Applications table
    if not filtered:
        st.markdown("""
        <div style="text-align:center;padding:48px;background:white;border-radius:16px;
                    border:1px solid #E2E8F0;">
            <div style="font-size:40px;margin-bottom:12px;">📭</div>
            <div style="font-size:16px;font-weight:600;color:#0D1B2A;">No applications found</div>
            <div style="font-size:13px;color:#64748B;margin-top:6px;">
                Try adjusting your filters, or scan your Gmail inbox to import applications.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for app in filtered:
            status = app.get("status", "applied")
            color, bg = STATUS_COLORS.get(status, ("#64748B", "#F1F5F9"))
            deadline = app.get("deadline","")
            notes = app.get("extra", {}).get("notes", "")

            st.markdown(f"""
            <div style="background:#FFFFFF;border-radius:14px;border:1px solid #E8EDF3;
                        padding:16px 20px;margin-bottom:10px;
                        box-shadow:0 1px 3px rgba(0,0,0,0.05);
                        display:flex;align-items:center;gap:18px;">
                <div style="width:44px;height:44px;background:{bg};border-radius:12px;
                            display:flex;align-items:center;justify-content:center;
                            font-size:20px;flex-shrink:0;">🏢</div>
                <div style="flex:1;min-width:0;">
                    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                        <span style="font-weight:700;font-size:15px;color:#0D1B2A;">{app.get('company','—')}</span>
                        {status_badge(status)}
                    </div>
                    <div style="font-size:13px;color:#475569;margin-top:3px;">
                        {app.get('role','—')} · {app.get('portal','') or 'Direct'}
                    </div>
                    {f'<div style="font-size:11px;color:#94A3B8;margin-top:4px;font-style:italic;">{notes}</div>' if notes else ''}
                </div>
                <div style="text-align:right;flex-shrink:0;">
                    <div style="font-size:12px;color:#64748B;">Applied</div>
                    <div style="font-size:13px;font-weight:600;color:#0D1B2A;">{app.get('applied_on','—')}</div>
                    {f'<div style="font-size:11px;color:{color};font-weight:600;margin-top:4px;">Due {deadline}</div>' if deadline else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Scan inbox CTA
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:linear-gradient(135deg,#EEF2FF,#F0FDF9);border-radius:16px;
                padding:24px;border:1px solid rgba(26,115,232,0.12);text-align:center;">
        <div style="font-size:16px;font-weight:700;color:#0D1B2A;margin-bottom:6px;">
            📬 Missing applications?
        </div>
        <div style="font-size:13px;color:#64748B;margin-bottom:16px;">
            Connect Gmail to automatically find and track job applications from your inbox.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("📧 Scan Gmail Inbox", type="primary", use_container_width=False):
        with st.spinner("Scanning Gmail for job applications..."):
            response, steps = run_agent_pipeline("Scan my Gmail inbox for job applications")
        st.success("Inbox scan complete!")
        st.markdown(f"""
        <div class="cs-bubble-ai" style="margin-top:12px;">
            <div class="cs-agent-tag">📥 Inbox Tracker</div>
            {response.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

    # Status breakdown chart
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="cs-section-header">
        <span class="cs-section-title">Status Breakdown</span>
    </div>
    """, unsafe_allow_html=True)

    df = pd.DataFrame([
        {"Status": s.title(), "Count": c, "Color": STATUS_COLORS[s][0]}
        for s, c in status_counts.items() if c > 0
    ])
    if not df.empty:
        fig = px.pie(df, names="Status", values="Count",
                     color_discrete_sequence=[STATUS_COLORS[s.lower()][0] for s in df["Status"].str.lower()])
        fig.update_traces(textposition="inside", textinfo="percent+label",
                         hole=0.45, marker=dict(line=dict(color="white", width=2)))
        fig.update_layout(
            showlegend=True, height=280,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", size=12),
            legend=dict(orientation="v", x=1, xanchor="left"),
        )
        c1, c2 = st.columns([3, 2])
        with c1:
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            for s, (color, bg) in STATUS_COLORS.items():
                count = status_counts.get(s, 0)
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:8px 0;
                            border-bottom:1px solid #F1F5F9;">
                    <div style="width:10px;height:10px;border-radius:2px;background:{color};flex-shrink:0;"></div>
                    <span style="font-size:13px;color:#475569;flex:1;">{s.title()}</span>
                    <span style="font-weight:700;font-size:14px;color:#0D1B2A;">{count}</span>
                </div>
                """, unsafe_allow_html=True)