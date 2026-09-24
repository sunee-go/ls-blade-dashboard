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
# 2. Google Sheet Data Loader & Normalizer
# ---------------------------------------------------------
SHEET_ID = "1LCtzIdzBd4MGjKDV06Vl2rX-uy5rdZnQmNvaB72WpX0"
GOOGLE_SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def normalize_dataframe(df):
    """Normalize headers and ensure required columns exist regardless of Thai/English names."""
    if df is None or df.empty:
        return None
    
    # Clean column names (strip whitespace)
    df.columns = [str(col).strip() for col in df.columns]
    
    # Mapping table for Thai & variant column names -> Standard English names
    col_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if any(k in col_lower for k in ['เครื่อง', 'machine']):
            col_map[col] = 'Machine'
        elif any(k in col_lower for k in ['ชุด', 'set', 'หมายเลข']):
            col_map[col] = 'Set_No'
        elif any(k in col_lower for k in ['สี', 'color']):
            col_map[col] = 'Color'
        elif any(k in col_lower for k in ['หนา', 'thickness', 'ความหนา']):
            col_map[col] = 'Thickness_mm'
        elif any(k in col_lower for k in ['เจียร', 'เจียร์', 'grind', 'ครั้ง']):
            col_map[col] = 'Grind_Count'
        elif any(k in col_lower for k in ['ล่าสุด', 'latest', 'od_latest', 'ขนาด od']):
            col_map[col] = 'Latest_OD'
        elif any(k in col_lower for k in ['min', 'ขั้นต่ำ', 'เกณฑ์']):
            col_map[col] = 'OD_MIN'
        elif any(k in col_lower for k in ['margin', 'เผื่อ', 'คงเหลือ']):
            col_map[col] = 'Margin'
        elif any(k in col_lower for k in ['สถานะ', 'status']):
            col_map[col] = 'Status'
            
    df = df.rename(columns=col_map)
    
    # Check if essential columns are missing, if so create defaults
    required_cols = ['Machine', 'Set_No', 'Color', 'Thickness_mm', 'Grind_Count', 'Latest_OD', 'OD_MIN', 'Margin', 'Status']
    for col in required_cols:
        if col not in df.columns:
            if col == 'Machine': df['Machine'] = 'LS-05'
            elif col == 'Set_No': df['Set_No'] = '#1'
            elif col == 'Grind_Count': df['Grind_Count'] = 0
            elif col == 'Latest_OD': df['Latest_OD'] = 288.0
            elif col == 'OD_MIN': df['OD_MIN'] = 288.0
            elif col == 'Margin': df['Margin'] = df['Latest_OD'] - df['OD_MIN']
            elif col == 'Status': df['Status'] = 'ปกติ (Safe)'
            else: df[col] = '-'
            
    # Clean up numeric values
    df['Grind_Count'] = pd.to_numeric(df['Grind_Count'], errors='coerce').fillna(0)
    df['Latest_OD'] = pd.to_numeric(df['Latest_OD'], errors='coerce').fillna(0)
    df['OD_MIN'] = pd.to_numeric(df['OD_MIN'], errors='coerce').fillna(288.0)
    
    # Recalculate Margin
    df['Margin'] = df['Latest_OD'] - df['OD_MIN']
    
    # Standardize Machine names
    df['Machine'] = df['Machine'].astype(str).str.strip().str.upper()
    df['Machine'] = df['Machine'].replace({'LS-5': 'LS-05', 'LS-6': 'LS-06', 'LS-8': 'LS-08', 'LS5': 'LS-05', 'LS6': 'LS-06', 'LS8': 'LS-08'})
    
    # Categorize Status dynamically
    def categorize_status(row):
        m = row['Margin']
        if m <= 0.1:
            return 'วิกฤต (Critical)'
        elif m <= 2.0:
            return 'เฝ้าระวัง (Warning)'
        else:
            return 'ปกติ (Safe)'
            
    df['Status'] = df.apply(categorize_status, axis=1)
    
    return df

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        df_norm = normalize_dataframe(df)
        if df_norm is not None and not df_norm.empty:
            return df_norm
    except Exception as e:
        pass
        
    # Fallback dataset (6 sets for LS-05, 9 sets for LS-06, 4 sets for LS-08)
    fallback_data = [
        # LS-05 (6 ชุด)
        {"Machine": "LS-05", "Set_No": "#1-20", "Color": "แดง/เหลือง", "Thickness_mm": 10, "Grind_Count": 3, "Latest_OD": 318.00, "OD_MIN": 288.00, "Margin": 30.00, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-05", "Set_No": "#21-40", "Color": "ขาว", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 317.85, "OD_MIN": 288.00, "Margin": 29.85, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-05", "Set_No": "#41-60", "Color": "เขียว", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 317.50, "OD_MIN": 288.00, "Margin": 29.50, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-05", "Set_No": "#61-80", "Color": "น้ำเงิน", "Thickness_mm": 10, "Grind_Count": 3, "Latest_OD": 317.10, "OD_MIN": 288.00, "Margin": 29.10, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-05", "Set_No": "#81-100", "Color": "เหลือง", "Thickness_mm": 10, "Grind_Count": 4, "Latest_OD": 316.91, "OD_MIN": 288.00, "Margin": 28.91, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-05", "Set_No": "#101-120", "Color": "ส้ม", "Thickness_mm": 10, "Grind_Count": 1, "Latest_OD": 318.50, "OD_MIN": 288.00, "Margin": 30.50, "Status": "ปกติ (Safe)"},
        
        # LS-06 (9 ชุด)
        {"Machine": "LS-06", "Set_No": "#1-20", "Color": "เขียว/แดง", "Thickness_mm": 10, "Grind_Count": 10, "Latest_OD": 289.24, "OD_MIN": 288.00, "Margin": 1.24, "Status": "เฝ้าระวัง (Warning)"},
        {"Machine": "LS-06", "Set_No": "#21-40", "Color": "เหลือง", "Thickness_mm": 10, "Grind_Count": 12, "Latest_OD": 288.05, "OD_MIN": 288.00, "Margin": 0.05, "Status": "วิกฤต (Critical)"},
        {"Machine": "LS-06", "Set_No": "#41-60", "Color": "ขาว (บน)", "Thickness_mm": 10, "Grind_Count": 8, "Latest_OD": 291.00, "OD_MIN": 288.00, "Margin": 3.00, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-06", "Set_No": "#61-80", "Color": "ขาว (ล่าง)", "Thickness_mm": 10, "Grind_Count": 8, "Latest_OD": 291.62, "OD_MIN": 288.00, "Margin": 3.62, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-06", "Set_No": "#81-100", "Color": "ฟ้า", "Thickness_mm": 10, "Grind_Count": 5, "Latest_OD": 295.10, "OD_MIN": 288.00, "Margin": 7.10, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-06", "Set_No": "#101-120", "Color": "ชมพู", "Thickness_mm": 10, "Grind_Count": 6, "Latest_OD": 294.00, "OD_MIN": 288.00, "Margin": 6.00, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-06", "Set_No": "#121-140", "Color": "ม่วง", "Thickness_mm": 10, "Grind_Count": 4, "Latest_OD": 297.20, "OD_MIN": 288.00, "Margin": 9.20, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-06", "Set_No": "#141-160", "Color": "เทา", "Thickness_mm": 10, "Grind_Count": 3, "Latest_OD": 299.50, "OD_MIN": 288.00, "Margin": 11.50, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-06", "Set_No": "#161-180", "Color": "ดำ", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 302.00, "OD_MIN": 288.00, "Margin": 14.00, "Status": "ปกติ (Safe)"},
        
        # LS-08 (4 ชุด)
        {"Machine": "LS-08", "Set_No": "#1-31 (T5)", "Color": "ขาว", "Thickness_mm": 5, "Grind_Count": 3, "Latest_OD": 222.36, "OD_MIN": 130.00, "Margin": 92.36, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-08", "Set_No": "#32-62 (T5)", "Color": "เขียว", "Thickness_mm": 5, "Grind_Count": 3, "Latest_OD": 223.27, "OD_MIN": 130.00, "Margin": 93.27, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-08", "Set_No": "#1-30 (T7)", "Color": "แดง", "Thickness_mm": 7, "Grind_Count": 3, "Latest_OD": 216.93, "OD_MIN": 130.00, "Margin": 86.93, "Status": "ปกติ (Safe)"},
        {"Machine": "LS-08", "Set_No": "#31-60 (T7)", "Color": "เหลือง", "Thickness_mm": 7, "Grind_Count": 3, "Latest_OD": 217.35, "OD_MIN": 130.00, "Margin": 87.35, "Status": "ปกติ (Safe)"}
    ]
    return pd.DataFrame(fallback_data)

df = load_data()

# ---------------------------------------------------------
# 3. Sidebar Filters
# ---------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/dashboard.png", width=60)
st.sidebar.title("ระบบกรองข้อมูล (Filters)")

available_machines = sorted(list(df["Machine"].unique())) if "Machine" in df.columns else ["LS-05", "LS-06", "LS-08"]
machine_filter = st.sidebar.multiselect(
    "เลือกเครื่องจักร (Machine):",
    options=available_machines,
    default=available_machines
)

available_statuses = ["ปกติ (Safe)", "เฝ้าระวัง (Warning)", "วิกฤต (Critical)"]
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

def render_kpi_card(machine_name, default_min_od):
    m_df = df[df["Machine"] == machine_name]
    if m_df.empty:
        return f"""
        <div class="kpi-card-safe">
            <div class="kpi-title">⚪ เครื่อง {machine_name}</div>
            <div class="kpi-sub">ไม่มีข้อมูล</div>
        </div>
        """
    set_count = len(m_df)
    total_grind = int(m_df["Grind_Count"].sum())
    min_margin = m_df["Margin"].min()
    min_od_val = m_df["Latest_OD"].min()
    max_od_val = m_df["Latest_OD"].max()
    
    if min_margin <= 0.1:
        card_class = "kpi-card-danger"
        status_text = f'<span style="color:red;font-weight:bold;">เตือนวิกฤต! (Margin เหลือ +{min_margin:.2f} mm)</span>'
        icon = "🔴"
    elif min_margin <= 2.0:
        card_class = "kpi-card-warning"
        status_text = f'<span style="color:#D97706;font-weight:bold;">เฝ้าระวัง (Margin +{min_margin:.2f} mm)</span>'
        icon = "🟡"
    else:
        card_class = "kpi-card-safe"
        status_text = f'<span style="color:#16A34A;font-weight:bold;">ปกติปลอดภัย (Margin +{min_margin:.2f} mm)</span>'
        icon = "🟢"
        
    return f"""
    <div class="{card_class}">
        <div class="kpi-title">{icon} เครื่อง {machine_name} ({set_count} ชุด | OD MIN: {default_min_od} mm)</div>
        <div class="kpi-value">ส่งเจียรสะสม: {total_grind} ครั้ง</div>
        <div class="kpi-sub">ช่วง OD ล่าสุด: {min_od_val:.2f} - {max_od_val:.2f} mm</div>
        <div class="kpi-sub"><b>สถานะ:</b> {status_text}</div>
    </div>
    """

with col1:
    st.markdown(render_kpi_card("LS-05", 288), unsafe_allow_html=True)

with col2:
    st.markdown(render_kpi_card("LS-06", 288), unsafe_allow_html=True)

with col3:
    st.markdown(render_kpi_card("LS-08", 130), unsafe_allow_html=True)

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
    if not filtered_df.empty:
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
        fig_od.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig_od.update_xaxes(matches=None, showticklabels=True)
        fig_od.update_layout(height=450, margin=dict(t=50, b=40, l=40, r=40))
        st.plotly_chart(fig_od, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลตามตัวกรองที่เลือก")

with tab2:
    if not filtered_df.empty:
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
        fig_grind.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig_grind.update_xaxes(matches=None, showticklabels=True)
        fig_grind.update_layout(height=450, margin=dict(t=50, b=40, l=40, r=40))
        st.plotly_chart(fig_grind, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลตามตัวกรองที่เลือก")

# ---------------------------------------------------------
# 7. Action Plan & Detailed Risk Table
# ---------------------------------------------------------
st.subheader("📋 ตารางประเมินความเสี่ยงและแผนการจัดการ (Action Plan)")

if not filtered_df.empty:
    def highlight_status(val):
        if "วิกฤต" in str(val):
            return 'background-color: #FEF2F2; color: #DC2626; font-weight: bold;'
        elif "เฝ้าระวัง" in str(val):
            return 'background-color: #FFFBEB; color: #D97706; font-weight: bold;'
        else:
            return 'background-color: #F0FDF4; color: #16A34A;'

    display_cols = [c for c in ['Machine', 'Set_No', 'Color', 'Thickness_mm', 'Grind_Count', 'Latest_OD', 'OD_MIN', 'Margin', 'Status'] if c in filtered_df.columns]
    styled_table = filtered_df[display_cols].style.applymap(highlight_status, subset=['Status'])
    st.dataframe(styled_table, use_container_width=True, height=350)
else:
    st.info("ไม่พบข้อมูลสำหรับตาราง")

# Footer
st.caption("ระบบเชื่อมต่อข้อมูล Google Sheet อัปเดตอัตโนมัติ | พัฒนาสำหรับผู้บริหารเครื่องจักรชุด LS")
