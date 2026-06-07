"""
🥦 다이어트 대결 앱 - Streamlit 버전
실행 방법: streamlit run diet_battle_app.py
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────────
# 테스트 모드 설정
# 테스트 끝나면 False로 바꾸면 "다음날" 버튼이 사라집니다
TEST_MODE = True
# ─────────────────────────────────────────────────────────────────

DATA_FILE = "diet_battle_data.json"
VEGGIE_EMOJIS = ["🥦", "🥕", "🍅", "🥑", "🍋", "🥝", "🍇", "🥬", "🌽", "🍓", "🫐", "🥭"]


# ── 데이터 저장/불러오기 ──────────────────────────────────────────
def load_data():
    default = {
        "users": [
            {
                "id": "u1", "username": "minji", "password": "1234",
                "name": "건강왕 민지", "emoji": "🥦",
                "initialWeight": 68.0, "currentWeight": 64.5,
                "weightHistory": {"2026-06-06": 65.0, "2026-06-07": 64.5},
                "meals": {
                    "2026-06-07": {"breakfast": "오트밀 + 블루베리", "lunch": "닭가슴살 샐러드", "dinner": "된장국 + 현미밥", "snacks": ["그릭요거트", "아몬드 한줌"]}
                },
                "comments": [], "likedBy": []
            },
            {
                "id": "u2", "username": "junho", "password": "1234",
                "name": "다이어터 준호", "emoji": "🥕",
                "initialWeight": 82.0, "currentWeight": 78.2,
                "weightHistory": {"2026-06-06": 79.0, "2026-06-07": 78.2},
                "meals": {
                    "2026-06-07": {"breakfast": "삶은 달걀 2개 + 토마토", "lunch": "연어 포케", "dinner": "닭가슴살 볶음 + 브로콜리", "snacks": ["프로틴바"]}
                },
                "comments": [], "likedBy": []
            },
            {
                "id": "u3", "username": "sua", "password": "1234",
                "name": "채식러버 수아", "emoji": "🥑",
                "initialWeight": 58.0, "currentWeight": 55.8,
                "weightHistory": {"2026-06-06": 56.2, "2026-06-07": 55.8},
                "meals": {
                    "2026-06-07": {"breakfast": "아보카도토스트", "lunch": "퀴노아 샐러드", "dinner": "두부 스테이크 + 채소구이", "snacks": ["과일 믹스", "견과류"]}
                },
                "comments": [], "likedBy": []
            }
        ],
        "sim_date": datetime.today().strftime("%Y-%m-%d")
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # weightHistory 없는 기존 유저에 추가
                for u in loaded["users"]:
                    if "weightHistory" not in u:
                        u["weightHistory"] = {}
                return loaded
        except Exception:
            pass
    return default


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_by_id(data, uid):
    return next((u for u in data["users"] if u["id"] == uid), None)


def get_user_by_username(data, username):
    return next((u for u in data["users"] if u["username"] == username), None)


def update_user(data, updated_user):
    data["users"] = [updated_user if u["id"] == updated_user["id"] else u for u in data["users"]]


def prev_day_str(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=1)
    return d.strftime("%Y-%m-%d")


# ── Streamlit 페이지 설정 ─────────────────────────────────────────
st.set_page_config(
    page_title="🥦 다이어트 대결",
    page_icon="🥦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Nanum Gothic', sans-serif; }
.stApp { background: linear-gradient(135deg, #e8f5e2 0%, #fff9e6 50%, #fde8f0 100%); }
.veggie-card {
    background: rgba(255,255,255,0.88); border-radius: 18px; padding: 20px 24px;
    margin-bottom: 16px; border: 1.5px solid #d4eebc;
    box-shadow: 0 4px 20px rgba(60,120,30,0.08);
}
.app-title { font-size: 2rem; font-weight: 800; color: #2d6a2d; letter-spacing: 1px; text-align: center; }
.error-box {
    background: #ffe8e8; border: 1.5px solid #f0b0b0; border-radius: 10px;
    padding: 10px 14px; color: #c0392b; font-size: 0.88rem; margin-bottom: 10px;
}
.hint-box {
    background: #f4fbef; border: 1px dashed #a8d890; border-radius: 10px;
    padding: 10px 14px; color: #5a8a3a; font-size: 0.78rem;
    text-align: center; margin-top: 12px; line-height: 1.7;
}
.meal-box {
    background: #f4fbef; border-radius: 10px; padding: 12px 14px;
    margin-bottom: 10px; border: 1px solid #d0ecc0; line-height: 1.9; font-size: 0.9rem;
}
.comment-bubble {
    background: #f0fbe8; border-radius: 10px; padding: 8px 12px;
    margin-bottom: 6px; font-size: 0.85rem; color: #3a5a1e; border: 1px solid #d0ecc0;
}
.snack-tag {
    display: inline-block; background: #e2f7d4; border: 1px solid #a8d890;
    border-radius: 20px; padding: 3px 10px; font-size: 0.82rem; color: #2d6a2d; margin: 3px 2px;
}
.weight-compare-box {
    background: rgba(255,255,255,0.9); border-radius: 14px; padding: 16px 18px;
    border: 1.5px solid #d4eebc; margin-bottom: 10px;
}
.my-feed-date {
    background: #e8f5e2; border-radius: 8px; padding: 4px 10px;
    font-size: 0.78rem; color: #4a7a2a; font-weight: 700; display: inline-block; margin-bottom: 8px;
}
.test-banner {
    background: linear-gradient(135deg, #fff3cd, #ffe08a); border: 1.5px solid #f0c040;
    border-radius: 10px; padding: 8px 14px; font-size: 0.82rem;
    color: #7a5500; font-weight: 700; text-align: center; margin-bottom: 12px;
}
.stButton > button { border-radius: 12px !important; font-family: 'Nanum Gothic', sans-serif !important; font-weight: 700 !important; }
.change-minus { color: #c0392b; font-weight: 800; }
.change-plus  { color: #2980b9; font-weight: 800; }
.change-zero  { color: #888;    font-weight: 800; }
</style>
""", unsafe_allow_html=True)


