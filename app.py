import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
from google import genai
from google.genai import types

# 1. Cấu hình giao diện ứng dụng Streamlit
st.set_page_config(
    page_title="TLC News to Facebook", 
    page_icon="📺", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📺 TLC News Săn Tin ➔ Facebook Post Generator")

# 2. Cấu hình API Key Gemini an toàn
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
if not api_key:
    st.error("⚠️ Chưa cấu hình GEMINI_API_KEY trong phần Secrets của Streamlit Cloud hoặc biến môi trường!")
    st.info("Hãy vào Settings > Secrets trên Streamlit Cloud và thêm: GEMINI_API_KEY = 'mã_api_key_của_bạn'")
    st.stop()

client = genai.Client(api_key=api_key)

# 3. Kết nối Google Sheet qua ID của bạn
SHEET_ID = "AQ.Ab8RN6Jp1HmMtGLsVtcOpaXOnDXzjvoGUJ4HUqFEQ45xiviXyg"
TAB_NAME = "Hôm nay"
encoded_tab = urllib.parse.quote(TAB_NAME)
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_tab}"

# Hàm tải dữ liệu (tự làm mới sau mỗi 5 phút hoặc khi bấm nút Refresh)
@st.cache_data(ttl=300)
def load_sheet_data(url):
    return pd.read_csv(url)

try:
    df = load_sheet_data(SHEET_URL)
except Exception as e:
    st.error(f"❌ Không thể đọc dữ liệu từ Google Sheet: {e}")
    st.warning("👉 Hãy đảm bảo bạn đã bật quyền chia sẻ: 'Bất kỳ ai có đường liên kết đều có thể xem' (Anyone with link can view) trên Google Sheet!")
    st.stop()

# 4. Thanh điều khiển bên trái (Sidebar)
st.sidebar.header("🔍 Bộ lọc tin tức")

if st.sidebar.button("🔄 Làm mới dữ liệu từ Sheet"):
    st.cache_data.clear()
    st.rerun()

all_shows = ["Tất cả"] + [str(s) for s in df['Show'].dropna().unique()]
selected_show = st.sidebar.selectbox("Chọn Show:", all_shows)

filter_status = st.sidebar.radio("Trạng thái:", ["Chỉ tin 'Mới'", "Tất cả"])

# Áp dụng bộ lọc
filtered_df = df.copy()
if selected_show != "Tất cả":
    filtered_df = filtered_df[filtered_df['Show'] == selected_show]
if filter_status == "Chỉ tin 'Mới'" and 'Trạng thái' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['Trạng thái'] == "Mới"]

st.sidebar.markdown(f"**Tổng số tin:** {len(filtered_df)}")

# 5. Bố cục 2 cột: Cột trái xem tin, Cột phải tạo bài
col_list, col_post = st.columns([1, 1.2])

with col_list:
    st.subheader(f"📋 Danh sách tin ({TAB_NAME})")
    
    if filtered_df.empty:
        st.info("Không có tin nào phù hợp với bộ lọc hiện tại.")
    else:
        for idx, row in filtered_df.iterrows():
            with st.container(border=True):
                st.markdown(f"**[{row.get('Show', '')}]** {row.get('Tiêu đề', '')}")
                
                info_text = f"Nguồn: {row.get('Nguồn', 'N/A')} | Loại: {row.get('Loại', 'N/A')}"
                if pd.notna(row.get('Tương tác')):
                    info_text += f" | {row.get('Tương tác')}"
                st.caption(info_text)
                
                if pd.notna(row.get('Nhạy cảm')):
                    st.warning(f"⚠️ Nhạy cảm: {row.get('Nhạy cảm')}")
                
                if st.button("🚀 Viết bài Facebook", key=f"btn_{idx}"):
                    st.session_state['selected_item'] = row.to_dict()
                    st.session_state['ai_result'] = None

