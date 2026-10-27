import streamlit as st
import pandas as pd
import re

# 1. Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="TLC Content Hub",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Kết nối Google Sheet qua Sheet ID và GID chuẩn của tab "Hôm nay"
SHEET_ID = "1MNbKOlFWj4NqDn9jaO44bWZLz9WPUKivgF0Uz_18mHc"
TAB_GID = "2042307707"  # GID tab "Hôm nay"

SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={TAB_GID}"

def find_col(columns, target_name):
    for c in columns:
        if str(c).strip().lower() == target_name.strip().lower():
            return c
    return None

@st.cache_data(ttl=60)
def load_data(url):
    data = pd.read_csv(url)
    data.columns = [str(c).strip() for c in data.columns]
    return data

try:
    df = load_data(SHEET_URL)
    
    first_col = str(df.columns[0]).lower()
    if "<!doctype" in first_col or "<html" in first_col:
        st.error("❌ Google Sheet chưa bật quyền công khai!")
        st.info("👉 Vào Google Sheet > Bấm 'Chia sẻ' (Share) > Chọn 'Bất kỳ ai có đường liên kết đều có thể xem'.")
        st.stop()
except Exception as e:
    st.error(f"❌ Không thể tải dữ liệu từ Google Sheet: {e}")
    st.stop()

# Xác định các cột thực tế
col_show = find_col(df.columns, "Show")
col_title = find_col(df.columns, "Tiêu đề")
col_source = find_col(df.columns, "Nguồn")
col_link = find_col(df.columns, "Link")
col_status = find_col(df.columns, "Trạng thái")
col_interact = find_col(df.columns, "Tương tác")
col_sensitive = find_col(df.columns, "Nhạy cảm")
col_script = find_col(df.columns, "Kịch bản")

if not col_show:
    st.error("⚠️ Không tìm thấy cột 'Show' trong bảng dữ liệu!")
    st.write("Các cột hiện có:", list(df.columns))
    st.stop()

# Hàm lấy nội dung kịch bản (ưu tiên Cột N / cột 14, fallback về cột Kịch bản)
def get_script_content(row):
    if len(row) >= 14 and pd.notna(row.iloc[13]):
        val = str(row.iloc[13]).strip()
        if val != "":
            return val
    if col_script and col_script in row and pd.notna(row[col_script]):
        val = str(row[col_script]).strip()
        if val != "":
            return val
    return ""

