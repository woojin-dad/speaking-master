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

# 🔥 [가로 공간 제로화] 버튼을 한 줄로 통일하고 가동성을 극대화한 CSS
st.markdown("""
    <style>
    /* 제목 스타일 */
    .custom-title {
        font-size: 26px !important;
        font-weight: bold !important;
        color: #2c3e50 !important;
        text-align: center !important;
        padding-top: 5px !important;
        padding-bottom: 5px !important;
    }
    
    /* 🔍 문장 버튼 내부 레이아웃 정렬 (한글/영어는 왼쪽, 번개와 버튼은 오른쪽) */
    div.stButton > button {
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important; /* 양끝 정렬 */
        background-color: #2c3e50 !important; /* 진한 남색 배경 */
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
    }
    
    /* 문장 글자 크기 및 스타일 (22px로 보기 좋게 최적화) */
    div.stButton > button p,
    div.stButton > button div,
    div.stButton > button span,
    div.stButton > button * {
        font-size: 22px !important; 
        font-weight: 900 !important; 
        color: #ffffff !important; 
        line-height: 1.2 !important;
    }
    
    /* ➕, ➖ 조절 미니 버튼 스타일 (문장 오른쪽에 배치용) */
    .sub-btn {
        background-color: #ffffff !important;
        color: #2c3e50 !important;
        border: 1px solid #dcdde1 !important;
        border-radius: 4px !important;
        padding: 2px 8px !important;
        font-size: 14px !important;
        font-weight: bold !important;
        margin-left: 4px !important;
        cursor: pointer;
    }
    
    /* 번개 이모지 스타일 */
    .energy-display {
        font-size: 16px !important;
        color: #ff4d4d !important; /* 불타는 빨간색 계열 유지 */
        margin-right: 10px !important;
        letter-spacing: 2px;
    }
    
    /* 조절 버튼 구역 크기 고정 */
    div[data-testid="stColumn"] {
        padding: 0px !important;
        margin: 0px !important;
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
    
    # 💡 컬럼 분할을 없애고 1개의 가로 칸으로 통일합니다!
    col1, col2 = st.columns([8.2, 1.8])
    
    with col1:
        state_key = f"show_{selected_user}_{i}"
        if state_key not in st.session_state:
            st.session_state[state_key] = False
            
        is_english = st.session_state[state_key]
        text_content = r['en'] if is_english else r['kr']
        
        # 에너지 번개 및 미 점수 세팅
        energy_val = int(r['energy']) if r['energy'] != "" else 0
        lightning_stars = "⚡" * energy_val + "·" * (5 - energy_val)
        
        # 버튼 하나로 통합 구현
        btn_label = f"{r['id']}. {text_content}"
        if st.button(btn_label, key=f"sentence_{selected_user}_{i}"):
            st.session_state[state_key] = not st.session_state[state_key]
            st.rerun()
            
    with col2:
        # 가로 공간을 방해하지 않도록 맨 우측에 번개와 조절 버튼을 수직 배치
        if is_english:
            if st.button("🔊", key=f"audio_{selected_user}_{i}"):
                tts = gTTS(text=r['en'], lang='en')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                st.audio(fp, format='audio/mp3', autoplay=True)
        else:
            # ➕, ➖ 버튼 세로 미니 배치
            st.write(f"<div style='color:#ff4d4d; font-size:13px; text-align:center;'>{lightning_stars}</div>", unsafe_allow_html=True)
            b1, b2 = st.columns(2)
            with b1:
                if st.button("+", key=f"plus_{selected_user}_{i}"):
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
                if st.button("-", key=f"minus_{selected_user}_{i}"):
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
