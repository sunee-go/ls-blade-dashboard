import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="LS Blade Executive Dashboard",
    page_icon="🔪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
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
# 2. Data Loading & Normalization
# ---------------------------------------------------------
SHEET_ID = "1LCtzIdzBd4MGjKDV06Vl2rX-uy5rdZnQmNvaB72WpX0"
GOOGLE_SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def normalize_dataframe(df):
    col_map = {}
    for col in df.columns:
        c_clean = str(col).strip().lower()
        if 'เครื่อง' in c_clean or 'machine' in c_clean:
            col_map[col] = 'Machine'
        elif 'ชุด' in c_clean or 'set' in c_clean or 'หมายเลข' in c_clean:
            col_map[col] = 'Set_No'
        elif 'สี' in c_clean or 'color' in c_clean:
            col_map[col] = 'Color'
        elif 'หนา' in c_clean or 'thick' in c_clean:
            col_map[col] = 'Thickness_mm'
        elif 'เจียร' in c_clean or 'grind' in c_clean or 'ครั้ง' in c_clean:
            col_map[col] = 'Grind_Count'
        elif 'ล่าสุด' in c_clean or 'od_latest' in c_clean or 'latest' in c_clean:
            col_map[col] = 'Latest_OD'
        elif 'min' in c_clean or 'ขั้นต่ำ' in c_clean:
            col_map[col] = 'OD_MIN'
        elif 'margin' in c_clean or 'ระยะ' in c_clean or 'เหลือ' in c_clean:
            col_map[col] = 'Margin'
        elif 'สถานะ' in c_clean or 'status' in c_clean:
            col_map[col] = 'Status'
        elif 'ผู้ตรวจ' in c_clean or 'inspector' in c_clean or 'ชื่อ' in c_clean:
            col_map[col] = 'Inspector'

    df = df.rename(columns=col_map)
    
    for col in ['Thickness_mm', 'Grind_Count', 'Latest_OD', 'OD_MIN', 'Margin']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    if 'Machine' not in df.columns:
        df['Machine'] = 'LS-05'
    if 'Set_No' not in df.columns:
        df['Set_No'] = df.index.map(lambda x: f"#{x+1}")
    if 'OD_MIN' not in df.columns:
        df['OD_MIN'] = df['Machine'].map({'LS-05': 288.0, 'LS-06': 288.0, 'LS-08': 130.0}).fillna(288.0)
    if 'Margin' not in df.columns and 'Latest_OD' in df.columns:
        df['Margin'] = df['Latest_OD'] - df['OD_MIN']
    if 'Status' not in df.columns and 'Margin' in df.columns:
        def calc_status(m):
            if m <= 0.1:
                return 'วิกฤต (Critical)'
            elif m <= 2.0:
                return 'เฝ้าระวัง (Warning)'
            return 'ปกติ (Safe)'
        df['Status'] = df['Margin'].apply(calc_status)
        
    return df

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        df = normalize_dataframe(df)
        if len(df) > 0 and 'Machine' in df.columns:
            return df
    except Exception as e:
        pass

    fallback_data = [
        # LS-05 (6 ชุด)
        {"Machine": "LS-05", "Set_No": "#1-20", "Color": "แดง/เหลือง", "Thickness_mm": 10, "Grind_Count": 3, "Latest_OD": 318.00, "OD_MIN": 288.00, "Margin": 30.00, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-05", "Set_No": "#21-40", "Color": "ขาว", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 317.85, "OD_MIN": 288.00, "Margin": 29.85, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-05", "Set_No": "#41-60", "Color": "เขียว", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 317.50, "OD_MIN": 288.00, "Margin": 29.50, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-05", "Set_No": "#61-80", "Color": "ฟ้า", "Thickness_mm": 10, "Grind_Count": 1, "Latest_OD": 319.10, "OD_MIN": 288.00, "Margin": 31.10, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-05", "Set_No": "#81-100", "Color": "เหลือง", "Thickness_mm": 10, "Grind_Count": 4, "Latest_OD": 316.91, "OD_MIN": 288.00, "Margin": 28.91, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-05", "Set_No": "#101-120", "Color": "ส้ม", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 318.20, "OD_MIN": 288.00, "Margin": 30.20, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        
        # LS-06 (9 ชุด)
        {"Machine": "LS-06", "Set_No": "#1-20", "Color": "เขียว/แดง", "Thickness_mm": 10, "Grind_Count": 10, "Latest_OD": 289.24, "OD_MIN": 288.00, "Margin": 1.24, "Status": "เฝ้าระวัง (Warning)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#21-40", "Color": "เหลือง", "Thickness_mm": 10, "Grind_Count": 12, "Latest_OD": 288.05, "OD_MIN": 288.00, "Margin": 0.05, "Status": "วิกฤต (Critical)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#41-60", "Color": "ขาว (บน)", "Thickness_mm": 10, "Grind_Count": 8, "Latest_OD": 291.00, "OD_MIN": 288.00, "Margin": 3.00, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#61-80", "Color": "ขาว (ล่าง)", "Thickness_mm": 10, "Grind_Count": 8, "Latest_OD": 291.62, "OD_MIN": 288.00, "Margin": 3.62, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#81-100", "Color": "น้ำเงิน", "Thickness_mm": 10, "Grind_Count": 6, "Latest_OD": 293.40, "OD_MIN": 288.00, "Margin": 5.40, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#101-120", "Color": "เทา", "Thickness_mm": 10, "Grind_Count": 5, "Latest_OD": 294.50, "OD_MIN": 288.00, "Margin": 6.50, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#121-140", "Color": "ม่วง", "Thickness_mm": 10, "Grind_Count": 4, "Latest_OD": 296.10, "OD_MIN": 288.00, "Margin": 8.10, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#141-160", "Color": "ชมพู", "Thickness_mm": 10, "Grind_Count": 3, "Latest_OD": 297.80, "OD_MIN": 288.00, "Margin": 9.80, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        {"Machine": "LS-06", "Set_No": "#161-180", "Color": "น้ำตาล", "Thickness_mm": 10, "Grind_Count": 2, "Latest_OD": 299.00, "OD_MIN": 288.00, "Margin": 11.00, "Status": "ปกติ (Safe)", "Inspector": "สมชาย / กิตติ"},
        
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

machine_options = sorted(list(df['Machine'].unique())) if 'Machine' in df.columns else ["LS-05", "LS-06", "LS-08"]
status_options = ["ปกติ (Safe)", "เฝ้าระวัง (Warning)", "วิกฤต (Critical)"]

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
st.markdown('<div class="sub-header">ระบบติดตามสภาพหน้าใบมีดสลิตชุดเครื่อง LS-05, LS-06, LS-08 (เชื่อมต่อ Google Sheet)</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Executive KPI Summary Cards
# ---------------------------------------------------------
st.subheader("📊 สรุปภาพรวมรายเครื่องจักร (Executive Summary)")
col1, col2, col3 = st.columns(3)

def render_kpi(col, m_name, od_min, card_type, status_text_extra=""):
    with col:
        m_df = df[df["Machine"] == m_name]
        if len(m_df) > 0:
            m_grind = int(m_df["Grind_Count"].sum()) if "Grind_Count" in m_df else 0
            m_min_margin = m_df["Margin"].min() if "Margin" in m_df else 0.0
            min_od = m_df['Latest_OD'].min() if "Latest_OD" in m_df else 0
            max_od = m_df['Latest_OD'].max() if "Latest_OD" in m_df else 0
            count_sets = len(m_df)
            
            st.markdown(f"""
            <div class="{card_type}">
                <div class="kpi-title">{m_name} (OD MIN: {od_min:.0f} mm | {count_sets} ชุด)</div>
                <div class="kpi-value">ส่งเจียรสะสม: {m_grind} ครั้ง</div>
                <div class="kpi-sub">ช่วง OD ล่าสุด: {min_od:.2f} - {max_od:.2f} mm</div>
                <div class="kpi-sub"><b>สถานะ:</b> {status_text_extra if status_text_extra else f'ปกติปลอดภัย (Margin +{m_min_margin:.2f} mm)'}</div>
            </div>
            """, unsafe_allow_html=True)

render_kpi(col1, "LS-05", 288, "kpi-card-safe", "🟢 ปกติปลอดภัยทุกชุด")
m6_crit = df[(df["Machine"]=="LS-06") & (df["Status"]=="วิกฤต (Critical)")]
if len(m6_crit) > 0:
    render_kpi(col2, "LS-06", 288, "kpi-card-danger", f'<span style="color:red;font-weight:bold;">🔴 เตือนวิกฤต! ชุด {m6_crit.iloc[0]["Set_No"]} เหลือ +{m6_crit.iloc[0]["Margin"]:.2f} mm</span>')
else:
    render_kpi(col2, "LS-06", 288, "kpi-card-safe", "🟢 ปกติปลอดภัยทุกชุด")
render_kpi(col3, "LS-08", 130, "kpi-card-safe", "🟢 ปกติปลอดภัยทุกชุด (T5/T7)")

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
    if len(filtered_df) > 0:
        fig_od = px.bar(
            filtered_df,
            x="Set_No",
            y="Latest_OD",
            color="Status",
            facet_col="Machine",
            color_discrete_map=color_map,
            text="Latest_OD",
            title="ค่า OD หลังเจียรล่าสุดแยกตามชุดใบมีด (mm) [สเกล 100 - 320 mm]",
            labels={"Set_No": "ชุดใบมีด / หมายเลข", "Latest_OD": "ขนาด OD (mm)"}
        )
        fig_od.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_od.update_xaxes(matches=None, showticklabels=True)
        # Set y-axis range from 100 to 320 with tick step of 20
        fig_od.update_yaxes(range=[100, 320], dtick=20)
        fig_od.update_layout(height=480, margin=dict(t=50, b=40, l=40, r=40))
        st.plotly_chart(fig_od, use_container_width=True)
    else:
        st.warning("ไม่พบข้อมูลตามตัวกรองที่เลือก")

with tab2:
    if len(filtered_df) > 0:
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
        fig_grind.update_xaxes(matches=None, showticklabels=True)
        fig_grind.update_layout(height=480, margin=dict(t=50, b=40, l=40, r=40))
        st.plotly_chart(fig_grind, use_container_width=True)
    else:
        st.warning("ไม่พบข้อมูลตามตัวกรองที่เลือก")

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

display_cols = [c for c in ['Machine', 'Set_No', 'Color', 'Thickness_mm', 'Grind_Count', 'Latest_OD', 'OD_MIN', 'Margin', 'Status', 'Inspector'] if c in filtered_df.columns]

if len(filtered_df) > 0:
    try:
        if hasattr(filtered_df.style, "map"):
            styled_table = filtered_df[display_cols].style.map(highlight_status, subset=['Status'])
        else:
            styled_table = filtered_df[display_cols].style.applymap(highlight_status, subset=['Status'])
        st.dataframe(styled_table, use_container_width=True, height=350)
    except Exception:
        st.dataframe(filtered_df[display_cols], use_container_width=True, height=350)

# Footer
st.caption("ระบบเชื่อมต่อข้อมูล Google Sheet อัปเดตอัตโนมัติ | พัฒนาสำหรับผู้บริหารเครื่องจักรชุด LS")
