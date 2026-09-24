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

def normalize_dataframe(raw_df):
    """Clean and map Google Sheet columns (Thai/English) to standard keys safely."""
    df = raw_df.copy()
    # Strip whitespace from column names
    df.columns = [str(c).strip() for c in df.columns]
    
    # Column mapping dictionary
    col_mapping = {}
    for c in df.columns:
        c_lower = c.lower()
        if any(k in c_lower or k in c for k in ['เครื่อง', 'machine', 'ls-']):
            col_mapping[c] = 'Machine'
        elif any(k in c_lower or k in c for k in ['ชุด', 'set']):
            col_mapping[c] = 'Set_No'
        elif any(k in c_lower or k in c for k in ['สี', 'color']):
            col_mapping[c] = 'Color'
        elif any(k in c_lower or k in c for k in ['ความหนา', 'thickness']):
            col_mapping[c] = 'Thickness_mm'
        elif any(k in c_lower or k in c for k in ['เจียร', 'เจียร์', 'grind']):
            col_mapping[c] = 'Grind_Count'
        elif any(k in c_lower or k in c for k in ['latest_od', 'ขนาด od', 'od ล่าสุด', 'od(mm)', 'od']):
            col_mapping[c] = 'Latest_OD'
        elif any(k in c_lower or k in c for k in ['od_min', 'od min', 'ขั้นต่ำ', 'min']):
            col_mapping[c] = 'OD_MIN'
        elif any(k in c_lower or k in c for k in ['margin', 'ระยะ', 'คงเหลือ']):
            col_mapping[c] = 'Margin'
        elif any(k in c_lower or k in c for k in ['สถานะ', 'status']):
            col_mapping[c] = 'Status'
        elif any(k in c_lower or k in c for k in ['ตรวจ', 'inspector', 'ผู้บันทึก']):
            col_mapping[c] = 'Inspector'
            
    df = df.rename(columns=col_mapping)
    
    # Ensure mandatory columns exist
    if 'Machine' not in df.columns:
        df['Machine'] = 'LS-05'
    if 'Set_No' not in df.columns:
        df['Set_No'] = [f'#{i+1}' for i in range(len(df))]
    if 'Grind_Count' not in df.columns:
        df['Grind_Count'] = 0
    if 'Latest_OD' not in df.columns:
        df['Latest_OD'] = 300.0
        
    # Clean Machine name values (e.g. LS-5 -> LS-05)
    df['Machine'] = df['Machine'].astype(str).str.strip().str.upper()
    df['Machine'] = df['Machine'].replace({'LS-5': 'LS-05', 'LS-6': 'LS-06', 'LS-8': 'LS-08'})
    
    # Ensure numeric types
    df['Latest_OD'] = pd.to_numeric(df['Latest_OD'], errors='coerce').fillna(300.0)
    df['Grind_Count'] = pd.to_numeric(df['Grind_Count'], errors='coerce').fillna(0).astype(int)
    
    # Set default OD_MIN based on Machine if missing
    if 'OD_MIN' not in df.columns:
        def get_default_min(m):
            return 130.0 if '08' in str(m) else 288.0
        df['OD_MIN'] = df['Machine'].apply(get_default_min)
    else:
        df['OD_MIN'] = pd.to_numeric(df['OD_MIN'], errors='coerce').fillna(288.0)
        
    # Calculate Margin if missing
    if 'Margin' not in df.columns:
        df['Margin'] = df['Latest_OD'] - df['OD_MIN']
    else:
        df['Margin'] = pd.to_numeric(df['Margin'], errors='coerce').fillna(df['Latest_OD'] - df['OD_MIN'])
        
    # Normalize or Calculate Status if missing
    def calculate_status(row):
        margin = row['Margin']
        if margin <= 0.5:
            return "วิกฤต (Critical)"
        elif margin <= 2.0:
            return "เฝ้าระวัง (Warning)"
        else:
            return "ปกติ (Safe)"

    if 'Status' not in df.columns:
        df['Status'] = df.apply(calculate_status, axis=1)
    else:
        def clean_status_val(val):
            val_str = str(val).strip()
            if 'วิกฤต' in val_str or 'Critical' in val_str or 'CRITICAL' in val_str:
                return "วิกฤต (Critical)"
            elif 'เฝ้าระวัง' in val_str or 'Warning' in val_str or 'WARN' in val_str:
                return "เฝ้าระวัง (Warning)"
            else:
                return "ปกติ (Safe)"
        df['Status'] = df['Status'].apply(clean_status_val)
        
    return df

