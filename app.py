import streamlit as st
import pandas as pd
import re
import html
import os
import json
import streamlit.components.v1 as components
from google import genai
from google.genai import types

# 1. Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="TLC Content Hub",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tối ưu giao diện: gọn trên desktop, đỡ cuộn dài trên điện thoại.
# Không thay đổi dữ liệu, thẻ hay nội dung kịch bản, chỉ thay đổi hiển thị.
st.markdown(
    """
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    @media (max-width: 768px) {
        .block-container { padding-left: 0.75rem; padding-right: 0.75rem; }
        .stButton button { padding: 0.5rem 0.75rem; font-size: 15px; }
        [data-testid="stMetricValue"] { font-size: 1.3rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
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

# Hàm lấy nội dung kịch bản (Ưu tiên Cột M / cột số 13, index 12)
def get_script_content(row):
    # Kiểm tra Cột M (Cột số 13, trong python index là 12)
    if len(row) >= 13 and pd.notna(row.iloc[12]):
        val = str(row.iloc[12]).strip()
        if val != "" and val.lower() != "nan":
            return val
    # Dự phòng tìm theo tên cột "Kịch bản"
    if col_script and col_script in row and pd.notna(row[col_script]):
        val = str(row[col_script]).strip()
        if val != "" and val.lower() != "nan":
            return val
    return ""
# Hàm bóc tách kịch bản
def parse_script(raw_text):
    if not raw_text:
        return None
    sections = {"witty": "", "gossip": "", "analytical": "", "comments": "", "translation": "", "image": ""}
    p_witty = re.search(r'\[OPTION 1:.*?\](.*?)(?=\[OPTION 2:|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_gossip = re.search(r'\[OPTION 2:.*?\](.*?)(?=\[OPTION 3:|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_anal = re.search(r'\[OPTION 3:.*?\](.*?)(?=\[SEED COMMENTS\]|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_comm = re.search(r'\[SEED COMMENTS\](.*?)(?=\[BẢN DỊCH TIẾNG VIỆT\]|\[GỢI Ý ẢNH\]|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_trans = re.search(r'\[BẢN DỊCH TIẾNG VIỆT\](.*?)(?=\[GỢI Ý ẢNH\]|$)', raw_text, re.DOTALL | re.IGNORECASE)
    p_image = re.search(r'\[GỢI Ý ẢNH\](.*?)(?=\[BẢN DỊCH TIẾNG VIỆT\]|$)', raw_text, re.DOTALL | re.IGNORECASE)

    sections["witty"] = p_witty.group(1).strip() if p_witty else ""
    sections["gossip"] = p_gossip.group(1).strip() if p_gossip else ""
    sections["analytical"] = p_anal.group(1).strip() if p_anal else ""
    sections["comments"] = p_comm.group(1).strip() if p_comm else ""
    sections["translation"] = p_trans.group(1).strip() if p_trans else ""
    sections["image"] = p_image.group(1).strip() if p_image else ""
    
    if not any([sections["witty"], sections["gossip"], sections["analytical"]]):
        sections["witty"] = raw_text
    return sections

# Nút Copy: Streamlit không có API clipboard phía server, nên dùng nút HTML/JS
# chạy trong trình duyệt để copy đúng đoạn văn bản đang hiển thị.
def copy_button(label, text, button_id):
    if not text:
        return
    payload = json.dumps(text)
    components.html(
        f"""
        <button id="{button_id}" style="width:100%;padding:8px 12px;border:1px solid #ccc;border-radius:8px;cursor:pointer;font-size:14px;background:transparent;">
            {label}
        </button>
        <script>
            (function() {{
                var btn = document.getElementById("{button_id}");
                var original = btn.innerText;
                btn.addEventListener("click", function() {{
                    var text = {payload};
                    function done() {{
                        btn.innerText = "✅ Đã copy!";
                        setTimeout(function() {{ btn.innerText = original; }}, 2000);
                    }}
                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                        navigator.clipboard.writeText(text).then(done).catch(function() {{
                            var ta = document.createElement("textarea");
                            ta.value = text;
                            document.body.appendChild(ta);
                            ta.select();
                            document.execCommand("copy");
                            document.body.removeChild(ta);
                            done();
                        }});
                    }} else {{
                        var ta = document.createElement("textarea");
                        ta.value = text;
                        document.body.appendChild(ta);
                        ta.select();
                        document.execCommand("copy");
                        document.body.removeChild(ta);
                        done();
                    }}
                }});
            }})();
        </script>
        """,
        height=45,
        scrolling=False,
    )

# Hàm gọi Gemini dịch sang tiếng Việt chuẩn văn phong hóng hớt / drama
def translate_to_vietnamese(text_en):
    if not client:
        return "⚠️ Chưa cấu hình GEMINI_API_KEY trong Secrets của Streamlit."
    
    prompt = f"""
  Hãy đóng vai trò như Google Dịch (Google Translate). Hãy dịch toàn bộ văn bản tiếng Anh dưới đây sang Tiếng Việt một cách trực tiếp, chuẩn xác và phổ thông nhất.

