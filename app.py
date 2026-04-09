import streamlit as st
import json
import os
from datetime import date
import calendar

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="소음 시험실 예약",
    page_icon="🔇",
    layout="wide"
)

# ── 비밀번호 설정 ─────────────────────────────────────────────
APP_PASSWORD = st.secrets.get("APP_PASSWORD", "lge1234")

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

# ── 시간 목록 ────────────────────────────────────────────────
HOURS = [f"{h:02d}:00" for h in range(0, 25)]  # 00:00 ~ 24:00

DATA_FILE = "bookings.json"

# ── 데이터 로드/저장 ─────────────────────────────────────────
def load_bookings():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_bookings(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def date_key(y, m, d):
    return f"{y}-{str(m).zfill(2)}-{str(d).zfill(2)}"

def time_to_min(t):
    h, _ = t.split(":")
    return int(h) * 60

def is_overlap(new_start, new_end, bookings_of_day):
    ns = time_to_min(new_start)
    ne = time_to_min(new_end)
    for b in bookings_of_day.values():
        bs = time_to_min(b["start"])
        be = time_to_min(b["end"])
        if ns < be and ne > bs:
            return True, b
    return False, None

def make_timeline(bookings_of_day):
    """달력 셀용 미니 타임라인 HTML"""
    if not bookings_of_day:
        return ""
    items = sorted(bookings_of_day.values(), key=lambda x: time_to_min(x["start"]))
    html = ""
    for b in items[:2]:
        html += f'<div style="background:#7F77DD;color:white;border-radius:4px;padding:1px 4px;font-size:10px;margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{b["start"]}~{b["end"]} {b["name"]}</div>'
    if len(items) > 2:
        html += f'<div style="font-size:10px;color:#888">+{len(items)-2}건</div>'
    return html

# ── 세션 초기화 ──────────────────────────────────────────────
defaults = {
    "view": "cal",
    "sel_year": date.today().year,
    "sel_month": date.today().month,
    "sel_date": None,
    "sel_booking_id": None,
    "bookings": load_bookings(),
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

bookings = st.session_state.bookings

# ── 스타일 ───────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1.5rem; padding-bottom: 1rem;}
</style>
""", unsafe_allow_html=True)

MONTHS_KR = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
DAYS_KR = ["월","화","수","목","금","토","일"]

# ── 사이드바 ─────────────────────────────────────────────────
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

    # 요일 헤더
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

                timeline_html = make_timeline(day_bookings)

                st.markdown(f"""
                <div style='border:1px solid #e0e0e0;border-radius:8px;padding:6px;min-height:90px;background:white'>
                    <div style='font-weight:600;font-size:14px;margin-bottom:4px'>
                        <span style='{today_style}'>{day}</span>
                    </div>
                    {timeline_html}
                </div>
                """, unsafe_allow_html=True)

                if st.button("선택", key=f"day_{y}_{m}_{day}", use_container_width=True):
                    st.session_state.sel_date = day
                    st.session_state.view = "day"
                    st.rerun()

# ════════════════════════════════════════════════════════════
# 뷰 2: 날짜별 예약 현황 + 예약 폼
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

    st.markdown(f"## {y}년 {MONTHS_KR[m-1]} {d}일")
    st.divider()

    # ── 타임라인 시각화 ──────────────────────────────────────
    st.markdown("#### 예약 현황")

    if day_bookings:
        # 24시간 타임라인 바
        timeline_html = '<div style="position:relative;height:40px;background:#f0f0f0;border-radius:8px;margin-bottom:8px;overflow:hidden">'
        colors = ["#7F77DD","#1D9E75","#D85A30","#D4537E","#378ADD","#639922","#BA7517","#A32D2D"]
        for i, (bid, b) in enumerate(sorted(day_bookings.items(), key=lambda x: time_to_min(x[1]["start"]))):
            s_pct = time_to_min(b["start"]) / 1440 * 100
            e_pct = time_to_min(b["end"]) / 1440 * 100
            w_pct = e_pct - s_pct
            color = colors[i % len(colors)]
            timeline_html += f'<div style="position:absolute;left:{s_pct:.1f}%;width:{w_pct:.1f}%;height:100%;background:{color};display:flex;align-items:center;justify-content:center;font-size:11px;color:white;overflow:hidden;white-space:nowrap;padding:0 4px">{b["name"]}</div>'
        timeline_html += '</div>'
        # 시간 눈금
        timeline_html += '<div style="display:flex;justify-content:space-between;font-size:10px;color:#aaa;margin-bottom:16px">'
        for h in [0, 6, 12, 18, 24]:
            timeline_html += f'<span>{h:02d}:00</span>'
        timeline_html += '</div>'
        st.markdown(timeline_html, unsafe_allow_html=True)

        # 예약 목록
        for bid, b in sorted(day_bookings.items(), key=lambda x: time_to_min(x[1]["start"])):
            col1, col2, col3 = st.columns([3, 4, 2])
            with col1:
                st.markdown(f"🕐 **{b['start']} ~ {b['end']}**")
            with col2:
                st.markdown(f"👤 {b['name']} &nbsp;·&nbsp; 📦 {b['product']}")
            with col3:
                if st.button("예약 취소", key=f"del_{bid}", type="secondary"):
                    del bookings[key][bid]
                    if not bookings[key]:
                        del bookings[key]
                    save_bookings(bookings)
                    st.session_state.bookings = bookings
                    st.rerun()
    else:
        st.markdown("<p style='color:#aaa'>이 날의 예약이 없습니다.</p>", unsafe_allow_html=True)

    st.divider()

    # ── 예약 폼 ──────────────────────────────────────────────
    st.markdown("#### 새 예약 추가")

    with st.form("booking_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.selectbox(
                "시작 시간 *",
                options=HOURS[:-1],  # 00:00 ~ 23:00
                index=8  # 기본값 08:00
            )
        with col2:
            # 시작 시간 이후 옵션만
            start_idx = HOURS.index(start_time)
            end_options = HOURS[start_idx + 1:]  # 최소 1시간 이후
            end_time = st.selectbox(
                "종료 시간 *",
                options=end_options,
                index=min(3, len(end_options) - 1)  # 기본값 시작+4시간
            )

        col3, col4 = st.columns(2)
        with col3:
            name = st.text_input("이름 *", placeholder="홍길동")
        with col4:
            product = st.text_input("제품명 *", placeholder="제품명을 입력하세요")

        submitted = st.form_submit_button("✅ 예약 확정", type="primary", use_container_width=True)

        if submitted:
            if not name.strip() or not product.strip():
                st.error("모든 항목을 입력해주세요.")
            else:
                overlap, conflict = is_overlap(start_time, end_time, day_bookings)
                if overlap:
                    st.error(f"⚠️ {conflict['start']}~{conflict['end']} ({conflict['name']}) 예약과 시간이 겹칩니다.")
                else:
                    if key not in bookings:
                        bookings[key] = {}
                    bid = str(len(bookings[key]))
                    # 중복 ID 방지
                    existing_ids = set(bookings[key].keys())
                    new_id = 0
                    while str(new_id) in existing_ids:
                        new_id += 1
                    bookings[key][str(new_id)] = {
                        "start": start_time,
                        "end": end_time,
                        "name": name.strip(),
                        "product": product.strip()
                    }
                    save_bookings(bookings)
                    st.session_state.bookings = bookings
                    st.success(f"✅ {start_time} ~ {end_time} 예약이 완료되었습니다!")
                    st.rerun()
