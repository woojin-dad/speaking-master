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

# 🔥 [버튼 최소화 및 터치형 게이지] ➕, ➖를 제거하고 막대기 클릭 스타일을 입힌 CSS
st.markdown("""
    <style>
    /* 모바일 화면에서 무조건 한 줄(Row)로 배치되도록 강제 고정 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 6px !important;
    }
   
    /* 🔍 [공간 효율 극대화] 문장 칸에 8.5를 몰아주고 막대기 칸은 1.5만 차지 */
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
    div.stButton > button {
        width: 100% !important;
        text-align: left !important;
        background-color: #2c3e50 !important; /* 진한 남색 배경 */
        border: none !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
    }
   
    /* 버튼 내부의 모든 글자 텍스트 태그들을 22px로 강제 확대!! */
    div.stButton > button p,
    div.stButton > button div,
    div.stButton > button span,
    div.stButton > button * {
        font-size: 22px !important; 
        font-weight: 900 !important; 
        color: #ffffff !important; 
        line-height: 1.2 !important;
    }
    
    /* 🔍 터치 버튼(세로 막대기 구역) 스타일 투명 껍데기화 */
    div[data-testid="stColumn"]:nth-child(2) .stButton>button {
        background-color: transparent !important;
        border: none !important;
        padding: 0px !important;
        margin: 0px !important;
        width: 100% !important;
        height: 38px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
   
    div.stButton > button:hover * {
        color: #f1c40f !important;
    }
    
    /* 직접 그리는 세로 막대기 디자인 컨테이너 */
    .bar-container {
        display: flex !important;
        justify-content: center !important;
        gap: 3px !important; 
    }
    /* 세로 길이 조절 구역 */
    .energy-bar {
        width: 6px !important;       
        height: 26px !important;     
        border-radius: 1px !important;
    }
    .bar-filled { background-color: #ff4d4d !important; } /* 채워진 칸: 불타는 빨간색 */
    .bar-empty { background-color: #dcdde1 !important; }  /* 비어있는 칸: 은은한 연회색 */
   
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
    
    # 💡 컬럼을 3개에서 2개([8.5, 1.5])로 줄여 가로 폭을 시원하게 통일!
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
            if st.button("🔊", key=f"audio_{selected_user}_{i}"):
                tts = gTTS(text=r['en'], lang='en')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                st.audio(fp, format='audio/mp3', autoplay=True)
        else:
            energy_val = int(r['energy']) if r['energy'] != "" else 0
            
            # HTML로 세로 막대기 그래픽 생성
            bar_html = "<div class='bar-container'>"
            for b in range(5):
                bar_class = "bar-filled" if b < energy_val else "bar-empty"
                bar_html += f"<div class='energy-bar {bar_class}'></div>"
            bar_html += "</div>"
            
            # 🔍 막대기 구역 자체를 하나의 큰 버튼으로 만들어 터치 인식!
            if st.button(bar_html, key=f"bar_touch_{selected_user}_{i}"):
                # 💡 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 다시 0점 순환 구조
                new_energy = energy_val + 1 if energy_val < 5 else 0
                st.session_state[user_data_key][i]['energy'] = new_energy
                if sheet:
                    try:
                        sheet.update_cell(row_idx, 4, str(new_energy))
                    except:
                        pass
                st.rerun()
                
    st.write("---")
