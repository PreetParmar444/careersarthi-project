"""
frontend/app.py
────────────────
CareerSarthi — AI Career Assistant Dashboard
Run: streamlit run frontend/app.py

NOTE ON THE FIX APPLIED HERE
─────────────────────────────
The previous version opened a raw <div class="cs-panel"> with st.markdown(),
then called other Streamlit widgets (st.button, st.plotly_chart, st.form...)
before closing the div in a later st.markdown() call. Streamlit renders every
widget as its own sibling element in the DOM — it does NOT nest widgets inside
an unclosed HTML tag from a previous call. That's why the cards rendered as
empty white boxes with the real content spilling out unstyled underneath.

The fix: wrap each group of widgets in st.container(key="some_key"), which
Streamlit renders as a real container with a `.st-key-some_key` class you can
target in CSS. See styles/main.css for the matching rules.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
from pathlib import Path

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CareerSarthi — AI Career Co-Pilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
css_path = Path(__file__).parent / "styles" / "main.css"
if css_path.exists():
    css_text = css_path.read_text()
    if css_text.strip():
        st.markdown(f"<style>{css_text}</style>", unsafe_allow_html=True)
    else:
        st.error(f"⚠️ CSS file found but is EMPTY: {css_path}")
else:
    # Fail loudly instead of silently doing nothing — this is the #1 cause
    # of "my styling isn't applying". Shows exactly where Python looked.
    st.error(
        f"⚠️ CSS file not found at: {css_path}\n\n"
        f"__file__ resolves to: {Path(__file__).resolve()}\n\n"
        f"Expected structure: frontend/app.py + frontend/styles/main.css"
    )

# ── Backend ────────────────────────────────────────────────────────────────────
from utils.backend import get_kpis, run_agent_pipeline, get_applications, get_deadlines

# ── Session state ──────────────────────────────────────────────────────────────
for k, v in [("chat_history", []), ("active_page", "Dashboard"), ("dark_mode", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:4px 4px 28px;display:flex;align-items:center;gap:12px;">
        <div style="width:42px;height:42px;background:linear-gradient(135deg,#1A73E8,#00C896);
                    border-radius:13px;display:flex;align-items:center;justify-content:center;
                    font-size:22px;flex-shrink:0;box-shadow:0 4px 12px rgba(26,115,232,0.35);">🚀</div>
        <div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:17px;font-weight:700;
                        color:#F1F5F9;line-height:1.15;">CareerSarthi</div>
            <div style="font-size:9.5px;color:#64748B;font-weight:500;letter-spacing:0.08em;
                        text-transform:uppercase;margin-top:1px;">AI Career Co-Pilot</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:9.5px;color:#475569;text-transform:uppercase;'
                'letter-spacing:0.1em;padding:0 4px;margin-bottom:6px;font-weight:600;">Main</div>',
                unsafe_allow_html=True)

    nav_items = [
        ("🏠", "Dashboard"),
        ("📧", "Applications"),
        ("📄", "Resume"),
        ("🎯", "Skill Gap"),
        ("📅", "Deadlines"),
        ("🎤", "Interview Prep"),
        ("🔒", "Privacy"),
        ("⚙️", "Settings"),
    ]
    for icon, name in nav_items:
        active = st.session_state.active_page == name
        if active:
            st.markdown(f"""
            <div style="background:rgba(26,115,232,0.18);border-radius:10px;
                        padding:9px 14px;margin:2px 0;color:#60A5FA;
                        font-size:13.5px;font-weight:600;font-family:'Inter',sans-serif;
                        display:flex;align-items:center;gap:10px;
                        border-left:3px solid #3B82F6;cursor:default;user-select:none;">
                {icon}&nbsp;&nbsp;{name}
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(f"{icon}  {name}", key=f"nav_{name}", use_container_width=True):
                st.session_state.active_page = name
                st.rerun()

    st.markdown('<div style="height:1px;background:rgba(255,255,255,0.08);margin:20px 0;"></div>',
                unsafe_allow_html=True)
    st.markdown('<div style="font-size:9.5px;color:#475569;text-transform:uppercase;'
                'letter-spacing:0.1em;padding:0 4px;margin-bottom:8px;font-weight:600;">Preferences</div>',
                unsafe_allow_html=True)

    dark = st.toggle("Dark mode", value=st.session_state.dark_mode)
    if dark != st.session_state.dark_mode:
        st.session_state.dark_mode = dark
        st.rerun()

    st.markdown('<div style="height:1px;background:rgba(255,255,255,0.08);margin:20px 0;"></div>',
                unsafe_allow_html=True)

    try:
        from careersarthi.utils.storage import get_all_applications as _test
        ok = True
    except Exception:
        ok = False

    dot_color = "#00C896" if ok else "#F59E0B"
    dot_label = "Live backend" if ok else "Demo mode"
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.06);border-radius:10px;padding:12px 14px;
                border:1px solid rgba(255,255,255,0.09);">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
            <div style="width:7px;height:7px;border-radius:50%;background:{dot_color};
                        box-shadow:0 0 6px {dot_color};flex-shrink:0;"></div>
            <span style="font-size:12px;color:#CBD5E1;font-weight:500;">{dot_label}</span>
        </div>
        <div style="font-size:10.5px;color:#64748B;padding-left:15px;line-height:1.5;">
            Google ADK · Gemini 2.0 Flash
        </div>
    </div>
    <div style="margin-top:18px;padding:0 2px;">
        <div style="font-size:10px;color:#475569;line-height:1.7;">
            © 2025 CareerSarthi<br>Built with Google ADK
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
page = st.session_state.active_page

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":

    # Hero
    st.markdown("""
    <div class="cs-hero">
        <h1 class="cs-hero-title" style="color:black;">CareerSarthi 🚀</h1>
        <h2 class="cs-hero-sub" style='color:black;'>AI-Powered Career Assistant — Google ADK Multi-Agent System</h2>
        <h3 class="cs-hero-sub" style="margin-top:5px;font-size:12.5px;opacity:0.65;color:black;">
            Inbox Tracker &nbsp;·&nbsp; Skill Gap Analyzer &nbsp;·&nbsp;
            Deadline Guardian &nbsp;·&nbsp; Interview Prep &nbsp;·&nbsp; Privacy Guardian
        </h3>
        
    </div>
    """, unsafe_allow_html=True)

    # ── KPI row ──────────────────────────────────────────────────────────────
    kpis = get_kpis()
    k1, k2, k3, k4 = st.columns(4, gap="small")

    def _kpi(col, number, label, delta, accent, icon, delta_color="#00C896"):
        col.markdown(f"""
        <div class="cs-kpi" style="--a:{accent};">
            <span class="cs-kpi-icon">{icon}</span>
            <div class="cs-kpi-num">{number}</div>
            <div class="cs-kpi-lbl">{label}</div>
            <div class="cs-kpi-delta" style="color:{delta_color};">{delta}</div>
        </div>
        """, unsafe_allow_html=True)

    _kpi(k1, kpis["total_applications"], "Applications Tracked",
         "↑ 2 this week", "#1A73E8", "📧")
    _kpi(k2, kpis["critical_deadlines"], "Critical Deadlines",
         "Requires attention", "#FF6B6B", "⏰", delta_color="#FF6B6B")
    _kpi(k3, f"{kpis['ats_score']:.0f}", "Avg ATS Score",
         "Grade B — improving", "#00C896", "📊")
    _kpi(k4, kpis["interviews_scheduled"], "Interviews Scheduled",
         "Active pipeline", "#F59E0B", "🎤", delta_color="#F59E0B")

    st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)

    # ── Chat + Activity ───────────────────────────────────────────────────────
    chat_col, right_col = st.columns([11, 9], gap="large")

    # ── Chat panel ────────────────────────────────────────────────────────────
    with chat_col:
        # Everything inside this container renders as real Streamlit widgets
        # nested inside a `.st-key-chat_panel` div — the CSS in main.css
        # styles that div as the white card, so nothing spills outside it.
        with st.container(key="chat_panel"):
            st.markdown("""
            <div class="cs-section-header">
                <span style="font-size:20px;">💬</span>
                <span class="cs-section-title">AI Assistant</span>
                <span class="cs-section-count">Ask anything</span>
            </div>
            """, unsafe_allow_html=True)

            if not st.session_state.chat_history:
                st.markdown("""
                <div class="cs-chat-empty">
                    <div style="font-size:48px;margin-bottom:14px;">🤖</div>
                    <div class="cs-chat-empty-title">Ready to help with your job search</div>
                    <div class="cs-chat-empty-sub">
                        Ask me anything about your applications, skill gaps, deadlines, or interview prep.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                qp_col1, qp_col2 = st.columns(2, gap="small")
                quick_prompts = [
                    ("📧", "Scan my Gmail inbox"),
                    ("🎯", "Analyze my skill gaps"),
                    ("📅", "Any urgent deadlines?"),
                    ("🎤", "Prep me for Turing interview"),
                ]
                for i, (icon, text) in enumerate(quick_prompts):
                    col = qp_col1 if i % 2 == 0 else qp_col2
                    if col.button(f"{icon} {text}", key=f"qp_{i}", use_container_width=True):
                        st.session_state.chat_history.append({"role": "user", "content": text})
                        with st.spinner("Agents working..."):
                            response, steps = run_agent_pipeline(text)
                        st.session_state.chat_history.append({
                            "role": "assistant", "content": response, "steps": steps
                        })
                        st.rerun()
            else:
                st.markdown('<div class="cs-chat-scroll">', unsafe_allow_html=True)
                for msg in st.session_state.chat_history:
                    if msg["role"] == "user":
                        st.markdown(f"""
                        <div style="display:flex;justify-content:flex-end;margin:4px 0;">
                            <div class="cs-bubble-user">{msg["content"]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        steps = msg.get("steps", [])
                        if steps:
                            with st.expander("🔧 Agent execution trace", expanded=False):
                                for step in steps:
                                    cls = "done" if step.get("done") else "active"
                                    ico = "✅" if step.get("done") else "⏳"
                                    st.markdown(f"""
                                    <div class="cs-tool-step {cls}">
                                        {ico}&nbsp; {step["label"]}
                                        <span style="margin-left:auto;font-size:11px;opacity:0.65;">
                                            {step.get("agent","")}
                                        </span>
                                    </div>
                                    """, unsafe_allow_html=True)
                        content = msg["content"].replace("\n", "<br>")
                        st.markdown(f"""
                        <div style="display:flex;justify-content:flex-start;margin:4px 0;">
                            <div class="cs-bubble-ai">
                                <div class="cs-agent-tag">🤖 CareerSarthi</div>
                                {content}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Chat input — inside the same card
            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            with st.form("chat_form", clear_on_submit=True):
                in_col, btn_col = st.columns([11, 1])
                with in_col:
                    user_input = st.text_input(
                        "msg", label_visibility="collapsed",
                        placeholder="Ask anything — 'Scan inbox', 'Prep me for Google', 'Any deadlines?'",
                    )
                with btn_col:
                    send = st.form_submit_button("➤", use_container_width=True)

            if send and user_input.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
                with st.spinner("Agents working..."):
                    response, steps = run_agent_pipeline(user_input.strip())
                st.session_state.chat_history.append({
                    "role": "assistant", "content": response, "steps": steps
                })
                st.rerun()

            if st.session_state.chat_history:
                if st.button("🗑️ Clear chat", key="clear_chat"):
                    st.session_state.chat_history = []
                    st.rerun()

    # ── Right panel: pipeline + deadlines ────────────────────────────────────
    with right_col:
        # Pipeline funnel
        with st.container(key="pipeline_panel"):
            st.markdown("""
            <div class="cs-section-header" style="margin-bottom:14px;">
                <span style="font-size:18px;">📊</span>
                <span class="cs-section-title">Pipeline</span>
            </div>
            """, unsafe_allow_html=True)

            statuses = kpis["active_statuses"]
            stage_vals = [
                statuses.get("applied", 0),
                statuses.get("assessment", 0),
                statuses.get("shortlisted", 0),
                statuses.get("interview", 0),
                statuses.get("offer", 0),
            ]
            fig_funnel = go.Figure(go.Funnel(
                y=["Applied", "Assessment", "Shortlisted", "Interview", "Offer"],
                x=stage_vals,
                textinfo="value+percent initial",
                textfont=dict(family="Inter", size=12, color="#0D1B2A"),
                marker=dict(
                    color=["#1A73E8", "#3B82F6", "#8B5CF6", "#F59E0B", "#00C896"],
                    line=dict(color="white", width=2),
                ),
                connector=dict(line=dict(color="rgba(0,0,0,0.06)", dash="dot", width=3)),
            ))
            fig_funnel.update_layout(
                margin=dict(l=0, r=0, t=4, b=4),
                height=240,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", size=12, color="#334155"),

                 yaxis=dict(
        tickfont=dict(
            color="black",   # <-- makes Applied, Assessment, etc. black
            size=12,
        )
    )
            )
            st.plotly_chart(fig_funnel, use_container_width=True, config={"displayModeBar": False})

        # Urgent deadlines
        with st.container(key="deadlines_panel"):
            st.markdown("""
            <div class="cs-section-header" style="margin-bottom:14px;">
                <span style="font-size:18px;">⏰</span>
                <span class="cs-section-title">Urgent Deadlines</span>
            </div>
            """, unsafe_allow_html=True)

            deadlines = get_deadlines()[:5]
            if deadlines:
                for d in deadlines:
                    urgency = d.get("urgency", "")
                    days = d.get("days_remaining", 0)
                    if "overdue" in urgency:
                        color, bg, icon = "#64748B", "#F1F5F9", "⚫"
                    elif "critical" in urgency:
                        color, bg, icon = "#E11D48", "#FFF1F2", "🔴"
                    elif "upcoming" in urgency:
                        color, bg, icon = "#B45309", "#FFFBEB", "🟡"
                    elif "on radar" in urgency:
                        color, bg, icon = "#059669", "#F0FDF9", "🟢"
                    else:
                        color, bg, icon = "#64748B", "#F8FAFD", "⚪"

                    days_label = "overdue" if days < 0 else f"{days}d left"
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:12px;padding:11px 13px;
                                background:{bg};border-radius:11px;margin-bottom:7px;
                                border-left:3px solid {color};">
                        <span style="font-size:15px;flex-shrink:0;">{icon}</span>
                        <div style="flex:1;min-width:0;">
                            <div style="font-weight:600;font-size:13px;color:#0D1B2A;
                                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                                {d["company"]}
                            </div>
                            <div style="font-size:11px;color:#64748B;margin-top:1px;
                                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                                {d.get("role","")}
                            </div>
                        </div>
                        <div style="font-weight:700;font-size:12.5px;color:{color};
                                    flex-shrink:0;text-align:right;">
                            {days_label}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align:center;padding:28px 16px;color:#94A3B8;">
                    <div style="font-size:28px;margin-bottom:8px;">🎉</div>
                    <div style="font-size:13px;">No urgent deadlines</div>
                </div>
                """, unsafe_allow_html=True)

            if st.button("View all deadlines →", key="view_deadlines"):
                st.session_state.active_page = "Deadlines"
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# OTHER PAGES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Applications":
    from pages._applications import render; render()

elif page == "Resume":
    from pages._resume import render; render()

elif page == "Skill Gap":
    from pages._skill_gap import render; render()

elif page == "Deadlines":
    from pages._deadlines import render; render()

elif page == "Interview Prep":
    from pages._interview_prep import render; render()

elif page == "Privacy":
    st.markdown("""
    <div class="cs-section-header">
        <span style="font-size:24px;">🔒</span>
        <span class="cs-section-title">Privacy & Security</span>
    </div>
    """, unsafe_allow_html=True)
    with st.container(key="privacy_panel"):
        if st.button("🔍 Run Privacy Audit", type="primary"):
            with st.spinner("Checking audit log..."):
                response, steps = run_agent_pipeline("Show me the audit log and confirm my data is safe.")
            st.markdown(f"""
            <div class="cs-bubble-ai" style="max-width:100%;margin-top:16px;">
                <div class="cs-agent-tag">🔒 Privacy Guardian</div>
                {response.replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)

elif page == "Settings":
    st.markdown("""
    <div class="cs-section-header">
        <span style="font-size:24px;">⚙️</span>
        <span class="cs-section-title">Settings</span>
    </div>
    """, unsafe_allow_html=True)
    st.info("Settings panel coming soon. Configure Gmail OAuth, resume path, and notification preferences here.")