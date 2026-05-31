import streamlit as st
import json
import os
from datetime import date, timedelta
import calendar

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="시험실 예약 시스템",
    page_icon="🏢",
    layout="wide"
)

# ── 비밀번호 설정 ─────────────────────────────────────────────
USER_PASSWORD  = st.secrets.get("USER_PASSWORD",  "1234")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "1996")

# ── 예약 공간 정의 ────────────────────────────────────────────
ROOMS = {
    "noise":   {"label": "🔇 소음 시험실", "color": "1E2D6B"},
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

def date_from_key(dk):
    y, m, d = dk.split("-")
    return date(int(y), int(m), int(d))

def time_to_min(t):
    return int(t.split(":")[0]) * 60

def datetime_to_sort_key(dk, t):
    return dk + " " + t

# ── 다중 날짜 예약 처리 ───────────────────────────────────────
def expand_booking_to_days(start_date, start_time, end_date, end_time):
    """
    시작일~종료일에 걸친 예약을 날짜별 슬롯으로 분리.
    반환: [(date_key, day_start, day_end), ...]
    """
    slots = []
    cur = start_date
    while cur <= end_date:
        dk = date_key(cur.year, cur.month, cur.day)
        if cur == start_date and cur == end_date:
            slots.append((dk, start_time, end_time))
        elif cur == start_date:
            slots.append((dk, start_time, "24:00"))
        elif cur == end_date:
            slots.append((dk, "00:00", end_time))
        else:
            slots.append((dk, "00:00", "24:00"))
        cur += timedelta(days=1)
    return slots

def is_overlap_day(new_start, new_end, day_bookings, exclude_gid=None):
    ns = time_to_min(new_start)
    ne = time_to_min(new_end)
    if ns >= ne:
        return False, None
    for bid, b in day_bookings.items():
        if exclude_gid and b.get("group_id") == exclude_gid:
            continue
        bs = time_to_min(b["start"])
        be = time_to_min(b["end"])
        if ns < be and ne > bs:
            return True, b
    return False, None

def get_all_bookings_for_room(room_key):
    return bookings.get(room_key, {})

def make_timeline(day_bookings, room_color):
    if not day_bookings:
        return ""
    items = sorted(day_bookings.values(), key=lambda x: time_to_min(x["start"]))
    html = ""
    for b in items[:2]:
        label = b.get("test_name") or b.get("name", "")
        html += f'<div style="background:#{room_color};color:white;border-radius:4px;padding:1px 4px;font-size:10px;margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{b["start"]}~{b["end"]} {label}</div>'
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
    "edit_group_id": None,
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
.admin-badge {background:#7C3AED;color:white;border-radius:12px;padding:2px 10px;font-size:12px;font-weight:600;}
.user-badge  {background:#0D9488;color:white;border-radius:12px;padding:2px 10px;font-size:12px;font-weight:600;}
</style>
""", unsafe_allow_html=True)

MONTHS_KR = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
DAYS_KR   = ["월","화","수","목","금","토","일"]

# ════════════════════════════════════════════════════════════
# 로그인
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
    if is_admin:
        st.markdown('<span class="admin-badge">👑 관리자</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="user-badge">👤 일반 사용자</span>', unsafe_allow_html=True)
    st.divider()
    st.markdown("**예약 공간 선택**")
    selected_room = st.radio(
        label="공간",
        options=list(ROOMS.keys()),
        format_func=lambda x: ROOMS[x]["label"],
        index=list(ROOMS.keys()).index(st.session_state.sel_room),
        label_visibility="collapsed"
    )
    if selected_room != st.session_state.sel_room:
        st.session_state.sel_room = selected_room
        st.session_state.view = "cal"
        st.rerun()
    st.divider()
    if st.button("🔒 로그아웃", use_container_width=True):
        for k in ["authenticated","is_admin","view","sel_date","edit_group_id"]:
            st.session_state[k] = defaults[k]
        st.rerun()

room_key   = st.session_state.sel_room
room_info  = ROOMS[room_key]
room_color = room_info["color"]
room_label = room_info["label"]

# ── 예약 폼 공통 함수 ─────────────────────────────────────────
def booking_form(form_key, existing=None):
    """
    예약 등록/수정 공통 폼.
    existing: 수정 시 기존 데이터 dict
    반환: (submitted, form_data) or (False, None)
    """
    today = date.today()
    is_edit = existing is not None

    if is_edit:
        init_start_date = date_from_key(existing["start_date"])
        init_end_date   = date_from_key(existing["end_date"])
        init_start_time = existing["start"]
        init_end_time   = existing["end"]
        init_name       = existing.get("name", "")
        init_test       = existing.get("test_name", "")
        init_product    = existing.get("product", "")
    else:
        init_start_date = today
        init_end_date   = today
        init_start_time = HOURS[8]   # 08:00
        init_end_time   = HOURS[12]  # 12:00
        init_name       = ""
        init_test       = ""
        init_product    = ""

    with st.form(form_key, clear_on_submit=not is_edit):
        st.markdown("**📅 기간 설정**")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작 날짜 *", value=init_start_date, min_value=date(2020,1,1))
            start_time = st.selectbox("시작 시간 *", options=HOURS[:-1],
                                      index=HOURS[:-1].index(init_start_time) if init_start_time in HOURS[:-1] else 8)
        with col2:
            end_date = st.date_input("종료 날짜 *", value=init_end_date, min_value=date(2020,1,1))
            # 같은 날이면 시작 이후 시간만, 다른 날이면 전체
            if end_date == start_date:
                end_hour_options = HOURS[HOURS.index(start_time)+1:]
            else:
                end_hour_options = HOURS[1:]  # 00:00 제외
            safe_end = init_end_time if init_end_time in end_hour_options else end_hour_options[min(3, len(end_hour_options)-1)]
            end_time = st.selectbox("종료 시간 *", options=end_hour_options,
                                    index=end_hour_options.index(safe_end))

        st.markdown("**👤 예약 정보**")
        col3, col4 = st.columns(2)
        with col3:
            name    = st.text_input("이름 *", value=init_name, placeholder="홍길동")
        with col4:
            test_name = st.text_input("시험명 *", value=init_test, placeholder="예: 소음 내구 시험")

        product = st.text_input("제품명 *", value=init_product, placeholder="제품명을 입력하세요")

        col_a, col_b = st.columns(2)
        with col_a:
            submitted = st.form_submit_button(
                "💾 수정 저장" if is_edit else "✅ 예약 확정",
                type="primary", use_container_width=True
            )
        with col_b:
            cancelled = st.form_submit_button("취소", use_container_width=True)

    if cancelled:
        st.session_state.view = "day" if is_edit else "day"
        st.session_state.edit_group_id = None
        st.rerun()

    if submitted:
        # 유효성 검사
        if not name.strip() or not test_name.strip() or not product.strip():
            st.error("모든 항목을 입력해주세요.")
            return False, None
        if end_date < start_date:
            st.error("종료 날짜는 시작 날짜 이후여야 합니다.")
            return False, None
        if end_date == start_date and time_to_min(end_time) <= time_to_min(start_time):
            st.error("종료 시간은 시작 시간 이후여야 합니다.")
            return False, None

        return True, {
            "start_date": date_key(start_date.year, start_date.month, start_date.day),
            "end_date":   date_key(end_date.year,   end_date.month,   end_date.day),
            "start": start_time,
            "end":   end_time,
            "name":      name.strip(),
            "test_name": test_name.strip(),
            "product":   product.strip(),
        }

    return False, None

def save_booking(form_data, exclude_gid=None):
    """
    날짜별로 분리해서 저장. 겹침 검사 포함.
    반환: (success, error_msg)
    """
    start_date = date_from_key(form_data["start_date"])
    end_date   = date_from_key(form_data["end_date"])
    slots = expand_booking_to_days(start_date, form_data["start"], end_date, form_data["end"])

    # 겹침 검사
    if room_key not in bookings:
        bookings[room_key] = {}
    for (dk, ds, de) in slots:
        if ds == de:
            continue
        day_bk = bookings[room_key].get(dk, {})
        overlap, conflict = is_overlap_day(ds, de, day_bk, exclude_gid=exclude_gid)
        if overlap:
            d_label = dk.replace("-", "/")
            return False, f"⚠️ {d_label} {conflict['start']}~{conflict['end']} ({conflict['name']}) 예약과 시간이 겹칩니다."

    # 기존 group_id 삭제
    if exclude_gid:
        for dk_val in list(bookings[room_key].keys()):
            for bid in list(bookings[room_key][dk_val].keys()):
                if bookings[room_key][dk_val][bid].get("group_id") == exclude_gid:
                    del bookings[room_key][dk_val][bid]
            if not bookings[room_key][dk_val]:
                del bookings[room_key][dk_val]

    # 저장
    import uuid
    gid = exclude_gid or str(uuid.uuid4())[:8]
    for (dk, ds, de) in slots:
        if ds == de:
            continue
        if dk not in bookings[room_key]:
            bookings[room_key][dk] = {}
        existing_ids = set(bookings[room_key][dk].keys())
        new_id = 0
        while str(new_id) in existing_ids:
            new_id += 1
        bookings[room_key][dk][str(new_id)] = {
            "group_id":   gid,
            "start_date": form_data["start_date"],
            "end_date":   form_data["end_date"],
            "start":      ds,
            "end":        de,
            "name":       form_data["name"],
            "test_name":  form_data["test_name"],
            "product":    form_data["product"],
        }

    save_bookings(bookings)
    st.session_state.bookings = bookings
    return True, None

# ════════════════════════════════════════════════════════════
# 뷰 1: 달력
# ════════════════════════════════════════════════════════════
if st.session_state.view == "cal":
    y = st.session_state.sel_year
    m = st.session_state.sel_month

    col_l, col_mid, col_r = st.columns([1, 2, 1])
    with col_l:
        if st.button("◀ 이전 달", use_container_width=True):
            if m == 1: st.session_state.sel_month=12; st.session_state.sel_year-=1
            else: st.session_state.sel_month -= 1
            st.rerun()
    with col_mid:
        st.markdown(f"<h2 style='text-align:center;margin:0'>{room_label} &nbsp;·&nbsp; {y}년 {MONTHS_KR[m-1]}</h2>", unsafe_allow_html=True)
    with col_r:
        if st.button("다음 달 ▶", use_container_width=True):
            if m == 12: st.session_state.sel_month=1; st.session_state.sel_year+=1
            else: st.session_state.sel_month += 1
            st.rerun()

    st.divider()
    if not is_admin:
        st.info("👤 일반 사용자 모드 — 예약 현황 조회만 가능합니다.")

    day_cols = st.columns(7)
    for i, d in enumerate(DAYS_KR):
        color = "#e53935" if i==6 else "#1565C0" if i==5 else "#333"
        day_cols[i].markdown(f"<div style='text-align:center;font-weight:600;color:{color};font-size:14px'>{d}</div>", unsafe_allow_html=True)

    cal   = calendar.monthcalendar(y, m)
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
                is_today = (y==today.year and m==today.month and day==today.day)
                num_color = "#e53935" if wi==6 else "#1565C0" if wi==5 else "#333"
                ts = f"background:#{room_color};color:white;border-radius:50%;width:24px;height:24px;display:inline-flex;align-items:center;justify-content:center;" if is_today else f"color:{num_color}"
                tl = make_timeline(day_bookings, room_color)
                st.markdown(f"""
                <div style='border:1px solid #e0e0e0;border-radius:8px;padding:6px;min-height:90px;background:white'>
                    <div style='font-weight:600;font-size:14px;margin-bottom:4px'><span style='{ts}'>{day}</span></div>
                    {tl}
                </div>""", unsafe_allow_html=True)
                if st.button("보기" if not is_admin else "선택", key=f"day_{y}_{m}_{day}", use_container_width=True):
                    st.session_state.sel_date = day
                    st.session_state.view = "day"
                    st.rerun()

# ════════════════════════════════════════════════════════════
# 뷰 2: 날짜별 현황
# ════════════════════════════════════════════════════════════
elif st.session_state.view == "day":
    y = st.session_state.sel_year
    m = st.session_state.sel_month
    d = st.session_state.sel_date
    dk = date_key(y, m, d)
    day_bookings = bookings.get(room_key, {}).get(dk, {})

    if st.button("← 달력으로"):
        st.session_state.view = "cal"
        st.rerun()

    st.markdown(f"## {room_label} &nbsp;·&nbsp; {y}년 {MONTHS_KR[m-1]} {d}일")
    st.divider()

    st.markdown("#### 예약 현황")
    if day_bookings:
        # 타임라인 바
        tl = f'<div style="position:relative;height:40px;background:#f0f0f0;border-radius:8px;margin-bottom:8px;overflow:hidden">'
        shades = [room_color,"4B5563","6D28D9","B45309","065F46","9D174D"]
        for i, (bid, b) in enumerate(sorted(day_bookings.items(), key=lambda x: time_to_min(x[1]["start"]))):
            sp = time_to_min(b["start"])/1440*100
            ep = time_to_min(b["end"])/1440*100
            wp = ep - sp
            c  = shades[i % len(shades)]
            label = b.get("test_name") or b.get("name","")
            tl += f'<div style="position:absolute;left:{sp:.1f}%;width:{wp:.1f}%;height:100%;background:#{c};display:flex;align-items:center;justify-content:center;font-size:11px;color:white;overflow:hidden;white-space:nowrap;padding:0 4px">{label}</div>'
        tl += '</div>'
        tl += '<div style="display:flex;justify-content:space-between;font-size:10px;color:#aaa;margin-bottom:16px">'
        for h in [0,6,12,18,24]:
            tl += f'<span>{h:02d}:00</span>'
        tl += '</div>'
        st.markdown(tl, unsafe_allow_html=True)

        for bid, b in sorted(day_bookings.items(), key=lambda x: time_to_min(x[1]["start"])):
            start_dk = b.get("start_date", dk)
            end_dk   = b.get("end_date",   dk)
            is_multi = start_dk != end_dk
            period_label = f"{start_dk.replace('-','/')} {b['start']} ~ {end_dk.replace('-','/')} {b['end']}" if is_multi else f"{b['start']} ~ {b['end']}"

            with st.container():
                col1, col2, col3 = st.columns([4, 4, 2])
                with col1:
                    st.markdown(f"🕐 **{period_label}**")
                    if is_multi:
                        st.caption("📌 다일 예약")
                with col2:
                    st.markdown(f"👤 {b['name']} &nbsp;·&nbsp; 🧪 {b.get('test_name','')} &nbsp;·&nbsp; 📦 {b.get('product','')}")
                with col3:
                    if is_admin:
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("수정", key=f"edit_{bid}", use_container_width=True):
                                st.session_state.edit_group_id = b.get("group_id", bid)
                                st.session_state.view = "edit"
                                st.rerun()
                        with c2:
                            if st.button("취소", key=f"del_{bid}", type="secondary", use_container_width=True):
                                gid = b.get("group_id")
                                if gid:
                                    # group_id 전체 삭제
                                    for dk_v in list(bookings[room_key].keys()):
                                        for bid_v in list(bookings[room_key][dk_v].keys()):
                                            if bookings[room_key][dk_v][bid_v].get("group_id") == gid:
                                                del bookings[room_key][dk_v][bid_v]
                                        if not bookings[room_key][dk_v]:
                                            del bookings[room_key][dk_v]
                                else:
                                    del bookings[room_key][dk][bid]
                                    if not bookings[room_key][dk]:
                                        del bookings[room_key][dk]
                                save_bookings(bookings)
                                st.session_state.bookings = bookings
                                st.rerun()
            st.divider()
    else:
        st.markdown("<p style='color:#aaa'>이 날의 예약이 없습니다.</p>", unsafe_allow_html=True)

    if is_admin:
        st.markdown("#### 새 예약 추가")
        submitted, form_data = booking_form("booking_form")
        if submitted and form_data:
            ok, err = save_booking(form_data)
            if ok:
                period = f"{form_data['start_date'].replace('-','/')} {form_data['start']} ~ {form_data['end_date'].replace('-','/')} {form_data['end']}"
                st.success(f"✅ {period} 예약이 완료되었습니다!")
                st.rerun()
            else:
                st.error(err)
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

    gid = st.session_state.edit_group_id
    existing = None
    for dk_v, day_bk in bookings.get(room_key, {}).items():
        for bid_v, b in day_bk.items():
            if b.get("group_id") == gid:
                existing = b
                break
        if existing:
            break

    if st.button("← 날짜로"):
        st.session_state.view = "day"
        st.session_state.edit_group_id = None
        st.rerun()

    st.markdown(f"## 예약 수정 &nbsp; <span style='font-size:14px;color:#888'>{room_label}</span>", unsafe_allow_html=True)
    st.divider()

    if not existing:
        st.warning("해당 예약을 찾을 수 없습니다.")
    else:
        submitted, form_data = booking_form("edit_form", existing=existing)
        if submitted and form_data:
            ok, err = save_booking(form_data, exclude_gid=gid)
            if ok:
                st.success("수정이 완료되었습니다!")
                st.session_state.view = "day"
                st.session_state.edit_group_id = None
                st.rerun()
            else:
                st.error(err)
