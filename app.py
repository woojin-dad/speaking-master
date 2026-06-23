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

# 🔥 [2안 적용] 가로 100% 문장 배치 + 하단 미니 컨트롤 바 CSS
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
    
    /* 🔍 문장 버튼이 가로 화면을 100% 꽉 채우도록 설정 */
    div.stButton > button {
        width: 100% !important;
        text-align: left !important;
        background-color: #2c3e50 !important; /* 진한 남색 배경 */
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
    }
    
    /* 문장 글자 크기 및 스타일 (22px로 시원하게 확대) */
    div.stButton > button p,
    div.stButton > button div,
    div.stButton > button span,
    div.stButton > button * {
        font-size: 22px !important; 
        font-weight: 900 !important; 
        color: #ffffff !important; 
        line-height: 1.3 !important;
    }
    
    /* ➕, ➖ 조절 미니 버튼 및 듣기 버튼 스타일 (하단 정렬용) */
    div[data-testid="stHorizontalBlock"] .stButton>button {
        background-color: #ffffff !important;
        color: #2c3e50 !important;
        border: 1px solid #dcdde1 !important;
        border-radius: 6px !important;
        padding: 4px 10px !important;
        font-size: 14px !important;
        font-weight: bold !important;
        text-align: center !important;
    }
    
    /* 하단 정렬 구역의 가로 컴포넌트 여백 최소화 */
    div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 10px !important;
        margin-top: -4px !important; /* 문장 바로 아래에 붙도록 조정 */
        padding-left: 5px !important;
    }
    
    /* 구분선 및 전체 여백 촘촘하게 */
    hr { margin: 8px 0px !important; padding: 0px !important; }
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
    
    state_key = f"show_{selected_user}_{i}"
    if state_key not in st.session_state:
        st.session_state[state_key] = False
        
    is_english = st.session_state[state_key]
    text_content = r['en'] if is_english else r['kr']
    
    # 1단계: 문장 버튼을 가로 100% 단독으로 배치
    btn_label = f"{r['id']}. {text_content}"
    if st.button(btn_label, key=f"sentence_{selected_user}_{i}"):
        st.session_state[state_key] = not st.session_state[state_key]
        st.rerun()
        
    # 2단계: 문장 버튼 바로 아래에 조절 바 레이아웃 배치
    energy_val = int(r['energy']) if r['energy'] != "" else 0
    lightning_stars = "⚡" * energy_val + "·" * (5 - energy_val)
    
    # 하단 바 구역 분할 (번개 및 조절 버튼)
    sub_col1, sub_col2, sub_col3 = st.columns([4, 3, 3])
    
    with sub_col1:
        # 번개 표시를 아래쪽에 아담하게 노출
        st.write(f"<div style='color:#ff4d4d; font-size:16px; font-weight:bold; padding-top:4px;'>{lightning_stars}</div>", unsafe_allow_html=True)
        
    with sub_col2:
        if is_english:
            if st.button("🔊 원어민 듣기", key=f"audio_{selected_user}_{i}"):
                tts = gTTS(text=r['en'], lang='en')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                st.audio(fp, format='audio/mp3', autoplay=True)
        else:
            if st.button("➕ 에너지", key=f"plus_{selected_user}_{i}"):
                if energy_val < 5:
                    new_energy = energy_val + 1
                    st.session_state[user_data_key][i]['energy'] = new_energy
                    if sheet:
                        try:
                            sheet.update_cell(row_idx, 4, str(new_energy))
                        except:
                            pass
                    st.rerun()
                    
    with sub_col3:
        if not is_english:
            if st.button("➖ 에너지", key=f"minus_{selected_user}_{i}"):
                if energy_val > 0:
                    new_energy = energy_val - 1
                    st.session_state[user_data_key][i]['energy'] = new_energy
                    if sheet:
                        try:
                            sheet.update_cell(row_idx, 4, str(new_energy))
                        except:
                            pass
                    st.rerun()
                    
    st.write("---")
