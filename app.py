import streamlit as st
import json
import os
from datetime import date
import calendar

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="시험실 예약 시스템",
    page_icon="🔇",
    layout="wide"
)

# ── 비밀번호 설정 ─────────────────────────────────────────────
USER_PASSWORD  = st.secrets.get("USER_PASSWORD",  "1234")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "1996")

# ── 예약 공간 정의 ────────────────────────────────────────────
ROOMS = {
    "noise": {"label": "🔇 소음 시험실", "color": "1E2D6B"},
    "chamber": {"label": "🌡️ 환경 챔버",  "color": "0D9488"},
}

# ── 시간 목록 ────────────────────────────────────────────────
HOURS = [f"{h:02d}:00" for h in range(0, 25)]

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
    return int(t.split(":")[0]) * 60

def is_overlap(new_start, new_end, bookings_of_day, exclude_id=None):
    ns = time_to_min(new_start)
    ne = time_to_min(new_end)
    for bid, b in bookings_of_day.items():
        if exclude_id and bid == exclude_id:
            continue
        bs = time_to_min(b["start"])
        be = time_to_min(b["end"])
        if ns < be and ne > bs:
            return True, b
    return False, None

def make_timeline(bookings_of_day, room_color):
    if not bookings_of_day:
        return ""
    items = sorted(bookings_of_day.values(), key=lambda x: time_to_min(x["start"]))
    html = ""
    for b in items[:2]:
        html += f'<div style="background:#{room_color};color:white;border-radius:4px;padding:1px 4px;font-size:10px;margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{b["start"]}~{b["end"]} {b["name"]}</div>'
    if len(items) > 2:
        html += f'<div style="font-size:10px;color:#888">+{len(items)-2}건</div>'
    return html

