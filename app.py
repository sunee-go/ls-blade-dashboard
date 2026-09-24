import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. Page Configuration (Responsive Wide Layout)
# ---------------------------------------------------------
st.set_page_config(
    page_title="LS Blade Executive Dashboard",
    page_icon="🔪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Mobile Responsiveness & Modern Design
st.markdown("""
<style>
    .main-header {
        font-size: 24px;
        font-weight: bold;
        color: #1E293B;
        margin-bottom: 5px;
    }
    .sub-header {
        font-size: 14px;
        color: #64748B;
        margin-bottom: 20px;
    }
    .kpi-card-safe {
        background-color: #F0FDF4;
        border-left: 5px solid #22C55E;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .kpi-card-danger {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .kpi-card-warning {
        background-color: #FFFBEB;
        border-left: 5px solid #F59E0B;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .kpi-title {
        font-size: 16px;
        font-weight: bold;
        color: #0F172A;
    }
    .kpi-value {
        font-size: 20px;
        font-weight: bold;
        color: #1E293B;
    }
    .kpi-sub {
        font-size: 13px;
        color: #475569;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Google Sheet Data Loader
# ---------------------------------------------------------
SHEET_ID = "1LCtzIdzBd4MGjKDV06Vl2rX-uy5rdZnQmNvaB72WpX0"
GOOGLE_SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        # Rename Thai column names if present
        column_mapping = {
            'เครื่องจักร': 'Machine',
            'ชุดใบมีด': 'Set_No',
            'หมายเลขชุด': 'Set_No',
            'สี': 'Color',
            'ความหนา (mm)': 'Thickness_mm',
            'จำนวนครั้งเจียร์': 'Grind_Count',
            'จำนวนเจียร์': 'Grind_Count',
            'ขนาด OD ล่าสุด': 'Latest_OD',
            'OD ล่าสุด': 'Latest_OD',
            'OD MIN': 'OD_MIN',
            'Margin': 'Margin',
            'สถานะ': 'Status',
            'ผู้ตรวจสอบ': 'Inspector'
        }
        df = df.rename(columns=column_mapping)
        return df
    except Exception as e:
        # Fallback dataset: LS-05 (6 ชุด), LS-06 (9 ชุด), LS-08 (4 ชุด)
        fallback_data = [
            # LS-05 (6 ชุด)
            {"Machine": "LS-05", "Set_No": "#1-20", "Color": "แดง/เหลือง", "Thickness_mm": 10, "Grind_Count": 3, "Latest_OD": 318.00, "OD_MIN": 288.00, "Margin": 30.00, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
            {"Machine": "LS-05", "Set_No": "#21-40", "Color": "ขาว", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 317.85, "OD_MIN": 288.00, "Margin": 29.85, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
            {"Machine": "LS-05", "Set_No": "#41-60", "Color": "เขียว", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 317.50, "OD_MIN": 288.00, "Margin": 29.50, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
            {"Machine": "LS-05", "Set_No": "#61-80", "Color": "ฟ้า", "Thickness_mm": 10, "Grind_Count": 3, "Latest_OD": 317.10, "OD_MIN": 288.00, "Margin": 29.10, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
            {"Machine": "LS-05", "Set_No": "#81-100", "Color": "เหลือง", "Thickness_mm": 10, "Grind_Count": 4, "Latest_OD": 316.91, "OD_MIN": 288.00, "Margin": 28.91, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
            {"Machine": "LS-05", "Set_No": "#101-120", "Color": "ส้ม", "Thickness_mm": 10, "Grind_Count": 1, "Latest_OD": 319.20, "OD_MIN": 288.00, "Margin": 31.20, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
            
            # LS-06 (9 ชุด)
            {"Machine": "LS-06", "Set_No": "#1-20", "Color": "เขียว/แดง", "Thickness_mm": 10, "Grind_Count": 10, "Latest_OD": 289.24, "OD_MIN": 288.00, "Margin": 1.24, "Status": "เฝ้าระวัง (Warning)", "Inspector": "สมชาย / กิตติ"},
            {"Machine": "LS-06", "Set_No": "#21-40", "Color": "เหลือง", "Thickness_mm": 10, "Grind_Count": 12, "Latest_OD": 288.05, "OD_MIN": 288.00, "Margin": 0.05, "Status": "วิกฤต (Critical)", "Inspector": "สมชาย / กิตติ"},
            {"Machine": "LS-06", "Set_No": "#41-60", "Color": "ขาว (บน)", "Thickness_mm": 10, "Grind_Count": 8, "Latest_OD": 291.00, "OD_MIN": 288.00, "Margin": 3.00, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
            {"Machine": "LS-06", "Set_No": "#61-80", "Color": "ขาว (ล่าง)", "Thickness_mm": 10, "Grind_Count": 8, "Latest_OD": 291.62, "OD_MIN": 288.00, "Margin": 3.62, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
            {"Machine": "LS-06", "Set_No": "#81-100", "Color": "น้ำเงิน", "Thickness_mm": 10, "Grind_Count": 6, "Latest_OD": 294.10, "OD_MIN": 288.00, "Margin": 6.10, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
            {"Machine": "LS-06", "Set_No": "#101-120", "Color": "เทา", "Thickness_mm": 10, "Grind_Count": 5, "Latest_OD": 296.50, "OD_MIN": 288.00, "Margin": 8.50, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
            {"Machine": "LS-06", "Set_No": "#121-140", "Color": "ม่วง", "Thickness_mm": 10, "Grind_Count": 4, "Latest_OD": 298.00, "OD_MIN": 288.00, "Margin": 10.00, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
            {"Machine": "LS-06", "Set_No": "#141-160", "Color": "ชมพู", "Thickness_mm": 10, "Grind_Count": 3, "Latest_OD": 302.20, "OD_MIN": 288.00, "Margin": 14.20, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
            {"Machine": "LS-06", "Set_No": "#161-180", "Color": "ดำ", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 305.00, "OD_MIN": 288.00, "Margin": 17.00, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},

            # LS-08 (4 ชุด)
            {"Machine": "LS-08", "Set_No": "#1-31 (T5)", "Color": "ขาว", "Thickness_mm": 5, "Grind_Count": 3, "Latest_OD": 222.36, "OD_MIN": 130.00, "Margin": 92.36, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / อภิชิต"},
            {"Machine": "LS-08", "Set_No": "#32-62 (T5)", "Color": "เขียว", "Thickness_mm": 5, "Grind_Count": 3, "Latest_OD": 223.27, "OD_MIN": 130.00, "Margin": 93.27, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / อภิชิต"},
            {"Machine": "LS-08", "Set_No": "#1-30 (T7)", "Color": "แดง", "Thickness_mm": 7, "Grind_Count": 3, "Latest_OD": 216.93, "OD_MIN": 130.00, "Margin": 86.93, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / อภิชิต"},
            {"Machine": "LS-08", "Set_No": "#31-60 (T7)", "Color": "เหลือง", "Thickness_mm": 7, "Grind_Count": 3, "Latest_OD": 217.35, "OD_MIN": 130.00, "Margin": 87.35, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / อภิชิต"}
        ]
        return pd.DataFrame(fallback_data)

df = load_data()

# ---------------------------------------------------------
# 3. Sidebar Filters
# ---------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/dashboard.png", width=60)
st.sidebar.title("ระบบกรองข้อมูล (Filters)")

machine_options = df["Machine"].unique().tolist() if "Machine" in df.columns else ["LS-05", "LS-06", "LS-08"]
status_options = df["Status"].unique().tolist() if "Status" in df.columns else ["ปกติ (Safe)", "เฝ้าระวัง (Warning)", "วิกฤต (Critical)"]

machine_filter = st.sidebar.multiselect(
    "เลือกเครื่องจักร (Machine):",
    options=machine_options,
    default=machine_options
)

status_filter = st.sidebar.multiselect(
    "เลือกสถานะ (Status):",
    options=status_options,
    default=status_options
)

# Filter Data
filtered_df = df[(df["Machine"].isin(machine_filter)) & (df["Status"].isin(status_filter))]

# ---------------------------------------------------------
# 4. Header Section
# ---------------------------------------------------------
st.markdown('<div class="main-header">🔪 Executive Blade Monitoring Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ระบบติดตามสภาพหน้าใบมีดสลิตชุดเครื่อง LS-05 (6 ชุด), LS-06 (9 ชุด), LS-08 (4 ชุด)</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Executive KPI Summary Cards
# ---------------------------------------------------------
st.subheader("📊 สรุปภาพรวมรายเครื่องจักร (Executive Summary)")
col1, col2, col3 = st.columns(3)

with col1:
    m5_df = df[df["Machine"] == "LS-05"] if "Machine" in df.columns else pd.DataFrame()
    if not m5_df.empty:
        m5_count = len(m5_df)
        m5_grind = m5_df["Grind_Count"].sum()
        m5_min_margin = m5_df["Margin"].min()
        st.markdown(f"""
        <div class="kpi-card-safe">
            <div class="kpi-title">🟢 เครื่อง LS-05 (OD MIN: 288 mm) - รวม {m5_count} ชุด</div>
            <div class="kpi-value">ส่งเจียรสะสม: {m5_grind} ครั้ง</div>
            <div class="kpi-sub">ช่วง OD ล่าสุด: {m5_df['Latest_OD'].min():.2f} - {m5_df['Latest_OD'].max():.2f} mm</div>
            <div class="kpi-sub"><b>สถานะ:</b> ปกติปลอดภัย (Margin +{m5_min_margin:.2f} mm)</div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    m6_df = df[df["Machine"] == "LS-06"] if "Machine" in df.columns else pd.DataFrame()
    if not m6_df.empty:
        m6_count = len(m6_df)
        m6_grind = m6_df["Grind_Count"].sum()
        m6_min_margin = m6_df["Margin"].min()
        st.markdown(f"""
        <div class="kpi-card-danger">
            <div class="kpi-title">🔴 เครื่อง LS-06 (OD MIN: 288 mm) - รวม {m6_count} ชุด</div>
            <div class="kpi-value">ส่งเจียรสะสม: {m6_grind} ครั้ง</div>
            <div class="kpi-sub">ช่วง OD ล่าสุด: {m6_df['Latest_OD'].min():.2f} - {m6_df['Latest_OD'].max():.2f} mm</div>
            <div class="kpi-sub"><b>สถานะ:</b> <span style="color:red;font-weight:bold;">เตือนวิกฤต! ชุด #21-40 เหลือ +{m6_min_margin:.2f} mm</span></div>
        </div>
        """, unsafe_allow_html=True)

with col3:
    m8_df = df[df["Machine"] == "LS-08"] if "Machine" in df.columns else pd.DataFrame()
    if not m8_df.empty:
        m8_count = len(m8_df)
        m8_grind = m8_df["Grind_Count"].sum()
        m8_min_margin = m8_df["Margin"].min()
        st.markdown(f"""
        <div class="kpi-card-safe">
            <div class="kpi-title">🟢 เครื่อง LS-08 (OD MIN: 130 mm) - รวม {m8_count} ชุด (T5, T7)</div>
            <div class="kpi-value">ส่งเจียรสะสม: {m8_grind} ครั้ง</div>
            <div class="kpi-sub">ช่วง OD ล่าสุด: {m8_df['Latest_OD'].min():.2f} - {m8_df['Latest_OD'].max():.2f} mm</div>
            <div class="kpi-sub"><b>สถานะ:</b> ปกติปลอดภัย (Margin +{m8_min_margin:.2f} mm)</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------
# 6. Bar Charts Section (Fix axis matching & show all sets cleanly)
# ---------------------------------------------------------
st.subheader("📈 วิเคราะห์ขนาดเส้นผ่านศูนย์กลางภายนอก (OD) & จำนวนครั้งเจียรรายชุด")

tab1, tab2 = st.tabs(["📏 ขนาด OD ล่าสุด เทียบ OD MIN", "🔄 จำนวนครั้งส่งเจียรสะสม"])

color_map = {
    "ปกติ (Safe)": "#22C55E",
    "เฝ้าระวัง (Warning)": "#F59E0B",
    "วิกฤต (Critical)": "#EF4444"
}

with tab1:
    fig_od = px.bar(
        filtered_df,
        x="Set_No",
        y="Latest_OD",
        color="Status",
        facet_col="Machine",
        color_discrete_map=color_map,
        text="Latest_OD",
        title="ค่า OD หลังเจียรล่าสุดแยกตามชุดใบมีด (mm)",
        labels={"Set_No": "ชุดใบมีด / หมายเลข", "Latest_OD": "ขนาด OD (mm)"}
    )
    fig_od.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_od.update_xaxes(matches=None, showticklabels=True)  # Fix: Independent X-axes for each machine!
    fig_od.update_layout(height=480, margin=dict(t=50, b=40, l=40, r=40))
    st.plotly_chart(fig_od, use_container_width=True)

with tab2:
    fig_grind = px.bar(
        filtered_df,
        x="Set_No",
        y="Grind_Count",
        color="Machine",
        facet_col="Machine",
        text="Grind_Count",
        title="จำนวนครั้งการส่งเจียร์สะสมแยกตามชุดใบมีด",
        labels={"Set_No": "ชุดใบมีด / หมายเลข", "Grind_Count": "จำนวนครั้งเจียร์"}
    )
    fig_grind.update_traces(texttemplate='%{text} ครั้ง', textposition='outside')
    fig_grind.update_xaxes(matches=None, showticklabels=True)  # Fix: Independent X-axes for each machine!
    fig_grind.update_layout(height=480, margin=dict(t=50, b=40, l=40, r=40))
    st.plotly_chart(fig_grind, use_container_width=True)

# ---------------------------------------------------------
# 7. Action Plan & Detailed Risk Table
# ---------------------------------------------------------
st.subheader("📋 ตารางประเมินความเสี่ยงและแผนการจัดการ (Action Plan)")

def highlight_status(val):
    if "วิกฤต" in str(val):
        return 'background-color: #FEF2F2; color: #DC2626; font-weight: bold;'
    elif "เฝ้าระวัง" in str(val):
        return 'background-color: #FFFBEB; color: #D97706; font-weight: bold;'
    else:
        return 'background-color: #F0FDF4; color: #16A34A;'

if "Status" in filtered_df.columns:
    styled_table = filtered_df.style.applymap(highlight_status, subset=['Status'])
    st.dataframe(styled_table, use_container_width=True, height=400)
else:
    st.dataframe(filtered_df, use_container_width=True, height=400)

st.caption("ระบบเชื่อมต่อข้อมูล Google Sheet อัปเดตอัตโนมัติ | พัฒนาสำหรับผู้บริหารเครื่องจักรชุด LS")
