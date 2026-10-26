import streamlit as st
import pandas as pd
import json
import os
from google import genai
from google.genai import types

st.set_page_config(page_title="TLC News to Facebook", page_icon="📺", layout="wide")
st.title("📺 TLC News Săn Tin ➔ Facebook Post Generator")

# Lấy API Key từ Secrets của Streamlit Cloud hoặc biến môi trường
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
if not api_key:
    st.error("Chưa cấu hình GEMINI_API_KEY trong Settings/Secrets!")
    st.stop()

client = genai.Client(api_key=api_key)

# Đọc dữ liệu từ file CSV
CSV_FILE = "TLC_Săn_tin_Hôm_nay.csv"

try:
    df = pd.read_csv(CSV_FILE)
except Exception as e:
    st.error(f"Không thể đọc dữ liệu từ {CSV_FILE}: {e}")
    st.stop()

st.sidebar.header("🔍 Bộ lọc tin")
all_shows = ["Tất cả"] + [s for s in df['Show'].dropna().unique()]
selected_show = st.sidebar.selectbox("Chọn Show:", all_shows)
filter_status = st.sidebar.radio("Trạng thái:", ["Chỉ tin 'Mới'", "Tất cả"])

filtered_df = df.copy()
if selected_show != "Tất cả":
    filtered_df = filtered_df[filtered_df['Show'] == selected_show]
if filter_status == "Chỉ tin 'Mới'":
    filtered_df = filtered_df[filtered_df['Trạng thái'] == "Mới"]

st.write(f"Đang hiển thị **{len(filtered_df)}** tin tức.")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📋 Danh sách tin")
    for idx, row in filtered_df.iterrows():
        with st.container(border=True):
            st.markdown(f"**[{row['Show']}]** {row['Tiêu đề']}")
            st.caption(f"Nguồn: {row.get('Nguồn', '')} | Tương tác: {row.get('Tương tác', '')} | Trạng thái: {row.get('Trạng thái', '')}")
            if pd.notna(row.get('Nhạy cảm')):
                st.warning(f"⚠️ Nhạy cảm: {row['Nhạy cảm']}")
            
            if st.button("🚀 Viết bài Facebook", key=f"btn_{idx}"):
                st.session_state['selected_item'] = row.to_dict()
                st.session_state['selected_idx'] = idx

with col2:
    st.subheader("✍️ Kết quả tạo bài từ Gemini")
    
    if 'selected_item' in st.session_state:
        item = st.session_state['selected_item']
        st.info(f"Đang chọn: **{item['Tiêu đề']}**")
        
        prompt = f"""
        Bạn là chuyên gia sáng tạo nội dung Facebook cho fanpage Reality TV TLC (US).
        Dựa vào tin tức sau:
        - Show: {item.get('Show')}
        - Tiêu đề: {item.get('Tiêu đề')}
        - Nguồn: {item.get('Nguồn')}
        - Link: {item.get('Link')}

        YÊU CẦU:
        1. Tuân thủ 100% Meta Policy (không thô tục, bạo lực hay quấy rối).
        2. Viết bằng tiếng Anh chuẩn văn phong Reality TV.
        3. Tạo ra đúng 3 phong cách (Sarcastic & Witty, Engaging Gossip, Analytical) và 4 bình luận mồi (seed comments).
        
        Trả về kết quả bằng JSON:
        {{
            "witty": "Nội dung bài sarcastic...",
            "gossip": "Nội dung bài engaging gossip...",
            "analytical": "Nội dung bài analytical...",
            "seed_comments": ["Comment 1", "Comment 2", "Comment 3", "Comment 4"]
        }}
        """
        
        if st.button("Bắt đầu sinh nội dung"):
            with st.spinner("Gemini đang viết bài..."):
                try:
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                    st.session_state['ai_result'] = json.loads(response.text)
                    st.success("Tạo bài thành công!")
                except Exception as e:
                    st.error(f"Lỗi: {e}")

        if 'ai_result' in st.session_state:
            res = st.session_state['ai_result']
            tab1, tab2, tab3 = st.tabs(["🔥 Sarcastic & Witty", "🗣️ Engaging Gossip", "🧐 Analytical"])
            with tab1:
                st.text_area("Copy bài Sarcastic:", res.get("witty", ""), height=220)
            with tab2:
                st.text_area("Copy bài Gossip:", res.get("gossip", ""), height=220)
            with tab3:
                st.text_area("Copy bài Analytical:", res.get("analytical", ""), height=220)
                
            st.markdown("#### 💬 Bình luận mồi:")
            for c in res.get("seed_comments", []):
                st.code(c, language="text")
    else:
        st.write("👈 Chọn một tin từ danh sách bên trái để tạo bài.")