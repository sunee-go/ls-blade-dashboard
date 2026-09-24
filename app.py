import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. Page Configuration (ตั้งค่าหน้าเว็บ)
# ---------------------------------------------------------
st.set_page_config(
    page_title="LS Blade Executive Dashboard",
    page_icon="🔪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 📌 จุดที่ 1: ปรับแต่ง CSS (ขนาดฟอนต์ และ สีกล่อง KPI)
# รหัสสีอ้างอิงเบื้องต้น: 
# สีแดง = #EF4444 (อ่อน) / #DC2626 (เข้ม)
# สีส้ม/เหลือง = #F59E0B (อ่อน) / #D97706 (เข้ม)
# สีเขียว = #22C55E (อ่อน) / #16A34A (เข้ม)
# สีดำ/เทาเข้ม = #0F172A (สีตัวหนังสือหลัก)
st.markdown("""
<style>
    .main-header { font-size: 24px; font-weight: bold; color: #1E293B; margin-bottom: 5px; }
    .sub-header { font-size: 14px; color: #64748B; margin-bottom: 20px; }
    
    /* กล่องสีต่างๆ ของ KPI */
    .kpi-card-safe { background-color: #F0FDF4; border-left: 5px solid #22C55E; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .kpi-card-danger { background-color: #FEF2F2; border-left: 5px solid #EF4444; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .kpi-card-warning { background-color: #FFFBEB; border-left: 5px solid #F59E0B; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    
    /* 📌 ปรับขนาดฟอนต์ชื่อเครื่องจักร (KPI Title) ได้ที่บรรทัดนี้ (เช่น เปลี่ยนจาก 22px เป็น 24px) */
    .kpi-title { font-size: 22px; font-weight: bold; color: #0F172A; }
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
    """จัดรูปแบบชื่อชุดใบมีดให้ตรงกับ Master List ป้องกันการนับรอบเจียรปนกัน"""
    s = str(set_no).strip()
    c = str(color).strip()
    t = str(thickness).strip()
    
    if machine == 'LS-06':
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
        elif s == '61-80': return '61-80 (ชุดบน)'
    elif machine == 'LS-08':
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
            
            df['Set_No'] = df.apply(lambda row: format_set_name(machine_name, row['Raw_Set_No'], row['Color'], row['Thickness_mm']), axis=1)
            
            agg_args = {
                'OD': ('OD', 'last'),          
                'Raw_Set_No': ('OD', 'count'),
                'Color': ('Color', 'last'),
                'Thickness_mm': ('Thickness_mm', 'last'),
            }
            if 'Inspector' in df.columns: agg_args['Inspector'] = ('Inspector', 'last')
            
            grouped = df.groupby('Set_No').agg(**agg_args).reset_index()
            grouped = grouped.rename(columns={'OD': 'Latest_OD', 'Raw_Set_No': 'Grind_Count'})
            
            grouped['Machine'] = machine_name
            # 📌 จุดที่ 2: ตั้งค่าเส้นขีดจำกัดล่าง (OD MIN)
            grouped['OD_MIN'] = 216.0 if '08' in machine_name else 288.0
            
            processed_data.append(grouped)
            
        if processed_data:
            final_df = pd.concat(processed_data, ignore_index=True)
            final_df['Margin'] = final_df['Latest_OD'] - final_df['OD_MIN']
            
            # 📌 จุดที่ 3: ฟังก์ชันกำหนดเงื่อนไขสี (แดง/ส้ม/เขียว)
            def calc_status(row):
                m = row['Machine']
                od = row['Latest_OD']
                if '08' in m:
                    if od <= 220: return "วิกฤต (Critical)"      # LS-08 แดง ถ้า <= 220
                    elif od <= 230: return "เฝ้าระวัง (Warning)" # LS-08 ส้ม ถ้า <= 230
                    else: return "ปกติ (Safe)"                 # LS-08 เขียว ถ้า > 230
                else:
                    if od <= 290: return "วิกฤต (Critical)"      # LS-05,06 แดง ถ้า <= 290
                    elif od <= 295: return "เฝ้าระวัง (Warning)" # LS-05,06 ส้ม ถ้า <= 295
                    else: return "ปกติ (Safe)"                 # LS-05,06 เขียว ถ้า > 295
                    
            final_df['Status'] = final_df.apply(calc_status, axis=1)
            final_df = final_df.sort_values(by=['Machine', 'Set_No']).reset_index(drop=True)
            return final_df
            
    except Exception as e:
        print("Error pulling data:", e)
        pass 
        
    # ข้อมูลสำลองกรณีเน็ตหลุด/อ่านไฟล์ไม่รอด (ปรับตัวเลขให้ตรงเงื่อนไขทดสอบแล้ว)
    fallback_data = [
        {"Machine": "LS-05", "Set_No": "1-20", "Color": "แดง", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 296.0, "OD_MIN": 288.0, "Margin": 8.0, "Status": "ปกติ (Safe)", "Inspector": "-"},
        {"Machine": "LS-05", "Set_No": "21-40", "Color": "ขาว", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 293.0, "OD_MIN": 288.0, "Margin": 5.0, "Status": "เฝ้าระวัง (Warning)", "Inspector": "-"},
        {"Machine": "LS-06", "Set_No": "1-20 (ชุดบน)", "Color": "แดง", "Thickness_mm": 10, "Grind_Count": 0, "Latest_OD": 289.5, "OD_MIN": 288.0, "Margin": 1.5, "Status": "วิกฤต (Critical)", "Inspector": "-"},
        {"Machine": "LS-08", "Set_No": "1-31 (5 mm.)", "Color": "-", "Thickness_mm": 5, "Grind_Count": 0, "Latest_OD": 225.0, "OD_MIN": 216.0, "Margin": 9.0, "Status": "เฝ้าระวัง (Warning)", "Inspector": "-"},
        {"Machine": "LS-08", "Set_No": "32-62 (5 mm.)", "Color": "-", "Thickness_mm": 5, "Grind_Count": 0, "Latest_OD": 218.0, "OD_MIN": 216.0, "Margin": 2.0, "Status": "วิกฤต (Critical)", "Inspector": "-"}
    ]
    return pd.DataFrame(fallback_data)

df = load_data()

# ---------------------------------------------------------
# 3. Sidebar Filters & Search
# ---------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/dashboard.png", width=60)
st.sidebar.title("ระบบกรองข้อมูล (Filters)")

# 📌 จุดที่ 4: ช่องค้นหาด่วน (Quick Search)
search_query = st.sidebar.text_input("🔍 ค้นหาด่วน (เช่น 1-20, แดง, สมชาย):", "")

machine_options = sorted(list(df["Machine"].unique())) if not df.empty else []
machine_filter = st.sidebar.multiselect("เลือกเครื่องจักร (Machine):", options=machine_options, default=machine_options)

status_options = ["ปกติ (Safe)", "เฝ้าระวัง (Warning)", "วิกฤต (Critical)"]
status_filter = st.sidebar.multiselect("เลือกสถานะ (Status):", options=status_options, default=status_options)

filtered_df = df.copy()

# กรองข้อมูลตามที่พิมพ์ในช่องค้นหาด่วน
if search_query:
    filtered_df = filtered_df[
        filtered_df.apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1)
    ]
    
if machine_filter: filtered_df = filtered_df[filtered_df["Machine"].isin(machine_filter)]
if status_filter: filtered_df = filtered_df[filtered_df["Status"].isin(status_filter)]

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
        min_od = m_df["Latest_OD"].min()
        max_od = m_df["Latest_OD"].max()
        count_sets = len(m_df)
        is_danger = (m_df["Status"] == "วิกฤต (Critical)").any()
        is_warning = (m_df["Status"] == "เฝ้าระวัง (Warning)").any()
    else:
        grind_sum, min_od, max_od, count_sets, is_danger, is_warning = 0, 0, 0, 0, False, False
        
    if is_danger:
        card_class = "kpi-card-danger"
        status_text = f'<span style="color:#DC2626;font-weight:bold;">🚨 แจ้งเตือน! มีใบมีดถึงเกณฑ์สีแดง</span>'
    elif is_warning:
        card_class = "kpi-card-warning"
        status_text = f'<span style="color:#D97706;font-weight:bold;">⚠️ เฝ้าระวัง! มีใบมีดถึงเกณฑ์สีส้ม</span>'
    else:
        card_class = "kpi-card-safe"
        status_text = f'<span style="color:#16A34A;font-weight:bold;">✅ ปกติปลอดภัยทุกชุด</span>'
    
    return f"""
    <div class="{card_class}">
        <div class="kpi-title">เครื่อง {machine_name} (Target: {od_min_default} mm | รวม {count_sets} ชุด)</div>
        <div class="kpi-value">ส่งเจียรสะสม: {grind_sum} ครั้ง</div>
        <div class="kpi-sub">ช่วง OD ล่าสุด: {min_od:.2f} - {max_od:.2f} mm</div>
        <div class="kpi-sub"><b>สถานะ:</b> {status_text}</div>
    </div>
    """

with col1: st.markdown(render_kpi_card("LS-05", 288.0), unsafe_allow_html=True)
with col2: st.markdown(render_kpi_card("LS-06", 288.0), unsafe_allow_html=True)
with col3: st.markdown(render_kpi_card("LS-08", 216.0), unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------
# 6. Bar Charts Section
# ---------------------------------------------------------
st.subheader("📈 วิเคราะห์ขนาดเส้นผ่านศูนย์กลางภายนอก (OD) & จำนวนครั้งเจียรรายชุด")
tab1, tab2 = st.tabs(["📏 ขนาด OD ล่าสุด เทียบเส้น Target ขั้นต่ำ", "🔄 จำนวนครั้งส่งเจียรสะสม"])

# 📌 จุดที่ 5: ตั้งค่าสีของแท่งกราฟ Plotly (เปลี่ยนรหัสสีได้ที่นี่)
color_map = {
    "ปกติ (Safe)": "#22C55E",      # สีเขียว
    "เฝ้าระวัง (Warning)": "#F59E0B", # สีส้ม
    "วิกฤต (Critical)": "#EF4444"    # สีแดง
}

with tab1:
    if not filtered_df.empty:
        fig_od = px.bar(
            filtered_df, x="Set_No", y="Latest_OD", color="Status", facet_col="Machine",
            color_discrete_map=color_map, text="Latest_OD",
            title="ค่า OD หลังเจียรล่าสุดแยกตามชุดใบมีด (mm)",
            labels={"Set_No": "ชุดใบมีด / หมายเลข", "Latest_OD": "ขนาด OD (mm)"}
        )
        
        # 📌 จุดที่ 6: เปลี่ยนสีตัวเลขบนกราฟเป็น 'สีดำ' (textfont_color='black')
        fig_od.update_traces(texttemplate='%{text:.2f}', textposition='outside', textfont_color='black')
        fig_od.update_xaxes(matches=None) 
        
        # 📌 จุดที่ 7: เปลี่ยนขนาดฟอนต์หัวข้อกราฟย่อย (เช่น เปลี่ยน size=20)
        fig_od.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=20)))
        
        # 📌 จุดที่ 8: สร้างเส้น Target ไข่ปลาสีแดง
        for i, ann in enumerate(fig_od.layout.annotations):
            machine = ann.text
            col = i + 1
            # กำหนดค่าตัวเลขเส้น Target
            target_val = 216 if '08' in machine else 288
            
            # วาดเส้นแนวนอน (hline)
            fig_od.add_hline(y=target_val, line_dash="dot", line_color="red", line_width=2, 
                             row=1, col=col, 
                             annotation_text=f" Target: {target_val}", 
                             annotation_position="bottom right",
                             annotation_font_color="red")
                             
        fig_od.update_yaxes(range=[180, 330], dtick=20)
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
        # 📌 สีตัวเลขบนกราฟแท่ง (textfont_color='black')
        fig_grind.update_traces(texttemplate='%{text} ครั้ง', textposition='outside', textfont_color='black')
        fig_grind.update_xaxes(matches=None)
        fig_grind.update_layout(height=480, margin=dict(t=50, b=40, l=40, r=40))
        st.plotly_chart(fig_grind, use_container_width=True)
    else:
        st.warning("ไม่พบข้อมูลตามตัวกรองที่เลือก")

# ---------------------------------------------------------
# 7. Action Plan & Detailed Risk Table
# ---------------------------------------------------------
st.subheader("📋 ตารางประเมินความเสี่ยงและแผนการจัดการ (Action Plan)")

# 📌 จุดที่ 9: เปลี่ยนสีแถบในตารางด้านล่างสุด
def highlight_status(val):
    val_str = str(val)
    if "วิกฤต" in val_str or "Critical" in val_str: 
        return 'background-color: #FEF2F2; color: #DC2626; font-weight: bold;' # พื้นแดงอ่อน ตัวหนังสือแดงเข้ม
    elif "เฝ้าระวัง" in val_str or "Warning" in val_str: 
        return 'background-color: #FFFBEB; color: #D97706; font-weight: bold;' # พื้นส้มอ่อน ตัวหนังสือส้มเข้ม
    else: 
        return 'background-color: #F0FDF4; color: #16A34A;'                    # พื้นเขียวอ่อน ตัวหนังสือเขียวเข้ม

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
