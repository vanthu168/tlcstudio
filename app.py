import streamlit as st
import pandas as pd
import urllib.parse
import re

# 1. Cau hinh giao dien
st.set_page_config(
    page_title="TLC Content Hub",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Ket noi Google Sheet
SHEET_ID = "1MNbKOlFWj4NqDn9jaO44bWZLz9WPUKivgF0Uz_18mHc"
TAB_NAME = "Hôm nay"
encoded_tab = urllib.parse.quote(TAB_NAME)
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_tab}"

@st.cache_data(ttl=120)
def load_data():
    data = pd.read_csv(SHEET_URL)
    data.columns = [str(c).strip() for c in data.columns]
    return data

try:
    df = load_data()
except Exception as e:
    st.error(f"Khong the tai du lieu tu Google Sheet: {e}")
    st.stop()

# Ham lay noi dung kich ban (Cột N hoac Cot M)
def get_script_content(row):
    if len(row) >= 14 and pd.notna(row.iloc[13]):
        val = str(row.iloc[13]).strip()
        if val != "":
            return val
    if "Kịch bản" in row and pd.notna(row["Kịch bản"]):
        val = str(row["Kịch bản"]).strip()
        if val != "":
            return val
    return ""

# Ham tach kich ban
def parse_script(raw_text):
    if not raw_text:
        return None
    
    sections = {
        "witty": "",
        "gossip": "",
        "analytical": "",
        "comments": ""
    }
    
    p_witty = re.search(r'\[OPTION 1:.*?\](.*?)(?=\[OPTION 2:|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_gossip = re.search(r'\[OPTION 2:.*?\](.*?)(?=\[OPTION 3:|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_anal = re.search(r'\[OPTION 3:.*?\](.*?)(?=\[SEED COMMENTS\]|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_comm = re.search(r'\[SEED COMMENTS\](.*)', raw_text, re.DOTALL | re.IGNORECASE)
    
    sections["witty"] = p_witty.group(1).strip() if p_witty else ""
    sections["gossip"] = p_gossip.group(1).strip() if p_gossip else ""
    sections["analytical"] = p_anal.group(1).strip() if p_anal else ""
    sections["comments"] = p_comm.group(1).strip() if p_comm else ""
    
    if not any([sections["witty"], sections["gossip"], sections["analytical"]]):
        sections["witty"] = raw_text
        
    return sections

# 3. Thong ke tren dau trang
st.title("📺 TLC News & Content Hub")
st.caption(f"Du lieu tu Google Sheet (Tab: {TAB_NAME})")

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
total_news = len(df)
has_script = sum(1 for _, r in df.iterrows() if get_script_content(r) != "")
new_news = total_news - has_script
sensitive_count = df['Nhạy cảm'].dropna().count() if 'Nhạy cảm' in df.columns else 0

col_m1.metric("Tong tin", total_news)
col_m2.metric("Co kich ban", has_script)
col_m3.metric("Cho kich ban", new_news)
col_m4.metric("Nhay cam", sensitive_count)

st.divider()

# 4. Sidebar bo loc
st.sidebar.header("Bo loc tin")

if st.sidebar.button("Lam moi du lieu", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

all_shows = ["Tat ca Show"] + [str(s) for s in df['Show'].dropna().unique()]
selected_show = st.sidebar.selectbox("Chon Show:", all_shows)

filter_status = st.sidebar.radio(
    "Trang thai:",
    ["Tat ca", "Da co kich ban", "Chua co kich ban"],
    index=1
)

search_kw = st.sidebar.text_input("Tim kiem theo tieu de:")

filtered_df = df.copy()

if selected_show != "Tat ca Show":
    filtered_df = filtered_df[filtered_df['Show'] == selected_show]

if filter_status == "Da co kich ban":
    filtered_df = filtered_df[filtered_df.apply(lambda r: get_script_content(r) != "", axis=1)]
elif filter_status == "Chua co kich ban":
    filtered_df = filtered_df[filtered_df.apply(lambda r: get_script_content(r) == "", axis=1)]

if search_kw.strip():
    filtered_df = filtered_df[filtered_df['Tiêu đề'].astype(str).str.contains(search_kw.strip(), case=False, na=False)]

# 5. Hien thi danh sach va chi tiet
col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader(f"Danh sach tin ({len(filtered_df)})")
    
    if filtered_df.empty:
        st.info("Khong co tin nao phu hop.")
    else:
        for idx, row in filtered_df.iterrows():
            script_text = get_script_content(row)
            is_ready = bool(script_text)
            
            with st.container(border=True):
                badge = "[Co kich ban]" if is_ready else "[Moi]"
                show_val = str(row.get('Show', ''))
                title_val = str(row.get('Tiêu đề', ''))
                
                st.markdown(f"**{badge} {show_val}**")
                st.write(title_val)
                
                source_val = str(row.get('Nguồn', 'N/A'))
                info_line = f"Nguon: {source_val}"
                tuong_tac = row.get('Tương tác')
                if pd.notna(tuong_tac):
                    info_line += f" | {tuong_tac}"
                st.caption(info_line)
                
                nhay_cam = row.get('Nhạy cảm')
                if pd.notna(nhay_cam) and str(nhay_cam).strip() != "":
                    st.warning(f"Nhay cam: {nhay_cam}")
                
                btn_name = "Xem kich ban & Copy" if is_ready else "Xem thong tin"
                if st.button(btn_name, key=f"btn_{idx}", use_container_width=True):
                    st.session_state['current_row'] = row
                    st.session_state['current_script'] = script_text

with col_right:
    st.subheader("Chi tiet Kich ban Facebook")
    
    if 'current_row' in st.session_state:
        cur = st.session_state['current_row']
        raw_script = st.session_state.get('current_script', '')
        
        with st.expander("Thong tin bai goc", expanded=False):
            st.write(f"Show: {cur.get('Show', '')}")
            st.write(f"Tieu de: {cur.get('Tiêu đề', '')}")
            st.write(f"Nguon: {cur.get('Nguồn', '')}")
            link_val = cur.get('Link')
            if pd.notna(link_val) and str(link_val).startswith("http"):
                st.link_button("Mo link goc", str(link_val))
        
        if raw_script:
            parsed = parse_script(raw_script)
            
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Sarcastic & Witty", 
                "Gossip & Viral", 
                "Analytical", 
                "Seed Comments",
                "Toan van"
            ])
            
            with tab1:
                st.text_area("Sarcastic:", parsed["witty"], height=280)
            
            with tab2:
                st.text_area("Gossip:", parsed["gossip"], height=280)
                
            with tab3:
                st.text_area("Analytical:", parsed["analytical"], height=280)
                
            with tab4:
                st.text_area("Seed Comments:", parsed["comments"], height=220)
                    
            with tab5:
                st.text_area("Noi dung goc tu Cot N:", raw_script, height=350)
        else:
            st.warning("Dong nay chua co kich ban trong Google Sheet.")
    else:
        st.info("Chon mot tin o danh sach ben trai de xem kich ban.")