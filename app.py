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

# 🔥 [여백 파괴] 문장 박스와 막대기 사이의 공백을 최소화하는 CSS
st.markdown("""
    <style>
    /* 모바일 화면에서 무조건 한 줄(Row)로 배치되도록 강제 고정 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 4px !important; /* 요소 사이의 간격을 4px로 극단적으로 줄임 */
    }
   
    /* 🔍 [비율 대조정] 문장 칸을 7.5로 대폭 늘리고, 막대기와 조절 버튼 칸을 빽빽하게 밀착 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) { flex: 7.5 1 0% !important; min-width: 0 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) { flex: 1.3 1 0% !important; min-width: 0 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) { flex: 1.2 1 0% !important; min-width: 0 !important; }
   
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
   
    /* 마우스 올렸을 때 하이라이트 */
    div.stButton > button:hover * {
        color: #f1c40f !important;
    }
   
    /* ➕, ➖ 조절 버튼 및 듣기 버튼 미니화 */
    div[data-testid="stColumn"]:nth-child(2) .stButton>button,
    div[data-testid="stColumn"]:nth-child(3) .stButton>button {
        background-color: #ffffff !important;
        border: 1px solid #dcdde1 !important;
        padding: 8px 2px !important; /* 가로 패딩을 줄여 공간 확보 */
    }
    div[data-testid="stColumn"]:nth-child(2) .stButton>button *,
    div[data-testid="stColumn"]:nth-child(3) .stButton>button * {
        font-size: 14px !important;
        color: #2c3e50 !important;
        font-weight: normal !important;
    }
    
    /* 직접 그리는 세로 막대기 디자인 컨테이너 */
    .bar-container {
        display: flex !important;
        justify-content: center !important;
        gap: 2px !important; /* 막대기 사이 간격도 촘촘하게 */
        padding-top: 4px !important;
    }
    /* 세로 길이 조절 구역 */
    .energy-bar {
        width: 6px !important;       /* 가로 두께를 살짝 줄여 공간 절약 */
        height: 26px !important;     /* 세로 길이는 웅장하게 유지 */
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
    
    # 💡 비율을 [6.0, 2.2, 1.8]에서 [7.5, 1.3, 1.2]로 획기적으로 조정한 칸 배치!
    col1, col2, col3 = st.columns([7.5, 1.3, 1.2])
    
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
            if st.button("🔊", key=f"audio_{selected_user}_{i}"): # 글자를 '🔊'로 축소하여 밀착 유도
                tts = gTTS(text=r['en'], lang='en')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                st.audio(fp, format='audio/mp3', autoplay=True)
        else:
            energy_val = int(r['energy']) if r['energy'] != "" else 0
            
            bar_html = "<div class='bar-container'>"
            for b in range(5):
                bar_class = "bar-filled" if b < energy_val else "bar-empty"
                bar_html += f"<div class='energy-bar {bar_class}'></div>"
            bar_html += "</div>"
            
            st.write(bar_html, unsafe_allow_html=True)
        
    with col3:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("➕", key=f"plus_{selected_user}_{i}"):
                current_energy = int(r['energy']) if r['energy'] != "" else 0
                if current_energy < 5:
                    new_energy = current_energy + 1
                    st.session_state[user_data_key][i]['energy'] = new_energy
                    if sheet:
                        try:
                            sheet.update_cell(row_idx, 4, str(new_energy))
                        except:
                            pass
                    st.rerun()
        with b2:
            if st.button("➖", key=f"minus_{selected_user}_{i}"):
                current_energy = int(r['energy']) if r['energy'] != "" else 0
                if current_energy > 0:
                    new_energy = current_energy - 1
                    st.session_state[user_data_key][i]['energy'] = new_energy
                    if sheet:
                        try:
                            sheet.update_cell(row_idx, 4, str(new_energy))
                        except:
                            pass
                    st.rerun()
    st.write("---")
