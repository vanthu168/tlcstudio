import streamlit as st
import pandas as pd
import re
import html
import urllib.request
import json
import streamlit.components.v1 as components

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
    /* Ghim panel kịch bản bên phải khi cuộn danh sách trên PC: cột phải
       (cột thứ 2 của khối 2 cột chính) dính ở đầu màn hình và tự cuộn
       nội dung bên trong nếu nó cao hơn màn hình, nên bấm tin ở cuối
       danh sách cũng thấy kịch bản ngay mà không phải kéo lên lại.
       Chỉ áp dụng trên màn hình rộng; trên điện thoại 2 cột xếp chồng
       lên nhau nên không ghim để khỏi che danh sách. Các khối ngang ngắn
       khác (thống kê, nút copy nhanh...) không bị ảnh hưởng vì khối cha
       của chúng thấp, sticky không có chỗ để phát huy tác dụng. */
    @media (min-width: 769px) {
        div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-of-type(2),
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
            position: sticky;
            top: 2rem;
            align-self: flex-start;
            max-height: calc(100vh - 4rem);
            overflow-y: auto;
            padding-right: 0.25rem;
        }
    }
    @media (max-width: 768px) {
        .block-container { padding-left: 0.75rem; padding-right: 0.75rem; }
        .stButton button { padding: 0.5rem 0.75rem; font-size: 15px; }
        [data-testid="stMetricValue"] { font-size: 1.3rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 2. Kết nối Google Sheet qua Sheet ID và GID tab "Hôm nay"
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
col_posted = find_col(df.columns, "Đăng lúc")

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

# Ghi trạng thái "Đã đăng" vào cột J của sheet qua Apps Script web app.
# Dash chỉ đọc sheet qua CSV công khai nên không tự ghi được; endpoint này
# là cầu nối ghi duy nhất. Endpoint và token lấy từ Streamlit Secrets:
# SHEETS_WRITE_URL và SHEETS_WRITE_TOKEN. Chưa cấu hình thì hàm trả False
# kèm hướng dẫn, app không crash và không báo ghi thành công giả.
# Apps Script định vị dòng theo Link (cột E) ở các tab dữ liệu + "Hôm nay",
# rồi đặt cột J thành "Đã đăng". Xem hướng dẫn thiết lập trong chat.
def mark_posted(link):
    try:
        url = st.secrets.get("SHEETS_WRITE_URL")
        token = st.secrets.get("SHEETS_WRITE_TOKEN")
    except Exception:
        url, token = None, None
    if not url or not token:
        return False, "Chưa cấu hình SHEETS_WRITE_URL / SHEETS_WRITE_TOKEN trong Streamlit Secrets, nên chưa ghi được vào sheet. Làm theo hướng dẫn thiết lập Apps Script rồi bấm lại."
    if not link or not str(link).strip().startswith(("http://", "https://")):
        return False, "Bài này không có link gốc hợp lệ để định vị dòng trong sheet."
    payload = json.dumps({"token": token, "link": str(link).strip(), "status": "Đã đăng"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return False, f"Không gọi được Apps Script: {e}"
    if data.get("ok"):
        updated = data.get("updated") or []
        if updated:
            return True, f"Đã ghi Đã đăng cho {len(updated)} dòng."
        return True, "Đã ghi Đã đăng (không tìm thấy dòng nào khớp link, hãy kiểm tra lại link trong sheet)."
    return False, f"Apps Script báo lỗi: {data.get('error', 'không rõ')}"

# Chạy script săn tin trên sheet qua cùng Apps Script web app (cùng URL/token
# với nút Đã đăng, không cần Secrets mới). Apps Script chạy hàm sanTin_ rồi
# trả về số tin mới thêm. Săn tin tải nhiều nguồn nên có thể mất 1-2 phút:
# timeout 300 giây. Nếu quá thời gian mà script vẫn chạy trên Google thì
# Dash báo lỗi kết nối, nhưng lần chạy đó có thể vẫn hoàn tất — kiểm tra
# tab "Nhật ký" trong sheet sau 1-2 phút thay vì bấm săn tin thêm lần nữa.
def run_hunt():
    try:
        url = st.secrets.get("SHEETS_WRITE_URL")
        token = st.secrets.get("SHEETS_WRITE_TOKEN")
    except Exception:
        url, token = None, None
    if not url or not token:
        return False, "Chưa cấu hình SHEETS_WRITE_URL / SHEETS_WRITE_TOKEN trong Streamlit Secrets, nên chưa chạy săn tin được. Làm theo hướng dẫn thiết lập Apps Script rồi bấm lại."
    payload = json.dumps({"token": token, "action": "sanTin"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return False, f"Không gọi được Apps Script (nếu script vẫn đang chạy trên Google, kiểm tra tab Nhật ký trong sheet sau 1-2 phút thay vì bấm lại): {e}"
    if data.get("ok"):
        added = data.get("added")
        errs = data.get("errors") or []
        msg = f"Đã săn tin xong, thêm {added} tin mới." if added is not None else "Đã săn tin xong."
        if errs:
            msg += f" Có {len(errs)} nguồn lỗi (xem tab Nhật ký trong sheet)."
        return True, msg
    return False, f"Apps Script báo lỗi: {data.get('error', 'không rõ')}"

# Làm mới trang "Hôm nay" trên sheet qua cùng Apps Script web app (cùng
# URL/token với nút Đã đăng và Săn tin, không cần Secrets mới). Apps Script
# chạy hàm lamMoiHomNay_ — chép lại toàn bộ cột A–M từ các tab show cho
# các bài trong 48 giờ qua vào tab "Hôm nay", sắp xếp mới nhất lên trên.
# Đây là cách đưa các bài đã có kịch bản ở tab show (nhưng chưa vào
# "Hôm nay") lên Dash, vì Dash chỉ đọc tab "Hôm nay". Làm mới chỉ đọc và
# chép lại, không săn tin báo mới, không đổi trạng thái nào. Timeout 120
# giây là đủ cho một lần chép lại; quá thời gian thì kiểm tra lại tab
# "Hôm nay" trong sheet thay vì bấm thêm lần nữa.
def run_refresh_today():
    try:
        url = st.secrets.get("SHEETS_WRITE_URL")
        token = st.secrets.get("SHEETS_WRITE_TOKEN")
    except Exception:
        url, token = None, None
    if not url or not token:
        return False, "Chưa cấu hình SHEETS_WRITE_URL / SHEETS_WRITE_TOKEN trong Streamlit Secrets, nên chưa làm mới được trang Hôm nay. Làm theo hướng dẫn thiết lập Apps Script rồi bấm lại."
    payload = json.dumps({"token": token, "action": "lamMoiHomNay"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return False, f"Không gọi được Apps Script (kiểm tra lại tab Hôm nay trong sheet thay vì bấm lại ngay): {e}"
    if data.get("ok"):
        rows = data.get("rows")
        msg = f"Đã làm mới trang Hôm nay, {rows} dòng." if rows is not None else "Đã làm mới trang Hôm nay."
        return True, msg
    return False, f"Apps Script báo lỗi: {data.get('error', 'không rõ')}"

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

_hunt_notice = st.session_state.pop('hunt_notice', None)
if _hunt_notice:
    st.sidebar.success(f"✅ {_hunt_notice}")

_refresh_notice = st.session_state.pop('refresh_notice', None)
if _refresh_notice:
    st.sidebar.success(f"✅ {_refresh_notice}")

_refresh_error = st.session_state.pop('refresh_error', None)
if _refresh_error:
    st.sidebar.warning(f"⚠️ {_refresh_error}")

if st.sidebar.button("🔄 Làm mới dữ liệu", use_container_width=True):
    # Nút này vừa làm mới dữ liệu hiển thị, vừa chép lại tab "Hôm nay"
    # từ các tab show qua Apps Script, để các bài đã có kịch bản ở tab
    # show (nhưng chưa vào "Hôm nay") cũng hiện lên Dash ngay, thay vì
    # chỉ tải lại bản snapshot cũ. Nếu gọi Apps Script thất bại (kẹt
    # khóa do một lần chạy khác, hết thời gian chờ, chưa cập nhật script),
    # vẫn xóa cache và tải lại danh sách cũ thay vì kẹt ở lỗi, và báo
    # lý do bằng thông báo cảnh báo sau khi tải lại.
    with st.spinner("Đang làm mới trang Hôm nay từ các tab show, đợi một chút..."):
        _ok, _msg = run_refresh_today()
    if _ok:
        st.session_state['refresh_notice'] = _msg
    else:
        st.session_state['refresh_error'] = f"{_msg} Danh sách bên dưới vẫn được tải lại từ tab Hôm nay hiện tại."
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("🔎 Săn tin ngay", use_container_width=True):
    with st.spinner("Đang săn tin, có thể mất 1-2 phút, đừng bấm thêm lần nữa..."):
        _ok, _msg = run_hunt()
    if _ok:
        st.session_state['hunt_notice'] = _msg
        st.cache_data.clear()
        st.rerun()
    else:
        st.sidebar.warning(_msg)
st.sidebar.caption("Làm mới dữ liệu chép lại tab Hôm nay từ các tab show rồi tải lại danh sách. Săn tin ngay chạy script trên sheet (tương đương menu Chạy ngay), rồi tải lại danh sách.")

show_values = [str(s) for s in df[col_show].dropna().unique() if str(s).strip() != ""]
all_shows = ["Tất cả Show"] + show_values
# Áp dụng lựa chọn show/trang đang chờ từ nút chip (xem nút chip bên dưới).
# Bắt buộc phải gán ở đây, trước khi các widget show_sidebar và page_num
# được vẽ, nếu không Streamlit báo lỗi WidgetAlreadyInstantiated.
# Show chờ phải còn trong danh sách show hiện tại mới được áp dụng.
if "pending_show" in st.session_state:
    _pending_show = st.session_state.pop("pending_show")
    if _pending_show in all_shows:
        st.session_state["show_sidebar"] = _pending_show
if "pending_page" in st.session_state:
    st.session_state["page_num"] = st.session_state.pop("pending_page")
selected_show = st.sidebar.selectbox("Chọn Show:", all_shows, key="show_sidebar")

filter_status = st.sidebar.radio(
    "Trạng thái kịch bản:",
    ["Tất cả", "Chỉ bài đã có kịch bản", "Chỉ bài mới (chưa có)", "Chỉ bài đã đăng"],
    index=1
)

search_kw = st.sidebar.text_input("Tìm kiếm theo tiêu đề:")
compact_mode = st.sidebar.checkbox("📱 Chế độ gọn (danh sách)", value=True)
page_size = st.sidebar.selectbox("Số bài mỗi trang:", [10, 20, 50], index=1)

filtered_df = df.copy()

if selected_show != "Tất cả Show":
    filtered_df = filtered_df[filtered_df[col_show] == selected_show]

if filter_status == "Chỉ bài đã có kịch bản":
    filtered_df = filtered_df[has_script_mask.loc[filtered_df.index]]
elif filter_status == "Chỉ bài mới (chưa có)":
    filtered_df = filtered_df[~has_script_mask.loc[filtered_df.index]]
elif filter_status == "Chỉ bài đã đăng":
    if col_status:
        filtered_df = filtered_df[filtered_df[col_status].fillna("").astype(str).str.strip() == "Đã đăng"]
    else:
        filtered_df = filtered_df.iloc[0:0]

if search_kw.strip() and col_title:
    filtered_df = filtered_df[filtered_df[col_title].astype(str).str.contains(search_kw.strip(), case=False, na=False)]

if 'current_row' not in st.session_state and not filtered_df.empty:
    first_row = filtered_df.iloc[0]
    st.session_state['current_row'] = first_row
    st.session_state['current_row_idx'] = first_row.name
    st.session_state['current_script'] = get_script_content(first_row)

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
                st.session_state["pending_show"] = _show
                st.session_state["pending_page"] = 1
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
                _status_val = str(row.get(col_status, "")).strip() if col_status else ""
                if _status_val == "Đã đăng":
                    badge = "✅ Đã đăng"
                elif is_ready:
                    badge = "🟢 Đã có kịch bản"
                else:
                    badge = "⚪ Mới"
                show_val = str(row.get(col_show, ''))
                title_val = str(row.get(col_title, ''))
                viewing = " 👈 Đang xem" if idx == current_idx else ""

                # Thẻ tin 2 dòng, áp dụng cho cả chế độ gọn và đầy đủ:
                # dòng 1: Show - Trạng thái - Đánh giá (tương tác) - Giờ đăng (cột G),
                # dòng 2: Tiêu đề.
                _is_sensitive = bool(
                    col_sensitive and pd.notna(row.get(col_sensitive))
                    and str(row.get(col_sensitive)).strip() != ""
                )
                _line1_parts = [f"[{show_val}]", badge]
                if col_interact and pd.notna(row.get(col_interact)):
                    _line1_parts.append(f"🔥 {row.get(col_interact)}")
                if col_posted and pd.notna(row.get(col_posted)):
                    _posted_val = str(row.get(col_posted)).strip()
                    # Cột G lưu dạng chữ "yyyy-MM-dd HH:mm"; nếu lỡ có giây thì bỏ ":00" cuối.
                    if len(_posted_val) == 19 and _posted_val.endswith(":00"):
                        _posted_val = _posted_val[:16]
                    if _posted_val and _posted_val.lower() != "nan":
                        _line1_parts.append(f"🕐 {_posted_val}")
                _line1 = " - ".join(_line1_parts) + viewing
                if compact_mode and _is_sensitive:
                    # Chế độ gọn: chỉ thêm icon cảnh báo vào dòng 1 để giữ đúng 2 dòng.
                    _line1 += " ⚠️"
                st.markdown(f"**{_line1}**")
                st.write(title_val)
                if not compact_mode:
                    source_val = str(row.get(col_source, 'N/A'))
                    st.caption(f"Nguồn: `{source_val}`")
                    if _is_sensitive:
                        st.warning(f"⚠️ Nhạy cảm: {row.get(col_sensitive)}")

                # Nút xem bài gốc đã chuyển sang đây, nằm cạnh nút xem kịch bản.
                # Dùng thẻ <a> thay cho link_button để khỏi trùng widget khi
                # lặp qua nhiều thẻ, và chỉ chấp nhận link http/https.
                if compact_mode:
                    btn_name = "👁️ Xem" if is_ready else "📝 Xem"
                else:
                    btn_name = "👁️ Xem kịch bản & Copy" if is_ready else "📝 Xem thông tin"
                _b1, _b2 = st.columns([2, 1])
                with _b1:
                    if st.button(btn_name, key=f"btn_{idx}", use_container_width=True):
                        st.session_state['current_row'] = row
                        st.session_state['current_row_idx'] = idx
                        st.session_state['current_script'] = script_text
                with _b2:
                    _link = row.get(col_link) if col_link else None
                    if pd.notna(_link) and str(_link).strip().startswith(("http://", "https://")):
                        _safe = html.escape(str(_link).strip(), quote=True)
                        st.markdown(
                            f'<a href="{_safe}" target="_blank" rel="noopener" '
                            'style="display:block;text-align:center;padding:8px 4px;'
                            'border:1px solid #ccc;border-radius:8px;'
                            'text-decoration:none;color:inherit;font-size:14px;">'
                            "🌐 Gốc</a>" if compact_mode else "🌐 Bài gốc</a>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("Không có link")

with col_right:
    st.subheader("📑 Kịch bản Facebook (Copy nhanh)")

    _posted_notice = st.session_state.pop('posted_notice', None)
    if _posted_notice:
        st.success("✅ Đã ghi Đã đăng vào sheet cho bài vừa chọn.")

    if 'current_row' in st.session_state:
        cur = st.session_state['current_row']
        raw_script = st.session_state.get('current_script', '')

        st.info(f"**[{cur.get(col_show, '')}]** {cur.get(col_title, '')}")

        # Nút Đã đăng: ghi thật vào cột J của sheet qua Apps Script.
        _cur_status = str(cur.get(col_status, "")).strip() if col_status else ""
        _cur_link = cur.get(col_link) if col_link else None
        if _cur_status == "Đã đăng":
            st.success("✅ Bài này đã được đánh dấu Đã đăng trong sheet.")
        elif st.button("✅ Đánh dấu Đã đăng", use_container_width=True):
            _ok, _msg = mark_posted(_cur_link)
            if _ok:
                st.session_state['posted_notice'] = str(cur.get(col_title, ''))
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning(_msg)
        
        if raw_script:
            # Nội dung hiển thị luôn là kịch bản gốc từ cột M.
            # (Tính năng dịch tự động đã gỡ; bản dịch tiếng Việt vẫn có ở
            # tab "🇻🇳 Bản dịch" nếu bài đó đã ghi [BẢN DỊCH TIẾNG VIỆT] vào cột M.)
            content_to_show = raw_script

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
                "✍️ Option 3",
                "💬 Seed Comments",
                "🇻🇳 Bản dịch",
                "🖼️ Gợi ý ảnh",
                "📄 Toàn văn"
            ])
            
            with tab1:
                st.caption("Phong cách Sarcastic:")
                copy_button("📋 Copy Sarcastic", parsed["witty"], "copy-witty")
                st.text_area("Sarcastic:", parsed["witty"], height=240)

            with tab2:
                st.caption("Phong cách Gossip:")
                copy_button("📋 Copy Gossip", parsed["gossip"], "copy-gossip")
                st.text_area("Gossip:", parsed["gossip"], height=240)

            with tab3:
                st.caption("Phong cách Option 3 (OP's Voice / Hot Take):")
                copy_button("📋 Copy Option 3", parsed["analytical"], "copy-analytical")
                st.text_area("Option 3:", parsed["analytical"], height=240)

            with tab4:
                st.caption("Bình luận mồi:")
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
                st.caption("Gợi ý ảnh:")
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