with col_post:
    st.subheader("✍️ Trợ lý Gemini lên bài")
    
    if 'selected_item' in st.session_state and st.session_state['selected_item'] is not None:
        item = st.session_state['selected_item']
        
        st.info(f"Đang chọn: **[{item.get('Show')}] {item.get('Tiêu đề')}**")
        if pd.notna(item.get('Link')):
            st.caption(f"🔗 Link gốc: {item.get('Link')}")
        
        prompt = f"""
        Bạn là chuyên gia sáng tạo nội dung hàng đầu cho fanpage Reality TV TLC (US).
        Dựa vào tin tức sau:
        - Show: {item.get('Show')}
        - Tiêu đề: {item.get('Tiêu đề')}
        - Nguồn: {item.get('Nguồn')}
        - Link: {item.get('Link')}
        - Tương tác: {item.get('Tương tác')}

        QUY ĐỊNH BẮT BUỘC:
        1. 100% tuân thủ Meta Policy (Facebook): Tuyệt đối không dùng từ ngữ thô tục, bạo lực, xúc phạm danh dự hay trigger kiểm duyệt.
        2. Viết bằng tiếng Anh chuẩn văn hóa fanpage TLC (dùng tiếng lóng, văn phong bàn tán sắc sảo, tự nhiên).
        3. Tạo ra đúng 3 phong cách (Sarcastic & Witty, Engaging Gossip, Analytical) và 4 bình luận mồi (seed comments).

        Trả về kết quả bằng định dạng JSON thuần túy (không kèm markdown ngoài) theo cấu trúc:
        {{
            "witty": "Nội dung bài viết phong cách sarcastic & witty...",
            "gossip": "Nội dung bài viết phong cách engaging gossip...",
            "analytical": "Nội dung bài viết phong cách analytical...",
            "seed_comments": ["Bình luận mồi 1", "Bình luận mồi 2", "Bình luận mồi 3", "Bình luận mồi 4"]
        }}
        """
        
        if st.button("✨ Bắt đầu tạo 3 phiên bản bài đăng"):
            import time
            
            with st.spinner("Gemini đang viết bài (đang kết nối máy chủ tối ưu nhất)..."):
                response_text = None
                
                # Danh sách các model theo thứ tự ưu tiên
                models_to_try = [
                    'gemini-2.5-flash',
                    'gemini-3.0-flash',
                    'gemini-flash-latest',
                    'gemini-1.5-flash'
                ]
                
                last_error = None
                
                # Quét qua từng model, nếu gặp 503 quá tải sẽ tự động chuyển sang model kế tiếp
                for model_name in models_to_try:
                    for attempt in range(2):  # Thử tối đa 2 lần cho mỗi model nếu server bận
                        try:
                            response = client.models.generate_content(
                                model=model_name,
                                contents=prompt,
                                config=types.GenerateContentConfig(
                                    response_mime_type="application/json"
                                )
                            )
                            if response and response.text:
                                response_text = response.text
                                break
                        except Exception as e:
                            last_error = e
                            error_str = str(e)
                            # Nếu gặp 503 (quá tải) hoặc 429 (hạn ngạch), đợi 2 giây rồi thử lại hoặc đổi model
                            if "503" in error_str or "429" in error_str:
                                time.sleep(2)
                                continue
                            else:
                                break  # Lỗi khác thì chuyển luôn sang model kế tiếp
                                
                    if response_text:
                        break  # Đã lấy được kết quả thành công, thoát vòng lặp
                
                if response_text:
                    try:
                        st.session_state['ai_result'] = json.loads(response_text)
                        st.success("Tạo bài thành công!")
                    except Exception as json_err:
                        st.error(f"Lỗi cấu trúc dữ liệu JSON: {json_err}")
                else:
                    st.error(f"Máy chủ Google đang quá tải tạm thời: {last_error}")
                    st.info("👉 Bạn hãy bấm lại nút một lần nữa sau vài giây nhé!")