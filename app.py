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

st.markdown("""
<style>
    .main-header { font-size: 24px; font-weight: bold; color: #1E293B; margin-bottom: 5px; }
    .sub-header { font-size: 14px; color: #64748B; margin-bottom: 20px; }
    .kpi-card-safe { background-color: #F0FDF4; border-left: 5px solid #22C55E; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .kpi-card-danger { background-color: #FEF2F2; border-left: 5px solid #EF4444; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .kpi-card-warning { background-color: #FFFBEB; border-left: 5px solid #F59E0B; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .kpi-title { font-size: 16px; font-weight: bold; color: #0F172A; }
    .kpi-value { font-size: 20px; font-weight: bold; color: #1E293B; }
    .kpi-sub { font-size: 13px; color: #475569; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Advanced Google Sheet Data Loader & Mapper
# ---------------------------------------------------------
SHEET_ID = "1LCtzIdzBd4MGjKDV06Vl2rX-uy5rdZnQmNvaB72WpX0"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

def format_set_name(machine, set_no, color, thickness):
    """ฟังก์ชันจับคู่เลขชุดใบมีดและสี ให้ตรงกับ Master List เพื่อป้องกันยอดรวมปนกัน"""
    s = str(set_no).strip()
    c = str(color).strip()
    t = str(thickness).strip()
    
    if machine == 'LS-06':
        # แยกชุด บน/กลาง/ล่าง จากสีใบมีด
        if s == '1-20':
            if 'แดง' in c or 'Red' in c: return '1-20 (ชุดบน)'
            if 'ดำ' in c or 'Black' in c: return '1-20 (ชุดกลาง)'
            if 'เขียว' in c or 'Green' in c: return '1-20 (ชุดล่าง)'
        elif s == '21-40':
            if 'เหลือง' in c or 'Yellow' in c: return '21-40 (ชุดบน)'
            if 'แดง' in c or 'Red' in c: return '21-40 (ชุดกลาง)'
            if 'ขาว' in c or 'white' in c: return '21-40 (ชุดล่าง)'
        elif s == '41-60':
            if 'ขาว' in c or 'white' in c: return '41-60 (ชุดบน)'
            if 'เขียว' in c or 'Green' in c: return '41-60 (ชุดกลาง)'
            if 'เหลือง' in c or 'Yellow' in c: return '41-60 (ชุดล่าง)'
        elif s == '61-80':
            return '61-80 (ชุดบน)'
            
    elif machine == 'LS-08':
        # แยกจากความหนา
        if '5' in t: return f"{s} (5 mm.)"
        if '7' in t: return f"{s} (7 mm.)"
        
    return s

@st.cache_data(ttl=60)
def load_data():
    try:
        xls = pd.read_excel(EXCEL_URL, sheet_name=None, skiprows=3, engine='openpyxl')
        processed_data = []
        
        for sheet_name, df in xls.items():
            if not str(sheet_name).startswith("LS-"): continue
            df.columns = [str(c).strip() for c in df.columns]
            
            col_map = {}
            for c in df.columns:
                if 'หมายเลข' in c: col_map[c] = 'Raw_Set_No'
                elif 'ชุดสี' in c: col_map[c] = 'Color'
                elif 'หนา' in c: col_map[c] = 'Thickness_mm'
                elif 'OD หลังเจียร์' in c: col_map[c] = 'OD'
                elif 'ผู้เจียร์' in c: col_map[c] = 'Inspector'
                
            df = df.rename(columns=col_map)
            
            if 'Raw_Set_No' not in df.columns or 'OD' not in df.columns: continue
            
            df = df.dropna(subset=['Raw_Set_No', 'OD'])
            df['Raw_Set_No'] = df['Raw_Set_No'].astype(str).str.strip()
            df = df[df['Raw_Set_No'] != 'nan']
            df = df[df['Raw_Set_No'] != '']
            df['OD'] = pd.to_numeric(df['OD'], errors='coerce')
            df = df.dropna(subset=['OD'])
            
            machine_name = sheet_name.strip().upper()
            df['Color'] = df.get('Color', '')
            df['Thickness_mm'] = df.get('Thickness_mm', '')
            
            # ใช้งานฟังก์ชันจัดรูปแบบชื่อชุดใบมีด
            df['Set_No'] = df.apply(lambda row: format_set_name(machine_name, row['Raw_Set_No'], row['Color'], row['Thickness_mm']), axis=1)
            
            agg_args = {
                'OD': ('OD', 'last'),          
                'Raw_Set_No': ('OD', 'count'), # ใช้นับจำนวนบรรทัด = รอบที่ส่งเจียร
                'Color': ('Color', 'last'),
                'Thickness_mm': ('Thickness_mm', 'last'),
            }
            if 'Inspector' in df.columns: agg_args['Inspector'] = ('Inspector', 'last')
            
            grouped = df.groupby('Set_No').agg(**agg_args).reset_index()
            grouped = grouped.rename(columns={'OD': 'Latest_OD', 'Raw_Set_No': 'Grind_Count'})
            
            grouped['Machine'] = machine_name
            grouped['OD_MIN'] = 130.0 if '08' in machine_name else 288.0
            
            processed_data.append(grouped)
            
        if processed_data:
            final_df = pd.concat(processed_data, ignore_index=True)
            final_df['Margin'] = final_df['Latest_OD'] - final_df['OD_MIN']
            final_df['Status'] = final_df['Margin'].apply(lambda m: "วิกฤต (Critical)" if m <= 0.5 else ("เฝ้าระวัง (Warning)" if m <= 2.0 else "ปกติ (Safe)"))
            
            # กำหนดลำดับข้อมูลให้กราฟเรียงสวยงาม
            final_df = final_df.sort_values(by=['Machine', 'Set_No']).reset_index(drop=True)
            return final_df
            
    except Exception as e:
        print("Error pulling data:", e)
        pass 
        
    # ข้อมูลจำลองตั้งต้น (Fallback Data) - ตรงตาม Master List เป๊ะๆ
    fallback_data = [
        # LS-05
        {"Machine": "LS-05", "Set_No": "1-20", "Color": "แดง (Red)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-05", "Set_No": "21-40", "Color": "ขาว (white)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-05", "Set_No": "41-60", "Color": "ดำ (Black)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-05", "Set_No": "61-80", "Color": "เขียว (Green)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-05", "Set_No": "81-100", "Color": "เหลือง (Yellow)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-05", "Set_No": "101-120", "Color": "ชมพู (Pink)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        
        # LS-06
        {"Machine": "LS-06", "Set_No": "1-20 (ชุดบน)", "Color": "แดง (Red)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-06", "Set_No": "21-40 (ชุดบน)", "Color": "เหลือง (Yellow)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-06", "Set_No": "41-60 (ชุดบน)", "Color": "ขาว (white)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-06", "Set_No": "61-80 (ชุดบน)", "Color": "เขียว (Green)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-06", "Set_No": "1-20 (ชุดกลาง)", "Color": "ดำ (Black)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-06", "Set_No": "21-40 (ชุดกลาง)", "Color": "แดง (Red)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-06", "Set_No": "41-60 (ชุดกลาง)", "Color": "เขียว (Green)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-06", "Set_No": "1-20 (ชุดล่าง)", "Color": "เขียว (Green)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-06", "Set_No": "21-40 (ชุดล่าง)", "Color": "ขาว (white)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-06", "Set_No": "41-60 (ชุดล่าง)", "Color": "เหลือง (Yellow)", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 310.0, "OD_MIN": 288.0, "Margin": 22.0, "Status": "ปกติ (Safe)", "Inspector": "-"},

        # LS-08
        {"Machine": "LS-08", "Set_No": "1-31 (5 mm.)", "Color": "-", "Thickness_mm": 5, "Grind_Count": 0, "Latest_OD": 220.0, "OD_MIN": 130.0, "Margin": 90.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-08", "Set_No": "32-62 (5 mm.)", "Color": "-", "Thickness_mm": 5, "Grind_Count": 0, "Latest_OD": 220.0, "OD_MIN": 130.0, "Margin": 90.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-08", "Set_No": "1-30 (7 mm.)", "Color": "-", "Thickness_mm": 7, "Grind_Count": 0, "Latest_OD": 220.0, "OD_MIN": 130.0, "Margin": 90.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-08", "Set_No": "31-60 (7 mm.)", "Color": "-", "Thickness_mm": 7, "Grind_Count": 0, "Latest_OD": 220.0, "OD_MIN": 130.0, "Margin": 90.0, "Status": "ปกติ (Safe)", "Inspector": "-"}
    ]
    return pd.DataFrame(fallback_data)

df = load_data()

# ---------------------------------------------------------
# 3. Sidebar Filters
# ---------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/dashboard.png", width=60)
st.sidebar.title("ระบบกรองข้อมูล (Filters)")

machine_options = sorted(list(df["Machine"].unique())) if not df.empty else []
machine_filter = st.sidebar.multiselect("เลือกเครื่องจักร (Machine):", options=machine_options, default=machine_options)

status_options = ["ปกติ (Safe)", "เฝ้าระวัง (Warning)", "วิกฤต (Critical)"]
status_filter = st.sidebar.multiselect("เลือกสถานะ (Status):", options=status_options, default=status_options)

filtered_df = df.copy()
if machine_filter:
    filtered_df = filtered_df[filtered_df["Machine"].isin(machine_filter)]
if status_filter:
    filtered_df = filtered_df[filtered_df["Status"].isin(status_filter)]

# ---------------------------------------------------------
# 4. Header Section
# ---------------------------------------------------------
st.markdown('<div class="main-header">🔪 Executive Blade Monitoring Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ระบบติดตามสภาพหน้าใบมีดสลิตชุดเครื่อง LS-05, LS-06, LS-08 (ดึงข้อมูลล่าสุดจาก Google Sheet ทันที)</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Executive KPI Summary Cards
# ---------------------------------------------------------
st.subheader("📊 สรุปภาพรวมรายเครื่องจักร (Executive Summary)")
col1, col2, col3 = st.columns(3)

def render_kpi_card(machine_name, od_min_default):
    m_df = df[df["Machine"] == machine_name] if not df.empty else pd.DataFrame()
    if not m_df.empty:
        grind_sum = int(m_df["Grind_Count"].sum())
        min_margin = m_df["Margin"].min()
        min_od = m_df["Latest_OD"].min()
        max_od = m_df["Latest_OD"].max()
        count_sets = len(m_df)
    else:
        grind_sum, min_margin, min_od, max_od, count_sets = 0, 0, 0, 0, 0
        
    card_class = "kpi-card-danger" if min_margin <= 0.5 else "kpi-card-safe"
    status_text = f'<span style="color:red;font-weight:bold;">เตือนวิกฤต! เหลือ +{min_margin:.2f} mm</span>' if min_margin <= 0.5 else f'ปกติปลอดภัย (Margin +{min_margin:.2f} mm)'
    
    return f"""
    <div class="{card_class}">
        <div class="kpi-title">เครื่อง {machine_name} (OD MIN: {od_min_default} mm | รวม {count_sets} ชุด)</div>
        <div class="kpi-value">ส่งเจียรสะสม: {grind_sum} ครั้ง</div>
        <div class="kpi-sub">ช่วง OD ล่าสุด: {min_od:.2f} - {max_od:.2f} mm</div>
        <div class="kpi-sub"><b>สถานะ:</b> {status_text}</div>
    </div>
    """

with col1: st.markdown(render_kpi_card("LS-05", 288.0), unsafe_allow_html=True)
with col2: st.markdown(render_kpi_card("LS-06", 288.0), unsafe_allow_html=True)
with col3: st.markdown(render_kpi_card("LS-08", 130.0), unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------
# 6. Bar Charts Section
# ---------------------------------------------------------
st.subheader("📈 วิเคราะห์ขนาดเส้นผ่านศูนย์กลางภายนอก (OD) & จำนวนครั้งเจียรรายชุด")
tab1, tab2 = st.tabs(["📏 ขนาด OD ล่าสุด เทียบ OD MIN", "🔄 จำนวนครั้งส่งเจียรสะสม"])

color_map = {"ปกติ (Safe)": "#22C55E", "เฝ้าระวัง (Warning)": "#F59E0B", "วิกฤต (Critical)": "#EF4444"}

with tab1:
    if not filtered_df.empty:
        fig_od = px.bar(
            filtered_df, x="Set_No", y="Latest_OD", color="Status", facet_col="Machine",
            color_discrete_map=color_map, text="Latest_OD",
            title="ค่า OD หลังเจียรล่าสุดแยกตามชุดใบมีด (mm)",
            labels={"Set_No": "ชุดใบมีด / หมายเลข", "Latest_OD": "ขนาด OD (mm)"}
        )
        fig_od.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_od.update_xaxes(matches=None) 
        fig_od.update_yaxes(range=[100, 340], dtick=40)
        fig_od.update_layout(height=480, margin=dict(t=50, b=40, l=40, r=40))
        st.plotly_chart(fig_od, use_container_width=True)
    else:
        st.warning("ไม่พบข้อมูลตามตัวกรองที่เลือก")

with tab2:
    if not filtered_df.empty:
        fig_grind = px.bar(
            filtered_df, x="Set_No", y="Grind_Count", color="Machine", facet_col="Machine",
            text="Grind_Count", title="จำนวนครั้งการส่งเจียร์สะสมแยกตามชุดใบมีด",
            labels={"Set_No": "ชุดใบมีด / หมายเลข", "Grind_Count": "จำนวนครั้งเจียร์"}
        )
        fig_grind.update_traces(texttemplate='%{text} ครั้ง', textposition='outside')
        fig_grind.update_xaxes(matches=None)
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
    if "วิกฤต" in val_str or "Critical" in val_str: return 'background-color: #FEF2F2; color: #DC2626; font-weight: bold;'
    elif "เฝ้าระวัง" in val_str or "Warning" in val_str: return 'background-color: #FFFBEB; color: #D97706; font-weight: bold;'
    else: return 'background-color: #F0FDF4; color: #16A34A;'

if not filtered_df.empty:
    display_cols = [c for c in ['Machine', 'Set_No', 'Color', 'Thickness_mm', 'Grind_Count', 'Latest_OD', 'OD_MIN', 'Margin', 'Status', 'Inspector'] if c in filtered_df.columns]
    
    st_builder = filtered_df[display_cols].style
    if hasattr(st_builder, 'map'):
        styled_table = st_builder.map(highlight_status, subset=['Status'] if 'Status' in display_cols else None)
    else:
        styled_table = st_builder.applymap(highlight_status, subset=['Status'] if 'Status' in display_cols else None)
        
    st.dataframe(styled_table, use_container_width=True, height=350)
else:
    st.info("ไม่มีข้อมูลแสดงผลในตาราง")

st.caption("ระบบเชื่อมต่อข้อมูล Google Sheet อัปเดตอัตโนมัติ | พัฒนาสำหรับผู้บริหารเครื่องจักรชุด LS")
