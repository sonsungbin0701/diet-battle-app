"""
🥦 다이어트 대결 앱 - Streamlit + Supabase 최종 버전
실행 방법: streamlit run diet_battle_app.py
"""

import streamlit as st
from datetime import datetime, timedelta
from supabase import create_client
import uuid

# ─────────────────────────────────────────────────────────────────
SUPABASE_URL = "https://qdjupvyeiqfwrgdxevph.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkanVwdnllaXFmd3JnZHhldnBoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA4MjcwNTgsImV4cCI6MjA5NjQwMzA1OH0.0A-JEDucci-hsAY4QSBN5zN7OPTTrx-gksDmBI1NVHU"
BUCKET_NAME  = "nuga-bar"
ADMIN_USERNAMES = {"hyoon", "dbsk", "손성빈"}
VEGGIE_EMOJIS = ["🥦","🥕","🍅","🥑","🍋","🥝","🍇","🥬","🌽","🍓","🫐","🥭"]
ALL_EMOJIS = ["🥦","🥕","🍅","🥑","🍋","🥝","🍇","🥬","🌽","🍓","🫐","🥭",
              "🍊","🍎","🍐","🍑","🍒","🍌","🍉","🍈","🍆","🧅","🧄","🌶️",
              "🥒","🌿","🌱","🎋","🎍","🍀","🌾","🥜","🫘","🫑","🥔","🌰"]
# ─────────────────────────────────────────────────────────────────

def sb(): return create_client(SUPABASE_URL, SUPABASE_KEY)
def fmt(d): return d.strftime("%Y-%m-%d")
def prev_day(s): return fmt(datetime.strptime(s,"%Y-%m-%d")-timedelta(days=1))
def next_day(s): return fmt(datetime.strptime(s,"%Y-%m-%d")+timedelta(days=1))
def is_admin(u): return u and u.get("username") in ADMIN_USERNAMES

# ── DB helpers ────────────────────────────────────────────────────
def db_all_users():
    return sb().table("users").select("*").execute().data or []

def db_user_by_username(u):
    r = sb().table("users").select("*").eq("username",u).execute()
    return r.data[0] if r.data else None

def db_user_by_id(uid):
    r = sb().table("users").select("*").eq("id",uid).execute()
    return r.data[0] if r.data else None

def db_create_user(u):
    sb().table("users").insert(u).execute()

def db_update_user(uid, fields):
    sb().table("users").update(fields).eq("id",uid).execute()

def db_get_meal(user_id, date):
    r = sb().table("meals").select("*").eq("user_id",user_id).eq("date",date).execute()
    return r.data[0] if r.data else None

def db_all_meals(user_id):
    return sb().table("meals").select("*").eq("user_id",user_id).order("date",desc=True).execute().data or []

def db_save_meal(user_id, date, breakfast, lunch, dinner, snacks, photo_url=""):
    existing = db_get_meal(user_id, date)
    d = {"user_id":user_id,"date":date,"breakfast":breakfast,
         "lunch":lunch,"dinner":dinner,"snacks":snacks,"photo_url":photo_url}
    if existing:
        sb().table("meals").update(d).eq("user_id",user_id).eq("date",date).execute()
    else:
        sb().table("meals").insert(d).execute()

def db_delete_meal(user_id, date):
    sb().table("meals").delete().eq("user_id",user_id).eq("date",date).execute()

def db_weight_history(user_id):
    return sb().table("weight_history").select("*").eq("user_id",user_id).order("date",desc=True).execute().data or []

def db_save_weight(user_id, date, weight):
    r = sb().table("weight_history").select("*").eq("user_id",user_id).eq("date",date).execute()
    if r.data:
        sb().table("weight_history").update({"weight":weight}).eq("user_id",user_id).eq("date",date).execute()
    else:
        sb().table("weight_history").insert({"user_id":user_id,"date":date,"weight":weight}).execute()

def db_comments(target_uid):
    return sb().table("comments").select("*").eq("target_user_id",target_uid).order("created_at").execute().data or []

def db_add_comment(target_uid, author, text):
    sb().table("comments").insert({"target_user_id":target_uid,"author":author,"text":text}).execute()

def db_toggle_like(target_uid, my_uid):
    u = db_user_by_id(target_uid)
    liked = u.get("liked_by") or []
    liked = [x for x in liked if x!=my_uid] if my_uid in liked else liked+[my_uid]
    db_update_user(target_uid,{"liked_by":liked})

def db_send_friend_request(from_id, to_id):
    existing = sb().table("friend_requests").select("*").eq("from_user_id",from_id).eq("to_user_id",to_id).execute().data
    if not existing:
        sb().table("friend_requests").insert({"from_user_id":from_id,"to_user_id":to_id,"status":"pending"}).execute()

def db_get_friend_requests(user_id):
    return sb().table("friend_requests").select("*").eq("to_user_id",user_id).eq("status","pending").execute().data or []

