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

# 🔥 [박스 내부 매립형 레이아웃] 문장 박스 안에 막대기와 텍스트를 공존시키는 CSS
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
   
    /* 🔍 문장 버튼 스타일 (가로 100% 꽉 채우고 내부 요소를 양끝 정렬) */
    div.stButton > button {
        width: 100% !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: space-between !important; /* 글자는 왼쪽, 막대기는 오른쪽 끝 */
        background-color: #2c3e50 !important; /* 진한 남색 배경 */
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
    }
   
    /* 버튼 내부의 문장 글자 스타일 */
    div.stButton > button p,
    div.stButton > button div,
    div.stButton > button span,
    div.stButton > button * {
        font-size: 22px !important; 
        font-weight: 900 !important; 
        color: #ffffff !important; 
        line-height: 1.2 !important;
        text-align: left !important;
    }
   
    div.stButton > button:hover * {
        color: #f1c40f !important;
    }
    
    /* 🔍 박스 내부에 그려지는 세로 막대기 스타일 */
    .inner-bar-container {
        display: flex !important;
        gap: 3px !important;
        padding-left: 15px !important; /* 문장 글자와의 최소 간격 확보 */
    }
    .inner-energy-bar {
        width: 6px !important;
        height: 24px !important;
        border-radius: 1px !important;
    }
    .inner-filled { background-color: #ff4d4d !important; } /* 채워진 막대: 빨간색 */
    .inner-empty { background-color: #7f8c8d !important; }  /* 비어있는 막대: 남색 배경에 잘 보이는 어두운 회색 */
    
    /* 원어민 듣기용 미니 버튼 스타일 */
    div[data-testid="stColumn"] .stButton>button {
        background-color: #ffffff !important;
        border: 1px solid #dcdde1 !important;
        padding: 6px !important;
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
    }
    div[data-testid="stColumn"] .stButton>button * {
        font-size: 16px !important;
        color: #2c3e50 !important;
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
    
    state_key = f"show_{selected_user}_{i}"
    if state_key not in st.session_state:
        st.session_state[state_key] = False
        
    is_english = st.session_state[state_key]
    text_content = r['en'] if is_english else r['kr']
    energy_val = int(r['energy']) if r['energy'] != "" else 0
    
    # 💡 영어 모드일 때는 우측에 스피커 버튼을 배치하기 위해 분할, 한국어 모드일 때는 100% 통짜 박스 사용
    if is_english:
        col1, col2 = st.columns([8.5, 1.5])
        with col1:
            btn_label = f"{r['id']}. {text_content}"
            if st.button(btn_label, key=f"sentence_{selected_user}_{i}"):
                st.session_state[state_key] = not st.session_state[state_key]
                st.rerun()
        with col2:
            if st.button("🔊", key=f"audio_{selected_user}_{i}"):
                tts = gTTS(text=r['en'], lang='en')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                st.audio(fp, format='audio/mp3', autoplay=True)
    else:
        # 🔍 한국어 모드일 때는 단 하나의 버튼만 배치 (가로 폭 100% 완전 점유)
        # 문자열 포맷팅을 사용해 버튼 하나 누르면 문장 전환과 에너지 조절을 동시에 처리하는 정교한 트릭 적용
        btn_label = f"{r['id']}. {text_content}"
        
        # 버튼을 생성하고 클릭하면 에너지가 순환(0~5)하며 올라가도록 설정
        if st.button(btn_label, key=f"sentence_block_{selected_user}_{i}"):
            # 💡 한국어 문장 자체를 누르면 에너지가 1씩 올라가고, 5점 만점에서 누르면 0으로 리셋된 후 영어 문장으로 반전!
            if energy_val < 5:
                new_energy = energy_val + 1
                st.session_state[user_data_key][i]['energy'] = new_energy
                if sheet:
                    try:
                        sheet.update_cell(row_idx, 4, str(new_energy))
                    except:
                        pass
            else:
                # 5점 만점일 때 누르면 에너지를 0으로 리셋하고 영어 문장을 보여줌
                st.session_state[user_data_key][i]['energy'] = 0
                if sheet:
                    try:
                        sheet.update_cell(row_idx, 4, "0")
                    except:
                        pass
                st.session_state[state_key] = True
            st.rerun()
            
        # 🔍 [마법의 구역] CSS 절대 좌표를 활용해 문장 박스 안쪽 오른쪽 끝에 막대기 그래픽을 강제로 쑤셔 넣음
        bar_html = "<div class='inner-bar-container'>"
        for b in range(5):
            bar_class = "inner-filled" if b < energy_val else "inner-empty"
            bar_html += f"<div class='inner-energy-bar {bar_class}'></div>"
        bar_html += "</div>"
        
        st.markdown(f"""
            <div style='margin-top: -41px; margin-bottom: 17px; float: right; padding-right: 15px; position: relative; z-index: 999; pointer-events: none;'>
                {bar_html}
            </div>
        """, unsafe_allow_html=True)
                
    st.write("---")
