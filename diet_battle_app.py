"""
🥦 다이어트 대결 앱 - Streamlit + Supabase 버전
실행 방법: streamlit run diet_battle_app.py
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from supabase import create_client

# ─────────────────────────────────────────────────────────────────
# 테스트 모드 설정
# 테스트 끝나면 False로 바꾸면 "다음날" 버튼이 사라집니다
TEST_MODE = True
# ─────────────────────────────────────────────────────────────────

SUPABASE_URL = "https://qdjupvyeiqfwrgdxevph.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkanVwdnllaXFmd3JnZHhldnBoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA4MjcwNTgsImV4cCI6MjA5NjQwMzA1OH0.0A-JEDucci-hsAY4QSBN5zN7OPTTrx-gksDmBI1NVHU"

VEGGIE_EMOJIS = ["🥦", "🥕", "🍅", "🥑", "🍋", "🥝", "🍇", "🥬", "🌽", "🍓", "🫐", "🥭"]

def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def dateToStr(d): return d.strftime("%Y-%m-%d")
def prev_day(s): return dateToStr(datetime.strptime(s, "%Y-%m-%d") - timedelta(days=1))
def next_day(s): return dateToStr(datetime.strptime(s, "%Y-%m-%d") + timedelta(days=1))

# ── DB 함수 ───────────────────────────────────────────────────────
def db_get_all_users():
    sb = get_supabase()
    res = sb.table("users").select("*").execute()
    return res.data or []

def db_get_user_by_username(username):
    sb = get_supabase()
    res = sb.table("users").select("*").eq("username", username).execute()
    return res.data[0] if res.data else None

def db_get_user_by_id(uid):
    sb = get_supabase()
    res = sb.table("users").select("*").eq("id", uid).execute()
    return res.data[0] if res.data else None

def db_create_user(user):
    sb = get_supabase()
    sb.table("users").insert(user).execute()

def db_update_user(uid, fields):
    sb = get_supabase()
    sb.table("users").update(fields).eq("id", uid).execute()

def db_get_meals(user_id, date):
    sb = get_supabase()
    res = sb.table("meals").select("*").eq("user_id", user_id).eq("date", date).execute()
    return res.data[0] if res.data else None

def db_get_all_meals(user_id):
    sb = get_supabase()
    res = sb.table("meals").select("*").eq("user_id", user_id).order("date", desc=True).execute()
    return res.data or []

def db_save_meals(user_id, date, breakfast, lunch, dinner, snacks):
    sb = get_supabase()
    existing = db_get_meals(user_id, date)
    data = {"user_id": user_id, "date": date, "breakfast": breakfast,
            "lunch": lunch, "dinner": dinner, "snacks": snacks}
    if existing:
        sb.table("meals").update(data).eq("user_id", user_id).eq("date", date).execute()
    else:
        sb.table("meals").insert(data).execute()

def db_get_weight_history(user_id):
    sb = get_supabase()
    res = sb.table("weight_history").select("*").eq("user_id", user_id).order("date", desc=True).execute()
    return res.data or []

def db_save_weight(user_id, date, weight):
    sb = get_supabase()
    res = sb.table("weight_history").select("*").eq("user_id", user_id).eq("date", date).execute()
    if res.data:
        sb.table("weight_history").update({"weight": weight}).eq("user_id", user_id).eq("date", date).execute()
    else:
        sb.table("weight_history").insert({"user_id": user_id, "date": date, "weight": weight}).execute()

def db_get_comments(target_user_id):
    sb = get_supabase()
    res = sb.table("comments").select("*").eq("target_user_id", target_user_id).order("created_at").execute()
    return res.data or []

def db_add_comment(target_user_id, author, text):
    sb = get_supabase()
    sb.table("comments").insert({"target_user_id": target_user_id, "author": author, "text": text}).execute()

def db_toggle_like(target_uid, my_uid):
    sb = get_supabase()
    user = db_get_user_by_id(target_uid)
    liked_by = user.get("liked_by") or []
    if my_uid in liked_by:
        liked_by = [x for x in liked_by if x != my_uid]
    else:
        liked_by = liked_by + [my_uid]
    db_update_user(target_uid, {"liked_by": liked_by})


# ── Streamlit 설정 ────────────────────────────────────────────────
st.set_page_config(page_title="🥦 다이어트 대결", page_icon="🥦", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Nanum Gothic', sans-serif; }
.stApp { background: linear-gradient(135deg, #e8f5e2 0%, #fff9e6 50%, #fde8f0 100%); }
.app-title { font-size: 2rem; font-weight: 800; color: #2d6a2d; letter-spacing: 1px; text-align: center; }
.meal-box { background: #f4fbef; border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; border: 1px solid #d0ecc0; line-height: 1.9; font-size: 0.9rem; }
.comment-bubble { background: #f0fbe8; border-radius: 10px; padding: 8px 12px; margin-bottom: 6px; font-size: 0.85rem; color: #3a5a1e; border: 1px solid #d0ecc0; }
.snack-tag { display: inline-block; background: #e2f7d4; border: 1px solid #a8d890; border-radius: 20px; padding: 3px 10px; font-size: 0.82rem; color: #2d6a2d; margin: 3px 2px; }
.error-box { background: #ffe8e8; border: 1.5px solid #f0b0b0; border-radius: 10px; padding: 10px 14px; color: #c0392b; font-size: 0.88rem; margin-bottom: 10px; }
.hint-box { background: #f4fbef; border: 1px dashed #a8d890; border-radius: 10px; padding: 10px 14px; color: #5a8a3a; font-size: 0.78rem; text-align: center; margin-top: 12px; line-height: 1.7; }
.test-banner { background: linear-gradient(135deg, #fff3cd, #ffe08a); border: 1.5px solid #f0c040; border-radius: 10px; padding: 8px 14px; font-size: 0.82rem; color: #7a5500; font-weight: 700; text-align: center; margin-bottom: 12px; }
.my-feed-date { background: #e8f5e2; border-radius: 8px; padding: 4px 10px; font-size: 0.78rem; color: #4a7a2a; font-weight: 700; display: inline-block; margin-bottom: 8px; }
.veggie-card { background: rgba(255,255,255,0.88); border-radius: 18px; padding: 20px 24px; margin-bottom: 16px; border: 1.5px solid #d4eebc; box-shadow: 0 4px 20px rgba(60,120,30,0.08); }
.stButton > button { border-radius: 12px !important; font-family: 'Nanum Gothic', sans-serif !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"
if "auth_error" not in st.session_state:
    st.session_state.auth_error = ""
if "sim_date" not in st.session_state:
    st.session_state.sim_date = dateToStr(datetime.today())

today_str = st.session_state.sim_date
yesterday_str = prev_day(today_str)

# ── 헤더 ─────────────────────────────────────────────────────────
st.markdown('<div class="app-title">🥦🍋🫐 다이어트 대결</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;color:#7a9a5a;letter-spacing:3px;font-size:0.75rem;margin-bottom:12px;">VEGGIE BATTLE</div>', unsafe_allow_html=True)
st.divider()

current_user = db_get_user_by_id(st.session_state.session_id) if st.session_state.session_id else None

# 테스트 배너
if TEST_MODE and current_user:
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f'<div class="test-banner">🧪 테스트 모드 | 현재 날짜: <b>{today_str}</b></div>', unsafe_allow_html=True)
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
            username_in = st.text_input("아이디", key="login_user")
            password_in = st.text_input("비밀번호", type="password", key="login_pw")
            if st.session_state.auth_error:
                st.markdown(f'<div class="error-box">⚠️ {st.session_state.auth_error}</div>', unsafe_allow_html=True)
            if st.button("🌿 로그인", use_container_width=True, type="primary"):
                found = db_get_user_by_username(username_in.strip())
                if not found:
                    st.session_state.auth_error = "존재하지 않는 아이디입니다."
                elif found["password"] != password_in:
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
            new_username  = st.text_input("아이디", key="su_user")
            new_password  = st.text_input("비밀번호", type="password", key="su_pw")
            new_password2 = st.text_input("비밀번호 확인", type="password", key="su_pw2")
            new_name      = st.text_input("닉네임", placeholder="예) 브로콜리 파이터", key="su_name")
            new_weight    = st.number_input("현재 몸무게 (kg)", min_value=30.0, max_value=200.0, value=65.0, step=0.1)
            if st.session_state.auth_error:
                st.markdown(f'<div class="error-box">⚠️ {st.session_state.auth_error}</div>', unsafe_allow_html=True)
            if st.button("🌱 가입하고 시작!", use_container_width=True, type="primary"):
                err = ""
                if not new_username.strip():        err = "아이디를 입력해주세요."
                elif not new_password:              err = "비밀번호를 입력해주세요."
                elif new_password != new_password2: err = "비밀번호가 일치하지 않습니다."
                elif not new_name.strip():          err = "닉네임을 입력해주세요."
                elif db_get_user_by_username(new_username.strip()): err = "이미 사용 중인 아이디입니다."
                if err:
                    st.session_state.auth_error = err
                    st.rerun()
                else:
                    new_id = f"u{int(datetime.now().timestamp()*1000)}"
                    db_create_user({
                        "id": new_id, "username": new_username.strip(),
                        "password": new_password, "name": new_name.strip(),
                        "emoji": emoji, "initial_weight": float(new_weight),
                        "current_weight": float(new_weight), "liked_by": []
                    })
                    db_save_weight(new_id, today_str, float(new_weight))
                    st.session_state.session_id = new_id
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
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown(f"**{current_user['emoji']} {current_user['name']}** `@{current_user['username']}`")
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
        st.markdown(f'<div style="text-align:center;padding:10px 0 16px"><span style="font-size:3rem">{current_user["emoji"]}</span><br><b style="font-size:1.3rem;color:#2d4a1e">{current_user["name"]}</b><br><span style="color:#7a9a5a;font-size:0.8rem">@{current_user["username"]}</span></div>', unsafe_allow_html=True)

        # 몸무게 비교
        st.markdown("#### ⚖️ 몸무게 관리")
        wh = db_get_weight_history(current_user["id"])
        wh_dict = {w["date"]: w["weight"] for w in wh}
        yesterday_weight = wh_dict.get(yesterday_str)
        current_weight   = current_user["current_weight"]
        initial_weight   = current_user["initial_weight"]

        st.markdown("**📅 전날 vs 오늘**")
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("어제", f"{yesterday_weight} kg" if yesterday_weight else "기록 없음")
        with c2: st.metric("오늘", f"{current_weight} kg")
        with c3:
            if yesterday_weight:
                d = current_weight - yesterday_weight
                color = "#c0392b" if d < 0 else ("#2980b9" if d > 0 else "#888")
                arrow = "▼" if d < 0 else ("▲" if d > 0 else "−")
                st.markdown(f'<div style="text-align:center;padding-top:8px"><div style="font-size:0.78rem;color:#7a9a5a">하루 변화</div><div style="font-size:1.3rem;font-weight:800;color:{color}">{arrow} {abs(d):.1f} kg</div></div>', unsafe_allow_html=True)
            else:
                st.metric("하루 변화", "—")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**🏁 처음 vs 지금**")
        c4, c5, c6 = st.columns(3)
        total = current_weight - initial_weight
        total_color = "#c0392b" if total < 0 else ("#2980b9" if total > 0 else "#888")
        total_arrow = "▼" if total < 0 else ("▲" if total > 0 else "−")
        with c4: st.metric("시작", f"{initial_weight} kg")
        with c5: st.metric("현재", f"{current_weight} kg")
        with c6:
            st.markdown(f'<div style="text-align:center;padding-top:8px"><div style="font-size:0.78rem;color:#7a9a5a">총 변화</div><div style="font-size:1.3rem;font-weight:800;color:{total_color}">{total_arrow} {abs(total):.1f} kg</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            new_w = st.number_input("오늘 몸무게 입력 (kg)", min_value=30.0, max_value=200.0,
                                    value=float(current_weight), step=0.1, key="weight_input")
            if st.button("⚖️ 오늘 몸무게 저장", type="primary", use_container_width=True):
                db_update_user(current_user["id"], {"current_weight": float(new_w)})
                db_save_weight(current_user["id"], today_str, float(new_w))
                st.success(f"✅ {today_str} 몸무게 {new_w}kg 저장!")
                st.rerun()

        st.divider()

        # 식단 입력
        st.markdown(f"#### 🥗 오늘의 식단 `{today_str}`")
        today_meals = db_get_meals(current_user["id"], today_str)
        with st.container(border=True):
            breakfast = st.text_input("🌅 아침", value=today_meals["breakfast"] if today_meals else "", key="bf")
            lunch     = st.text_input("☀️ 점심", value=today_meals["lunch"]     if today_meals else "", key="lun")
            dinner    = st.text_input("🌙 저녁", value=today_meals["dinner"]    if today_meals else "", key="din")

            st.markdown("**🍎 간식**")
            current_snacks = list(today_meals["snacks"] if today_meals and today_meals["snacks"] else [])
            sc1, sc2 = st.columns([3, 1])
            with sc1:
                new_snack = st.text_input("간식", placeholder="간식 입력 후 추가", label_visibility="collapsed", key="snack_input")
            with sc2:
                add_snack_btn = st.button("+ 추가", key="add_snack")

            if current_snacks:
                st.markdown("".join([f'<span class="snack-tag">{s}</span>' for s in current_snacks]), unsafe_allow_html=True)
                snack_to_remove = st.selectbox("삭제할 간식", ["선택 안 함"] + current_snacks, label_visibility="collapsed", key="snack_remove")
                if snack_to_remove != "선택 안 함":
                    if st.button(f"❌ '{snack_to_remove}' 삭제", key="del_snack"):
                        current_snacks = [s for s in current_snacks if s != snack_to_remove]
                        db_save_meals(current_user["id"], today_str, breakfast, lunch, dinner, current_snacks)
                        st.rerun()

            if add_snack_btn and new_snack.strip():
                current_snacks = current_snacks + [new_snack.strip()]

            if st.button("💾 식단 저장", type="primary", use_container_width=True, key="save_meal"):
                db_save_meals(current_user["id"], today_str, breakfast, lunch, dinner, current_snacks)
                st.success("✅ 오늘의 식단이 저장되었습니다!")
                st.rerun()

    # ════════════════════════════════════════════════════════
    # 탭2: 내 피드
    # ════════════════════════════════════════════════════════
    with tab2:
        st.markdown("#### 📋 내 식단 기록")
        wh = db_get_weight_history(current_user["id"])
        wh_dict = {w["date"]: w["weight"] for w in wh}
        all_meals = db_get_all_meals(current_user["id"])

        if not all_meals:
            st.info("아직 기록된 식단이 없어요! 내 페이지에서 입력해보세요 🥗")
        else:
            for meal in all_meals:
                date = meal["date"]
                is_today = (date == today_str)
                day_weight = wh_dict.get(date)
                with st.container(border=True):
                    dh1, dh2 = st.columns([3, 1])
                    with dh1:
                        label = f"📅 {date}" + (" ← 오늘" if is_today else "")
                        st.markdown(f'<span class="my-feed-date">{label}</span>', unsafe_allow_html=True)
                    with dh2:
                        if day_weight:
                            st.markdown(f'<div style="text-align:right;color:#2d6a2d;font-weight:700;font-size:0.9rem">⚖️ {day_weight}kg</div>', unsafe_allow_html=True)
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
                    if is_today:
                        st.caption("✏️ 오늘 식단은 '내 페이지'에서 수정할 수 있어요!")

    # ════════════════════════════════════════════════════════
    # 탭3: 순위
    # ════════════════════════════════════════════════════════
    with tab3:
        st.markdown("#### 🏆 다이어트 대결 순위")
        all_users = db_get_all_users()
        ranked = sorted(all_users, key=lambda u: u["current_weight"] - u["initial_weight"])
        medals = ["🥇", "🥈", "🥉"]
        for i, u in enumerate(ranked):
            change = u["current_weight"] - u["initial_weight"]
            medal = medals[i] if i < 3 else f"{i+1}위"
            bg = "#fff9e6" if i == 0 else "#f8fdf4"
            is_me = u["id"] == current_user["id"]
            border = "2px solid #4caf50" if is_me else "1.5px solid #d4eebc"
            color = "#c0392b" if change < 0 else ("#2980b9" if change > 0 else "#888")
            me_label = "<span style='color:#4caf50;font-size:0.75rem'> ← 나</span>" if is_me else ""
            st.markdown(f"""
            <div class="veggie-card" style="background:{bg};border:{border};">
                <div style="display:flex;align-items:center;gap:14px;">
                    <span style="font-size:1.6rem">{medal}</span>
                    <span style="font-size:2rem">{u['emoji']}</span>
                    <div style="flex:1">
                        <div style="font-weight:700;color:#2d4a1e">{u['name']}{me_label}</div>
                        <div style="font-size:0.78rem;color:#6b7b5a">{u['initial_weight']}kg → {u['current_weight']}kg</div>
                    </div>
                    <div style="font-size:1.1rem;font-weight:800;color:{color}">{"+" if change>0 else ""}{change:.1f}kg</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # 탭4: 친구 피드
    # ════════════════════════════════════════════════════════
    with tab4:
        st.markdown(f"#### 🌿 친구들의 식단 `{today_str}`")
        all_users = db_get_all_users()
        others = [u for u in all_users if u["id"] != current_user["id"]]

        if not others:
            st.info("아직 다른 참가자가 없어요 🌱")
        else:
            for u in others:
                liked_by   = u.get("liked_by") or []
                is_liked   = current_user["id"] in liked_by
                like_count = len(liked_by)
                other_meal = db_get_meals(u["id"], today_str)
                comments   = db_get_comments(u["id"])

                with st.container(border=True):
                    uc1, uc2 = st.columns([1, 5])
                    with uc1:
                        st.markdown(f"<span style='font-size:2.2rem'>{u['emoji']}</span>", unsafe_allow_html=True)
                    with uc2:
                        change_u = u["current_weight"] - u["initial_weight"]
                        st.markdown(f"**{u['name']}**")
                        st.caption(f"{u['current_weight']}kg (총 변화: {change_u:+.1f}kg)")

                    if other_meal:
                        lines = []
                        if other_meal.get("breakfast"): lines.append(f"🌅 <b>아침:</b> {other_meal['breakfast']}")
                        if other_meal.get("lunch"):     lines.append(f"☀️ <b>점심:</b> {other_meal['lunch']}")
                        if other_meal.get("dinner"):    lines.append(f"🌙 <b>저녁:</b> {other_meal['dinner']}")
                        snacks = other_meal.get("snacks") or []
                        if snacks: lines.append(f"🍎 <b>간식:</b> {', '.join(snacks)}")
                        if lines:
                            st.markdown(f'<div class="meal-box">{"<br>".join(lines)}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("오늘 식단이 아직 없어요.")

                    lc1, lc2 = st.columns([2, 3])
                    with lc1:
                        like_label = f"💚 공감함 {like_count}" if is_liked else f"🤍 공감 {like_count}"
                        if st.button(like_label, key=f"like_{u['id']}", use_container_width=True):
                            db_toggle_like(u["id"], current_user["id"])
                            st.rerun()
                    with lc2:
                        if is_liked:
                            st.caption("💡 한 번 더 누르면 취소")

                    st.divider()

                    for c in comments:
                        st.markdown(f'<div class="comment-bubble"><b style="color:#3a7a2a">{c["author"]}</b>: {c["text"]}</div>', unsafe_allow_html=True)

                    cc1, cc2 = st.columns([4, 1])
                    with cc1:
                        comment_text = st.text_input("댓글", placeholder="댓글 달기...",
                                                     label_visibility="collapsed", key=f"comment_input_{u['id']}")
                    with cc2:
                        if st.button("등록", key=f"comment_btn_{u['id']}", use_container_width=True):
                            if comment_text.strip():
                                db_add_comment(u["id"], current_user["name"], comment_text.strip())
                                st.rerun()
