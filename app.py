import streamlit as st
import pandas as pd
import urllib.parse
import re

# 1. Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="TLC Content Hub",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Cấu hình kết nối Google Sheet
SHEET_ID = "1MNbKOlFWj4NqDn9jaO44bWZLz9WPUKivgF0Uz_18mHc"
TAB_NAME = "Hôm nay"
encoded_tab = urllib.parse.quote(TAB_NAME)
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_tab}"

# Hàm tải dữ liệu (Cache 2 phút để tải siêu nhanh trên mobile, tự làm mới khi bấm nút)
@st.cache_data(ttl=120)
def load_data():
    data = pd.read_csv(SHEET_URL)
    # Chuẩn hóa tên cột để tránh khoảng trắng thừa
    data.columns = [c.strip() for c in data.columns]
    return data

try:
    df = load_data()
except Exception as e:
    st.error(f"❌ Không thể tải dữ liệu từ Google Sheet: {e}")
    st.info("👉 Hãy đảm bảo bảng tính đã bật chia sẻ: 'Bất kỳ ai có đường liên kết đều có thể xem'.")
    st.stop()

# Hàm lấy nội dung kịch bản (ưu tiên Cột N / cột số 14)
def get_script_content(row):
    # Nếu có cột thứ 14 (Cột N)
    if len(row) >= 14 and pd.notna(row.iloc[13]) and str(row.iloc[13]).strip() != "":
        return str(row.iloc[13]).strip()
    # Nếu Cột N chưa có, kiểm tra Cột M (Kịch bản)
    if "Kịch bản" in row and pd.notna(row["Kịch bản"]) and str(row["Kịch bản"]).strip() != "":
        return str(row["Kịch bản"]).strip()
    return ""

# Hàm bóc tách nội dung kịch bản thành từng phần hiển thị
def parse_script(raw_text):
    if not raw_text:
        return None
    
    sections = {
        "witty": "",
        "gossip": "",
        "analytical": "",
        "comments": ""
    }
    
    # Tách theo các thẻ tiêu đề
    p_witty = re.search(r'\[OPTION 1:.*?\](.*?)(?=\[OPTION 2:|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_gossip = re.search(r'\[OPTION 2:.*?\](.*?)(?=\[OPTION 3:|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_anal = re.search(r'\[OPTION 3:.*?\](.*?)(?=\[SEED COMMENTS\]|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_comm = re.search(r'\[SEED COMMENTS\](.*)', raw_text, re.DOTALL | re.IGNORECASE)
    
    sections["witty"] = p_witty.group(1).strip() if p_witty else ""
    sections["gossip"] = p_gossip.group(1).strip() if p_gossip else ""
    sections["analytical"] = p_anal.group(1).strip() if p_anal else ""
    sections["comments"] = p_comm.group(1).strip() if p_comm else ""
    
    # Nếu không khớp regex chuẩn thì hiển thị toàn bộ vào witty
    if not any([sections["witty"], sections["gossip"], sections["analytical"]]):
        sections["witty"] = raw_text
        
    return sections

# 3. Tiêu đề ứng dụng & Thống kê nhanh
st.title("📺 TLC News & Content Hub")
st.caption(f"Dữ liệu trực tiếp từ Google Sheet (Tab: **{TAB_NAME}**)")

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
total_news = len(df)
has_script = sum(1 for _, r in df.iterrows() if get_script_content(r) != "")
new_news = total_news - has_script
sensitive_count = df['Nhạy cảm'].dropna().count() if 'Nhạy cảm' in df.columns else 0

col_m1.metric("Tổng số tin", total_news)
col_m2.metric("✅ Đã có kịch bản", has_script)
col_m3.metric("🆕 Đang chờ kịch bản", new_news)
col_m4.metric("⚠️ Cảnh báo nhạy cảm", sensitive_count)

st.divider()

# 4. Thanh công cụ bên trái (Sidebar)
st.sidebar.header("🔍 Bộ lọc & Tìm kiếm")

if st.sidebar.button("🔄 Làm mới dữ liệu", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Bộ lọc Show
all_shows = ["Tất cả Show"] + [str(s) for s in df['Show'].dropna().unique()]
selected_show = st.sidebar.selectbox("Lọc theo Show:", all_shows)

# Bộ lọc trạng thái
filter_status = st.sidebar.radio(
    "Lọc kịch bản:",
    ["Tất cả", "Chỉ bài 'Đã có kịch bản'", "Chỉ bài 'Mới'"],
    index=1  # Mặc định mở bài đã có kịch bản để bạn copy nhanh
)

# Tìm kiếm từ khóa
search_kw = st.sidebar.text_input("Tìm kiếm tiêu đề:", placeholder="Nhập tên nhân vật, từ khóa...")

# Lọc dữ liệu
filtered_df = df.copy()

if selected_show != "Tất cả Show":
    filtered_df = filtered_df[filtered_df['Show'] == selected_show]

if filter_status == "Chỉ bài 'Đã có kịch bản'":
    filtered_df = filtered_df[filtered_df.apply(lambda r: get_script_content(r) != "", axis=1)]
elif filter_status == "Chỉ bài 'Mới'":
    filtered_df = filtered_df[filtered_df.apply(lambda r: get_script_content(r) == "", axis=1)]

if search_kw.strip():
    filtered_df = filtered_df[filtered_df['Tiêu đề'].astype(str).str.contains(search_kw.strip(), case=False, na=False)]

# 5. Bố cục hiển thị chính: Cột trái (Danh sách) | Cột phải (Chi tiết & Copy)
col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader(f"📋 Danh sách tin ({len(filtered_df)})")
    
    if filtered_df.empty:
        st.info("Không tìm thấy tin nào phù hợp.")
    else:
        for idx, row in filtered_df.iterrows():
            script_text = get_script_content(row)
            is_ready = bool(script_text)
            
            with st.container(border=True):
                # Header thẻ tin
                badge = "🟢 Đã có kịch bản" if is_ready else "⚪ Mới"
                st.markdown(f"**[{row.get('Show', '')}]** {badge}")
                st.markdown(f"**{row.get('Tiêu đề', '')}**")
                
                # Thông tin phụ
                sub_info = f"Nguồn: `{row.get('