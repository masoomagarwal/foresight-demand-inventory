import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# Make the project-root auth_store module importable regardless of cwd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth_store import create_user, verify_user, get_display_name

st.set_page_config(
    page_title="Project FORESIGHT",
    page_icon="📦",
    layout="wide"
)

# ---------- Paths ----------
APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"

def show_auth():
    # ---------- Page-level styling for the auth screen ----------
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0f2027 0%, #0c6e63 45%, #14b8a6 100%);
        }
        .block-container { padding-top: 3rem; }

        .auth-logo {
            text-align:center; font-size:46px; line-height:1; margin-bottom:2px;
        }
        .auth-title {
            text-align:center; font-size:32px; font-weight:800;
            background: linear-gradient(135deg, #0c6e63, #ff7a5c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing:0.5px; margin-bottom:2px;
        }
        .auth-subtitle {
            text-align:center; color:#7a7a8c; font-size:14.5px; margin-bottom:22px;
        }

        /* Card that wraps the form */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff;
            border-radius: 18px !important;
            box-shadow: 0 25px 60px rgba(6, 40, 36, 0.45);
            border: none !important;
            padding: 8px 6px;
        }

        /* Segmented Login/Register control */
        div[role="radiogroup"] {
            display:flex; justify-content:center; gap:8px; margin-bottom: 6px;
        }
        div[role="radiogroup"] label {
            border: 1.5px solid #e4e4ef;
            padding: 6px 22px;
            border-radius: 20px;
            transition: 0.15s ease-in-out;
        }
        div[role="radiogroup"] label:has(input:checked) {
            background: linear-gradient(135deg, #0c6e63, #14b8a6);
            border-color: transparent;
        }
        div[role="radiogroup"] label:has(input:checked) p {
            color: #ffffff !important; font-weight:600;
        }

        /* Inputs */
        .stTextInput input {
            border-radius: 9px !important;
            border: 1.5px solid #e4e4ef !important;
            padding: 10px 12px !important;
        }
        .stTextInput input:focus {
            border-color: #14b8a6 !important;
            box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.18) !important;
        }

        /* Submit buttons — coral accent, pops against the teal card */
        div[data-testid="stFormSubmitButton"] button {
            background: linear-gradient(135deg, #ff7a5c, #ff5e78);
            color: #ffffff; border: none; border-radius: 9px;
            padding: 10px 0; font-weight: 700; letter-spacing: 0.3px;
            box-shadow: 0 8px 20px rgba(255, 94, 120, 0.35);
            transition: transform 0.15s ease, opacity 0.15s ease;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-1px); opacity: 0.92; color:#ffffff;
        }
    </style>
    """, unsafe_allow_html=True)

    # ---------- Bug fix ----------
    # Streamlit raises StreamlitAPIException if st.session_state[key] is
    # reassigned AFTER the widget with that key has been instantiated in the
    # same run (e.g. setting st.session_state["auth_mode"] right after the
    # st.radio(key="auth_mode") widget was already created below). To flip
    # the radio back to "Login" post-registration, set a plain flag instead,
    # then apply it here, BEFORE the radio widget is created.
    if st.session_state.get("just_registered"):
        st.session_state["auth_mode"] = "Login"
        st.session_state["just_registered"] = False

    left, center, right = st.columns([1, 1.3, 1])
    with center:
        st.markdown('<div class="auth-logo">📦</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">FORESIGHT</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Demand forecasting & inventory risk intelligence</div>', unsafe_allow_html=True)

        with st.container(border=True):
            st.write("")
            mode = st.radio(
                "Account",
                ["Login", "Register"],
                horizontal=True,
                label_visibility="collapsed",
                key="auth_mode"
            )

            if mode == "Register":
                st.markdown("#### Create a new account")
                st.caption("Register first. Then use your new username and password to log in.")

                with st.form("register_form"):
                    name = st.text_input("Full Name", placeholder="Enter your name")
                    username = st.text_input("Username", placeholder="Choose a username")
                    email = st.text_input("Email", placeholder="Enter your email")
                    password = st.text_input("Password", type="password", placeholder="Create a password")
                    confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
                    submitted = st.form_submit_button("Create Account", use_container_width=True)

                if submitted:
                    username_clean = username.strip().lower()
                    if not name.strip() or not username_clean or not email.strip() or not password:
                        st.error("Please fill in all fields.")
                    elif len(username_clean) < 3:
                        st.error("Username must contain at least 3 characters.")
                    elif len(password) < 6:
                        st.error("Password must contain at least 6 characters.")
                    elif password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        success, message = create_user(
                            username_clean, password, name=name.strip(), email=email.strip()
                        )
                        if success:
                            st.success("Account created successfully! Redirecting you to Login…")
                            # Don't touch st.session_state["auth_mode"] here — the
                            # radio widget for that key already ran this script
                            # execution. Set a flag and let the top of this
                            # function apply it on the NEXT run instead.
                            st.session_state["just_registered"] = True
                            st.rerun()
                        else:
                            st.error(message)

            else:
                st.markdown("#### Welcome back")
                st.caption("Sign in to access the FORESIGHT dashboard.")

                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submitted = st.form_submit_button("Login", use_container_width=True)

                if submitted:
                    username_clean = username.strip().lower()
                    if verify_user(username_clean, password):
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username_clean
                        st.session_state["display_name"] = get_display_name(username_clean)
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
            st.write("")

    return False

if not st.session_state.get("authenticated", False):
    show_auth()
    st.stop()

# ---------- Custom styling (post-login dashboard) ----------
# Same teal/coral palette as the login screen, so the app doesn't feel like
# two different products stitched together.
st.markdown("""
<style>
    .stApp { background: #f5f7fa; }
    .block-container { padding-top: 1.6rem; max-width: 1200px; }

    /* ---- Hero banner ---- */
    .hero-banner {
        background: linear-gradient(135deg, #0f2027 0%, #0c6e63 55%, #14b8a6 100%);
        border-radius: 18px;
        padding: 26px 32px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 24px;
        box-shadow: 0 14px 34px rgba(6, 40, 36, 0.22);
    }
    .hero-title {
        color: #ffffff; font-size: 27px; font-weight: 800; letter-spacing: 0.3px;
        margin: 0;
    }
    .hero-subtitle { color: #d9f2ee; font-size: 14px; margin-top: 5px; }
    .hero-badge {
        color: #ffffff; background: rgba(255,255,255,0.16);
        padding: 8px 16px; border-radius: 22px;
        font-size: 13.5px; font-weight: 600;
        border: 1px solid rgba(255,255,255,0.25);
    }

    /* ---- KPI stat cards ---- */
    .stat-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 18px 20px 16px;
        box-shadow: 0 4px 16px rgba(15, 32, 39, 0.07);
        border-left: 5px solid #14b8a6;
        height: 100%;
    }
    .stat-icon { font-size: 21px; margin-bottom: 6px; }
    .stat-value { font-size: 25px; font-weight: 800; color: #0f2027; line-height: 1.15; }
    .stat-label { font-size: 12.5px; color: #6b7280; margin-top: 3px; font-weight: 500; }

    /* ---- Section headers ---- */
    .section-title { font-size: 18px; font-weight: 700; color: #0f2027; margin-bottom: 2px; }
    .section-caption { color: #6b7280; font-size: 13.5px; margin-bottom: 14px; }

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 8px 18px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0c6e63, #14b8a6) !important;
        color: #ffffff !important;
    }

    /* ---- Card containers (bordered st.container) ---- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important;
        border: 1px solid #e8ebef !important;
        background: #ffffff;
    }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #edeef2; }
    .sidebar-brand { font-size: 15px; font-weight: 800; color: #0c6e63; letter-spacing: 0.3px; margin-bottom: 14px; }
    .sidebar-user-card {
        background: linear-gradient(135deg, #0c6e63, #14b8a6);
        border-radius: 14px; padding: 14px 16px; margin-bottom: 14px; color: #ffffff;
    }
    .sidebar-avatar {
        width: 38px; height: 38px; border-radius: 50%;
        background: rgba(255,255,255,0.22);
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 15px; margin-bottom: 8px;
    }
    .sidebar-user-name { font-weight: 700; font-size: 14.5px; }
    .sidebar-user-sub { font-size: 11.5px; opacity: 0.85; }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #ff7a5c, #ff5e78);
        color: #ffffff; border: none; border-radius: 8px; font-weight: 700;
        box-shadow: 0 6px 16px rgba(255, 94, 120, 0.3);
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover { opacity: 0.92; color: #ffffff; }

    /* ---- Footer ---- */
    .app-footer {
        text-align: center; color: #9aa0a6; font-size: 12px;
        padding: 18px 0 6px; border-top: 1px solid #e8ebef; margin-top: 26px;
    }
</style>
""", unsafe_allow_html=True)


def stat_card(icon: str, value: str, label: str, accent: str):
    st.markdown(f"""
    <div class="stat-card" style="border-left-color:{accent};">
        <div class="stat-icon">{icon}</div>
        <div class="stat-value">{value}</div>
        <div class="stat-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def style_chart_axes(ax):
    """Shared matplotlib look so both charts match the rest of the UI."""
    ax.set_facecolor("#fbfbfd")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#d7dbe0")
    ax.spines["bottom"].set_color("#d7dbe0")
    ax.tick_params(colors="#5b6470", labelsize=9.5)
    ax.grid(alpha=0.18)


display_name = st.session_state.get("display_name", "User")
initials = "".join(part[0] for part in display_name.split()[:2]).upper() or "U"

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="sidebar-brand">📦 FORESIGHT</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sidebar-user-card">
        <div class="sidebar-avatar">{initials}</div>
        <div class="sidebar-user-name">{display_name}</div>
        <div class="sidebar-user-sub">Signed in</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Logout", use_container_width=True):
        for key in ["authenticated", "username", "display_name"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.write("")


@st.cache_data
def load_data():
    """
    Load the processed CSVs once per data change and cache them.
    Without this, every filter tweak or tab switch reruns the whole
    script and re-reads all three files from disk on every interaction —
    fine locally, but noticeably slower once deployed.
    """
    risk = pd.read_csv(DATA_DIR / "risk_scored.csv")

    weekly = pd.read_csv(DATA_DIR / "weekly_demand.csv")
    weekly["week_start"] = pd.to_datetime(weekly["week_start"])

    horizon = pd.read_csv(DATA_DIR / "horizon_forecast.csv")
    horizon["week_start"] = pd.to_datetime(horizon["week_start"])

    return risk, weekly, horizon


risk_data, weekly_demand, horizon_forecast = load_data()

# ---------- Sidebar filters ----------
with st.sidebar:
    with st.container(border=True):
        st.markdown("**🔍 Filters**")
        category_filter = st.multiselect(
            "Risk category",
            options=risk_data["risk_category"].unique(),
            default=risk_data["risk_category"].unique()
        )
        product_category_filter = st.multiselect(
            "Product category",
            options=sorted(risk_data["category"].unique()),
            default=sorted(risk_data["category"].unique())
        )
        sku_search = st.text_input("Search SKU ID", placeholder="e.g. SKU0077")

    st.write("")
    st.caption("📦 Project FORESIGHT · Internal Analytics Tool")

filtered = risk_data[
    risk_data["risk_category"].isin(category_filter) &
    risk_data["category"].isin(product_category_filter)
]
if sku_search:
    # regex=False: a raw substring match. Without it, a search term with
    # regex special characters (e.g. "SKU(01") raises a re.error instead
    # of just returning no matches — an easy crash for a non-technical
    # user to trigger by accident.
    filtered = filtered[filtered["sku_id"].str.contains(sku_search, case=False, regex=False)]
filtered = filtered.sort_values("stockout_value_at_risk", ascending=False)

# ---------- Hero banner ----------
st.markdown(f"""
<div class="hero-banner">
    <div>
        <div class="hero-title">📦 Project FORESIGHT</div>
        <div class="hero-subtitle">Demand forecasting & inventory risk intelligence for <b>NorthBay Living</b></div>
    </div>
    <div class="hero-badge">👋 Welcome, {display_name}</div>
</div>
""", unsafe_allow_html=True)

# ---------- KPI cards ----------
col1, col2, col3, col4 = st.columns(4)
with col1:
    stat_card("📦", f"{len(risk_data)}", "Total SKUs", "#14b8a6")
with col2:
    stat_card("🔴", f"{(risk_data['risk_category'] == 'Reorder Now').sum()}", "Reorder Now", "#e74c3c")
with col3:
    stat_card("🟣", f"{(risk_data['risk_category'] == 'Markdown / Clear').sum()}", "Markdown / Clear", "#8e44ad")
with col4:
    stat_card("💰", f"₹{risk_data['stockout_value_at_risk'].sum():,.0f}", "Sales at Risk", "#ff7a5c")

st.write("")

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["📋  Risk Table", "📊  Decisioning Grid", "📈  Forecast vs Actual"])

with tab1:
    with st.container(border=True):
        st.markdown('<div class="section-title">SKU Risk & Recommendations</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">Sorted by rupee value at risk — most urgent items first</div>', unsafe_allow_html=True)

        if len(filtered) == 0:
            st.warning("No SKUs match your current filters. Try adjusting the category filter or search term.")
        else:
            badge_colors = {
                "Reorder Now": "background-color: #ffe3e3; color: #c0392b; font-weight: 600;",
                "Markdown / Clear": "background-color: #f0e3ff; color: #7d3c98; font-weight: 600;",
                "Watch / Volatile": "background-color: #fff3cd; color: #b8860b; font-weight: 600;",
                "Healthy": "background-color: #e3fce8; color: #1e8449; font-weight: 600;",
            }

            def style_category(val):
                return badge_colors.get(val, "")

            display_df = filtered[["sku_id", "risk_category", "recommended_action",
                                    "demand_8weeks", "on_hand_units",
                                    "stockout_value_at_risk", "overstock_capital_locked"]].copy()

            styled = display_df.style.map(style_category, subset=["risk_category"]) \
                .format({
                    "demand_8weeks": "{:.1f}",
                    "on_hand_units": "{:.1f}",
                    "stockout_value_at_risk": "₹{:,.0f}",
                    "overstock_capital_locked": "₹{:,.0f}",
                })

            st.dataframe(styled, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(filtered)} of {len(risk_data)} SKUs")

with tab2:
    with st.container(border=True):
        st.markdown('<div class="section-title">Risk Decisioning Grid</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">Every SKU plotted by stockout risk vs. overstock risk</div>', unsafe_allow_html=True)

        colors = {
            "Reorder Now": "#e74c3c",
            "Markdown / Clear": "#8e44ad",
            "Watch / Volatile": "#f39c12",
            "Healthy": "#27ae60"
        }
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor("#ffffff")
        for category, color in colors.items():
            subset = filtered[filtered["risk_category"] == category]
            ax.scatter(subset["overstock_risk_ratio"], subset["stockout_risk_ratio"],
                       label=category, color=color, alpha=0.8, s=60, edgecolors="white", linewidth=0.5)
        ax.set_xlabel("Overstock Risk Ratio", fontsize=11, color="#374151")
        ax.set_ylabel("Stockout Risk Ratio", fontsize=11, color="#374151")
        ax.legend(frameon=False)
        style_chart_axes(ax)
        st.pyplot(fig)

with tab3:
    with st.container(border=True):
        st.markdown('<div class="section-title">Forecast vs Actual Demand</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">Recent history and the 8-week forecast ahead, for a single SKU</div>', unsafe_allow_html=True)

        selected_sku = st.selectbox("Choose a SKU", options=sorted(filtered["sku_id"].unique()) or ["No SKUs match filters"])

        sku_history = weekly_demand[weekly_demand["sku_id"] == selected_sku].sort_values("week_start").tail(26)
        sku_forecast = horizon_forecast[horizon_forecast["sku_id"] == selected_sku].sort_values("week_start")

        if len(sku_history) == 0:
            st.warning("No historical data available for this SKU.")
        else:
            fig, ax = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor("#ffffff")
            ax.plot(sku_history["week_start"], sku_history["units_sold"],
                    label="Actual (last 26 weeks)", color="#0c6e63", linewidth=1.8)
            ax.plot(sku_forecast["week_start"], sku_forecast["predicted_demand"],
                    label="Forecast (8 weeks ahead)", color="#ff5e78", linewidth=2.2,
                    linestyle="--", marker="o", markersize=4)
            ax.set_xlabel("Week", fontsize=11, color="#374151")
            ax.set_ylabel("Units", fontsize=11, color="#374151")
            ax.legend(frameon=False)
            style_chart_axes(ax)
            st.pyplot(fig)

# ---------- Footer ----------
st.markdown(
    '<div class="app-footer">Project FORESIGHT · Internal Analytics Tool · Built for NorthBay Living</div>',
    unsafe_allow_html=True
)