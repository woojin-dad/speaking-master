import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from gtts import gTTS
import io

# 1. 웹페이지 기본 설정
st.set_page_config(
    page_title="스피킹 마스터",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 🔥 [버그 제로 CSS] HTML 주입을 없애고 순수 텍스트 에너지바를 길쭉하게 늘려 우측 밀착
st.markdown("""
    <style>
    /* 모바일 화면에서 무조건 한 줄(Row)로 배치되도록 강제 고정 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 2px !important; /* 간격을 최소화하여 밀착 */
    }
   
    /* 🔍 [우측 밀착 비율] 문장 칸에 8.4를 주고, 에너지바 칸은 1.6만 주어 맨 오른쪽 끝으로 밀어붙임 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) { flex: 8.4 1 0% !important; min-width: 0 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) { flex: 1.6 1 0% !important; min-width: 0 !important; }
   
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
   
    /* 🔍 [에너지바 버튼 스타일] 테두리를 없애고 우측 정렬 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button {
        background-color: #ffffff !important;
        color: #ff4d4d !important; /* 불타는 빨간색 */
        border: none !important;
        padding: 4px 0px !important;
        width: 100% !important;
        display: flex !important;
        justify-content: flex-end !important; /* 오른쪽 끝으로 밀착 */
        align-items: center !important;
    }
    
    /* 🔍 [세로로 길쭉하게 늘리기] 에너지바 이모지 텍스트 크기를 28px로 키우고 세로 비율 강제 확대 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button * {
        font-size: 28px !important; /* 💡 크기를 확 키워서 세로로 길쭉하게 만듭니다 */
        font-weight: 900 !important;
        letter-spacing: -2px !important; /* 사각형 사이 간격을 촘촘하게 밀착 */
        display: inline-block !important;
        transform: scaleY(1.3) !important; /* 💡 세로 길이만 위아래로 1.3배 더 길쭉하게 늘리는 마법 */
    }
    
    /* 비어있는 사각형(▯)은 은은한 회색으로 보이도록 리셋 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button:not(:hover) {
        text-shadow: none !important;
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

# 3. 화면에 문장 리스트 출력
for i, r in enumerate(records):
    row_idx = i + 2
    
    col1, col2 = st.columns([8.4, 1.6])
    
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
            if st.button("🔊", key=f"audio_{selected_user}_{i}"):
                st.markdown("<style>div[key*='audio_'] > button { background-color: #ffffff !important; border: 1px solid #dcdde1 !important; font-size:16px !important; justify-content:center !important; }</style>", unsafe_allow_html=True)
                tts = gTTS(text=r['en'], lang='en')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                st.audio(fp, format='audio/mp3', autoplay=True)
        else:
            energy_val = int(r['energy']) if r['energy'] != "" else 0
            # 🔍 깨질 위험이 없는 순수 문자 사각형 주입 (▮: 채워짐, ▯: 비어있음)
            rectangles = "▮" * energy_val + "▯" * (5 - energy_val)
            
            # 버튼 텍스트로 안전하게 집어넣어 클릭 감지
            if st.button(rectangles, key=f"bar_touch_{selected_user}_{i}"):
                new_energy = energy_val + 1 if energy_val < 5 else 0
                st.session_state[user_data_key][i]['energy'] = new_energy
                if sheet:
                    try:
                        sheet.update_cell(row_idx, 4, str(new_energy))
                    except:
                        pass
                st.rerun()
                
    st.write("---")
