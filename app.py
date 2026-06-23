import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from gtts import gTTS
import io

# 1. 웹페이지 기본 설정 (모바일에서 꽉 차게 보이도록 레이아웃 변경)
st.set_page_config(
    page_title="스피킹 마스터", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 🔥 [모바일 초강력 최적화] 스마트폰에서도 한 줄로 고정하고 여백을 줄이는 CSS
st.markdown("""
    <style>
    /* 1. 모바일 화면에서 무조건 한 줄(Row)로 배치되도록 강제 고정 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 8px !important;
    }
    
    /* 2. 각 요소들의 모바일 가로 비율 강제 분배 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) { flex: 5.5 1 0% !important; min-width: 0 !important; } /* 문장 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) { flex: 2.5 1 0% !important; min-width: 0 !important; } /* 별 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) { flex: 2.0 1 0% !important; min-width: 0 !important; } /* ➕➖ */
    
    /* 3. 제목 글씨 크기 조정 */
    .custom-title {
        font-size: 24px;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        padding-top: 5px;
        padding-bottom: 5px;
    }
    
    /* 4. 문장 버튼 스타일 슬림화 (여백 줄여서 많이 들어가게) */
    .stButton>button {
        width: 100%;
        text-align: left;
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #dcdde1;
        border-radius: 8px;
        padding: 8px 12px; /* 패딩을 줄여 상하 두께를 슬림하게 만들었습니다 */
        font-size: 16px !important; /* 모바일에서 짤리지 않는 최적의 크기 */
        font-weight: bold;
        line-height: 1.3;
    }
    .stButton>button:hover {
        border-color: #3498db;
        color: #3498db;
    }
    
    /* 5. ➕, ➖ 조절 버튼 및 듣기 버튼 미니화 */
    div[data-testid="stColumn"] .stButton>button {
        padding: 6px 4px !important;
        font-size: 14px !important;
        text-align: center;
    }
    
    /* 6. 문장 사이의 구분선(hr)과 전체 여백 촘촘하게 조절 */
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
users = ["우진", "동탕"]
selected_user = st.selectbox("👤 학습자를 선택하세요", users)

# 👑 선택한 사용자에 따라 제목 변경
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
    
    # 가로 배치용 컬럼 생성
    col1, col2, col3 = st.columns([5.5, 2.5, 2])
    
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
            if st.button("🔊 듣기", key=f"audio_{selected_user}_{i}"):
                tts = gTTS(text=r['en'], lang='en')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                st.audio(fp, format='audio/mp3', autoplay=True)
        else:
            energy_val = int(r['energy']) if r['energy'] != "" else 0
            stars = "★" * energy_val + "☆" * (5 - energy_val)
            # 모바일 화면 크기에 맞춰 별 크기를 16px로 소폭 조정하여 한 줄 고정 유도
            st.write(f"<div style='color:#ff4d4d; font-size:16px; text-align:center; padding-top:6px;'>{stars}</div>", unsafe_allow_html=True)
        
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
