from __future__ import annotations
import streamlit as st
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timezone
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from utils.backend import get_deadlines, run_agent_pipeline

def render():
    st.markdown("""
    <div class="cs-section-header">
        <span style="font-size:24px;">📅</span>
        <span class="cs-section-title">Deadline Tracker</span>
    </div>
    """, unsafe_allow_html=True)

    deadlines = get_deadlines()

    if st.button("🔄 Refresh Deadlines", type="primary"):
        with st.spinner("Checking deadlines..."):
            response, _ = run_agent_pipeline("What deadlines are coming up?")
        st.info(response[:300] + "..." if len(response) > 300 else response)

    # Summary row
    critical = [d for d in deadlines if "critical" in d.get("urgency","")]
    upcoming = [d for d in deadlines if "upcoming" in d.get("urgency","")]
    onradar = [d for d in deadlines if "on radar" in d.get("urgency","")]
    overdue = [d for d in deadlines if "overdue" in d.get("urgency","")]

    s1, s2, s3, s4 = st.columns(4)
    for col, count, label, color, bg, icon in [
        (s1, len(overdue), "Overdue", "#FF6B6B", "#FFF1F2", "⚫"),
        (s2, len(critical), "Critical (≤3d)", "#FF6B6B", "#FFF1F2", "🔴"),
        (s3, len(upcoming), "Upcoming (≤7d)", "#F59E0B", "#FFFBEB", "🟡"),
        (s4, len(onradar), "On Radar (≤14d)", "#00C896", "#F0FDF9", "🟢"),
    ]:
        col.markdown(f"""
        <div style="background:{bg};border-radius:16px;padding:20px;text-align:center;
                    border:1px solid {color}22;">
            <div style="font-size:24px;">{icon}</div>
            <div style="font-size:32px;font-weight:800;color:{color};font-family:'Space Grotesk',sans-serif;margin-top:4px;">{count}</div>
            <div style="font-size:11px;color:{color};font-weight:600;margin-top:2px;">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    if not deadlines:
        st.markdown("""
        <div style="text-align:center;padding:48px;background:white;border-radius:16px;
                    border:1px solid #E2E8F0;">
            <div style="font-size:40px;">🎉</div>
            <div style="font-size:16px;font-weight:600;color:#0D1B2A;margin-top:12px;">No deadlines tracked</div>
            <div style="font-size:13px;color:#64748B;margin-top:6px;">
                Add applications with deadlines to see them here.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Timeline view
    left_col, right_col = st.columns([6, 4], gap="large")

    with left_col:
        st.markdown("""
        <div class="cs-section-header">
            <span class="cs-section-title">Urgency Timeline</span>
        </div>
        """, unsafe_allow_html=True)

        for d in deadlines:
            urgency = d.get("urgency","")
            days = d.get("days_remaining", 0)
            status = d.get("status","")

            if "overdue" in urgency:
                color, bg, dot_bg, icon = "#FF6B6B", "#FFF1F2", "#FFE4E6", "⚫"
                label = "OVERDUE"
            elif "critical" in urgency:
                color, bg, dot_bg, icon = "#FF6B6B", "#FFF1F2", "#FFE4E6", "🔴"
                label = f"{days}d left"
            elif "upcoming" in urgency:
                color, bg, dot_bg, icon = "#F59E0B", "#FFFBEB", "#FEF3C7", "🟡"
                label = f"{days}d left"
            elif "on radar" in urgency:
                color, bg, dot_bg, icon = "#00C896", "#F0FDF9", "#D1FAE5", "🟢"
                label = f"{days}d left"
            else:
                color, bg, dot_bg, icon = "#64748B", "#F8FAFD", "#F1F5F9", "⚪"
                label = f"{days}d left"

            status_html = f'<span style="background:{bg};color:{color};padding:2px 8px;border-radius:12px;font-size:10px;font-weight:700;">{status.upper()}</span>'

            deadline_str = d.get("deadline","")
            try:
                dl_dt = datetime.fromisoformat(deadline_str)
                dl_formatted = dl_dt.strftime("%b %d, %Y")
            except Exception:
                dl_formatted = deadline_str

            st.markdown(f"""
            <div style="display:flex;gap:16px;padding:16px 0;
                        border-bottom:1px solid #F1F5F9;align-items:flex-start;">
                <div style="width:40px;height:40px;border-radius:50%;background:{dot_bg};
                            display:flex;align-items:center;justify-content:center;
                            font-size:18px;flex-shrink:0;">{icon}</div>
                <div style="flex:1;">
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                        <span style="font-weight:700;font-size:15px;color:#0D1B2A;">{d.get('company','')}</span>
                        {status_html}
                    </div>
                    <div style="font-size:12px;color:#64748B;margin-top:3px;">{d.get('role','')}</div>
                    <div style="font-size:11px;color:{color};font-weight:600;margin-top:6px;">
                        📅 {dl_formatted}
                    </div>
                </div>
                <div style="text-align:right;flex-shrink:0;">
                    <div style="font-size:20px;font-weight:800;color:{color};
                                font-family:'Space Grotesk',sans-serif;">{label}</div>
                    <div style="font-size:10px;color:#94A3B8;margin-top:2px;">
                        {urgency.split(' ',1)[-1] if ' ' in urgency else urgency}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with right_col:
        # Gantt-style calendar
        st.markdown("""
        <div class="cs-section-header">
            <span class="cs-section-title">Calendar View</span>
        </div>
        """, unsafe_allow_html=True)

        now = datetime.now(timezone.utc)

        fig = go.Figure()
        for i, d in enumerate(deadlines[:8]):
            days = d.get("days_remaining", 0)
            urgency = d.get("urgency","")
            color = "#FF6B6B" if "critical" in urgency or "overdue" in urgency else \
                    "#F59E0B" if "upcoming" in urgency else \
                    "#00C896" if "on radar" in urgency else "#94A3B8"

            fig.add_trace(go.Bar(
                name=d.get("company",""),
                y=[f"{d.get('company','')} – {d.get('role','')}"],
                x=[max(days, 1)],
                orientation="h",
                marker=dict(color=color, line=dict(color="white", width=1.5)),
                text=f"{max(days,0)}d",
                textposition="inside",
                showlegend=False,
                hovertemplate=f"<b>{d.get('company','')}</b><br>{max(days,0)} days remaining<extra></extra>",
            ))

        fig.update_layout(
            barmode="overlay",
            height=max(200, len(deadlines[:8]) * 44),
            margin=dict(l=0, r=10, t=10, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Days remaining", gridcolor="#F1F5F9", zeroline=False),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=11)),
            font=dict(family="Inter", size=11),
        )
        # Add urgency zone lines
        fig.add_vline(x=3, line_dash="dot", line_color="#FF6B6B", opacity=0.5,
                      annotation_text="3d", annotation_font_size=10)
        fig.add_vline(x=7, line_dash="dot", line_color="#F59E0B", opacity=0.5,
                      annotation_text="7d", annotation_font_size=10)

        st.plotly_chart(fig, use_container_width=True)

        # Action CTA
        st.markdown("""
        <div style="background:linear-gradient(135deg,#EEF2FF,#F0FDF9);border-radius:14px;
                    padding:20px;border:1px solid rgba(26,115,232,0.12);margin-top:8px;">
            <div style="font-weight:700;font-size:14px;color:#0D1B2A;margin-bottom:6px;">
                📆 Add Calendar Reminders
            </div>
            <div style="font-size:12px;color:#64748B;margin-bottom:12px;">
                Automatically create Google Calendar events for critical deadlines.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📆 Sync to Google Calendar", use_container_width=True):
            with st.spinner("Creating calendar events..."):
                response, _ = run_agent_pipeline("Add calendar reminders for all critical deadlines")
            st.success("Calendar events created!")
