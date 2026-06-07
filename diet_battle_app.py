"""
🥦 다이어트 대결 앱 - Streamlit + Supabase 버전
실행 방법: streamlit run diet_battle_app.py
"""

import streamlit as st
from datetime import datetime, timedelta
from supabase import create_client

# ─────────────────────────────────────────────────────────────────
SUPABASE_URL = "https://qdjupvyeiqfwrgdxevph.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkanVwdnllaXFmd3JnZHhldnBoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA4MjcwNTgsImV4cCI6MjA5NjQwMzA1OH0.0A-JEDucci-hsAY4QSBN5zN7OPTTrx-gksDmBI1NVHU"

# 조건3, 조건5: 운영자 계정
ADMIN_USERNAMES = {"hyoon", "dbsk", "손성빈"}

VEGGIE_EMOJIS = ["🥦", "🥕", "🍅", "🥑", "🍋", "🥝", "🍇", "🥬", "🌽", "🍓", "🫐", "🥭"]
# ─────────────────────────────────────────────────────────────────

def get_sb():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def fmt(d): return d.strftime("%Y-%m-%d")
def prev_day(s): return fmt(datetime.strptime(s, "%Y-%m-%d") - timedelta(days=1))
def next_day(s): return fmt(datetime.strptime(s, "%Y-%m-%d") + timedelta(days=1))

def is_admin(user):
    return user and user.get("username") in ADMIN_USERNAMES

# ── DB helpers ────────────────────────────────────────────────────
def db_all_users():
    return get_sb().table("users").select("*").execute().data or []

def db_user_by_username(u):
    r = get_sb().table("users").select("*").eq("username", u).execute()
    return r.data[0] if r.data else None

def db_user_by_id(uid):
    r = get_sb().table("users").select("*").eq("id", uid).execute()
    return r.data[0] if r.data else None

def db_create_user(u):
    get_sb().table("users").insert(u).execute()

def db_update_user(uid, fields):
    get_sb().table("users").update(fields).eq("id", uid).execute()

def db_get_meal(user_id, date):
    r = get_sb().table("meals").select("*").eq("user_id", user_id).eq("date", date).execute()
    return r.data[0] if r.data else None

def db_all_meals(user_id):
    return get_sb().table("meals").select("*").eq("user_id", user_id).order("date", desc=True).execute().data or []

def db_save_meal(user_id, date, breakfast, lunch, dinner, snacks):
    existing = db_get_meal(user_id, date)
    d = {"user_id": user_id, "date": date, "breakfast": breakfast,
         "lunch": lunch, "dinner": dinner, "snacks": snacks}
    if existing:
        get_sb().table("meals").update(d).eq("user_id", user_id).eq("date", date).execute()
    else:
        get_sb().table("meals").insert(d).execute()

def db_weight_history(user_id):
    return get_sb().table("weight_history").select("*").eq("user_id", user_id).order("date", desc=True).execute().data or []

def db_save_weight(user_id, date, weight):
    r = get_sb().table("weight_history").select("*").eq("user_id", user_id).eq("date", date).execute()
    if r.data:
        get_sb().table("weight_history").update({"weight": weight}).eq("user_id", user_id).eq("date", date).execute()
    else:
        get_sb().table("weight_history").insert({"user_id": user_id, "date": date, "weight": weight}).execute()

def db_comments(target_uid):
    return get_sb().table("comments").select("*").eq("target_user_id", target_uid).order("created_at").execute().data or []

def db_add_comment(target_uid, author, text):
    get_sb().table("comments").insert({"target_user_id": target_uid, "author": author, "text": text}).execute()

def db_toggle_like(target_uid, my_uid):
    u = db_user_by_id(target_uid)
    liked = u.get("liked_by") or []
    liked = [x for x in liked if x != my_uid] if my_uid in liked else liked + [my_uid]
    db_update_user(target_uid, {"liked_by": liked})