@st.cache_data(ttl=60)
def load_data():
    try:
        df_raw = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        if not df_raw.empty:
            return normalize_dataframe(df_raw)
    except Exception as e:
        pass
        
    # Fallback structured dataset
    fallback_data = [
        # LS-05 (6 ชุด)
        {"Machine": "LS-05", "Set_No": "#1-20", "Color": "แดง/เหลือง", "Thickness_mm": 10, "Grind_Count": 3, "Latest_OD": 318.00, "OD_MIN": 288.00, "Margin": 30.00, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-05", "Set_No": "#21-40", "Color": "ขาว", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 317.85, "OD_MIN": 288.00, "Margin": 29.85, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-05", "Set_No": "#41-60", "Color": "เขียว", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 317.50, "OD_MIN": 288.00, "Margin": 29.50, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-05", "Set_No": "#61-80", "Color": "น้ำเงิน", "Thickness_mm": 10, "Grind_Count": 3, "Latest_OD": 317.10, "OD_MIN": 288.00, "Margin": 29.10, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-05", "Set_No": "#81-100", "Color": "เหลือง", "Thickness_mm": 10, "Grind_Count": 4, "Latest_OD": 316.91, "OD_MIN": 288.00, "Margin": 28.91, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-05", "Set_No": "#101-120", "Color": "ส้ม", "Thickness_mm": 10, "Grind_Count": 1, "Latest_OD": 319.20, "OD_MIN": 288.00, "Margin": 31.20, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        
        # LS-06 (9 ชุด)
        {"Machine": "LS-06", "Set_No": "#1-20", "Color": "เขียว/แดง", "Thickness_mm": 10, "Grind_Count": 10, "Latest_OD": 289.24, "OD_MIN": 288.00, "Margin": 1.24, "Status": "เฝ้าระวัง (Warning)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#21-40", "Color": "เหลือง", "Thickness_mm": 10, "Grind_Count": 12, "Latest_OD": 288.05, "OD_MIN": 288.00, "Margin": 0.05, "Status": "วิกฤต (Critical)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#41-60", "Color": "ขาว (บน)", "Thickness_mm": 10, "Grind_Count": 8, "Latest_OD": 291.00, "OD_MIN": 288.00, "Margin": 3.00, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#61-80", "Color": "ขาว (ล่าง)", "Thickness_mm": 10, "Grind_Count": 8, "Latest_OD": 291.62, "OD_MIN": 288.00, "Margin": 3.62, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#81-100", "Color": "ฟ้า", "Thickness_mm": 10, "Grind_Count": 5, "Latest_OD": 298.40, "OD_MIN": 288.00, "Margin": 10.40, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#101-120", "Color": "ม่วง", "Thickness_mm": 10, "Grind_Count": 4, "Latest_OD": 302.10, "OD_MIN": 288.00, "Margin": 14.10, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#121-140", "Color": "ชมพู", "Thickness_mm": 10, "Grind_Count": 3, "Latest_OD": 305.50, "OD_MIN": 288.00, "Margin": 17.50, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#141-160", "Color": "เทา", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 310.00, "OD_MIN": 288.00, "Margin": 22.00, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#161-180", "Color": "ดำ", "Thickness_mm": 10, "Grind_Count": 1, "Latest_OD": 315.20, "OD_MIN": 288.00, "Margin": 27.20, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},

        # LS-08 (4 ชุด - T5/T7)
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

machine_options = sorted(list(df["Machine"].unique())) if "Machine" in df.columns else ["LS-05", "LS-06", "LS-08"]
machine_filter = st.sidebar.multiselect(
    "เลือกเครื่องจักร (Machine):",
    options=machine_options,
    default=machine_options
)

status_options = ["ปกติ (Safe)", "เฝ้าระวัง (Warning)", "วิกฤต (Critical)"]
status_filter = st.sidebar.multiselect(
    "เลือกสถานะ (Status):",
    options=status_options,
    default=status_options
)

# Safe Filter Application
filtered_df = df.copy()
if "Machine" in filtered_df.columns and machine_filter:
    filtered_df = filtered_df[filtered_df["Machine"].isin(machine_filter)]
if "Status" in filtered_df.columns and status_filter:
    filtered_df = filtered_df[filtered_df["Status"].isin(status_filter)]

# ---------------------------------------------------------
# 4. Header Section
# ---------------------------------------------------------
st.markdown('<div class="main-header">🔪 Executive Blade Monitoring Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ระบบติดตามสภาพหน้าใบมีดสลิตชุดเครื่อง LS-05, LS-06, LS-08 (เชื่อมต่อ Google Sheet)</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Executive KPI Summary Cards
# ---------------------------------------------------------
st.subheader("📊 สรุปภาพรวมรายเครื่องจักร (Executive Summary)")
col1, col2, col3 = st.columns(3)

def render_kpi_card(machine_name, od_min_default, is_danger=False):
    m_df = df[df["Machine"] == machine_name] if "Machine" in df.columns else pd.DataFrame()
    if not m_df.empty:
        grind_sum = int(m_df["Grind_Count"].sum())
        min_margin = m_df["Margin"].min()
        min_od = m_df["Latest_OD"].min()
        max_od = m_df["Latest_OD"].max()
        count_sets = len(m_df)
    else:
        grind_sum, min_margin, min_od, max_od, count_sets = 0, 0, 0, 0, 0
        
    card_class = "kpi-card-danger" if is_danger or min_margin <= 0.5 else "kpi-card-safe"
    status_text = f'<span style="color:red;font-weight:bold;">เตือนวิกฤต! เหลือ +{min_margin:.2f} mm</span>' if min_margin <= 0.5 else f'ปกติปลอดภัย (Margin +{min_margin:.2f} mm)'
    
    return f"""
    <div class="{card_class}">
        <div class="kpi-title">เครื่อง {machine_name} (OD MIN: {od_min_default} mm | รวม {count_sets} ชุด)</div>
        <div class="kpi-value">ส่งเจียรสะสม: {grind_sum} ครั้ง</div>
        <div class="kpi-sub">ช่วง OD ล่าสุด: {min_od:.2f} - {max_od:.2f} mm</div>
        <div class="kpi-sub"><b>สถานะ:</b> {status_text}</div>
    </div>
    """

with col1:
    st.markdown(render_kpi_card("LS-05", 288.0), unsafe_allow_html=True)

with col2:
    st.markdown(render_kpi_card("LS-06", 288.0, is_danger=True), unsafe_allow_html=True)

with col3:
    st.markdown(render_kpi_card("LS-08", 130.0), unsafe_allow_html=True)

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
        fig_od.update_xaxes(matches=None)  # Independent X axes for each machine facet
        
        # Adjust Y-axis scale: range 100 to 320 with step 20
        fig_od.update_yaxes(range=[100, 320], dtick=20)
        
        fig_od.update_layout(height=480, margin=dict(t=50, b=40, l=40, r=40))
        st.plotly_chart(fig_od, use_container_width=True)
    else:
        st.warning("ไม่พบข้อมูลตามตัวกรองที่เลือก")

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
        fig_grind.update_xaxes(matches=None)  # Independent X axes
        fig_grind.update_layout(height=480, margin=dict(t=50, b=40, l=40, r=40))
        st.plotly_chart(fig_grind, use_container_width=True)
    else:
        st.warning("ไม่พบข้อมูลตามตัวกรองที่เลือก")

# ---------------------------------------------------------
# 7. Action Plan & Detailed Risk Table
# ---------------------------------------------------------
st.subheader("📋 ตารางประเมินความเสี่ยงและแผนการจัดการ (Action Plan)")

def highlight_status(val):
    val_str = str(val)
    if "วิกฤต" in val_str or "Critical" in val_str:
        return 'background-color: #FEF2F2; color: #DC2626; font-weight: bold;'
    elif "เฝ้าระวัง" in val_str or "Warning" in val_str:
        return 'background-color: #FFFBEB; color: #D97706; font-weight: bold;'
    else:
        return 'background-color: #F0FDF4; color: #16A34A;'

if not filtered_df.empty:
    display_cols = [c for c in ['Machine', 'Set_No', 'Color', 'Thickness_mm', 'Grind_Count', 'Latest_OD', 'OD_MIN', 'Margin', 'Status', 'Inspector'] if c in filtered_df.columns]
    
    # Check Pandas version compatibility for map/applymap
    st_builder = filtered_df[display_cols].style
    if hasattr(st_builder, 'map'):
        styled_table = st_builder.map(highlight_status, subset=['Status'] if 'Status' in display_cols else None)
    else:
        styled_table = st_builder.applymap(highlight_status, subset=['Status'] if 'Status' in display_cols else None)
        
    st.dataframe(styled_table, use_container_width=True, height=350)
else:
    st.info("ไม่มีข้อมูลแสดงผลในตาราง")

# Footer
st.caption("ระบบเชื่อมต่อข้อมูล Google Sheet อัปเดตอัตโนมัติ | พัฒนาสำหรับผู้บริหารเครื่องจักรชุด LS")
