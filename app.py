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

# 🔥 [최종 완결 CSS] 순수 텍스트 정렬을 지원하는 문장 박스 스타일
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
   
    /* 🔍 문장 버튼이 가로 화면을 100% 꽉 채우도록 정돈 */
    div.stButton > button {
        width: 100% !important;
        text-align: left !important;
        background-color: #2c3e50 !important; /* 진한 남색 배경 */
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
    }
   
    /* 🔍 박스 내부의 모든 텍스트(문장 + 에너지바) 스타일 일괄 지정 */
    div.stButton > button p,
    div.stButton > button div,
    div.stButton > button span,
    div.stButton > button * {
        font-size: 22px !important; /* 동탕님 눈이 편안한 크기 */
        font-weight: 900 !important;
        color: #ffffff !important;
        line-height: 1.2 !important;
        white-space: pre !important; /* 💡 여백 공백(Space)을 압축하지 않고 그대로 유지하는 핵심 규칙 */
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
    
    # 💡 [문자열 마법] HTML 없이 파이썬 계산으로 문장은 왼쪽, 에너지바는 오른쪽 끝에 배치
    # 모바일 표준 해상도 기준(약 26자 공간)으로 문장 뒤에 자동으로 빈 공백을 계산해 채워 넣습니다.
    left_text = f"{r['id']}. {text_content}"
    
    if is_english:
        # 영어일 때는 오디오 버튼이 아래에 따로 있으므로 우측 정렬만 깔끔하게 처리
        btn_label = f"{left_text:<20}{rectangles:>5}"
    else:
        # 한국어일 때는 터치 정렬을 위해 공백을 넉넉히 주어 양끝으로 밀어냅니다.
        btn_label = f"{left_text:<18}   {rectangles:>5}"
    
    # 🔍 에러가 나던 unsafe_allow_html을 완전히 삭제하고 순수 텍스트 라벨로 실행!
    if st.button(btn_label, key=f"sentence_block_{selected_user}_{i}"):
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