# ── 페이지 설정 ───────────────────────────────────────────────────
st.set_page_config(page_title="🥦 다이어트 대결", page_icon="🥦", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Nanum Gothic', sans-serif; }
.stApp { background: linear-gradient(135deg, #e8f5e2 0%, #fff9e6 50%, #fde8f0 100%); }

/* 앱 타이틀 */
.app-title {
    font-size: 1.8rem; font-weight: 800; color: #2d6a2d;
    text-align: center; letter-spacing: 1px; padding: 8px 0 2px;
}
.app-sub {
    text-align: center; color: #7a9a5a;
    letter-spacing: 3px; font-size: 0.72rem; margin-bottom: 8px;
}

/* 카드 */
.vcard {
    background: rgba(255,255,255,0.92);
    border-radius: 16px; padding: 16px 18px; margin-bottom: 14px;
    border: 1.5px solid #d4eebc;
    box-shadow: 0 2px 12px rgba(60,120,30,0.07);
}

/* 식단 박스 */
.meal-box {
    background: #f4fbef; border-radius: 10px;
    padding: 10px 14px; margin: 8px 0;
    border: 1px solid #d0ecc0; line-height: 2; font-size: 0.88rem;
}
.meal-box-compact {
    background: #f4fbef; border-radius: 10px;
    padding: 8px 14px; margin: 8px 0;
    border: 1px solid #d0ecc0; font-size: 0.85rem;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* 댓글 */
.comment-item {
    background: #f0fbe8; border-radius: 10px;
    padding: 7px 12px; margin-bottom: 5px;
    font-size: 0.83rem; color: #3a5a1e;
    border: 1px solid #d0ecc0;
}

/* 스낵 태그 */
.snack-tag {
    display: inline-block; background: #e2f7d4;
    border: 1px solid #a8d890; border-radius: 20px;
    padding: 2px 10px; font-size: 0.8rem; color: #2d6a2d; margin: 2px;
}

/* 에러 */
.err-box {
    background: #ffe8e8; border: 1.5px solid #f0b0b0;
    border-radius: 10px; padding: 9px 13px;
    color: #c0392b; font-size: 0.85rem; margin-bottom: 10px;
}

/* 힌트 */
.hint-box {
    background: #f4fbef; border: 1px dashed #a8d890;
    border-radius: 10px; padding: 9px 13px;
    color: #5a8a3a; font-size: 0.76rem;
    text-align: center; margin-top: 10px; line-height: 1.7;
}

/* 테스트 배너 */
.test-banner {
    background: linear-gradient(135deg, #fff3cd, #ffe08a);
    border: 1.5px solid #f0c040; border-radius: 10px;
    padding: 7px 13px; font-size: 0.8rem;
    color: #7a5500; font-weight: 700; text-align: center;
}

/* 날짜 뱃지 */
.date-badge {
    background: #e8f5e2; border-radius: 8px;
    padding: 3px 10px; font-size: 0.76rem;
    color: #4a7a2a; font-weight: 700; display: inline-block; margin-bottom: 6px;
}

/* 순위 카드 */
.rank-card {
    background: rgba(255,255,255,0.9);
    border-radius: 14px; padding: 12px 16px; margin-bottom: 8px;
    border: 1.5px solid #d4eebc;
    display: flex; align-items: center; gap: 12px;
}

/* 운영자 뱃지 */
.admin-badge {
    background: #2d6a2d; color: white;
    border-radius: 6px; padding: 1px 7px;
    font-size: 0.68rem; font-weight: 700; margin-left: 6px;
}

/* 비공개 뱃지 */
.private-badge {
    background: #e8e8e8; color: #888;
    border-radius: 6px; padding: 1px 7px;
    font-size: 0.68rem; font-weight: 700;
}

.stButton > button {
    border-radius: 10px !important;
    font-family: 'Nanum Gothic', sans-serif !important;
    font-weight: 700 !important;
}

/* 구분선 */
hr { border-color: #d4eebc !important; margin: 10px 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Session State ─────────────────────────────────────────────────
for k, v in [("session_id", None), ("auth_page", "login"),
             ("auth_error", ""), ("sim_date", fmt(datetime.today())),
             ("feed_compact", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

today_str     = st.session_state.sim_date
yesterday_str = prev_day(today_str)
current_user  = db_user_by_id(st.session_state.session_id) if st.session_state.session_id else None
admin         = is_admin(current_user)


# ── 헤더 ─────────────────────────────────────────────────────────
st.markdown('<div class="app-title">🥦 다이어트 대결</div>', unsafe_allow_html=True)
st.markdown('<div class="app-sub">VEGGIE BATTLE</div>', unsafe_allow_html=True)
st.divider()

# 조건8: 운영자만 날짜 버튼 표시
if admin:
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f'<div class="test-banner">🔧 운영자 모드 | 날짜: <b>{today_str}</b></div>', unsafe_allow_html=True)
    with c2:
        if st.button("📅 +1일", use_container_width=True):
            st.session_state.sim_date = next_day(today_str)
            st.rerun()


# ══════════════════════════════════════════════════════════════════
# 비로그인
# ══════════════════════════════════════════════════════════════════
if not current_user:

    if st.session_state.auth_page == "login":
        st.markdown("### 🌿 로그인")
        with st.container(border=True):
            uid_in = st.text_input("아이디", key="login_user")
            pw_in  = st.text_input("비밀번호", type="password", key="login_pw")
            if st.session_state.auth_error:
                st.markdown(f'<div class="err-box">⚠️ {st.session_state.auth_error}</div>', unsafe_allow_html=True)
            if st.button("🌿 로그인", use_container_width=True, type="primary"):
                found = db_user_by_username(uid_in.strip())
                if not found:
                    st.session_state.auth_error = "존재하지 않는 아이디입니다."
                elif found["password"] != pw_in:
                    st.session_state.auth_error = "비밀번호가 틀렸습니다."
                else:
                    st.session_state.session_id = found["id"]
                    st.session_state.auth_error = ""
                    st.rerun()
            st.markdown("---")
            c1, c2 = st.columns([2, 1])
            with c1: st.caption("계정이 없으신가요?")
            with c2:
                if st.button("회원가입 →", use_container_width=True):
                    st.session_state.auth_page = "signup"
                    st.session_state.auth_error = ""
                    st.rerun()

    else:
        import random
        if "signup_emoji" not in st.session_state:
            st.session_state.signup_emoji = random.choice(VEGGIE_EMOJIS)
        emoji = st.session_state.signup_emoji
        st.markdown(f"### {emoji} 회원가입")
        with st.container(border=True):
            new_id  = st.text_input("아이디", key="su_user")
            new_pw  = st.text_input("비밀번호", type="password", key="su_pw")
            new_pw2 = st.text_input("비밀번호 확인", type="password", key="su_pw2")
            new_nm  = st.text_input("닉네임", placeholder="예) 브로콜리 파이터", key="su_name")
            new_wt  = st.number_input("현재 몸무게 (kg)", min_value=30.0, max_value=200.0, value=65.0, step=0.1)
            # 조건2: 몸무게 공개/비공개 설정
            weight_public = st.radio("몸무게 공개 설정", ["공개", "비공개"], horizontal=True)
            if st.session_state.auth_error:
                st.markdown(f'<div class="err-box">⚠️ {st.session_state.auth_error}</div>', unsafe_allow_html=True)
            if st.button("🌱 가입하고 시작!", use_container_width=True, type="primary"):
                err = ""
                if not new_id.strip():        err = "아이디를 입력해주세요."
                elif not new_pw:              err = "비밀번호를 입력해주세요."
                elif new_pw != new_pw2:       err = "비밀번호가 일치하지 않습니다."
                elif not new_nm.strip():      err = "닉네임을 입력해주세요."
                elif db_user_by_username(new_id.strip()): err = "이미 사용 중인 아이디입니다."
                if err:
                    st.session_state.auth_error = err
                    st.rerun()
                else:
                    uid = f"u{int(datetime.now().timestamp()*1000)}"
                    db_create_user({
                        "id": uid, "username": new_id.strip(), "password": new_pw,
                        "name": new_nm.strip(), "emoji": emoji,
                        "initial_weight": float(new_wt), "current_weight": float(new_wt),
                        "weight_public": weight_public == "공개",
                        "liked_by": []
                    })
                    db_save_weight(uid, today_str, float(new_wt))
                    st.session_state.session_id = uid
                    st.session_state.auth_error = ""
                    if "signup_emoji" in st.session_state:
                        del st.session_state.signup_emoji
                    st.rerun()
            st.markdown("---")
            c1, c2 = st.columns([2, 1])
            with c1: st.caption("이미 계정이 있으신가요?")
            with c2:
                if st.button("로그인 →", use_container_width=True):
                    st.session_state.auth_page = "login"
                    st.session_state.auth_error = ""
                    st.rerun()


# ══════════════════════════════════════════════════════════════════
# 로그인 상태
# ══════════════════════════════════════════════════════════════════
else:
    # 상단 유저 정보
    c1, c2 = st.columns([4, 1])
    with c1:
        admin_badge = '<span class="admin-badge">운영자</span>' if admin else ""
        st.markdown(f"**{current_user['emoji']} {current_user['name']}** `@{current_user['username']}`{admin_badge}", unsafe_allow_html=True)
    with c2:
        if st.button("로그아웃", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.auth_page = "login"
            st.rerun()

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["🥕 내 페이지", "📋 내 피드", "🏆 순위", "🌿 친구 피드"])


    # ════════════════════════════════════════════════════════
    # 탭1: 내 페이지
    # ════════════════════════════════════════════════════════
    with tab1:
        st.markdown(f'<div style="text-align:center;padding:8px 0 14px"><span style="font-size:2.8rem">{current_user["emoji"]}</span><br><b style="font-size:1.2rem;color:#2d4a1e">{current_user["name"]}</b><br><span style="color:#7a9a5a;font-size:0.78rem">@{current_user["username"]}</span></div>', unsafe_allow_html=True)

        # ── 몸무게 ──────────────────────────────────────────
        st.markdown("#### ⚖️ 몸무게")
        wh_dict = {w["date"]: w["weight"] for w in db_weight_history(current_user["id"])}
        yw = wh_dict.get(yesterday_str)
        cw = current_user["current_weight"]
        iw = current_user["initial_weight"]

        # 조건2: 차이만 표시
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div style="background:rgba(255,255,255,0.9);border-radius:12px;padding:12px;border:1px solid #d4eebc;text-align:center"><div style="font-size:0.72rem;color:#7a9a5a;margin-bottom:4px">📅 전날 대비</div>' +
                (f'<div style="font-size:1.4rem;font-weight:800;color:{"#c0392b" if cw-yw<0 else "#2980b9"}">{"▼" if cw-yw<0 else "▲"} {abs(cw-yw):.1f} kg</div>' if yw else '<div style="font-size:1.1rem;color:#aaa">기록 없음</div>') +
                '</div>', unsafe_allow_html=True)
        with c2:
            total = cw - iw
            st.markdown(f'<div style="background:rgba(255,255,255,0.9);border-radius:12px;padding:12px;border:1px solid #d4eebc;text-align:center"><div style="font-size:0.72rem;color:#7a9a5a;margin-bottom:4px">🏁 처음 대비</div><div style="font-size:1.4rem;font-weight:800;color:{"#c0392b" if total<0 else "#2980b9"}">{"▼" if total<0 else "▲"} {abs(total):.1f} kg</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            new_w = st.number_input("오늘 몸무게 (kg)", min_value=30.0, max_value=200.0,
                                    value=float(cw), step=0.1, key="wi")
            # 조건2: 공개/비공개 설정
            cur_public = current_user.get("weight_public", True)
            wp = st.radio("몸무게 공개", ["공개", "비공개"],
                          index=0 if cur_public else 1, horizontal=True, key="wp_radio")
            if st.button("⚖️ 저장", type="primary", use_container_width=True):
                db_update_user(current_user["id"], {
                    "current_weight": float(new_w),
                    "weight_public": wp == "공개"
                })
                db_save_weight(current_user["id"], today_str, float(new_w))
                st.success(f"✅ {today_str} — {new_w}kg 저장!")
                st.rerun()

        st.divider()

        # ── 식단 ────────────────────────────────────────────
        st.markdown(f"#### 🥗 오늘의 식단 `{today_str}`")
        tm = db_get_meal(current_user["id"], today_str)

        with st.container(border=True):
            bf  = st.text_input("🌅 아침",  value=tm["breakfast"] if tm else "", key="bf")
            lun = st.text_input("☀️ 점심",  value=tm["lunch"]     if tm else "", key="lun")
            din = st.text_input("🌙 저녁",  value=tm["dinner"]    if tm else "", key="din")

            st.markdown("**🍎 간식**")

            # 조건6: 간식 여러번 추가 가능하도록 session_state로 관리
            if "snack_list" not in st.session_state:
                st.session_state.snack_list = list(tm["snacks"] if tm and tm["snacks"] else [])

            # 날짜 바뀌면 간식 초기화
            if "snack_date" not in st.session_state or st.session_state.snack_date != today_str:
                st.session_state.snack_list = list(tm["snacks"] if tm and tm["snacks"] else [])
                st.session_state.snack_date = today_str

            sc1, sc2 = st.columns([3, 1])
            with sc1:
                new_snack = st.text_input("간식", placeholder="간식 입력 후 추가",
                                          label_visibility="collapsed", key="snack_in")
            with sc2:
                if st.button("+ 추가", key="add_snk"):
                    if new_snack.strip():
                        st.session_state.snack_list.append(new_snack.strip())
                        st.rerun()

            if st.session_state.snack_list:
                st.markdown("".join([f'<span class="snack-tag">{s}</span>' for s in st.session_state.snack_list]), unsafe_allow_html=True)
                snack_to_del = st.selectbox("삭제할 간식 선택", ["선택 안 함"] + st.session_state.snack_list,
                                            label_visibility="collapsed", key="snack_del")
                if snack_to_del != "선택 안 함":
                    if st.button(f"❌ '{snack_to_del}' 삭제", key="del_snk"):
                        st.session_state.snack_list.remove(snack_to_del)
                        st.rerun()

            if st.button("💾 식단 저장", type="primary", use_container_width=True, key="save_meal"):
                db_save_meal(current_user["id"], today_str, bf, lun, din, st.session_state.snack_list)
                st.success("✅ 식단 저장 완료!")
                st.rerun()


    # ════════════════════════════════════════════════════════
    # 탭2: 내 피드
    # ════════════════════════════════════════════════════════
    with tab2:
        st.markdown("#### 📋 내 식단 기록")
        wh_dict = {w["date"]: w["weight"] for w in db_weight_history(current_user["id"])}
        all_meals = db_all_meals(current_user["id"])

        if not all_meals:
            st.info("아직 기록된 식단이 없어요! 내 페이지에서 입력해보세요 🥗")
        else:
            for meal in all_meals:
                date = meal["date"]
                is_today = (date == today_str)
                dw = wh_dict.get(date)
                with st.container(border=True):
                    dh1, dh2 = st.columns([3, 1])
                    with dh1:
                        label = f"📅 {date}" + (" ← 오늘" if is_today else "")
                        st.markdown(f'<span class="date-badge">{label}</span>', unsafe_allow_html=True)
                    with dh2:
                        if dw:
                            st.markdown(f'<div style="text-align:right;color:#2d6a2d;font-weight:700;font-size:0.88rem">⚖️ {dw}kg</div>', unsafe_allow_html=True)
                    lines = []
                    if meal.get("breakfast"): lines.append(f"🌅 <b>아침:</b> {meal['breakfast']}")
                    if meal.get("lunch"):     lines.append(f"☀️ <b>점심:</b> {meal['lunch']}")
                    if meal.get("dinner"):    lines.append(f"🌙 <b>저녁:</b> {meal['dinner']}")
                    snacks = meal.get("snacks") or []
                    if snacks: lines.append(f"🍎 <b>간식:</b> {', '.join(snacks)}")
                    if lines:
                        st.markdown(f'<div class="meal-box">{"<br>".join(lines)}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("식단 내용이 없어요.")


    # ════════════════════════════════════════════════════════
    # 탭3: 순위
    # ════════════════════════════════════════════════════════
    with tab3:
        st.markdown("#### 🏆 순위")
        all_users = db_all_users()
        ranked = sorted(all_users, key=lambda u: u["current_weight"] - u["initial_weight"])
        medals = ["🥇", "🥈", "🥉"]

        for i, u in enumerate(ranked):
            change = u["current_weight"] - u["initial_weight"]
            medal  = medals[i] if i < 3 else f"{i+1}위"
            is_me  = u["id"] == current_user["id"]
            bg     = "#fffbe6" if i == 0 else "rgba(255,255,255,0.9)"
            border = "2px solid #4caf50" if is_me else "1.5px solid #d4eebc"
            color  = "#c0392b" if change < 0 else ("#2980b9" if change > 0 else "#888")
            me_tag = " ← 나" if is_me else ""
            admin_tag = " 🔧" if is_admin(u) else ""

            # 조건2: 몸무게 공개 여부 확인 (운영자는 항상 볼 수 있음)
            weight_public = u.get("weight_public", True)
            if admin or weight_public or is_me:
                weight_info = f"{u['initial_weight']}kg → {u['current_weight']}kg"
            else:
                weight_info = "몸무게 비공개"

            st.markdown(f"""
            <div style="background:{bg};border-radius:14px;padding:12px 16px;margin-bottom:8px;border:{border};display:flex;align-items:center;gap:12px;">
                <span style="font-size:1.5rem;min-width:30px">{medal}</span>
                <span style="font-size:1.8rem">{u['emoji']}</span>
                <div style="flex:1">
                    <div style="font-weight:700;color:#2d4a1e">{u['name']}{admin_tag}<span style="color:#4caf50;font-size:0.72rem">{me_tag}</span></div>
                    <div style="font-size:0.76rem;color:#6b7b5a">{weight_info}</div>
                </div>
                <div style="font-size:1.1rem;font-weight:800;color:{color}">{"+" if change>0 else ""}{change:.1f}kg</div>
            </div>
            """, unsafe_allow_html=True)


    # ════════════════════════════════════════════════════════
    # 탭4: 친구 피드
    # ════════════════════════════════════════════════════════
    with tab4:
        # 조건7: 한줄/두줄 토글 버튼 오른쪽 위
        fc1, fc2 = st.columns([3, 1])
        with fc1:
            st.markdown(f"#### 🌿 친구 피드 `{today_str}`")
        with fc2:
            compact_label = "📄 두줄보기" if st.session_state.feed_compact else "📋 한줄보기"
            if st.button(compact_label, use_container_width=True, key="feed_toggle"):
                st.session_state.feed_compact = not st.session_state.feed_compact
                st.rerun()

        compact = st.session_state.feed_compact
        all_users = db_all_users()
        others = [u for u in all_users if u["id"] != current_user["id"]]

        if not others:
            st.info("아직 다른 참가자가 없어요 🌱")
        else:
            for u in others:
                liked_by   = u.get("liked_by") or []
                is_liked   = current_user["id"] in liked_by
                like_count = len(liked_by)
                other_meal = db_get_meal(u["id"], today_str)
                comments   = db_comments(u["id"])

                # 조건4: 비공개 피드 처리 (운영자는 다 볼 수 있음)
                weight_public = u.get("weight_public", True)

                with st.container(border=True):
                    # 유저 헤더
                    uh1, uh2 = st.columns([1, 5])
                    with uh1:
                        st.markdown(f"<span style='font-size:2rem'>{u['emoji']}</span>", unsafe_allow_html=True)
                    with uh2:
                        change_u = u["current_weight"] - u["initial_weight"]
                        admin_tag = " 🔧" if is_admin(u) else ""
                        # 조건2: 몸무게 공개 여부
                        if admin or weight_public:
                            weight_str = f"{u['current_weight']}kg (변화: {change_u:+.1f}kg)"
                        else:
                            weight_str = "몸무게 비공개 🔒"
                        st.markdown(f"**{u['name']}**{admin_tag}")
                        st.caption(weight_str)

                    # 식단 표시
                    if other_meal:
                        lines = []
                        if other_meal.get("breakfast"): lines.append(f"🌅 <b>아침:</b> {other_meal['breakfast']}")
                        if other_meal.get("lunch"):     lines.append(f"☀️ <b>점심:</b> {other_meal['lunch']}")
                        if other_meal.get("dinner"):    lines.append(f"🌙 <b>저녁:</b> {other_meal['dinner']}")
                        snacks = other_meal.get("snacks") or []
                        if snacks: lines.append(f"🍎 <b>간식:</b> {', '.join(snacks)}")
                        if lines:
                            # 조건7: 한줄/두줄 모드
                            if compact:
                                st.markdown(f'<div class="meal-box-compact">{"　|　".join(lines)}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="meal-box">{"<br>".join(lines)}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("오늘 식단이 아직 없어요.")

                    # 공감 버튼
                    lc1, lc2 = st.columns([2, 3])
                    with lc1:
                        lbl = f"💚 공감함 {like_count}" if is_liked else f"🤍 공감 {like_count}"
                        if st.button(lbl, key=f"like_{u['id']}", use_container_width=True):
                            db_toggle_like(u["id"], current_user["id"])
                            st.rerun()
                    with lc2:
                        if is_liked:
                            st.caption("한 번 더 누르면 취소")

                    # 댓글
                    if comments:
                        st.markdown("---")
                        for c in comments:
                            st.markdown(f'<div class="comment-item"><b style="color:#3a7a2a">{c["author"]}</b>: {c["text"]}</div>', unsafe_allow_html=True)

                    cc1, cc2 = st.columns([4, 1])
                    with cc1:
                        ct = st.text_input("댓글", placeholder="댓글 달기...",
                                           label_visibility="collapsed", key=f"ci_{u['id']}")
                    with cc2:
                        if st.button("등록", key=f"cb_{u['id']}", use_container_width=True):
                            if ct.strip():
                                db_add_comment(u["id"], current_user["name"], ct.strip())
                                st.rerun()
