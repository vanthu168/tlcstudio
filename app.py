import streamlit as st
import pandas as pd
import re
import os
from google import genai
from google.genai import types

# 1. Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="TLC Content Hub",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Khởi tạo Gemini Client (để phục vụ tính năng dịch)
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
client = genai.Client(api_key=api_key) if api_key else None

# 3. Kết nối Google Sheet qua Sheet ID và GID tab "Hôm nay"
SHEET_ID = "1MNbKOlFWj4NqDn9jaO44bWZLz9WPUKivgF0Uz_18mHc"
TAB_GID = "2042307707"

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
        st.stop()
except Exception as e:
    st.error(f"❌ Không thể tải dữ liệu từ Google Sheet: {e}")
    st.stop()

col_show = find_col(df.columns, "Show")
col_title = find_col(df.columns, "Tiêu đề")
col_source = find_col(df.columns, "Nguồn")
col_link = find_col(df.columns, "Link")
col_status = find_col(df.columns, "Trạng thái")
col_interact = find_col(df.columns, "Tương tác")
col_sensitive = find_col(df.columns, "Nhạy cảm")
col_script = find_col(df.columns, "Kịch bản")

# Hàm lấy kịch bản từ Cột N hoặc Cột M
def get_script_content(row):
    if len(row) >= 14 and pd.notna(row.iloc[13]):
        val = str(row.iloc[13]).strip()
        if val != "" and val.lower() != "nan":
            return val
    if col_script and col_script in row and pd.notna(row[col_script]):
        val = str(row[col_script]).strip()
        if val != "" and val.lower() != "nan":
            return val
    return ""

# Hàm bóc tách kịch bản
def parse_script(raw_text):
    if not raw_text:
        return None
    sections = {"witty": "", "gossip": "", "analytical": "", "comments": ""}
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

# Hàm gọi  dịch sát nghĩa nhất theo nguyên bản
def translate_to_vietnamese(text_en):
    if not client:
        return "⚠️ Chưa cấu hình _API_KEY trong Secrets của Streamlit."
    
    prompt = f"""
Bạn là một dịch giả chuyên nghiệp. Hãy dịch toàn bộ nội dung kịch bản tiếng Anh sau đây sang Tiếng Việt theo tiêu chuẩn SÁT NGHĨA NHẤT (Faithful & Literal Translation).

QUY TẮC DỊCH THUẬT:
1. Sát nghĩa từng câu chữ: Bám sát cấu trúc ngữ pháp và ý tứ của câu gốc. Truyền tải chính xác 100% nội dung, số liệu, sự việc; tuyệt đối không phóng tác, không tự ý thêm bớt ý, không chèn từ lóng không có trong bản gốc.
2. Giữ nguyên sắc thái gốc: 
   - Phần Sarcastic: Dịch chuẩn xác sự mỉa mai/châm biếm của tác giả gốc.
   - Phần Gossip / Analytical: Dịch đúng nhận định, lập luận khách quan theo nguyên tác.
3. Giữ nguyên tên riêng & thực thể: Giữ nguyên tên các nhân vật (Kody, Meri, Christine, Stephen...), tên show (90 Day Fiancé, Sister Wives, TLC...).
4. Giữ nguyên định dạng: Giữ nguyên cấu trúc các thẻ phân đoạn [OPTION 1:...], [OPTION 2:...], [OPTION 3:...], [SEED COMMENTS].

Nội dung cần dịch:
{text_en}
"""
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1  # Giữ nhiệt độ thấp để bản dịch bám sát nguyên gốc tuyệt đối
            )
        )
        return response.text
    except Exception as e:
        return f"Lỗi khi dịch: {e}"

# 4. Tiêu đề ứng dụng & Thống kê
st.title("📺 TLC News & Content Hub")

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

# 5. Sidebar bộ lọc
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

if 'current_row' not in st.session_state and not filtered_df.empty:
    first_row = filtered_df.iloc[0]
    st.session_state['current_row'] = first_row
    st.session_state['current_script'] = get_script_content(first_row)
    st.session_state['translated_script'] = None

# 6. Giao diện hiển thị: 2 Cột
col_left, col_right = st.columns([1, 1.25])

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
                    st.session_state['translated_script'] = None  # Reset bản dịch khi chọn tin khác

with col_right:
    st.subheader("📑 Kịch bản Facebook (Copy nhanh)")
    
    if 'current_row' in st.session_state:
        cur = st.session_state['current_row']
        raw_script = st.session_state.get('current_script', '')
        
        st.info(f"**[{cur.get(col_show, '')}]** {cur.get(col_title, '')}")
        
        if raw_script:
            # THANH ĐIỀU KHIỂN DỊCH
            c_trans1, c_trans2 = st.columns([1, 1])
            with c_trans1:
                if st.button("🇻🇳 Dịch sang Tiếng Việt", use_container_width=True):
                    with st.spinner("Gemini đang dịch sang tiếng Việt chuẩn drama..."):
                        translated = translate_to_vietnamese(raw_script)
                        st.session_state['translated_script'] = translated
            
            with c_trans2:
                # Chọn ngôn ngữ hiển thị
                has_trans = bool(st.session_state.get('translated_script'))
                lang_options = ["🇺🇸 Tiếng Anh (Gốc)", "🇻🇳 Tiếng Việt"] if has_trans else ["🇺🇸 Tiếng Anh (Gốc)"]
                chosen_lang = st.radio("Ngôn ngữ hiển thị:", lang_options, horizontal=True)

            # Chọn nội dung để hiển thị
            content_to_show = raw_script
            if chosen_lang == "🇻🇳 Tiếng Việt" and st.session_state.get('translated_script'):
                content_to_show = st.session_state['translated_script']

            parsed = parse_script(content_to_show)
            
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🔥 Sarcastic & Witty", 
                "🗣️ Gossip & Viral", 
                "🧐 Analytical", 
                "💬 Seed Comments",
                "📄 Toàn văn"
            ])
            
            with tab1:
                st.caption(f"Phong cách Sarcastic ({chosen_lang}):")
                st.text_area("Sarcastic:", parsed["witty"], height=280)
            
            with tab2:
                st.caption(f"Phong cách Gossip ({chosen_lang}):")
                st.text_area("Gossip:", parsed["gossip"], height=280)
                
            with tab3:
                st.caption(f"Phong cách Analytical ({chosen_lang}):")
                st.text_area("Analytical:", parsed["analytical"], height=280)
                
            with tab4:
                st.caption(f"Bình luận mồi ({chosen_lang}):")
                if parsed["comments"]:
                    st.text_area("Seed comments:", parsed["comments"], height=220)
                else:
                    st.info("Chưa có danh sách bình luận mồi riêng.")
                    
            with tab5:
                st.text_area("Toàn văn nội dung:", content_to_show, height=350)
        else:
            st.warning("⚠️ Dòng này chưa có nội dung kịch bản trong Google Sheet.")
            st.info("👉 Mở Google Sheet, click dòng này và bấm '🤖 TLC AI Content > 🚀 Tạo kịch bản'.")
            
        with st.expander("🔗 Xem nguồn & link bài gốc", expanded=False):
            st.write(f"**Nguồn:** {cur.get(col_source, '')}")
            link_val = cur.get(col_link) if col_link else None
            if pd.notna(link_val) and str(link_val).startswith("http"):
                st.link_button("🌐 Mở link bài viết gốc", str(link_val))
    else:
        st.info("👈 Chọn một tin ở danh sách bên trái để xem nội dung.")
