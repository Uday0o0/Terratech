"""Government Official — Reports page."""

import streamlit as st
from src.reports import export_projects_csv, export_issues_csv, export_officer_workload_csv


def render():
    from src.ui import html, section

    section("Reports", "Export project data, issues, and officer workload")

    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        html('<div class="tt-panel"><h3>Project Summary Report</h3>'
             '<p style="font-size:12px;color:var(--ink-soft)">All projects with risk scores, '
             'progress, and status.</p></div>')
        csv_data = export_projects_csv()
        if csv_data:
            st.download_button(
                "Download CSV",
                data=csv_data,
                file_name="terratech_projects_report.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with c2:
        html('<div class="tt-panel"><h3>Issues Report</h3>'
             '<p style="font-size:12px;color:var(--ink-soft)">Legal, compensation, and '
             'documentation issues across all projects.</p></div>')
        csv_issues = export_issues_csv()
        if csv_issues:
            st.download_button(
                "Download CSV",
                data=csv_issues,
                file_name="terratech_issues_report.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with c3:
        html('<div class="tt-panel"><h3>Officer Workload Report</h3>'
             '<p style="font-size:12px;color:var(--ink-soft)">Assignment distribution '
             'and workload for all officers.</p></div>')
        csv_workload = export_officer_workload_csv()
        if csv_workload:
            st.download_button(
                "Download CSV",
                data=csv_workload,
                file_name="terratech_officer_workload.csv",
                mime="text/csv",
                use_container_width=True,
            )

    st.write("")
    html('<div class="tt-note">Reports are generated from the current database state. '
         'For PDF export, use your browser\'s print function (Ctrl+P / Cmd+P).</div>')
