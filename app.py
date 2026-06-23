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

# 💡 [핵심 추가] 스마트폰에서 손가락으로 화면을 쭉쭉 확대(Zoom)할 수 있도록 허용하는 메타 태그 주입!
# user-scalable=yes 설정을 주어 모바일 브라우저의 확대 잠금을 강제로 해제합니다.
st.markdown("""
    <script>
        var meta = document.createElement('meta');
        meta.name = 'viewport';
        meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
        document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
""", unsafe_allow_html=True)

# 🔥 [순수 대왕 아이콘 CSS] 스타일 유지
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
   
    /* [우측 밀착 비율] 문장 칸(8.5)과 신호등 칸(1.5) 분배 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) { flex: 8.5 1 0% !important; min-width: 0 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) { flex: 1.5 1 0% !important; min-width: 0 !important; }
   
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
        padding: 4px 0px !important;
        width: 100% !important;
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
    }
   
    /* 아이콘 폰트 크기 32px 대왕 크기 고정 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button p,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button div,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button span,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button * {
        font-size: 32px !important;
        white-space: nowrap !important;
        display: inline-block !important;
    }
   
    /* 원어민 듣기 🔊 버튼 스타일 유지 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button[help="audio-btn"] * {
        font-size: 16px !important;
        color: #2c3e50 !important;
        font-weight: bold !important;
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
    
    col1, col2 = st.columns([8.5, 1.5])
    
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
            
            if energy_val == 0: status_icon = "🚨"
            elif energy_val == 1: status_icon = "🔴"
            elif energy_val == 2: status_icon = "🟠"
            elif energy_val == 3: status_icon = "🟡"
            elif energy_val == 4: status_icon = "🟢"
            else: status_icon = "👑"
            
            if st.button(status_icon, key=f"bar_touch_{selected_user}_{i}"):
                new_energy = energy_val + 1 if energy_val < 5 else 0
                st.session_state[user_data_key][i]['energy'] = new_energy
                
                threading.Thread(
                    target=save_to_google_sheet, 
                    args=(sheet, row_idx, 4, new_energy), 
                    daemon=True
                ).start()
                
                st.rerun()
                
    st.write("---")
