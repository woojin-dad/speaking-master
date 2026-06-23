import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from gtts import gTTS
import io
import threading  # 백그라운드 초고속 모듈 유지

# 1. 웹페이지 기본 설정
st.set_page_config(
    page_title="스피킹 마스터",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 🔥 [상하 정렬 + 대왕 아이콘] 이모지를 키우고 글씨를 아래로 내리는 CSS
st.markdown("""
    <style>
    /* 모바일 화면에서 무조건 한 줄(Row)로 배치되도록 강제 고정 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 0px !important;
    }
   
    /* [우측 밀착 비율] 문장 칸(8.3)과 신호등 칸(1.7) 분배 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) { flex: 8.3 1 0% !important; min-width: 0 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) { flex: 1.7 1 0% !important; min-width: 0 !important; }
   
    /* 제목 스타일 */
    .custom-title {
        font-size: 26px !important;
        font-weight: bold !important;
        color: #2c3e50 !important;
        text-align: center !important;
        padding-top: 5px !important;
        padding-bottom: 5px !important;
    }
   
    /* 문장 버튼 자체 크기 강제 고정 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button {
        width: 100% !important;
        text-align: left !important;
        background-color: #2c3e50 !important; /* 진한 남색 배경 */
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 10px !important;
    }
   
    /* 문장 버튼 내부의 글자 확대 (22px) */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button p,
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button div,
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button span,
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button * {
        font-size: 22px !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        line-height: 1.2 !important;
    }
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button:hover * {
        color: #f1c40f !important;
    }
   
    /* [신호등 버튼 정돈] 우측 정렬 및 배경 투명화 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton {
        text-align: right !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button {
        background-color: #ffffff !important;
        border: none !important;
        padding: 2px 0px !important;
        width: 100% !important;
        display: flex !important;
        justify-content: flex-end !important; /* 오른쪽 끝 바짝 밀착 */
        align-items: center !important;
    }
   
    /* 🔍 [상하 정렬 핵심] 버튼 내부 요소를 위아래(column)로 강제 정렬 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button p,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button div,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button span,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button * {
        display: flex !important;
        flex-direction: column !important; /* 💡 위아래로 쌓이게 설정 */
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
        line-height: 1.1 !important;
    }
    
    /* 🔍 위쪽 이모지만 쏙 골라내서 32px 대왕 크기로 확대 */
    .big-emoji {
        font-size: 32px !important; /* 💡 아이콘을 엄청 크게 키웠습니다! */
        margin-bottom: 2px !important;
    }
    
    /* 🔍 아래쪽 상태 글씨는 아담하고 진하게 조절 */
    .sub-text {
        font-size: 11px !important; /* 💡 아래쪽 글씨는 작고 깔끔하게 배치 */
        font-weight: bold !important;
        color: #7f8c8d !important; /* 세련된 회색 톤 */
    }
   
    /* 원어민 듣기 🔊 버튼 스타일 유지 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button[help="audio-btn"] * {
        font-size: 16px !important;
        color: #2c3e50 !important;
        font-weight: bold !important;
        flex-direction: row !important; /* 듣기 버튼은 상하정렬 제외 */
    }
   
    /* 구분선 및 전체 여백 촘촘하게 */
    hr { margin: 6px 0px !important; padding: 0px !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
   
    /* 하단 플랫폼 메뉴 완벽 차단 */
    [data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    footer {visibility: hidden !important; height: 0px !important; padding: 0px !important;}
    header {visibility: hidden !important; height: 0px !important;}
    .stAppDeployButton {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important; visibility: hidden !important;}
    [data-testid="stToolbar"] {display: none !important; visibility: hidden !important;}
    </style>
""", unsafe_allow_html=True)

# 👥 사용자 선택 메뉴
users = ["동탕", "우진"]
selected_user = st.selectbox("👤 학습자를 선택하세요", users)

# 👑 제목 설정
st.markdown(f"<div class='custom-title'>👑 {selected_user}의 스피킹 마스터 👑</div>", unsafe_allow_html=True)
st.write("---")

# 2. 구글 시트 연동 설정
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

user_data_key = f"records_{selected_user}"
user_sheet_key = f"sheet_{selected_user}"

if "last_user" not in st.session_state:
    st.session_state["last_user"] = selected_user

if st.session_state["last_user"] != selected_user:
    if user_data_key in st.session_state:
        del st.session_state[user_data_key]
    st.session_state["last_user"] = selected_user

if user_sheet_key not in st.session_state or st.session_state[user_sheet_key] is None:
    try:
        client = init_gspread()
        st.session_state[user_sheet_key] = client.open("SpeakingMaster").worksheet(selected_user)
    except:
        st.session_state[user_sheet_key] = None

if user_data_key not in st.session_state:
    if st.session_state[user_sheet_key]:
        try:
            st.session_state[user_data_key] = st.session_state[user_sheet_key].get_all_records()
        except:
            st.session_state[user_data_key] = []
    else:
        st.session_state[user_data_key] = []

records = st.session_state[user_data_key]
sheet = st.session_state[user_sheet_key]

# 백그라운드 구글 시트 업데이트 함수 유지
def save_to_google_sheet(sheet_obj, row, col, val):
    if sheet_obj:
        try:
            sheet_obj.update_cell(row, col, str(val))
        except:
            pass

# 3. 화면에 문장 리스트 출력
for i, r in enumerate(records):
    row_idx = i + 2
    
    col1, col2 = st.columns([8.3, 1.7])
    
    with col1:
        state_key = f"show_{selected_user}_{i}"
        if state_key not in st.session_state:
            st.session_state[state_key] = False
            
        is_english = st.session_state[state_key]
        text_content = r['en'] if is_english else r['kr']
        btn_label = f"{r['id']}. {text_content}"
        
        if st.button(btn_label, key=f"sentence_{selected_user}_{i}"):
            st.session_state[state_key] = not st.session_state[state_key]
            st.rerun()
            
    with col2:
        if is_english:
            if st.button("🔊", key=f"audio_{selected_user}_{i}", help="audio-btn"):
                tts = gTTS(text=r['en'], lang='en')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                st.audio(fp, format='audio/mp3', autoplay=True)
        else:
            energy_val = int(r['energy']) if r['energy'] != "" else 0
            
            # 🔍 [구조 변경] HTML 태그를 사용해 아이콘과 글씨를 명확히 위아래로 분리!
            if energy_val == 0:
                status_html = "<span class='big-emoji'>🚨</span><span class='sub-text'>미암기</span>"
            elif energy_val == 1:
                status_html = "<span class='big-emoji'>🔴</span><span class='sub-text'>위험</span>"
            elif energy_val == 2:
                status_html = "<span class='big-emoji'>🟠</span><span class='sub-text'>보통</span>"
            elif energy_val == 3:
                status_html = "<span class='big-emoji'>🟡</span><span class='sub-text'>가물</span>"
            elif energy_val == 4:
                status_html = "<span class='big-emoji'>🟢</span><span class='sub-text'>안심</span>"
            else:
                status_html = "<span class='big-emoji'>👑</span><span class='sub-text'>마스터</span>"
            
            # 💡 버튼 겉모양은 빈 텍스트로 만들고, 내부에 주입된 마크다운 스타일이 상하정렬을 제어
            if st.button(status_html, key=f"bar_touch_{selected_user}_{i}"):
                new_energy = energy_val + 1 if energy_val < 5 else 0
                st.session_state[user_data_key][i]['energy'] = new_energy
                
                # 비동기 백그라운드 처리 유지
                threading.Thread(
                    target=save_to_google_sheet, 
                    args=(sheet, row_idx, 4, new_energy), 
                    daemon=True
                ).start()
                
                st.rerun()
                
    st.write("---")
