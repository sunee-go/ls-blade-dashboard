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
# 2. Advanced Google Sheet Data Loader
# ---------------------------------------------------------
SHEET_ID = "1LCtzIdzBd4MGjKDV06Vl2rX-uy5rdZnQmNvaB72WpX0"
# เปลียนมาดึงเป็นนามสกุล xlsx แทนเพื่อให้ดึงข้อมูลได้ทุก Tabs
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    try:
        # อ่านไฟล์ Excel โดยดึงทุก Sheet และข้าม 3 บรรทัดบน (skiprows=3) เพื่อให้บรรทัดที่ 4 เป็นหัวตาราง
        xls = pd.read_excel(EXCEL_URL, sheet_name=None, skiprows=3, engine='openpyxl')
        
        processed_data = []
        
        for sheet_name, df in xls.items():
            # เลือกเฉพาะชีตที่มีชื่อขึ้นต้นด้วย LS- (ป้องกันการดึงชีตเปล่ามา)
            if not str(sheet_name).startswith("LS-"):
                continue
                
            df.columns = [str(c).strip() for c in df.columns]
            
            # Map ชื่อคอลัมน์ภาษาไทยให้ตรงกับตัวแปรที่ระบบต้องการ
            col_map = {}
            for c in df.columns:
                if 'หมายเลข' in c: col_map[c] = 'Set_No'
                elif 'ชุดสี' in c: col_map[c] = 'Color'
                elif 'หนา' in c: col_map[c] = 'Thickness_mm'
                elif 'OD หลังเจียร์' in c: col_map[c] = 'OD'
                elif 'ผู้เจียร์' in c: col_map[c] = 'Inspector'
                
            df = df.rename(columns=col_map)
            
            # ถ้าชีตนั้นไม่มีข้อมูลเลขชุดใบมีด หรือ ค่า OD ให้ข้ามไป
            if 'Set_No' not in df.columns or 'OD' not in df.columns:
                continue
                
            # ลบแถวว่างทิ้ง
            df = df.dropna(subset=['Set_No'])
            df['Set_No'] = df['Set_No'].astype(str).str.strip()
            df = df[df['Set_No'] != 'nan']
            df = df[df['Set_No'] != '']
            
            df['OD'] = pd.to_numeric(df['OD'], errors='coerce')
            df = df.dropna(subset=['OD']) # ตัดแถวที่เจียรแต่ยังไม่ลงค่า OD ออก
            
            # หัวใจสำคัญ: จัดกลุ่ม (Group by) เพื่อ "นับรอบเจียร" และ "ดึงค่า OD ล่าสุด"
            agg_args = {
                'Grind_Count': ('OD', 'count'),  # นับจำนวนบรรทัด = รอบที่เจียร
                'Latest_OD': ('OD', 'last')      # ดึงค่า OD บรรทัดล่างสุด
            }
            if 'Color' in df.columns: agg_args['Color'] = ('Color', 'last')
            if 'Thickness_mm' in df.columns: agg_args['Thickness_mm'] = ('Thickness_mm', 'last')
            if 'Inspector' in df.columns: agg_args['Inspector'] = ('Inspector', 'last')
            
            grouped = df.groupby('Set_No').agg(**agg_args).reset_index()
            
            grouped['Machine'] = sheet_name.strip().upper()
            grouped['OD_MIN'] = 130.0 if '08' in sheet_name else 288.0
            
            processed_data.append(grouped)
            
        if processed_data:
            final_df = pd.concat(processed_data, ignore_index=True)
            
            final_df['Margin'] = final_df['Latest_OD'] - final_df['OD_MIN']
            
            def calc_status(margin):
                if margin <= 0.5: return "วิกฤต (Critical)"
                elif margin <= 2.0: return "เฝ้าระวัง (Warning)"
                else: return "ปกติ (Safe)"
                
            final_df['Status'] = final_df['Margin'].apply(calc_status)
            
            # ใส่สัญลักษณ์ # นำหน้าชื่อชุดใบมีดให้ดูสวยงาม
            final_df['Set_No'] = "#" + final_df['Set_No']
            
            # เรียงลำดับให้สวยงาม
            final_df = final_df.sort_values(by=['Machine', 'Set_No']).reset_index(drop=True)
            return final_df
            
    except Exception as e:
        print("Error pulling data:", e)
        pass # ปล่อยให้ไหลไปใช้ข้อมูลสำรองหากพัง
        
    # ข้อมูลสำรอง (Fallback Data)
    return pd.DataFrame([
        {"Machine": "ERROR", "Set_No": "#N/A", "Grind_Count": 0, "Latest_OD": 0, "OD_MIN": 0, "Margin": 0, "Status": "วิกฤต (Critical)"}
    ])

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