QUY TẮC:
1. Dịch trung tính, tự nhiên, thông thường như Google Translate.
2. Giữ nguyên cấu trúc các thẻ phân đoạn trong ngoặc vuông: [OPTION 1:...], [OPTION 2:...], [OPTION 3:...], [SEED COMMENTS], [BẢN DỊCH TIẾNG VIỆT], [GỢI Ý ẢNH].

Văn bản cần dịch:
{text_en}
    """
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Lỗi khi dịch: {e}"

# 4. Tiêu đề ứng dụng & Thống kê
st.title("📺 TLC News & Content Hub")

# Mask "đã có kịch bản" tính một lần bằng vector hoá (cột M, index 12),
# thay cho vòng lặp iterrows qua toàn bộ sheet mỗi lần tải lại trang.
if len(df.columns) >= 13:
    _m_col = df.iloc[:, 12].fillna("").astype(str).str.strip()
    has_script_mask = _m_col.ne("") & (_m_col.str.lower() != "nan")
else:
    has_script_mask = pd.Series(False, index=df.index)
if col_script and col_script in df.columns:
    _s_col = df[col_script].fillna("").astype(str).str.strip()
    has_script_mask = has_script_mask | (_s_col.ne("") & (_s_col.str.lower() != "nan"))

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
total_news = len(df)
has_script = int(has_script_mask.sum())
new_news = total_news - has_script
sensitive_count = df[col_sensitive].dropna().count() if col_sensitive else 0
# Tổng bình luận cũng tính vector hoá từ cột "Tương tác" (dạng "x điểm / y BL").
total_comments = 0
if col_interact:
    _bl = df[col_interact].astype(str).str.extract(r"(\d+)\s*BL", expand=False)
    total_comments = int(pd.to_numeric(_bl, errors="coerce").fillna(0).sum())

col_m1.metric("Tổng số tin", total_news)
col_m2.metric("✅ Đã có kịch bản", has_script)
col_m3.metric("🆕 Chờ kịch bản", new_news)
col_m4.metric("⚠️ Nhạy cảm", sensitive_count)
col_m5.metric("💬 Tổng bình luận", total_comments)

st.divider()

# 5. Sidebar bộ lọc
st.sidebar.header("🔍 Bộ lọc tin")

if st.sidebar.button("🔄 Làm mới dữ liệu", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

show_values = [str(s) for s in df[col_show].dropna().unique() if str(s).strip() != ""]
all_shows = ["Tất cả Show"] + show_values
selected_show = st.sidebar.selectbox("Chọn Show:", all_shows, key="show_sidebar")

filter_status = st.sidebar.radio(
    "Trạng thái kịch bản:",
    ["Tất cả", "Chỉ bài đã có kịch bản", "Chỉ bài mới (chưa có)"],
    index=1
)

search_kw = st.sidebar.text_input("Tìm kiếm theo tiêu đề:")
compact_mode = st.sidebar.checkbox("📱 Chế độ gọn (danh sách)", value=False)
page_size = st.sidebar.selectbox("Số bài mỗi trang:", [10, 20, 50], index=1)

filtered_df = df.copy()

if selected_show != "Tất cả Show":
    filtered_df = filtered_df[filtered_df[col_show] == selected_show]

if filter_status == "Chỉ bài đã có kịch bản":
    filtered_df = filtered_df[has_script_mask.loc[filtered_df.index]]
elif filter_status == "Chỉ bài mới (chưa có)":
    filtered_df = filtered_df[~has_script_mask.loc[filtered_df.index]]

if search_kw.strip() and col_title:
    filtered_df = filtered_df[filtered_df[col_title].astype(str).str.contains(search_kw.strip(), case=False, na=False)]

if 'translations_cache' not in st.session_state:
    st.session_state['translations_cache'] = {}
if 'current_row' not in st.session_state and not filtered_df.empty:
    first_row = filtered_df.iloc[0]
    st.session_state['current_row'] = first_row
    st.session_state['current_row_idx'] = first_row.name
    st.session_state['current_script'] = get_script_content(first_row)
    st.session_state['translated_script'] = st.session_state['translations_cache'].get(first_row.name)

# Phân trang: chỉ render số bài của trang hiện tại, thay vì render hết
# danh sách đã lọc (nguyên nhân chính gây lag khi sheet có 200+ dòng).
import math
total_pages = max(1, math.ceil(len(filtered_df) / page_size)) if not filtered_df.empty else 1
page_input = st.sidebar.number_input(
    "Trang:", min_value=1, max_value=total_pages, value=1, step=1, key="page_num"
)
current_page = min(int(page_input), total_pages)
page_start = (current_page - 1) * page_size
page_df = filtered_df.iloc[page_start:page_start + page_size]

# Lọc nhanh theo show (thêm ngoài lọc sidebar): hiển thị luôn ở khu vực chính
# để khỏi phải mở sidebar, nhất là trên điện thoại. Bấm một nút sẽ đặt lại
# đúng giá trị của lọc sidebar rồi chạy lại trang, nên hai chỗ luôn đồng bộ.
st.markdown("🎬 **Lọc nhanh theo show:**")
_short_show = {
    "Tất cả Show": "Tất cả",
    "90 Day Fiancé": "90 Day",
    "Sister Wives": "Sister Wives",
    "1000-Lb Sisters": "1000-Lb",
    "Welcome to Plathville": "Plathville",
    "Khác": "Khác",
}
_chip_shows = ["Tất cả Show"] + show_values
for _r in range(0, len(_chip_shows), 3):
    _cols = st.columns(3)
    for _c, _show in enumerate(_chip_shows[_r:_r + 3]):
        _label = _short_show.get(_show, _show)
        if _show == selected_show:
            _label = f"✅ {_label}"
        with _cols[_c]:
            if st.button(_label, key=f"chip_show_{_r + _c}", use_container_width=True):
                st.session_state["show_sidebar"] = _show
                st.session_state["page_num"] = 1
                st.rerun()

# 6. Giao diện hiển thị: 2 Cột
col_left, col_right = st.columns([1, 1.25])

with col_left:
    st.subheader(f"📋 Danh sách tin ({len(filtered_df)}) — Trang {current_page}/{total_pages}")
    if not filtered_df.empty:
        st.caption(f"Đang hiển thị {len(page_df)} bài (từ bài {page_start + 1} đến {page_start + len(page_df)}). Đổi trang ở sidebar.")

    if filtered_df.empty:
        st.info("Không có tin nào phù hợp với bộ lọc.")
    else:
        current_idx = st.session_state.get('current_row_idx')
        for idx, row in page_df.iterrows():
            script_text = get_script_content(row)
            is_ready = bool(script_text)

            with st.container(border=True):
                badge = "🟢 Đã có kịch bản" if is_ready else "⚪ Mới"
                show_val = str(row.get(col_show, ''))
                title_val = str(row.get(col_title, ''))
                viewing = " 👈 Đang xem" if idx == current_idx else ""

                st.markdown(f"**[{show_val}]** {badge}{viewing}")
                st.write(title_val)

                if not compact_mode:
                    source_val = str(row.get(col_source, 'N/A'))
                    info_line = f"Nguồn: `{source_val}`"
                    if col_interact and pd.notna(row.get(col_interact)):
                        info_line += f" | 🔥 {row.get(col_interact)}"
                    st.caption(info_line)
                elif col_interact and pd.notna(row.get(col_interact)):
                    st.caption(f"🔥 {row.get(col_interact)}")

                if col_sensitive and pd.notna(row.get(col_sensitive)) and str(row.get(col_sensitive)).strip() != "":
                    if compact_mode:
                        st.caption(f"⚠️ Nhạy cảm: {row.get(col_sensitive)}")
                    else:
                        st.warning(f"⚠️ Nhạy cảm: {row.get(col_sensitive)}")

                # Nút xem bài gốc đã chuyển sang đây, nằm cạnh nút xem kịch bản.
                # Dùng thẻ <a> thay cho link_button để khỏi trùng widget khi
                # lặp qua nhiều thẻ, và chỉ chấp nhận link http/https.
                btn_name = "👁️ Xem kịch bản & Copy" if is_ready else "📝 Xem thông tin"
                _b1, _b2 = st.columns([2, 1])
                with _b1:
                    if st.button(btn_name, key=f"btn_{idx}", use_container_width=True):
                        st.session_state['current_row'] = row
                        st.session_state['current_row_idx'] = idx
                        st.session_state['current_script'] = script_text
                        # Lấy lại bản dịch đã dịch trước đó của đúng bài này (nếu có),
                        # thay vì reset mất và phải dịch lại từ đầu.
                        st.session_state['translated_script'] = st.session_state['translations_cache'].get(idx)
                with _b2:
                    _link = row.get(col_link) if col_link else None
                    if pd.notna(_link) and str(_link).strip().startswith(("http://", "https://")):
                        _safe = html.escape(str(_link).strip(), quote=True)
                        st.markdown(
                            f'<a href="{_safe}" target="_blank" rel="noopener" '
                            'style="display:block;text-align:center;padding:8px 4px;'
                            'border:1px solid #ccc;border-radius:8px;'
                            'text-decoration:none;color:inherit;font-size:14px;">'
                            "🌐 Bài gốc</a>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("Không có link")

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
                        st.session_state['translations_cache'][st.session_state.get('current_row_idx')] = translated
            
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
            copy_button("📋 Copy toàn văn", content_to_show, "copy-full")

            st.caption("⚡ Copy nhanh (không cần chuyển tab):")
            q1, q2 = st.columns(2)
            with q1:
                copy_button("📋 Copy Option 1", parsed["witty"], "copy-quick-witty")
            with q2:
                if parsed["translation"]:
                    copy_button("📋 Copy Bản dịch", parsed["translation"], "copy-quick-translation")
                else:
                    st.caption("Chưa có bản dịch trong cột M.")

            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "🔥 Sarcastic & Witty",
                "🗣️ Gossip & Viral",
                "🧐 Analytical",
                "💬 Seed Comments",
                "🇻🇳 Bản dịch",
                "🖼️ Gợi ý ảnh",
                "📄 Toàn văn"
            ])
            
            with tab1:
                st.caption(f"Phong cách Sarcastic ({chosen_lang}):")
                copy_button("📋 Copy Sarcastic", parsed["witty"], "copy-witty")
                st.text_area("Sarcastic:", parsed["witty"], height=240)

            with tab2:
                st.caption(f"Phong cách Gossip ({chosen_lang}):")
                copy_button("📋 Copy Gossip", parsed["gossip"], "copy-gossip")
                st.text_area("Gossip:", parsed["gossip"], height=240)

            with tab3:
                st.caption(f"Phong cách Analytical ({chosen_lang}):")
                copy_button("📋 Copy Analytical", parsed["analytical"], "copy-analytical")
                st.text_area("Analytical:", parsed["analytical"], height=240)

            with tab4:
                st.caption(f"Bình luận mồi ({chosen_lang}):")
                if parsed["comments"]:
                    copy_button("📋 Copy Seed Comments", parsed["comments"], "copy-comments")
                    st.text_area("Seed comments:", parsed["comments"], height=220)
                else:
                    st.info("Chưa có danh sách bình luận mồi riêng.")

            with tab5:
                st.caption("Bản dịch tiếng Việt (ghi trong cột M):")
                if parsed["translation"]:
                    copy_button("📋 Copy Bản dịch", parsed["translation"], "copy-translation")
                    st.text_area("Bản dịch:", parsed["translation"], height=240)
                else:
                    st.info("Chưa có bản dịch ghi trong cột M cho bài này (các bài mới sẽ có phần [BẢN DỊCH TIẾNG VIỆT] trong cột M).")

            with tab6:
                st.caption(f"Gợi ý ảnh ({chosen_lang}):")
                if parsed["image"]:
                    copy_button("📋 Copy Gợi ý ảnh", parsed["image"], "copy-image")
                    st.text_area("Gợi ý ảnh:", parsed["image"], height=220)
                else:
                    st.info("Chưa có gợi ý ảnh cho bài này (các bài mới sẽ có phần [GỢI Ý ẢNH] trong cột M).")

            with tab7:
                copy_button("📋 Copy toàn văn", content_to_show, "copy-full-tab")
                st.text_area("Toàn văn nội dung:", content_to_show, height=300)
        else:
            st.warning("⚠️ Dòng này chưa có nội dung kịch bản trong Google Sheet.")
            st.info("👉 Mở Google Sheet, click dòng này và bấm '🤖 TLC AI Content > 🚀 Tạo kịch bản'.")
            
        with st.expander("📌 Nguồn bài viết", expanded=False):
            st.write(f"**Nguồn:** {cur.get(col_source, '')}")
            st.caption("Nút xem bài gốc đã chuyển sang thẻ tin ở danh sách bên trái.")
    else:
        st.info("👈 Chọn một tin ở danh sách bên trái để xem nội dung.")