def db_accept_friend(req_id, from_id, to_id):
    sb().table("friend_requests").update({"status":"accepted"}).eq("id",req_id).execute()
    sb().table("friends").insert({"user_id":from_id,"friend_id":to_id}).execute()
    sb().table("friends").insert({"user_id":to_id,"friend_id":from_id}).execute()

def db_get_friends(user_id):
    r = sb().table("friends").select("*").eq("user_id",user_id).execute().data or []
    return [f["friend_id"] for f in r]

def db_is_friend(user_id, other_id):
    r = sb().table("friends").select("*").eq("user_id",user_id).eq("friend_id",other_id).execute().data
    return bool(r)

def db_is_request_sent(from_id, to_id):
    r = sb().table("friend_requests").select("*").eq("from_user_id",from_id).eq("to_user_id",to_id).eq("status","pending").execute().data
    return bool(r)

def db_suspend_user(user_id, days, reason):
    until = datetime.now() + timedelta(days=days)
    db_update_user(user_id, {"is_suspended": True})
    existing = sb().table("suspensions").select("*").eq("user_id",user_id).execute().data
    if existing:
        sb().table("suspensions").update({"suspended_until":until.isoformat(),"reason":reason}).eq("user_id",user_id).execute()
    else:
        sb().table("suspensions").insert({"user_id":user_id,"suspended_until":until.isoformat(),"reason":reason}).execute()

def db_unsuspend_user(user_id):
    db_update_user(user_id, {"is_suspended": False})

def db_get_suspension(user_id):
    r = sb().table("suspensions").select("*").eq("user_id",user_id).execute().data
    return r[0] if r else None

def is_suspended(user):
    if not user.get("is_suspended"): return False
    susp = db_get_suspension(user["id"])
    if not susp: return False
    until = datetime.fromisoformat(susp["suspended_until"])
    if datetime.now() > until:
        db_unsuspend_user(user["id"])
        return False
    return True

def upload_photo(file, user_id, date, idx=0):
    ext = file.name.split(".")[-1]
    path = f"{user_id}/{date}_{idx}.{ext}"
    sb().storage.from_(BUCKET_NAME).upload(path, file.read(), {"content-type": file.type, "upsert": "true"})
    url = sb().storage.from_(BUCKET_NAME).get_public_url(path)
    return url


