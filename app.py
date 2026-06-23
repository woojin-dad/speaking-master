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

# 🔥 [박스 내부 매립형 CSS] 100% 통짜 버튼 및 내부 양끝 정렬 최적화
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
   
    /* 🔍 문장 버튼이 가로 화면을 100% 꽉 채우고 내부 요소를 양끝으로 배치 */
    div.stButton > button {
        width: 100% !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: space-between !important; /* 글자는 왼쪽, 에너지바는 오른쪽 끝 고정 */
        background-color: #2c3e50 !important; /* 진한 남색 배경 */
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
    }
   
    /* 🔍 문장 버튼 내부의 글자 크기 및 스타일 (22px) */
    div.stButton > button p,
    div.stButton > button div,
    div.stButton > button span {
        font-size: 22px !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        line-height: 1.2 !important;
        text-align: left !important;
        white-space: nowrap !important; /* 문장 기본 줄바꿈 방지 */
    }
    
    /* 🔍 박스 내부 오른쪽에 들어갈 에너지바(텍스트 이모지) 스타일 정의 */
    .inner-bars {
        font-size: 26px !important; /* 대왕 크기 유지 */
        color: #ff4d4d !important; /* 선명한 빨간색 */
        font-weight: 900 !important;
        letter-spacing: -4px !important; /* 사각형 사이 초밀착 */
        white-space: nowrap !important; /* 아이폰에서 절대 줄바꿈 금지 */
        display: inline-block !important;
        transform: scaleY(1.2) !important; /* 세로로 길쭉하게 확장 */
        padding-left: 10px !important;
    }
   
    div.stButton > button:hover * {
        color: #f1c40f !important;
    }
   
    /* 원어민 듣기용 미니 버튼 스타일 */
    .audio-container .stButton > button {
        background-color: #ffffff !important;
        color: #2c3e50 !important;
        border: 1px solid #dcdde1 !important;
        border-radius: 6px !important;
        padding: 4px 12px !important;
        font-size: 14px !important;
        font-weight: bold !important;
        width: auto !important;
        margin-top: 4px !important;
        margin-bottom: 10px !important;
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
    
    # 🔍 세로 직사각형 이모지 세팅
    rectangles = "▮" * energy_val + "▯" * (5 - energy_val)
    
    # 💡 [핵심 연동 개조] 버튼 하나 안에 문장과 에너지바를 HTML로 완벽 결합
    # 양끝 정렬(flex) 규칙 덕분에 문장은 왼쪽, 에너지바는 무조건 오른쪽 끝에 붙습니다.
    button_html = f"""
        <div style='display: flex; justify-content: space-between; align-items: center; width: 100%;'>
            <span>{r['id']}. {text_content}</span>
            <span class='inner-bars'>{rectangles}</span>
        </div>
    """
    
    # 한국어/영어 전환 및 에너지 점수 토글 통합 제어
    if st.button(button_html, key=f"sentence_block_{selected_user}_{i}", unsafe_allow_html=True):
        if is_english:
            # 영어 상태일 때는 누르면 다시 한국어 상태로 리셋
            st.session_state[state_key] = False
        else:
            # 한국어 상태일 때는 누를 때마다 에너지가 1씩 증가 (0 -> 1 -> 5)
            if energy_val < 5:
                new_energy = energy_val + 1
                st.session_state[user_data_key][i]['energy'] = new_energy
                if sheet:
                    try:
                        sheet.update_cell(row_idx, 4, str(new_energy))
                    except:
                        pass
            else:
                # 5칸 만점일 때 한 번 더 누르면 에너지를 0으로 리셋하면서 영어 문장으로 반전!
                st.session_state[user_data_key][i]['energy'] = 0
                if sheet:
                    try:
                        sheet.update_cell(row_idx, 4, "0")
                    except:
                        pass
                st.session_state[state_key] = True
        st.rerun()
        
    # 영어 모드일 때만 문장 바로 밑에 아담하게 '🔊 듣기' 버튼을 제공
    if is_english:
        st.markdown("<div class='audio-container'>", unsafe_allow_html=True)
        if st.button("🔊 원어민 듣기", key=f"audio_{selected_user}_{i}"):
            tts = gTTS(text=r['en'], lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            st.audio(fp, format='audio/mp3', autoplay=True)
        st.markdown("</div>", unsafe_allow_html=True)
                
    st.write("---")