# ── Session State 초기화 ──────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"
if "auth_error" not in st.session_state:
    st.session_state.auth_error = ""
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "mypage"

data = st.session_state.data
today_str = data.get("sim_date", datetime.today().strftime("%Y-%m-%d"))
yesterday_str = prev_day_str(today_str)
current_user = get_user_by_id(data, st.session_state.session_id) if st.session_state.session_id else None


# ── 헤더 ─────────────────────────────────────────────────────────
st.markdown('<div class="app-title">🥦🍋🫐 다이어트 대결</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;color:#7a9a5a;letter-spacing:3px;font-size:0.75rem;margin-bottom:12px;">VEGGIE BATTLE</div>', unsafe_allow_html=True)
st.divider()

# 테스트 모드 배너
if TEST_MODE and current_user:
    col_date, col_btn = st.columns([3, 1])
    with col_date:
        st.markdown(f'<div class="test-banner">🧪 테스트 모드 | 현재 날짜: <b>{today_str}</b></div>', unsafe_allow_html=True)
    with col_btn:
        if st.button("📅 +1일", use_container_width=True):
            next_day = (datetime.strptime(today_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            data["sim_date"] = next_day
            save_data(data)
            st.rerun()


# ══════════════════════════════════════════════════════════════════
# 비로그인 상태
# ══════════════════════════════════════════════════════════════════
if not current_user:

    if st.session_state.auth_page == "login":
        st.markdown("### 🌿 로그인")
        st.caption("다시 만나서 반가워요!")
        with st.container(border=True):
            username_in = st.text_input("아이디", placeholder="아이디를 입력하세요", key="login_user")
            password_in = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", key="login_pw")
            if st.session_state.auth_error:
                st.markdown(f'<div class="error-box">⚠️ {st.session_state.auth_error}</div>', unsafe_allow_html=True)
            if st.button("🌿 로그인", use_container_width=True, type="primary"):
                found = get_user_by_username(data, username_in.strip())
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
        st.markdown('<div class="hint-box">💡 데모 계정: <b>minji / 1234</b> &nbsp;|&nbsp; <b>junho / 1234</b> &nbsp;|&nbsp; <b>sua / 1234</b></div>', unsafe_allow_html=True)

    else:
        import random
        if "signup_emoji" not in st.session_state:
            st.session_state.signup_emoji = random.choice(VEGGIE_EMOJIS)
        emoji = st.session_state.signup_emoji
        st.markdown(f"### {emoji} 회원가입")
        st.caption("채소처럼 건강하게, 과일처럼 달콤하게 🍓")
        with st.container(border=True):
            new_username  = st.text_input("아이디", key="su_user")
            new_password  = st.text_input("비밀번호", type="password", key="su_pw")
            new_password2 = st.text_input("비밀번호 확인", type="password", key="su_pw2")
            new_name      = st.text_input("닉네임", placeholder="예) 브로콜리 파이터", key="su_name")
            new_weight    = st.number_input("현재 몸무게 (kg)", min_value=30.0, max_value=200.0, value=65.0, step=0.1, key="su_weight")
            if st.session_state.auth_error:
                st.markdown(f'<div class="error-box">⚠️ {st.session_state.auth_error}</div>', unsafe_allow_html=True)
            if st.button("🌱 가입하고 시작!", use_container_width=True, type="primary"):
                err = ""
                if not new_username.strip():        err = "아이디를 입력해주세요."
                elif not new_password:              err = "비밀번호를 입력해주세요."
                elif new_password != new_password2: err = "비밀번호가 일치하지 않습니다."
                elif not new_name.strip():          err = "닉네임을 입력해주세요."
                elif get_user_by_username(data, new_username.strip()): err = "이미 사용 중인 아이디입니다."
                if err:
                    st.session_state.auth_error = err
                    st.rerun()
                else:
                    new_user = {
                        "id": f"u{int(datetime.now().timestamp()*1000)}",
                        "username": new_username.strip(), "password": new_password,
                        "name": new_name.strip(), "emoji": emoji,
                        "initialWeight": float(new_weight), "currentWeight": float(new_weight),
                        "weightHistory": {today_str: float(new_weight)},
                        "meals": {}, "comments": [], "likedBy": []
                    }
                    data["users"].append(new_user)
                    save_data(data)
                    st.session_state.session_id = new_user["id"]
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
    col_user, col_logout = st.columns([4, 1])
    with col_user:
        st.markdown(f"**{current_user['emoji']} {current_user['name']}** `@{current_user['username']}`")
    with col_logout:
        if st.button("로그아웃", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.auth_page = "login"
            st.session_state.auth_error = ""
            st.rerun()

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["🥕 내 페이지", "📋 내 피드", "🏆 순위", "🌿 친구 피드"])


    # ════════════════════════════════════════════════════════
    # 탭1: 내 페이지
    # ════════════════════════════════════════════════════════
    with tab1:
        st.markdown(f'<div style="text-align:center;padding:10px 0 16px"><span style="font-size:3rem">{current_user["emoji"]}</span><br><b style="font-size:1.3rem;color:#2d4a1e">{current_user["name"]}</b><br><span style="color:#7a9a5a;font-size:0.8rem">@{current_user["username"]}</span></div>', unsafe_allow_html=True)

        # ── 조건3: 몸무게 비교 (전날 vs 오늘 / 처음 vs 지금) ────
        st.markdown("#### ⚖️ 몸무게 관리")

        weight_history = current_user.get("weightHistory", {})
        yesterday_weight = weight_history.get(yesterday_str)
        initial_weight   = current_user["initialWeight"]
        current_weight   = current_user["currentWeight"]

        # 전날 vs 오늘 비교
        st.markdown("**📅 전날 vs 오늘**")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("어제", f"{yesterday_weight} kg" if yesterday_weight else "기록 없음")
        with c2:
            st.metric("오늘", f"{current_weight} kg")
        with c3:
            if yesterday_weight:
                day_change = current_weight - yesterday_weight
                arrow = "▼" if day_change < 0 else ("▲" if day_change > 0 else "−")
                color = "#c0392b" if day_change < 0 else ("#2980b9" if day_change > 0 else "#888")
                st.markdown(f'<div style="text-align:center;padding-top:8px"><div style="font-size:0.78rem;color:#7a9a5a">하루 변화</div><div style="font-size:1.3rem;font-weight:800;color:{color}">{arrow} {abs(day_change):.1f} kg</div></div>', unsafe_allow_html=True)
            else:
                st.metric("하루 변화", "—")

        st.markdown("<br>", unsafe_allow_html=True)

        # 처음 vs 지금 비교
        st.markdown("**🏁 처음 vs 지금**")
        c4, c5, c6 = st.columns(3)
        total_change = current_weight - initial_weight
        total_arrow = "▼" if total_change < 0 else ("▲" if total_change > 0 else "−")
        total_color = "#c0392b" if total_change < 0 else ("#2980b9" if total_change > 0 else "#888")
        with c4:
            st.metric("시작 몸무게", f"{initial_weight} kg")
        with c5:
            st.metric("현재 몸무게", f"{current_weight} kg")
        with c6:
            st.markdown(f'<div style="text-align:center;padding-top:8px"><div style="font-size:0.78rem;color:#7a9a5a">총 변화</div><div style="font-size:1.3rem;font-weight:800;color:{total_color}">{total_arrow} {abs(total_change):.1f} kg</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 몸무게 업데이트 입력
        with st.container(border=True):
            new_w = st.number_input("오늘 몸무게 입력 (kg)", min_value=30.0, max_value=200.0,
                                    value=float(current_weight), step=0.1, key="weight_input")
            if st.button("⚖️ 오늘 몸무게 저장", type="primary", use_container_width=True):
                current_user["currentWeight"] = float(new_w)
                if "weightHistory" not in current_user:
                    current_user["weightHistory"] = {}
                current_user["weightHistory"][today_str] = float(new_w)
                update_user(data, current_user)
                save_data(data)
                st.success(f"✅ 오늘({today_str}) 몸무게 {new_w}kg 저장!")
                st.rerun()

        st.divider()

        # ── 오늘의 식단 입력 ──────────────────────────────
        st.markdown(f"#### 🥗 오늘의 식단 `{today_str}`")
        today_meals = current_user["meals"].get(today_str, {"breakfast": "", "lunch": "", "dinner": "", "snacks": []})

        with st.container(border=True):
            breakfast = st.text_input("🌅 아침", value=today_meals.get("breakfast", ""), placeholder="아침 식단 입력...", key="bf")
            lunch     = st.text_input("☀️ 점심", value=today_meals.get("lunch", ""),     placeholder="점심 식단 입력...", key="lun")
            dinner    = st.text_input("🌙 저녁", value=today_meals.get("dinner", ""),    placeholder="저녁 식단 입력...", key="din")

            st.markdown("**🍎 간식**")
            current_snacks = list(today_meals.get("snacks", []))
            snack_cols = st.columns([3, 1])
            with snack_cols[0]:
                new_snack = st.text_input("간식", placeholder="간식 입력 후 추가 버튼", label_visibility="collapsed", key="snack_input")
            with snack_cols[1]:
                add_snack_btn = st.button("+ 추가", key="add_snack")

            if current_snacks:
                snack_html = "".join([f'<span class="snack-tag">{s}</span>' for s in current_snacks])
                st.markdown(snack_html, unsafe_allow_html=True)
                snack_to_remove = st.selectbox("간식 삭제 선택", ["선택 안 함"] + current_snacks,
                                               key="snack_remove", label_visibility="collapsed")
                if snack_to_remove != "선택 안 함":
                    if st.button(f"❌ '{snack_to_remove}' 삭제", key="del_snack"):
                        current_snacks = [s for s in current_snacks if s != snack_to_remove]
                        current_user["meals"][today_str] = {**today_meals, "snacks": current_snacks}
                        update_user(data, current_user)
                        save_data(data)
                        st.rerun()

            if add_snack_btn and new_snack.strip():
                current_snacks = current_snacks + [new_snack.strip()]

            if st.button("💾 식단 저장", type="primary", use_container_width=True, key="save_meal"):
                current_user["meals"][today_str] = {
                    "breakfast": breakfast, "lunch": lunch,
                    "dinner": dinner, "snacks": current_snacks
                }
                update_user(data, current_user)
                save_data(data)
                st.success("✅ 오늘의 식단이 저장되었습니다!")
                st.rerun()


    # ════════════════════════════════════════════════════════
    # 탭2: 내 피드 (조건1: 내가 올린 식단 전체 보기)
    # ════════════════════════════════════════════════════════
    with tab2:
        st.markdown("#### 📋 내 식단 기록")
        st.caption("내가 기록한 모든 날의 식단이에요")

        my_meals = current_user.get("meals", {})
        weight_history = current_user.get("weightHistory", {})

        if not my_meals:
            st.info("아직 기록된 식단이 없어요. 내 페이지에서 식단을 입력해보세요! 🥗")
        else:
            # 날짜 내림차순 정렬 (최신 날짜가 위)
            sorted_dates = sorted(my_meals.keys(), reverse=True)

            for date in sorted_dates:
                meal = my_meals[date]
                day_weight = weight_history.get(date)
                is_today = (date == today_str)

                # 날짜 라벨
                date_label = f"📅 {date}" + (" ← 오늘" if is_today else "")

                with st.container(border=True):
                    # 날짜 + 몸무게
                    dh1, dh2 = st.columns([3, 1])
                    with dh1:
                        st.markdown(f'<span class="my-feed-date">{date_label}</span>', unsafe_allow_html=True)
                    with dh2:
                        if day_weight:
                            st.markdown(f'<div style="text-align:right;color:#2d6a2d;font-weight:700;font-size:0.9rem">⚖️ {day_weight}kg</div>', unsafe_allow_html=True)

                    # 식단 내용
                    meal_lines = []
                    if meal.get("breakfast"): meal_lines.append(f"🌅 <b>아침:</b> {meal['breakfast']}")
                    if meal.get("lunch"):     meal_lines.append(f"☀️ <b>점심:</b> {meal['lunch']}")
                    if meal.get("dinner"):    meal_lines.append(f"🌙 <b>저녁:</b> {meal['dinner']}")
                    snacks = meal.get("snacks", [])
                    if snacks:                meal_lines.append(f"🍎 <b>간식:</b> {', '.join(snacks)}")

                    if meal_lines:
                        st.markdown(f'<div class="meal-box">{"<br>".join(meal_lines)}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("식단 내용이 없어요.")

                    # 조건2: 오늘 날짜면 수정 버튼 (매일 새로운 피드 가능)
                    if is_today:
                        st.caption("✏️ 오늘 식단은 '내 페이지'에서 수정할 수 있어요!")


    # ════════════════════════════════════════════════════════
    # 탭3: 순위
    # ════════════════════════════════════════════════════════
    with tab3:
        st.markdown("#### 🏆 다이어트 대결 순위")

        ranked = sorted(data["users"], key=lambda u: u["currentWeight"] - u["initialWeight"])
        medals = ["🥇", "🥈", "🥉"]

        for i, u in enumerate(ranked):
            change = u["currentWeight"] - u["initialWeight"]
            change_str = f"{'+'if change>0 else ''}{change:.1f} kg"
            medal = medals[i] if i < 3 else f"{i+1}위"
            bg = "#fff9e6" if i == 0 else "#f8fdf4"
            is_me = u["id"] == current_user["id"]
            border = "2px solid #4caf50" if is_me else "1.5px solid #d4eebc"
            change_color = "#c0392b" if change < 0 else ("#2980b9" if change > 0 else "#888")

            st.markdown(f"""
            <div class="veggie-card" style="background:{bg};border:{border};">
                <div style="display:flex;align-items:center;gap:14px;">
                    <span style="font-size:1.6rem">{medal}</span>
                    <span style="font-size:2rem">{u['emoji']}</span>
                    <div style="flex:1">
                        <div style="font-weight:700;color:#2d4a1e;font-size:1rem">
                            {u['name']} {"<span style='color:#4caf50;font-size:0.75rem'> ← 나</span>" if is_me else ""}
                        </div>
                        <div style="font-size:0.78rem;color:#6b7b5a">{u['initialWeight']}kg → {u['currentWeight']}kg</div>
                    </div>
                    <div style="font-size:1.1rem;font-weight:800;color:{change_color}">{change_str}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


    # ════════════════════════════════════════════════════════
    # 탭4: 친구 피드
    # ════════════════════════════════════════════════════════
    with tab4:
        st.markdown(f"#### 🌿 친구들의 식단 `{today_str}`")

        others = [u for u in data["users"] if u["id"] != current_user["id"]]

        if not others:
            st.info("아직 다른 참가자가 없어요 🌱")
        else:
            for u in others:
                today_meals_other = u["meals"].get(today_str)
                liked_by   = u.get("likedBy", [])
                is_liked   = current_user["id"] in liked_by
                like_count = len(liked_by)

                with st.container(border=True):
                    uc1, uc2 = st.columns([1, 5])
                    with uc1:
                        st.markdown(f"<span style='font-size:2.2rem'>{u['emoji']}</span>", unsafe_allow_html=True)
                    with uc2:
                        change_u = u["currentWeight"] - u["initialWeight"]
                        st.markdown(f"**{u['name']}**")
                        st.caption(f"{u['currentWeight']}kg (총 변화: {change_u:+.1f}kg)")

                    if today_meals_other:
                        meal_lines = []
                        if today_meals_other.get("breakfast"): meal_lines.append(f"🌅 <b>아침:</b> {today_meals_other['breakfast']}")
                        if today_meals_other.get("lunch"):     meal_lines.append(f"☀️ <b>점심:</b> {today_meals_other['lunch']}")
                        if today_meals_other.get("dinner"):    meal_lines.append(f"🌙 <b>저녁:</b> {today_meals_other['dinner']}")
                        snacks = today_meals_other.get("snacks", [])
                        if snacks: meal_lines.append(f"🍎 <b>간식:</b> {', '.join(snacks)}")
                        st.markdown(f'<div class="meal-box">{"<br>".join(meal_lines)}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("오늘 식단이 아직 없어요.")

                    # 공감 토글
                    lc1, lc2 = st.columns([2, 3])
                    with lc1:
                        like_label = f"💚 공감함 {like_count}" if is_liked else f"🤍 공감 {like_count}"
                        if st.button(like_label, key=f"like_{u['id']}", use_container_width=True):
                            if is_liked:
                                u["likedBy"] = [uid for uid in liked_by if uid != current_user["id"]]
                            else:
                                u["likedBy"] = liked_by + [current_user["id"]]
                            update_user(data, u)
                            save_data(data)
                            st.rerun()
                    with lc2:
                        if is_liked:
                            st.caption("💡 한 번 더 누르면 취소")

                    st.divider()

                    # 댓글 목록
                    for c in u.get("comments", []):
                        st.markdown(f'<div class="comment-bubble"><b style="color:#3a7a2a">{c["author"]}</b>: {c["text"]}</div>', unsafe_allow_html=True)

                    # 댓글 입력
                    cc1, cc2 = st.columns([4, 1])
                    with cc1:
                        comment_text = st.text_input("댓글", placeholder="댓글 달기...",
                                                     label_visibility="collapsed", key=f"comment_input_{u['id']}")
                    with cc2:
                        if st.button("등록", key=f"comment_btn_{u['id']}", use_container_width=True):
                            if comment_text.strip():
                                u.setdefault("comments", []).append({"author": current_user["name"], "text": comment_text.strip()})
                                update_user(data, u)
                                save_data(data)
                                st.rerun()
