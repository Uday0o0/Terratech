"""Citizen Portal — Home page."""

import streamlit as st


def render():
    from src.ui import html, section, TEAL, NAVY_DEEP

    html(
        f'<div style="text-align:center;padding:40px 20px">'
        f'<div style="width:60px;height:60px;border-radius:14px;'
        f'background:linear-gradient(135deg,{TEAL},{NAVY_DEEP});'
        f'margin:0 auto 16px;display:flex;align-items:center;justify-content:center">'
        f'<span style="color:#fff;font-size:28px;font-weight:700">T</span></div>'
        f'<h1 style="margin:0 0 8px">TerraTech</h1>'
        f'<p style="font-size:14px;color:var(--ink-soft);max-width:480px;margin:0 auto">'
        f'Track public land acquisition projects in your area. View project progress, '
        f'check your land status, and stay informed about compensation and legal updates.</p>'
        f'</div>'
    )

    st.write("")

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        html(
            '<div class="tt-panel" style="text-align:center;padding:24px">'
            '<h3>Local Projects</h3>'
            '<p style="font-size:12.5px;color:var(--ink-soft)">'
            'View land acquisition projects in your district and state.</p>'
            '</div>'
        )
    with c2:
        html(
            '<div class="tt-panel" style="text-align:center;padding:24px">'
            '<h3>My Land</h3>'
            '<p style="font-size:12.5px;color:var(--ink-soft)">'
            'Check the status of your land using your Parcel ID.</p>'
            '</div>'
        )
    with c3:
        html(
            '<div class="tt-panel" style="text-align:center;padding:24px">'
            '<h3>Project Search</h3>'
            '<p style="font-size:12.5px;color:var(--ink-soft)">'
            'Search for any project by name, ID, or location.</p>'
            '</div>'
        )

    st.write("")
    html('<div class="tt-note">Use the sidebar navigation to access these features. '
         'This portal shows public project information only. Internal government '
         'analytics are not accessible from this portal.</div>')

    st.write("")

    # FAQ
    section("Frequently Asked Questions", "Common questions about land acquisition")

    with st.expander("What is land acquisition?"):
        st.markdown(
            "Land acquisition is the process by which the government acquires "
            "private land for public purposes such as infrastructure development, "
            "under the Right to Fair Compensation and Transparency in Land Acquisition, "
            "Rehabilitation and Resettlement Act, 2013 (LARR Act)."
        )
    with st.expander("How is compensation determined?"):
        st.markdown(
            "Compensation is determined based on the market value of the land, "
            "plus a solatium (100% of market value in rural areas, 100% in urban). "
            "The Collector assesses the value based on recent sales and registration data."
        )
    with st.expander("What if I have an objection?"):
        st.markdown(
            "Under Section 15 of the LARR Act, any affected person may file an objection "
            "within 60 days of the notification. The Collector shall hear all objections "
            "and submit a report to the appropriate Government."
        )
    with st.expander("How can I track my land status?"):
        st.markdown(
            "Navigate to **My Land** in the sidebar and enter your Parcel ID. "
            "You can view the current acquisition status, compensation status, "
            "survey status, and any outstanding issues."
        )
