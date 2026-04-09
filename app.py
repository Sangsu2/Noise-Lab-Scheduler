import streamlit as st
import json
import os
from datetime import datetime, date
import calendar

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="소음 시험실 예약",
    page_icon="🔇",
    layout="wide"
)

# ── 비밀번호 설정 ─────────────────────────────────────────────
# .streamlit/secrets.toml 에 설정된 비밀번호 사용
# 없을 경우 기본값 "lge1234" 사용
APP_PASSWORD = st.secrets.get("APP_PASSWORD", "lge1234")

# ── 로그인 체크 ───────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <div style='max-width:360px;margin:80px auto;text-align:center'>
        <div style='font-size:48px;margin-bottom:16px'>🔇</div>
        <h2 style='margin-bottom:8px'>소음 시험실 예약</h2>
        <p style='color:#888;margin-bottom:32px'>접속하려면 비밀번호를 입력하세요</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pw_input = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")
        if st.button("입력", use_container_width=True, type="primary"):
            if pw_input == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
    st.stop()

# ── 슬롯 정의 ────────────────────────────────────────────────
SLOTS = [
    {"id": 0, "label": "1타임", "time": "08:00 ~ 12:00"},
    {"id": 1, "label": "2타임", "time": "12:00 ~ 16:00"},
    {"id": 2, "label": "3타임", "time": "16:00 ~ 20:00"},
    {"id": 3, "label": "4타임", "time": "20:00 ~ 24:00"},
    {"id": 4, "label": "5타임", "time": "00:00 ~ 04:00"},
    {"id": 5, "label": "6타임", "time": "04:00 ~ 08:00"},
]

SLOT_COLORS = ["#7F77DD", "#1D9E75", "#D85A30", "#D4537E", "#378ADD", "#639922"]

DATA_FILE = "bookings.json"

# ── 데이터 로드/저장 ─────────────────────────────────────────
def load_bookings():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_bookings(bookings):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(bookings, f, ensure_ascii=False, indent=2)

def date_key(y, m, d):
    return f"{y}-{str(m).zfill(2)}-{str(d).zfill(2)}"

# ── 세션 초기화 ──────────────────────────────────────────────
if "view" not in st.session_state:
    st.session_state.view = "cal"
if "sel_year" not in st.session_state:
    st.session_state.sel_year = date.today().year
if "sel_month" not in st.session_state:
    st.session_state.sel_month = date.today().month
if "sel_date" not in st.session_state:
    st.session_state.sel_date = None
if "sel_slot" not in st.session_state:
    st.session_state.sel_slot = None
if "bookings" not in st.session_state:
    st.session_state.bookings = load_bookings()

bookings = st.session_state.bookings