# ── 세션 초기화 ──────────────────────────────────────────────
defaults = {
    "authenticated": False,
    "is_admin": False,
    "view": "cal",
    "sel_year": date.today().year,
    "sel_month": date.today().month,
    "sel_date": None,
    "sel_room": "noise",
    "edit_booking_id": None,
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
.admin-badge {
    background: #7C3AED; color: white;
    border-radius: 12px; padding: 2px 10px;
    font-size: 12px; font-weight: 600;
}
.user-badge {
    background: #0D9488; color: white;
    border-radius: 12px; padding: 2px 10px;
    font-size: 12px; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

MONTHS_KR = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
DAYS_KR   = ["월","화","수","목","금","토","일"]

# ════════════════════════════════════════════════════════════
# 로그인 화면
# ════════════════════════════════════════════════════════════
if not st.session_state.authenticated:
    st.markdown("""
    <div style='max-width:380px;margin:80px auto;text-align:center'>
        <div style='font-size:52px;margin-bottom:12px'>🏢</div>
        <h2 style='margin-bottom:6px'>시험실 예약 시스템</h2>
        <p style='color:#888;margin-bottom:28px'>비밀번호를 입력하세요</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pw = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")
        if st.button("입력", use_container_width=True, type="primary"):
            if pw == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.is_admin = True
                st.rerun()
            elif pw == USER_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.is_admin = False
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
        st.markdown("""
        <div style='margin-top:16px;padding:10px;background:#f8f8f8;border-radius:8px;font-size:12px;color:#888;text-align:left'>
        일반 사용자: 예약 현황 조회만 가능<br>
        관리자: 예약 등록·수정·취소 가능
        </div>
        """, unsafe_allow_html=True)
    st.stop()

is_admin = st.session_state.is_admin

# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏢 시험실 예약 시스템")
    st.divider()

    # 권한 배지
    if is_admin:
        st.markdown('<span class="admin-badge">👑 관리자</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="user-badge">👤 일반 사용자</span>', unsafe_allow_html=True)

    st.divider()

    # 공간 선택
    st.markdown("**예약 공간 선택**")
    room_labels = {k: v["label"] for k, v in ROOMS.items()}
    selected_room = st.radio(
        label="공간",
        options=list(ROOMS.keys()),
        format_func=lambda x: room_labels[x],
        index=list(ROOMS.keys()).index(st.session_state.sel_room),
        label_visibility="collapsed"
    )
    if selected_room != st.session_state.sel_room:
        st.session_state.sel_room = selected_room
        st.session_state.view = "cal"
        st.rerun()

    st.divider()
    if st.button("🔒 로그아웃", use_container_width=True):
        for k in ["authenticated", "is_admin", "view", "sel_date", "edit_booking_id"]:
            st.session_state[k] = defaults[k]
        st.rerun()

room_key   = st.session_state.sel_room
room_info  = ROOMS[room_key]
room_color = room_info["color"]
room_label = room_info["label"]

# ════════════════════════════════════════════════════════════
# 뷰 1: 달력
# ════════════════════════════════════════════════════════════
if st.session_state.view == "cal":
    y = st.session_state.sel_year
    m = st.session_state.sel_month

    col_l, col_mid, col_r = st.columns([1, 2, 1])
    with col_l:
        if st.button("◀ 이전 달", use_container_width=True):
            if m == 1: st.session_state.sel_month = 12; st.session_state.sel_year -= 1
            else: st.session_state.sel_month -= 1
            st.rerun()
    with col_mid:
        st.markdown(f"<h2 style='text-align:center;margin:0'>{room_label} &nbsp;·&nbsp; {y}년 {MONTHS_KR[m-1]}</h2>", unsafe_allow_html=True)
    with col_r:
        if st.button("다음 달 ▶", use_container_width=True):
            if m == 12: st.session_state.sel_month = 1; st.session_state.sel_year += 1
            else: st.session_state.sel_month += 1
            st.rerun()

    st.divider()

    # 읽기 전용 안내
    if not is_admin:
        st.info("👤 일반 사용자 모드 — 예약 현황 조회만 가능합니다.")

    # 요일 헤더
    day_cols = st.columns(7)
    for i, d in enumerate(DAYS_KR):
        color = "#e53935" if i == 6 else "#1565C0" if i == 5 else "#333"
        day_cols[i].markdown(f"<div style='text-align:center;font-weight:600;color:{color};font-size:14px'>{d}</div>", unsafe_allow_html=True)

    cal  = calendar.monthcalendar(y, m)
    today = date.today()

    for week in cal:
        cols = st.columns(7)
        for wi, day in enumerate(week):
            with cols[wi]:
                if day == 0:
                    st.markdown("<div style='min-height:90px'></div>", unsafe_allow_html=True)
                    continue

                dk = date_key(y, m, day)
                day_bookings = bookings.get(room_key, {}).get(dk, {})
                is_today = (y == today.year and m == today.month and day == today.day)
                num_color = "#e53935" if wi == 6 else "#1565C0" if wi == 5 else "#333"
                today_style = f"background:#{room_color};color:white;border-radius:50%;width:24px;height:24px;display:inline-flex;align-items:center;justify-content:center;" if is_today else f"color:{num_color}"

                timeline_html = make_timeline(day_bookings, room_color)

                st.markdown(f"""
                <div style='border:1px solid #e0e0e0;border-radius:8px;padding:6px;min-height:90px;background:white'>
                    <div style='font-weight:600;font-size:14px;margin-bottom:4px'>
                        <span style='{today_style}'>{day}</span>
                    </div>
                    {timeline_html}
                </div>
                """, unsafe_allow_html=True)

                if st.button("보기" if not is_admin else "선택", key=f"day_{y}_{m}_{day}", use_container_width=True):
                    st.session_state.sel_date = day
                    st.session_state.view = "day"
                    st.rerun()

# ════════════════════════════════════════════════════════════
# 뷰 2: 날짜별 예약 현황
# ════════════════════════════════════════════════════════════
elif st.session_state.view == "day":
    y = st.session_state.sel_year
    m = st.session_state.sel_month
    d = st.session_state.sel_date
    dk = date_key(y, m, d)
    day_bookings = bookings.get(room_key, {}).get(dk, {})

    if st.button("← 달력으로"):
        st.session_state.view = "cal"
        st.session_state.edit_booking_id = None
        st.rerun()

    st.markdown(f"## {room_label} &nbsp;·&nbsp; {y}년 {MONTHS_KR[m-1]} {d}일")
    st.divider()

    # 타임라인 바
    st.markdown("#### 예약 현황")
    if day_bookings:
        tl = f'<div style="position:relative;height:40px;background:#f0f0f0;border-radius:8px;margin-bottom:8px;overflow:hidden">'
        shades = [room_color, "4B5563", "6D28D9", "B45309", "065F46", "9D174D"]
        for i, (bid, b) in enumerate(sorted(day_bookings.items(), key=lambda x: time_to_min(x[1]["start"]))):
            sp = time_to_min(b["start"]) / 1440 * 100
            ep = time_to_min(b["end"])   / 1440 * 100
            wp = ep - sp
            c  = shades[i % len(shades)]
            tl += f'<div style="position:absolute;left:{sp:.1f}%;width:{wp:.1f}%;height:100%;background:#{c};display:flex;align-items:center;justify-content:center;font-size:11px;color:white;overflow:hidden;white-space:nowrap;padding:0 4px">{b["name"]}</div>'
        tl += '</div>'
        tl += '<div style="display:flex;justify-content:space-between;font-size:10px;color:#aaa;margin-bottom:16px">'
        for h in [0, 6, 12, 18, 24]:
            tl += f'<span>{h:02d}:00</span>'
        tl += '</div>'
        st.markdown(tl, unsafe_allow_html=True)

        for bid, b in sorted(day_bookings.items(), key=lambda x: time_to_min(x[1]["start"])):
            col1, col2, col3 = st.columns([3, 4, 3])
            with col1:
                st.markdown(f"🕐 **{b['start']} ~ {b['end']}**")
            with col2:
                st.markdown(f"👤 {b['name']} &nbsp;·&nbsp; 📦 {b['product']}")
            with col3:
                if is_admin:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("수정", key=f"edit_{bid}", use_container_width=True):
                            st.session_state.edit_booking_id = bid
                            st.session_state.view = "edit"
                            st.rerun()
                    with c2:
                        if st.button("취소", key=f"del_{bid}", type="secondary", use_container_width=True):
                            del bookings[room_key][dk][bid]
                            if not bookings[room_key][dk]:
                                del bookings[room_key][dk]
                            save_bookings(bookings)
                            st.session_state.bookings = bookings
                            st.rerun()
    else:
        st.markdown("<p style='color:#aaa'>이 날의 예약이 없습니다.</p>", unsafe_allow_html=True)

    # 예약 폼 (관리자만)
    if is_admin:
        st.divider()
        st.markdown("#### 새 예약 추가")
        with st.form("booking_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.selectbox("시작 시간 *", options=HOURS[:-1], index=8)
            with col2:
                start_idx  = HOURS.index(start_time)
                end_options = HOURS[start_idx + 1:]
                end_time   = st.selectbox("종료 시간 *", options=end_options, index=min(3, len(end_options)-1))

            col3, col4 = st.columns(2)
            with col3:
                name = st.text_input("이름 *", placeholder="홍길동")
            with col4:
                product = st.text_input("제품명 *", placeholder="제품명을 입력하세요")

            if st.form_submit_button("✅ 예약 확정", type="primary", use_container_width=True):
                if not name.strip() or not product.strip():
                    st.error("모든 항목을 입력해주세요.")
                else:
                    overlap, conflict = is_overlap(start_time, end_time, day_bookings)
                    if overlap:
                        st.error(f"⚠️ {conflict['start']}~{conflict['end']} ({conflict['name']}) 예약과 시간이 겹칩니다.")
                    else:
                        if room_key not in bookings: bookings[room_key] = {}
                        if dk not in bookings[room_key]: bookings[room_key][dk] = {}
                        existing = set(bookings[room_key][dk].keys())
                        new_id = 0
                        while str(new_id) in existing: new_id += 1
                        bookings[room_key][dk][str(new_id)] = {
                            "start": start_time, "end": end_time,
                            "name": name.strip(), "product": product.strip()
                        }
                        save_bookings(bookings)
                        st.session_state.bookings = bookings
                        st.success(f"✅ {start_time} ~ {end_time} 예약이 완료되었습니다!")
                        st.rerun()
    else:
        st.divider()
        st.info("👤 예약 등록 및 수정은 관리자만 가능합니다.")

# ════════════════════════════════════════════════════════════
# 뷰 3: 예약 수정 (관리자 전용)
# ════════════════════════════════════════════════════════════
elif st.session_state.view == "edit":
    if not is_admin:
        st.error("관리자만 접근할 수 있습니다.")
        st.stop()

    y   = st.session_state.sel_year
    m   = st.session_state.sel_month
    d   = st.session_state.sel_date
    dk  = date_key(y, m, d)
    bid = st.session_state.edit_booking_id
    day_bookings = bookings.get(room_key, {}).get(dk, {})
    existing = day_bookings.get(bid, {})

    if st.button("← 날짜로"):
        st.session_state.view = "day"
        st.session_state.edit_booking_id = None
        st.rerun()

    st.markdown(f"## 예약 수정 &nbsp; <span style='font-size:14px;color:#888'>{room_label} · {y}년 {MONTHS_KR[m-1]} {d}일</span>", unsafe_allow_html=True)
    st.divider()

    if not existing:
        st.warning("해당 예약을 찾을 수 없습니다.")
    else:
        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                cur_start_idx = HOURS.index(existing["start"]) if existing["start"] in HOURS else 8
                start_time = st.selectbox("시작 시간 *", options=HOURS[:-1], index=cur_start_idx)
            with col2:
                start_idx   = HOURS.index(start_time)
                end_options = HOURS[start_idx + 1:]
                cur_end_idx = end_options.index(existing["end"]) if existing["end"] in end_options else min(3, len(end_options)-1)
                end_time    = st.selectbox("종료 시간 *", options=end_options, index=cur_end_idx)

            col3, col4 = st.columns(2)
            with col3:
                name    = st.text_input("이름 *", value=existing.get("name", ""))
            with col4:
                product = st.text_input("제품명 *", value=existing.get("product", ""))

            col_a, col_b = st.columns(2)
            with col_a:
                save = st.form_submit_button("💾 수정 저장", type="primary", use_container_width=True)
            with col_b:
                cancel = st.form_submit_button("취소", use_container_width=True)

            if save:
                if not name.strip() or not product.strip():
                    st.error("모든 항목을 입력해주세요.")
                else:
                    overlap, conflict = is_overlap(start_time, end_time, day_bookings, exclude_id=bid)
                    if overlap:
                        st.error(f"⚠️ {conflict['start']}~{conflict['end']} ({conflict['name']}) 예약과 시간이 겹칩니다.")
                    else:
                        bookings[room_key][dk][bid] = {
                            "start": start_time, "end": end_time,
                            "name": name.strip(), "product": product.strip()
                        }
                        save_bookings(bookings)
                        st.session_state.bookings = bookings
                        st.success("수정이 완료되었습니다!")
                        st.session_state.view = "day"
                        st.session_state.edit_booking_id = None
                        st.rerun()

            if cancel:
                st.session_state.view = "day"
                st.session_state.edit_booking_id = None
                st.rerun()
