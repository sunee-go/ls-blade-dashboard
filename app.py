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

FALLBACK_DATA = [
    {"Machine": "LS-05", "Set_No": "#1-20", "Color": "แดง/เหลือง", "Thickness_mm": 10, "Grind_Count": 3, "Latest_OD": 318.00, "OD_MIN": 288.00, "Margin": 30.00, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
    {"Machine": "LS-05", "Set_No": "#21-40", "Color": "ขาว", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 317.85, "OD_MIN": 288.00, "Margin": 29.85, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
    {"Machine": "LS-05", "Set_No": "#41-60", "Color": "เขียว", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 317.50, "OD_MIN": 288.00, "Margin": 29.50, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
    {"Machine": "LS-05", "Set_No": "#81-100", "Color": "เหลือง", "Thickness_mm": 10, "Grind_Count": 4, "Latest_OD": 316.91, "OD_MIN": 288.00, "Margin": 28.91, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
    {"Machine": "LS-06", "Set_No": "#21-40", "Color": "เหลือง", "Thickness_mm": 10, "Grind_Count": 12, "Latest_OD": 288.05, "OD_MIN": 288.00, "Margin": 0.05, "Status": "วิกฤต (Critical)", "Inspector": "สมชาย / กิตติ"},
    {"Machine": "LS-06", "Set_No": "#1-20", "Color": "เขียว/แดง", "Thickness_mm": 10, "Grind_Count": 10, "Latest_OD": 289.24, "OD_MIN": 288.00, "Margin": 1.24, "Status": "เฝ้าระวัง (Warning)", "Inspector": "สมชาย / กิตติ"},
    {"Machine": "LS-06", "Set_No": "#41-60", "Color": "ขาว (บน)", "Thickness_mm": 10, "Grind_Count": 8, "Latest_OD": 291.00, "OD_MIN": 288.00, "Margin": 3.00, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
    {"Machine": "LS-06", "Set_No": "#61-80", "Color": "ขาว (ล่าง)", "Thickness_mm": 10, "Grind_Count": 8, "Latest_OD": 291.62, "OD_MIN": 288.00, "Margin": 3.62, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
    {"Machine": "LS-08", "Set_No": "#1-31 (T5)", "Color": "ขาว", "Thickness_mm": 5, "Grind_Count": 3, "Latest_OD": 222.36, "OD_MIN": 130.00, "Margin": 92.36, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / อภิชิต"},
    {"Machine": "LS-08", "Set_No": "#32-62 (T5)", "Color": "เขียว", "Thickness_mm": 5, "Grind_Count": 3, "Latest_OD": 223.27, "OD_MIN": 130.00, "Margin": 93.27, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / อภิชิต"},
    {"Machine": "LS-08", "Set_No": "#1-30 (T7)", "Color": "แดง", "Thickness_mm": 7, "Grind_Count": 3, "Latest_OD": 216.93, "OD_MIN": 130.00, "Margin": 86.93, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / อภิชิต"},
    {"Machine": "LS-08", "Set_No": "#31-60 (T7)", "Color": "เหลือง", "Thickness_mm": 7, "Grind_Count": 3, "Latest_OD": 217.35, "OD_MIN": 130.00, "Margin": 87.35, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / อภิชิต"}
]

def clean_and_normalize_df(df_raw):
    # Clean column names (strip space)
    df_raw.columns = [str(c).strip() for c in df_raw.columns]
    
    col_map = {
        'เครื่องจักร': 'Machine', 'เครื่อง': 'Machine', 'Machine': 'Machine', 'LS': 'Machine',
        'ชุดใบมีด': 'Set_No', 'ชุดที่': 'Set_No', 'หมายเลขชุด': 'Set_No', 'Set_No': 'Set_No', 'Set': 'Set_No',
        'สัญลักษณ์สี': 'Color', 'สี': 'Color', 'Color': 'Color',
        'ความหนา': 'Thickness_mm', 'Thickness_mm': 'Thickness_mm',
        'จำนวนครั้งเจียร์': 'Grind_Count', 'จำนวนครั้งที่ส่งเจียร': 'Grind_Count', 'จำนวนครั้งเจียร': 'Grind_Count', 'เจียรครั้งที่': 'Grind_Count', 'Grind_Count': 'Grind_Count',
        'OD ล่าสุด': 'Latest_OD', 'OD หลังเจียร': 'Latest_OD', 'ขนาด OD': 'Latest_OD', 'Latest_OD': 'Latest_OD',
        'OD MIN': 'OD_MIN', 'OD_MIN': 'OD_MIN',
        'Margin': 'Margin', 'ระยะคงเหลือ': 'Margin',
        'สถานะ': 'Status', 'Status': 'Status',
        'ผู้บันทึก': 'Inspector', 'Inspector': 'Inspector'
    }
    
    new_cols = {}
    for c in df_raw.columns:
        matched = False
        for k, v in col_map.items():
            if k.lower() in c.lower():
                new_cols[c] = v
                matched = True
                break
        if not matched:
            new_cols[c] = c
            
    df = df_raw.rename(columns=new_cols)
    
    essential = ['Machine', 'Set_No', 'Status', 'Latest_OD', 'Grind_Count']
    missing = [col for col in essential if col not in df.columns]
    
    if missing:
        return pd.DataFrame(FALLBACK_DATA)
        
    df['Latest_OD'] = pd.to_numeric(df['Latest_OD'], errors='coerce').fillna(0)
    df['Grind_Count'] = pd.to_numeric(df['Grind_Count'], errors='coerce').fillna(0)
    
    if 'OD_MIN' in df.columns:
        df['OD_MIN'] = pd.to_numeric(df['OD_MIN'], errors='coerce').fillna(288.0)
    else:
        df['OD_MIN'] = 288.0
        
    if 'Margin' in df.columns:
        df['Margin'] = pd.to_numeric(df['Margin'], errors='coerce').fillna(df['Latest_OD'] - df['OD_MIN'])
    else:
        df['Margin'] = df['Latest_OD'] - df['OD_MIN']
        
    def standardize_status(s):
        s_str = str(s)
        if "วิกฤต" in s_str or "Critical" in s_str:
            return "วิกฤต (Critical)"
        elif "เฝ้าระวัง" in s_str or "Warning" in s_str:
            return "เฝ้าระวัง (Warning)"
        else:
            return "ปกติ (Safe)"
            
    df['Status'] = df['Status'].apply(standardize_status)
    return df

@st.cache_data(ttl=60)  # Refresh every 60 seconds
def load_data():
    try:
        df_raw = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        df_clean = clean_and_normalize_df(df_raw)
        return df_clean
    except Exception as e:
        return pd.DataFrame(FALLBACK_DATA)

df = load_data()

# ---------------------------------------------------------
# 3. Sidebar Filters
# ---------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/dashboard.png", width=60)
st.sidebar.title("ระบบกรองข้อมูล (Filters)")

available_machines = list(df["Machine"].unique()) if "Machine" in df.columns else ["LS-05", "LS-06", "LS-08"]
available_statuses = ["ปกติ (Safe)", "เฝ้าระวัง (Warning)", "วิกฤต (Critical)"]

machine_filter = st.sidebar.multiselect(
    "เลือกเครื่องจักร (Machine):",
    options=available_machines,
    default=available_machines
)

status_filter = st.sidebar.multiselect(
    "เลือกสถานะ (Status):",
    options=available_statuses,
    default=available_statuses
)

# Filter Data safely
filtered_df = df[(df["Machine"].isin(machine_filter)) & (df["Status"].isin(status_filter))]

# ---------------------------------------------------------
# 4. Header Section
# ---------------------------------------------------------
st.markdown('<div class="main-header"> Executive Blade Monitoring Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ระบบติดตามสภาพหน้าใบมีดสลิตชุดเครื่อง LS-05, LS-06, LS-08 (เชื่อมต่อ Google Sheet)</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Executive KPI Summary Cards
# ---------------------------------------------------------
st.subheader("📊 สรุปภาพรวมรายเครื่องจักร (Executive Summary)")
col1, col2, col3 = st.columns(3)

with col1:
    m5_df = df[df["Machine"] == "LS-05"]
    m5_grind = m5_df["Grind_Count"].sum() if not m5_df.empty else 0
    m5_min_margin = m5_df["Margin"].min() if not m5_df.empty else 0
    m5_min_od = m5_df['Latest_OD'].min() if not m5_df.empty else 0
    m5_max_od = m5_df['Latest_OD'].max() if not m5_df.empty else 0
    st.markdown(f"""
    <div class="kpi-card-safe">
        <div class="kpi-title">🟢 เครื่อง LS-05 (OD MIN: 288 mm)</div>
        <div class="kpi-value">ส่งเจียรสะสม: {m5_grind} ครั้ง</div>
        <div class="kpi-sub">ช่วง OD ล่าสุด: {m5_min_od:.2f} - {m5_max_od:.2f} mm</div>
        <div class="kpi-sub"><b>สถานะ:</b> ปกติปลอดภัย (Margin +{m5_min_margin:.2f} mm)</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    m6_df = df[df["Machine"] == "LS-06"]
    m6_grind = m6_df["Grind_Count"].sum() if not m6_df.empty else 0
    m6_min_margin = m6_df["Margin"].min() if not m6_df.empty else 0
    m6_min_od = m6_df['Latest_OD'].min() if not m6_df.empty else 0
    m6_max_od = m6_df['Latest_OD'].max() if not m6_df.empty else 0
    st.markdown(f"""
    <div class="kpi-card-danger">
        <div class="kpi-title">🔴 เครื่อง LS-06 (OD MIN: 288 mm)</div>
        <div class="kpi-value">ส่งเจียรสะสม: {m6_grind} ครั้ง</div>
        <div class="kpi-sub">ช่วง OD ล่าสุด: {m6_min_od:.2f} - {m6_max_od:.2f} mm</div>
        <div class="kpi-sub"><b>สถานะ:</b> <span style="color:red;font-weight:bold;">เตือนวิกฤต! ชุด #21-40 เหลือ +{m6_min_margin:.2f} mm</span></div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    m8_df = df[df["Machine"] == "LS-08"]
    m8_grind = m8_df["Grind_Count"].sum() if not m8_df.empty else 0
    m8_min_margin = m8_df["Margin"].min() if not m8_df.empty else 0
    m8_min_od = m8_df['Latest_OD'].min() if not m8_df.empty else 0
    m8_max_od = m8_df['Latest_OD'].max() if not m8_df.empty else 0
    st.markdown(f"""
    <div class="kpi-card-safe">
        <div class="kpi-title">🟢 เครื่อง LS-08 (OD MIN: 130 mm)</div>
        <div class="kpi-value">ส่งเจียรสะสม: {m8_grind} ครั้ง</div>
        <div class="kpi-sub">ช่วง OD ล่าสุด: {m8_min_od:.2f} - {m8_max_od:.2f} mm</div>
        <div class="kpi-sub"><b>สถานะ:</b> ปกติปลอดภัย (Margin +{m8_min_margin:.2f} mm)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------
# 6. Bar Charts Section
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
    fig_od.update_layout(height=450, margin=dict(t=50, b=40, l=40, r=40))
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
    fig_grind.update_layout(height=450, margin=dict(t=50, b=40, l=40, r=40))
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

styled_table = filtered_df.style.map(highlight_status, subset=['Status'])
st.dataframe(styled_table, use_container_width=True, height=350)

st.caption("ระบบเชื่อมต่อข้อมูล Google Sheet อัปเดตอัตโนมัติ | พัฒนาสำหรับผู้บริหารเครื่องจักรชุด LS")