# Hàm bóc tách kịch bản thành từng tone
def parse_script(raw_text):
    if not raw_text:
        return None
    sections = {"witty": "", "gossip": "", "analytical": "", "comments": ""}
    p_witty = re.search(r'\[OPTION 1:.*?\](.*?)(?=\[OPTION 2:|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_gossip = re.search(r'\[OPTION 2:.*?\](.*?)(?=\[OPTION 3:|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_anal = re.search(r'\[OPTION 3:.*?\](.*?)(?=[SEED COMMENTS]|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_comm = re.search(r'[SEED COMMENTS](.*)', raw_text, re.DOTALL | re.IGNORECASE)
    
    sections["witty"] = p_witty.group(1).strip() if p_witty else ""
    sections["gossip"] = p_gossip.group(1).strip() if p_gossip else ""
    sections["analytical"] = p_anal.group(1).strip() if p_anal else ""
    sections["comments"] = p_comm.group(1).strip() if p_comm else ""
    
    if not any([sections["witty"], sections["gossip"], sections["analytical"]]):
        sections["witty"] = raw_text
    return sections

# 3. Tiêu đề ứng dụng & Thống kê
st.title("📺 TLC News & Content Hub")
st.caption("Dữ liệu tự động đồng bộ từ tab **Hôm nay**")

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
total_news = len(df)
has_script = sum(1 for _, r in df.iterrows() if get_script_content(r) != "")
new_news = total_news - has_script
sensitive_count = df[col_sensitive].dropna().count() if col_sensitive else 0

col_m1.metric("Tổng số tin", total_news)
col_m2.metric("✅ Đã có kịch bản", has_script)
col_m3.metric("🆕 Chờ kịch bản", new_news)
col_m4.metric("⚠️ Nhạy cảm", sensitive_count)

st.divider()

# 4. Sidebar bộ lọc
st.sidebar.header("🔍 Bộ lọc tin")

if st.sidebar.button("🔄 Làm mới dữ liệu", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

show_values = [str(s) for s in df[col_show].dropna().unique() if str(s).strip() != ""]
all_shows = ["Tất cả Show"] + show_values
selected_show = st.sidebar.selectbox("Chọn Show:", all_shows)

filter_status = st.sidebar.radio(
    "Trạng thái kịch bản:",
    ["Tất cả", "Chỉ bài đã có kịch bản", "Chỉ bài mới (chưa có)"],
    index=1
)

search_kw = st.sidebar.text_input("Tìm kiếm theo tiêu đề:")

filtered_df = df.copy()

if selected_show != "Tất cả Show":
    filtered_df = filtered_df[filtered_df[col_show] == selected_show]

if filter_status == "Chỉ bài đã có kịch bản":
    filtered_df = filtered_df[filtered_df.apply(lambda r: get_script_content(r) != "", axis=1)]
elif filter_status == "Chỉ bài mới (chưa có)":
    filtered_df = filtered_df[filtered_df.apply(lambda r: get_script_content(r) == "", axis=1)]

if search_kw.strip() and col_title:
    filtered_df = filtered_df[filtered_df[col_title].astype(str).str.contains(search_kw.strip(), case=False, na=False)]

# 5. Hiển thị danh sách & Chi tiết kịch bản
col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader(f"📋 Danh sách tin ({len(filtered_df)})")
    
    if filtered_df.empty:
        st.info("Không có tin nào phù hợp với bộ lọc.")
    else:
        for idx, row in filtered_df.iterrows():
            script_text = get_script_content(row)
            is_ready = bool(script_text)
            
            with st.container(border=True):
                badge = "🟢 Đã có kịch bản" if is_ready else "⚪ Mới"
                show_val = str(row.get(col_show, ''))
                title_val = str(row.get(col_title, ''))
                
                st.markdown(f"**[{show_val}]** {badge}")
                st.write(title_val)
                
                source_val = str(row.get(col_source, 'N/A'))
                info_line = f"Nguồn: `{source_val}`"
                if col_interact and pd.notna(row.get(col_interact)):
                    info_line += f" | 🔥 {row.get(col_interact)}"
                st.caption(info_line)
                
                if col_sensitive and pd.notna(row.get(col_sensitive)) and str(row.get(col_sensitive)).strip() != "":
                    st.warning(f"⚠️ Nhạy cảm: {row.get(col_sensitive)}")
                
                btn_name = "👁️ Xem kịch bản & Copy" if is_ready else "📝 Xem thông tin"
                if st.button(btn_name, key=f"btn_{idx}", use_container_width=True):
                    st.session_state['current_row'] = row
                    st.session_state['current_script'] = script_text

with col_right:
    st.subheader("📑 Chi tiết Kịch bản Facebook")
    
    if 'current_row' in st.session_state:
        cur = st.session_state['current_row']
        raw_script = st.session_state.get('current_script', '')
        
        with st.expander("📌 Thông tin bài gốc", expanded=False):
            st.write(f"**Show:** {cur.get(col_show, '')}")
            st.write(f"**Tiêu đề:** {cur.get(col_title, '')}")
            st.write(f"**Nguồn:** {cur.get(col_source, '')}")
            link_val = cur.get(col_link) if col_link else None
            if pd.notna(link_val) and str(link_val).startswith("http"):
                st.link_button("🌐 Mở link bài gốc", str(link_val))
        
        if raw_script:
            parsed = parse