# ── 스타일 ───────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1.5rem; padding-bottom: 1rem;}
.slot-badge {
    border-radius: 4px; padding: 2px 5px;
    font-size: 11px; margin-bottom: 2px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    color: white;
}
</style>
""", unsafe_allow_html=True)

MONTHS_KR = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
DAYS_KR = ["월","화","수","목","금","토","일"]

# ── 로그아웃 버튼 ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔇 소음 시험실 예약")
    st.divider()
    if st.button("🔒 로그아웃", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.view = "cal"
        st.rerun()

# ════════════════════════════════════════════════════════════
# 뷰 1: 달력
# ════════════════════════════════════════════════════════════
if st.session_state.view == "cal":
    y = st.session_state.sel_year
    m = st.session_state.sel_month

    col_l, col_mid, col_r = st.columns([1, 2, 1])
    with col_l:
        if st.button("◀ 이전 달", use_container_width=True):
            if m == 1:
                st.session_state.sel_month = 12
                st.session_state.sel_year -= 1
            else:
                st.session_state.sel_month -= 1
            st.rerun()
    with col_mid:
        st.markdown(f"<h2 style='text-align:center;margin:0'>🔇 소음 시험실 예약 &nbsp;·&nbsp; {y}년 {MONTHS_KR[m-1]}</h2>", unsafe_allow_html=True)
    with col_r:
        if st.button("다음 달 ▶", use_container_width=True):
            if m == 12:
                st.session_state.sel_month = 1
                st.session_state.sel_year += 1
            else:
                st.session_state.sel_month += 1
            st.rerun()

    st.divider()

    day_cols = st.columns(7)
    for i, d in enumerate(DAYS_KR):
        color = "#e53935" if i == 6 else "#1565C0" if i == 5 else "#333"
        day_cols[i].markdown(f"<div style='text-align:center;font-weight:600;color:{color};font-size:14px'>{d}</div>", unsafe_allow_html=True)

    cal = calendar.monthcalendar(y, m)
    today = date.today()

    for week in cal:
        cols = st.columns(7)
        for wi, day in enumerate(week):
            with cols[wi]:
                if day == 0:
                    st.markdown("<div style='min-height:90px'></div>", unsafe_allow_html=True)
                    continue

                key = date_key(y, m, day)
                day_bookings = bookings.get(key, {})
                is_today = (y == today.year and m == today.month and day == today.day)

                num_color = "#e53935" if wi == 6 else "#1565C0" if wi == 5 else "#333"
                today_style = "background:#534AB7;color:white;border-radius:50%;width:24px;height:24px;display:inline-flex;align-items:center;justify-content:center;" if is_today else f"color:{num_color}"

                badges_html = ""
                for sid_str, info in list(day_bookings.items())[:3]:
                    sid = int(sid_str)
                    color = SLOT_COLORS[sid % len(SLOT_COLORS)]
                    label = SLOTS[sid]["label"]
                    name = info.get("name", "")
                    badges_html += f'<div class="slot-badge" style="background:{color}">{label} {name}</div>'
                if len(day_bookings) > 3:
                    badges_html += f'<div class="slot-badge" style="background:#888">+{len(day_bookings)-3}건</div>'

                st.markdown(f"""
                <div style='border:1px solid #e0e0e0;border-radius:8px;padding:6px;min-height:90px;background:white'>
                    <div style='font-weight:600;font-size:14px;margin-bottom:4px'>
                        <span style='{today_style}'>{day}</span>
                    </div>
                    {badges_html}
                </div>
                """, unsafe_allow_html=True)

                if st.button("선택", key=f"day_{y}_{m}_{day}", use_container_width=True):
                    st.session_state.sel_date = day
                    st.session_state.view = "day"
                    st.rerun()

# ════════════════════════════════════════════════════════════
# 뷰 2: 날짜별 슬롯
# ════════════════════════════════════════════════════════════
elif st.session_state.view == "day":
    y = st.session_state.sel_year
    m = st.session_state.sel_month
    d = st.session_state.sel_date
    key = date_key(y, m, d)
    day_bookings = bookings.get(key, {})

    if st.button("← 달력으로"):
        st.session_state.view = "cal"
        st.rerun()

    st.markdown(f"## {y}년 {MONTHS_KR[m-1]} {d}일 예약 현황")
    st.divider()

    for slot in SLOTS:
        sid = str(slot["id"])
        info = day_bookings.get(sid)

        col1, col2, col3 = st.columns([3, 4, 2])
        with col1:
            st.markdown(f"**{slot['label']}** &nbsp; `{slot['time']}`")
        with col2:
            if info:
                st.markdown(f"👤 {info['name']} &nbsp;·&nbsp; 📦 {info['product']}")
            else:
                st.markdown("<span style='color:#aaa'>예약 가능</span>", unsafe_allow_html=True)
        with col3:
            if info:
                if st.button("예약 취소", key=f"del_{sid}", type="secondary"):
                    del bookings[key][sid]
                    if not bookings[key]:
                        del bookings[key]
                    save_bookings(bookings)
                    st.session_state.bookings = bookings
                    st.rerun()
            else:
                if st.button("예약하기", key=f"book_{sid}", type="primary"):
                    st.session_state.sel_slot = slot["id"]
                    st.session_state.view = "booking"
                    st.rerun()
        st.divider()

# ════════════════════════════════════════════════════════════
# 뷰 3: 예약 폼
# ════════════════════════════════════════════════════════════
elif st.session_state.view == "booking":
    y = st.session_state.sel_year
    m = st.session_state.sel_month
    d = st.session_state.sel_date
    sid = st.session_state.sel_slot
    slot = SLOTS[sid]

    if st.button("← 날짜로"):
        st.session_state.view = "day"
        st.rerun()

    st.markdown(f"## 예약 등록")
    st.markdown(f"**{y}년 {MONTHS_KR[m-1]} {d}일 · {slot['label']} {slot['time']}**")
    st.divider()

    with st.form("booking_form"):
        name = st.text_input("이름 *", placeholder="홍길동")
        product = st.text_input("제품명 *", placeholder="제품명을 입력하세요")

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("✅ 예약 확정", type="primary", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("취소", use_container_width=True)

        if submitted:
            if not name.strip() or not product.strip():
                st.error("모든 항목을 입력해주세요.")
            else:
                key = date_key(y, m, d)
                if key not in bookings:
                    bookings[key] = {}
                bookings[key][str(sid)] = {
                    "name": name.strip(),
                    "product": product.strip()
                }
                save_bookings(bookings)
                st.session_state.bookings = bookings
                st.success("예약이 완료되었습니다!")
                st.session_state.view = "day"
                st.rerun()

        if cancelled:
            st.session_state.view = "day"
            st.rerun()
