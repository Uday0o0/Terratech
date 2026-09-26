"""Government Official — Analytics page."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from src.analytics import (
    get_risk_distribution, get_delay_distribution,
    get_district_comparison, get_stage_bottleneck_analysis,
)
from src.database import get_officer_workload, get_projects_by_type, get_projects_by_status


def render():
    from src.ui import html, section, BAND_HEX, RUST, MARIGOLD, GREEN, TEAL, NAVY

    section("Project Analytics", "Comprehensive analysis across all projects")

    # --- Risk distribution chart ---
    c1, c2 = st.columns(2, gap="medium")

    with c1:
        with st.container(border=True):
            st.subheader("Risk Distribution")
            risk_dist = get_risk_distribution()
            colors = [BAND_HEX[k] for k in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]]
            fig = go.Figure(go.Bar(
                x=list(risk_dist.keys()),
                y=list(risk_dist.values()),
                marker_color=colors,
                text=list(risk_dist.values()),
                textposition="auto",
            ))
            fig.update_layout(
                height=300, margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", size=12),
                yaxis=dict(gridcolor="rgba(0,0,0,0.05)", visible=False),
                xaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with c2:
        with st.container(border=True):
            st.subheader("Delay Distribution")
            delay_dist = get_delay_distribution()
            fig2 = go.Figure(go.Bar(
                x=[d["bucket"] for d in delay_dist],
                y=[d["count"] for d in delay_dist],
                marker_color=[GREEN, TEAL, MARIGOLD, RUST, "#8E3A1F"],
                text=[d["count"] for d in delay_dist],
                textposition="auto",
            ))
            fig2.update_layout(
                height=300, margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", size=12),
                yaxis=dict(gridcolor="rgba(0,0,0,0.05)", visible=False),
                xaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

    st.write("")

    # --- Project type & Status ---
    c3, c4 = st.columns(2, gap="medium")

    with c3:
        with st.container(border=True):
            st.subheader("Projects by Type")
            by_type = get_projects_by_type()
        if by_type:
            fig3 = go.Figure(go.Pie(
                labels=[d["project_type"] for d in by_type],
                values=[d["count"] for d in by_type],
                hole=0.45,
                marker=dict(colors=px.colors.qualitative.Set3),
            ))
            fig3.update_layout(
                height=300, margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", size=11),
                showlegend=True,
                legend=dict(font=dict(size=10), orientation="h", yanchor="bottom", y=-0.2),
            )
            st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

    with c4:
        with st.container(border=True):
            st.subheader("Projects by Status")
            by_status = get_projects_by_status()
            if by_status:
                status_colors = {
                    "In Progress": TEAL, "Completed": GREEN,
                    "On Hold": MARIGOLD, "Not Started": "#8B9B9C", "Cancelled": RUST,
                }
                fig4 = go.Figure(go.Pie(
                    labels=[d["project_status"] for d in by_status],
                    values=[d["count"] for d in by_status],
                    hole=0.45,
                    marker=dict(colors=[status_colors.get(d["project_status"], TEAL) for d in by_status]),
                ))
                fig4.update_layout(
                    height=300, margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", size=11),
                    showlegend=True,
                    legend=dict(font=dict(size=10), orientation="h", yanchor="bottom", y=-0.2),
                )
                st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

    # --- Stage bottleneck ---
    st.write("")
    section("Stage Bottleneck Analysis", "Which stages have the most projects currently")

    stages = get_stage_bottleneck_analysis()
    if stages:
        import pandas as pd
        df = pd.DataFrame(stages)
        df.rename(columns={"current_stage": "Stage", "count": "Projects"}, inplace=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # --- District comparison ---
    st.write("")
    section("District Comparison", "Performance across districts")

    districts = get_district_comparison()
    if districts:
        import pandas as pd
        df = pd.DataFrame(districts[:20])
        df.rename(columns={
            "district": "District", "state": "State", 
            "count": "Projects", "avg_progress": "Avg Progress", "avg_risk": "Avg Risk"
        }, inplace=True)
        st.dataframe(
            df, 
            column_config={
                "Avg Progress": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
                "Avg Risk": st.column_config.NumberColumn(format="%.1f")
            },
            use_container_width=True, 
            hide_index=True
        )

    # --- Officer workload ---
    st.write("")
    section("Officer Workload", "Assignment distribution across employees")

    workload = get_officer_workload()
    if workload:
        import pandas as pd
        df = pd.DataFrame(workload)
        df.rename(columns={
            "name": "Officer", "designation": "Designation", "department": "Department",
            "project_count": "Projects", "assignment_count": "Assignments", "active_count": "Active"
        }, inplace=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