# ── 페이지 설정 ───────────────────────────────────────────────────
st.set_page_config(page_title="🥦 다이어트 대결", page_icon="🥦", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Nanum Gothic', sans-serif; }
.stApp { background: linear-gradient(135deg, #e8f5e2 0%, #fff9e6 50%, #fde8f0 100%); }
.app-title { font-size: 1.8rem; font-weight: 800; color: #2d6a2d; text-align: center; letter-spacing: 1px; padding: 8px 0 2px; }
.app-sub { text-align: center; color: #7a9a5a; letter-spacing: 3px; font-size: 0.72rem; margin-bottom: 8px; }
.meal-box { background: #f4fbef; border-radius: 10px; padding: 10px 14px; margin: 8px 0; border: 1px solid #d0ecc0; line-height: 2; font-size: 0.88rem; }
.meal-compact { background: #f4fbef; border-radius: 10px; padding: 8px 14px; margin: 8px 0; border: 1px solid #d0ecc0; font-size: 0.85rem; }
.comment-item { background: #f0fbe8; border-radius: 10px; padding: 7px 12px; margin-bottom: 5px; font-size: 0.83rem; color: #3a5a1e; border: 1px solid #d0ecc0; }
.snack-tag { display: inline-flex; align-items: center; gap: 4px; background: #e2f7d4; border: 1px solid #a8d890; border-radius: 20px; padding: 2px 10px; font-size: 0.8rem; color: #2d6a2d; margin: 2px; }
.err-box { background: #ffe8e8; border: 1.5px solid #f0b0b0; border-radius: 10px; padding: 9px 13px; color: #c0392b; font-size: 0.85rem; margin-bottom: 10px; }
.test-banner { background: linear-gradient(135deg, #fff3cd, #ffe08a); border: 1.5px solid #f0c040; border-radius: 10px; padding: 7px 13px; font-size: 0.8rem; color: #7a5500; font-weight: 700; text-align: center; }
.date-badge { background: #e8f5e2; border-radius: 8px; padding: 3px 10px; font-size: 0.76rem; color: #4a7a2a; font-weight: 700; display: inline-block; margin-bottom: 6px; }
.admin-badge { background: #2d6a2d; color: white; border-radius: 6px; padding: 1px 7px; font-size: 0.68rem; font-weight: 700; margin-left: 6px; }
.suspend-banner { background: #ffe8e8; border: 2px solid #f0b0b0; border-radius: 12px; padding: 16px; text-align: center; color: #c0392b; }
.agree-box { background: rgba(255,255,255,0.9); border: 1.5px solid #d4eebc; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; font-size: 0.82rem; line-height: 1.7; color: #3a5a1e; max-height: 120px; overflow-y: auto; }
.agree-title { font-weight: 800; color: #2d6a2d; font-size: 0.88rem; margin-bottom: 6px; }
.stButton > button { border-radius: 10px !important; font-family: 'Nanum Gothic', sans-serif !important; font-weight: 700 !important; }
hr { border-color: #d4eebc !important; margin: 10px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────
for k,v in [("session_id",None),("auth_page","login"),("auth_error",""),
            ("sim_date",fmt(datetime.today())),("feed_compact",False),
            ("snack_list",[]),("snack_date",""),("show_photo",{})]:
    if k not in st.session_state:
        st.session_state[k] = v

today_str    = st.session_state.sim_date
yesterday_str= prev_day(today_str)
current_user = db_user_by_id(st.session_state.session_id) if st.session_state.session_id else None
admin        = is_admin(current_user)

# ── 헤더 ─────────────────────────────────────────────────────────
st.markdown('<div class="app-title">🥦 다이어트 대결</div>', unsafe_allow_html=True)
st.markdown('<div class="app-sub">VEGGIE BATTLE</div>', unsafe_allow_html=True)
st.divider()

if admin:
    c1,c2 = st.columns([3,1])
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

    # ── 로그인 ────────────────────────────────────────────────────
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
                elif is_suspended(found):
                    susp = db_get_suspension(found["id"])
                    until = datetime.fromisoformat(susp["suspended_until"]).strftime("%Y-%m-%d %H:%M")
                    st.session_state.auth_error = f"계정이 정지되었습니다. 정지 해제: {until}\n사유: {susp.get('reason','')}"
                else:
                    st.session_state.session_id = found["id"]
                    st.session_state.auth_error = ""
                    st.rerun()
            st.markdown("---")
            c1,c2 = st.columns([2,1])
            with c1: st.caption("계정이 없으신가요?")
            with c2:
                if st.button("회원가입 →", use_container_width=True):
                    st.session_state.auth_page = "signup"
                    st.session_state.auth_error = ""
                    st.rerun()

    # ── 회원가입 ──────────────────────────────────────────────────
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
            weight_public = st.radio("몸무게 공개 설정", ["공개","비공개"], horizontal=True)

            st.markdown("---")
            st.markdown("#### 📋 약관 동의")

            # 약관1: 이용약관
            st.markdown("""
            <div class="agree-title">[필수] 서비스 이용약관</div>
            <div class="agree-box">
            누가바 다이어트 대결 서비스를 이용함에 있어 아래 규칙을 준수합니다.<br>
            • 타인을 비방하거나 불쾌감을 주는 게시물 금지<br>
            • 개인정보 무단 수집 및 공유 금지<br>
            • 운영자의 사전 동의 없이 서비스를 상업적으로 이용 금지<br>
            • <b>운영자는 서비스 운영을 위해 게시물 삭제 및 계정 정지 조치를 취할 수 있음</b><br>
            • 계정 정지 기간(1일~30일) 동안 서비스 이용이 제한될 수 있음<br>
            • 위반 시 운영자가 계정을 영구 삭제할 수 있음
            </div>
            """, unsafe_allow_html=True)
            agree1 = st.checkbox("서비스 이용약관에 동의합니다 (필수)", key="ag1")

            # 약관2: 개인정보
            st.markdown("""
            <div class="agree-title">[필수] 개인정보 수집 및 이용 동의</div>
            <div class="agree-box">
            <b>제공받는 자:</b> 누가바 다이어트 대결 운영자<br>
            <b>이용 목적:</b> 회원 식별, 로그인, 다이어트 기록 관리, 피드 공유, 서비스 운영 및 부정이용 방지<br>
            <b>수집 항목:</b> 아이디, 비밀번호, 닉네임, 몸무게, 식단 기록, 업로드 사진, 계정 정지 이력<br>
            <b>보유 기간:</b> 회원 탈퇴 시까지 보유 후 즉시 파기<br>
            <b>거부 권리:</b> 동의를 거부할 권리가 있으나, 거부 시 서비스 이용이 불가합니다.
            </div>
            """, unsafe_allow_html=True)
            agree2 = st.checkbox("개인정보 수집 및 이용에 동의합니다 (필수)", key="ag2")

            # 약관3: 운영정책
            st.markdown("""
            <div class="agree-title">[필수] 운영 정책 동의</div>
            <div class="agree-box">
            • 운영자는 부적절한 게시물을 사전 고지 없이 삭제할 수 있습니다<br>
            • 운영자는 규칙 위반 시 계정을 일정 기간 정지할 수 있습니다<br>
            • 정지 기간은 위반 정도에 따라 1일 ~ 30일로 결정됩니다<br>
            • 정지된 계정은 정지 기간 동안 로그인이 불가합니다
            </div>
            """, unsafe_allow_html=True)
            agree3 = st.checkbox("운영 정책에 동의합니다 (필수)", key="ag3")

            # 약관4: 만 14세
            agree4 = st.checkbox("본인은 만 14세 이상임을 확인합니다 (필수)", key="ag4")

            # 약관5: 마케팅 (선택)
            st.markdown("""
            <div class="agree-title">[선택] 마케팅 수신 동의</div>
            <div class="agree-box">
            이벤트, 챌린지, 서비스 업데이트 등 유용한 소식을 받아볼 수 있습니다.<br>
            • 동의 거부 시에도 서비스 이용에 불이익 없음<br>
            • 언제든지 설정에서 철회 가능
            </div>
            """, unsafe_allow_html=True)
            agree5 = st.checkbox("마케팅 수신에 동의합니다 (선택)", key="ag5")

            if st.session_state.auth_error:
                st.markdown(f'<div class="err-box">⚠️ {st.session_state.auth_error}</div>', unsafe_allow_html=True)

            if st.button("🌱 가입하고 시작!", use_container_width=True, type="primary"):
                err = ""
                if not new_id.strip():        err = "아이디를 입력해주세요."
                elif not new_pw:              err = "비밀번호를 입력해주세요."
                elif new_pw != new_pw2:       err = "비밀번호가 일치하지 않습니다."
                elif not new_nm.strip():      err = "닉네임을 입력해주세요."
                elif db_user_by_username(new_id.strip()): err = "이미 사용 중인 아이디입니다."
                elif not agree1:              err = "서비스 이용약관에 동의해주세요."
                elif not agree2:              err = "개인정보 수집 및 이용에 동의해주세요."
                elif not agree3:              err = "운영 정책에 동의해주세요."
                elif not agree4:              err = "만 14세 이상 확인이 필요합니다."
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
                        "marketing_agree": agree5,
                        "is_suspended": False,
                        "liked_by": []
                    })
                    db_save_weight(uid, today_str, float(new_wt))
                    st.session_state.session_id = uid
                    st.session_state.auth_error = ""
                    if "signup_emoji" in st.session_state:
                        del st.session_state.signup_emoji
                    st.rerun()

            st.markdown("---")
            c1,c2 = st.columns([2,1])
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
    # 정지 확인
    if is_suspended(current_user):
        susp = db_get_suspension(current_user["id"])
        until = datetime.fromisoformat(susp["suspended_until"]).strftime("%Y-%m-%d %H:%M")
        st.markdown(f"""
        <div class="suspend-banner">
            <div style="font-size:2rem">🚫</div>
            <div style="font-size:1.1rem;font-weight:800;margin:8px 0">계정이 정지되었습니다</div>
            <div>정지 해제 일시: <b>{until}</b></div>
            <div style="margin-top:6px;font-size:0.85rem">사유: {susp.get('reason','')}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("로그아웃"):
            st.session_state.session_id = None
            st.rerun()
        st.stop()

    # 상단
    c1,c2 = st.columns([4,1])
    with c1:
        ab = '<span class="admin-badge">운영자</span>' if admin else ""
        st.markdown(f"**{current_user['emoji']} {current_user['name']}** `@{current_user['username']}`{ab}", unsafe_allow_html=True)
    with c2:
        if st.button("로그아웃", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.auth_page = "login"
            st.rerun()

    # 친구 신청 알림
    requests = db_get_friend_requests(current_user["id"])
    if requests:
        st.info(f"📬 친구 신청 {len(requests)}개가 있어요! '친구' 탭에서 확인하세요.")

    st.divider()

    tabs = st.tabs(["🥕 내 페이지","📋 내 피드","🏆 순위","🌿 친구 피드","👥 친구","🔍 검색"] + (["🔧 운영자"] if admin else []))
    tab_my, tab_feed_me, tab_rank, tab_feed, tab_friends, tab_search = tabs[:6]
    tab_admin = tabs[6] if admin else None


    # ════════════════════════════════════════════════════════
    # 탭1: 내 페이지
    # ════════════════════════════════════════════════════════
    with tab_my:
        # 프로필
        st.markdown(f'<div style="text-align:center;padding:8px 0 10px"><span style="font-size:2.8rem">{current_user["emoji"]}</span><br><b style="font-size:1.2rem;color:#2d4a1e">{current_user["name"]}</b><br><span style="color:#7a9a5a;font-size:0.78rem">@{current_user["username"]}</span></div>', unsafe_allow_html=True)

        # 이모지 변경
        if "show_emoji_picker" not in st.session_state:
            st.session_state.show_emoji_picker = False

        ec1, ec2, ec3 = st.columns([2,1,2])
        with ec2:
            if st.button("🎨 이모지 변경", use_container_width=True):
                st.session_state.show_emoji_picker = not st.session_state.show_emoji_picker

        if st.session_state.show_emoji_picker:
            with st.container(border=True):
                st.markdown("**프로필 이모지 선택**")
                # 한 줄에 8개씩 표시
                rows = [ALL_EMOJIS[i:i+8] for i in range(0, len(ALL_EMOJIS), 8)]
                for row in rows:
                    cols = st.columns(len(row))
                    for j, emoji in enumerate(row):
                        with cols[j]:
                            if st.button(emoji, key=f"emoji_{emoji}"):
                                db_update_user(current_user["id"], {"emoji": emoji})
                                st.session_state.show_emoji_picker = False
                                st.success(f"이모지가 {emoji}로 변경됐어요!")
                                st.rerun()

        st.divider()

        # 몸무게
        st.markdown("#### ⚖️ 몸무게")
        wh_dict = {w["date"]:w["weight"] for w in db_weight_history(current_user["id"])}
        yw = wh_dict.get(yesterday_str)
        cw = current_user["current_weight"]
        iw = current_user["initial_weight"]

        c1,c2 = st.columns(2)
        with c1:
            if yw:
                d = cw-yw
                color = "#c0392b" if d<0 else "#2980b9"
                arrow = "▼" if d<0 else "▲"
                st.markdown(f'<div style="background:rgba(255,255,255,0.9);border-radius:12px;padding:12px;border:1px solid #d4eebc;text-align:center"><div style="font-size:0.72rem;color:#7a9a5a;margin-bottom:4px">📅 전날 대비</div><div style="font-size:1.4rem;font-weight:800;color:{color}">{arrow} {abs(d):.1f} kg</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="background:rgba(255,255,255,0.9);border-radius:12px;padding:12px;border:1px solid #d4eebc;text-align:center"><div style="font-size:0.72rem;color:#7a9a5a;margin-bottom:4px">📅 전날 대비</div><div style="color:#aaa">기록 없음</div></div>', unsafe_allow_html=True)
        with c2:
            total = cw-iw
            tc = "#c0392b" if total<0 else "#2980b9"
            ta = "▼" if total<0 else "▲"
            st.markdown(f'<div style="background:rgba(255,255,255,0.9);border-radius:12px;padding:12px;border:1px solid #d4eebc;text-align:center"><div style="font-size:0.72rem;color:#7a9a5a;margin-bottom:4px">🏁 처음 대비</div><div style="font-size:1.4rem;font-weight:800;color:{tc}">{ta} {abs(total):.1f} kg</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            new_w = st.number_input("오늘 몸무게 (kg)", min_value=30.0, max_value=200.0, value=float(cw), step=0.1, key="wi")
            wp = st.radio("몸무게 공개", ["공개","비공개"], index=0 if current_user.get("weight_public",True) else 1, horizontal=True)
            if st.button("⚖️ 저장", type="primary", use_container_width=True):
                db_update_user(current_user["id"], {"current_weight":float(new_w),"weight_public":wp=="공개"})
                db_save_weight(current_user["id"], today_str, float(new_w))
                st.success(f"✅ {today_str} — {new_w}kg 저장!")
                st.rerun()

        st.divider()

        # 식단
        st.markdown(f"#### 🥗 오늘의 식단 `{today_str}`")
        tm = db_get_meal(current_user["id"], today_str)

        # 간식 session state 초기화
        if st.session_state.snack_date != today_str:
            st.session_state.snack_list = list(tm["snacks"] if tm and tm["snacks"] else [])
            st.session_state.snack_date = today_str

        with st.container(border=True):
            bf  = st.text_input("🌅 아침", value=tm["breakfast"] if tm else "", key="bf")
            lun = st.text_input("☀️ 점심", value=tm["lunch"]    if tm else "", key="lun")
            din = st.text_input("🌙 저녁", value=tm["dinner"]   if tm else "", key="din")

            st.markdown("**🍎 간식**")
            sc1,sc2 = st.columns([3,1])
            with sc1:
                new_snack = st.text_input("간식", placeholder="간식 입력 후 추가", label_visibility="collapsed", key="snack_in")
            with sc2:
                if st.button("+ 추가", key="add_snk"):
                    if new_snack.strip():
                        st.session_state.snack_list.append(new_snack.strip())
                        st.rerun()

            # 조건5: X버튼으로 간식 삭제
            if st.session_state.snack_list:
                cols = st.columns(len(st.session_state.snack_list))
                for i, snack in enumerate(st.session_state.snack_list):
                    with cols[i]:
                        if st.button(f"❌ {snack}", key=f"del_snk_{i}"):
                            st.session_state.snack_list.pop(i)
                            st.rerun()

            # 사진 업로드 (여러 장)
            st.markdown("**📸 사진 (선택, 여러 장 가능)**")
            uploaded_files = st.file_uploader("사진 업로드", type=["jpg","jpeg","png","webp"],
                                              label_visibility="collapsed", key="photo_up",
                                              accept_multiple_files=True)
            # 기존 사진 목록 표시
            existing_photos = []
            if tm and tm.get("photo_url"):
                try:
                    existing_photos = json.loads(tm["photo_url"]) if tm["photo_url"].startswith("[") else [tm["photo_url"]]
                except:
                    existing_photos = [tm["photo_url"]] if tm["photo_url"] else []
            if existing_photos:
                st.caption(f"현재 사진: {len(existing_photos)}장 ✅")

            if st.button("💾 식단 저장", type="primary", use_container_width=True, key="save_meal"):
                photo_urls = existing_photos.copy()
                if uploaded_files:
                    for idx, f in enumerate(uploaded_files):
                        try:
                            url = upload_photo(f, current_user["id"], today_str, len(photo_urls)+idx)
                            photo_urls.append(url)
                        except Exception as e:
                            st.warning(f"사진 업로드 실패: {e}")
                import json as _json
                photo_url_str = _json.dumps(photo_urls) if photo_urls else ""
                db_save_meal(current_user["id"], today_str, bf, lun, din,
                             st.session_state.snack_list, photo_url_str)
                st.success("✅ 식단 저장 완료!")
                st.rerun()


    # ════════════════════════════════════════════════════════
    # 탭2: 내 피드
    # ════════════════════════════════════════════════════════
    with tab_feed_me:
        st.markdown("#### 📋 내 식단 기록")
        wh_dict = {w["date"]:w["weight"] for w in db_weight_history(current_user["id"])}
        all_meals = db_all_meals(current_user["id"])

        if not all_meals:
            st.info("아직 기록된 식단이 없어요 🥗")
        else:
            for meal in all_meals:
                date = meal["date"]
                is_today = (date == today_str)
                dw = wh_dict.get(date)
                with st.container(border=True):
                    dh1,dh2 = st.columns([3,1])
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

                    # 사진 보기 버튼 (여러 장)
                    if meal.get("photo_url"):
                        import json as _json
                        try:
                            photos = _json.loads(meal["photo_url"]) if meal["photo_url"].startswith("[") else [meal["photo_url"]]
                        except:
                            photos = [meal["photo_url"]]
                        photo_key = f"my_photo_{date}"
                        if st.button(f"📸 사진 보기 ({len(photos)}장)", key=photo_key):
                            st.session_state.show_photo[photo_key] = not st.session_state.show_photo.get(photo_key, False)
                        if st.session_state.show_photo.get(photo_key, False):
                            for p in photos:
                                st.image(p, use_column_width=True)


    # ════════════════════════════════════════════════════════
    # 탭3: 순위
    # ════════════════════════════════════════════════════════
    with tab_rank:
        st.markdown("#### 🏆 순위")
        all_users = db_all_users()
        ranked = sorted(all_users, key=lambda u: u["current_weight"]-u["initial_weight"])
        medals = ["🥇","🥈","🥉"]

        for i,u in enumerate(ranked):
            change = u["current_weight"]-u["initial_weight"]
            medal  = medals[i] if i<3 else f"{i+1}위"
            is_me  = u["id"]==current_user["id"]
            bg     = "#fffbe6" if i==0 else "rgba(255,255,255,0.9)"
            border = "2px solid #4caf50" if is_me else "1.5px solid #d4eebc"
            color  = "#c0392b" if change<0 else ("#2980b9" if change>0 else "#888")
            me_tag = " ← 나" if is_me else ""
            at     = " 🔧" if is_admin(u) else ""
            wp     = u.get("weight_public",True)
            if admin or wp or is_me:
                winfo = f"{u['initial_weight']}kg → {u['current_weight']}kg"
            else:
                winfo = "몸무게 비공개 🔒"

            st.markdown(f"""
            <div style="background:{bg};border-radius:14px;padding:12px 16px;margin-bottom:8px;border:{border};display:flex;align-items:center;gap:12px;">
                <span style="font-size:1.5rem;min-width:30px">{medal}</span>
                <span style="font-size:1.8rem">{u['emoji']}</span>
                <div style="flex:1">
                    <div style="font-weight:700;color:#2d4a1e">{u['name']}{at}<span style="color:#4caf50;font-size:0.72rem">{me_tag}</span></div>
                    <div style="font-size:0.76rem;color:#6b7b5a">{winfo}</div>
                </div>
                <div style="font-size:1.1rem;font-weight:800;color:{color}">{"+" if change>0 else ""}{change:.1f}kg</div>
            </div>
            """, unsafe_allow_html=True)


    # ════════════════════════════════════════════════════════
    # 탭4: 친구 피드
    # ════════════════════════════════════════════════════════
    with tab_feed:
        fc1,fc2 = st.columns([3,1])
        with fc1:
            st.markdown(f"#### 🌿 친구 피드 `{today_str}`")
        with fc2:
            cl = "📋 한줄보기" if not st.session_state.feed_compact else "📄 두줄보기"
            if st.button(cl, use_container_width=True, key="feed_toggle"):
                st.session_state.feed_compact = not st.session_state.feed_compact
                st.rerun()

        compact = st.session_state.feed_compact
        friend_ids = db_get_friends(current_user["id"])
        all_users = db_all_users()

        # 친구만 or 운영자는 전체
        if admin:
            feed_users = [u for u in all_users if u["id"] != current_user["id"]]
        else:
            feed_users = [u for u in all_users if u["id"] in friend_ids]

        if not feed_users:
            if admin:
                st.info("아직 다른 참가자가 없어요 🌱")
            else:
                st.info("친구를 추가하면 피드가 보여요! '검색' 탭에서 친구를 찾아보세요 👥")
        else:
            for u in feed_users:
                liked_by   = u.get("liked_by") or []
                is_liked   = current_user["id"] in liked_by
                like_count = len(liked_by)
                other_meal = db_get_meal(u["id"], today_str)
                comments   = db_comments(u["id"])
                wp         = u.get("weight_public",True)

                with st.container(border=True):
                    uh1,uh2 = st.columns([1,5])
                    with uh1:
                        st.markdown(f"<span style='font-size:2rem'>{u['emoji']}</span>", unsafe_allow_html=True)
                    with uh2:
                        cu = u["current_weight"]-u["initial_weight"]
                        at = " 🔧" if is_admin(u) else ""
                        wstr = f"{u['current_weight']}kg (변화: {cu:+.1f}kg)" if (admin or wp) else "몸무게 비공개 🔒"
                        st.markdown(f"**{u['name']}**{at}")
                        st.caption(wstr)

                    if other_meal:
                        lines = []
                        if other_meal.get("breakfast"): lines.append(f"🌅 <b>아침:</b> {other_meal['breakfast']}")
                        if other_meal.get("lunch"):     lines.append(f"☀️ <b>점심:</b> {other_meal['lunch']}")
                        if other_meal.get("dinner"):    lines.append(f"🌙 <b>저녁:</b> {other_meal['dinner']}")
                        snacks = other_meal.get("snacks") or []
                        if snacks: lines.append(f"🍎 <b>간식:</b> {', '.join(snacks)}")
                        if lines:
                            cls = "meal-compact" if compact else "meal-box"
                            sep = "　|　" if compact else "<br>"
                            st.markdown(f'<div class="{cls}">{sep.join(lines)}</div>', unsafe_allow_html=True)

                        # 사진 보기 버튼 (여러 장)
                        if other_meal.get("photo_url"):
                            import json as _json
                            try:
                                photos = _json.loads(other_meal["photo_url"]) if other_meal["photo_url"].startswith("[") else [other_meal["photo_url"]]
                            except:
                                photos = [other_meal["photo_url"]]
                            pk = f"feed_photo_{u['id']}"
                            if st.button(f"📸 사진 보기 ({len(photos)}장)", key=pk):
                                st.session_state.show_photo[pk] = not st.session_state.show_photo.get(pk,False)
                            if st.session_state.show_photo.get(pk,False):
                                for p in photos:
                                    st.image(p, use_column_width=True)
                    else:
                        st.caption("오늘 식단이 아직 없어요.")

                    # 공감
                    lc1,lc2 = st.columns([2,3])
                    with lc1:
                        lbl = f"💚 공감함 {like_count}" if is_liked else f"🤍 공감 {like_count}"
                        if st.button(lbl, key=f"like_{u['id']}", use_container_width=True):
                            db_toggle_like(u["id"], current_user["id"])
                            st.rerun()
                    with lc2:
                        if is_liked: st.caption("한 번 더 누르면 취소")

                    # 운영자 피드 삭제
                    if admin and other_meal:
                        if st.button(f"🗑️ 피드 삭제", key=f"del_feed_{u['id']}", type="secondary"):
                            db_delete_meal(u["id"], today_str)
                            st.success("피드가 삭제됐어요!")
                            st.rerun()

                    # 댓글
                    if comments:
                        st.markdown("---")
                        for c in comments:
                            st.markdown(f'<div class="comment-item"><b style="color:#3a7a2a">{c["author"]}</b>: {c["text"]}</div>', unsafe_allow_html=True)

                    cc1,cc2 = st.columns([4,1])
                    with cc1:
                        ct = st.text_input("댓글", placeholder="댓글 달기...", label_visibility="collapsed", key=f"ci_{u['id']}")
                    with cc2:
                        if st.button("등록", key=f"cb_{u['id']}", use_container_width=True):
                            if ct.strip():
                                db_add_comment(u["id"], current_user["name"], ct.strip())
                                st.rerun()


    # ════════════════════════════════════════════════════════
    # 탭5: 친구 관리
    # ════════════════════════════════════════════════════════
    with tab_friends:
        st.markdown("#### 👥 친구 관리")

        # 받은 친구 신청
        requests = db_get_friend_requests(current_user["id"])
        if requests:
            st.markdown("**📬 받은 친구 신청**")
            for req in requests:
                sender = db_user_by_id(req["from_user_id"])
                if sender:
                    rc1,rc2,rc3 = st.columns([3,1,1])
                    with rc1:
                        st.markdown(f"{sender['emoji']} **{sender['name']}** `@{sender['username']}`")
                    with rc2:
                        if st.button("✅ 수락", key=f"acc_{req['id']}", use_container_width=True):
                            db_accept_friend(req["id"], req["from_user_id"], req["to_user_id"])
                            st.success(f"{sender['name']}님과 친구가 됐어요!")
                            st.rerun()
                    with rc3:
                        if st.button("❌ 거절", key=f"rej_{req['id']}", use_container_width=True):
                            sb().table("friend_requests").update({"status":"rejected"}).eq("id",req["id"]).execute()
                            st.rerun()
            st.divider()

        # 친구 목록
        friend_ids = db_get_friends(current_user["id"])
        st.markdown(f"**친구 {len(friend_ids)}명**")
        if not friend_ids:
            st.caption("아직 친구가 없어요. '검색' 탭에서 친구를 찾아보세요!")
        else:
            all_users = db_all_users()
            friends = [u for u in all_users if u["id"] in friend_ids]
            for f in friends:
                st.markdown(f"{f['emoji']} **{f['name']}** `@{f['username']}`")


    # ════════════════════════════════════════════════════════
    # 탭6: 검색
    # ════════════════════════════════════════════════════════
    with tab_search:
        st.markdown("#### 🔍 유저 검색")
        search_q = st.text_input("닉네임 또는 아이디로 검색", placeholder="검색어 입력...", key="search_q")

        if search_q.strip():
            all_users = db_all_users()
            results = [u for u in all_users
                      if search_q.lower() in u["name"].lower()
                      or search_q.lower() in u["username"].lower()
                      and u["id"] != current_user["id"]]

            if not results:
                st.caption("검색 결과가 없어요.")
            else:
                for u in results:
                    if u["id"] == current_user["id"]: continue
                    is_friend = db_is_friend(current_user["id"], u["id"])
                    is_sent   = db_is_request_sent(current_user["id"], u["id"])
                    with st.container(border=True):
                        sc1,sc2 = st.columns([4,1])
                        with sc1:
                            at = " 🔧" if is_admin(u) else ""
                            st.markdown(f"{u['emoji']} **{u['name']}**{at} `@{u['username']}`")
                        with sc2:
                            if is_friend:
                                st.markdown("✅ 친구")
                            elif is_sent:
                                st.markdown("📨 신청중")
                            else:
                                if st.button("친구 신청", key=f"fr_{u['id']}", use_container_width=True):
                                    db_send_friend_request(current_user["id"], u["id"])
                                    st.success(f"{u['name']}님께 친구 신청을 보냈어요!")
                                    st.rerun()


    # ════════════════════════════════════════════════════════
    # 탭7: 운영자 (운영자만)
    # ════════════════════════════════════════════════════════
    if admin and tab_admin:
        with tab_admin:
            st.markdown("#### 🔧 운영자 패널")

            all_users = db_all_users()
            normal_users = [u for u in all_users if not is_admin(u)]

            st.markdown("**👤 회원 관리**")
            for u in normal_users:
                susp = db_get_suspension(u["id"])
                is_susp = u.get("is_suspended", False)
                with st.container(border=True):
                    uc1,uc2 = st.columns([3,2])
                    with uc1:
                        status = "🚫 정지중" if is_susp else "✅ 정상"
                        st.markdown(f"{u['emoji']} **{u['name']}** `@{u['username']}` {status}")
                        if is_susp and susp:
                            until = datetime.fromisoformat(susp["suspended_until"]).strftime("%Y-%m-%d")
                            st.caption(f"정지 해제: {until} | 사유: {susp.get('reason','')}")
                    with uc2:
                        if is_susp:
                            if st.button("정지 해제", key=f"unsp_{u['id']}", use_container_width=True):
                                db_unsuspend_user(u["id"])
                                st.success(f"{u['name']}님 정지 해제!")
                                st.rerun()
                        else:
                            days_key = f"days_{u['id']}"
                            reason_key = f"reason_{u['id']}"
                            days = st.number_input("정지 일수", min_value=1, max_value=30,
                                                  value=1, key=days_key, label_visibility="collapsed")
                            reason = st.text_input("사유", placeholder="정지 사유 입력",
                                                  key=reason_key, label_visibility="collapsed")
                            if st.button(f"🚫 {days}일 정지", key=f"sp_{u['id']}", use_container_width=True):
                                db_suspend_user(u["id"], days, reason)
                                st.success(f"{u['name']}님을 {days}일 정지했어요!")
                                st.rerun()
