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

# 대시보드 스타일링 (CSS)
st.markdown("""
    <style>
    /* 👑 제목 글씨 크기 조정 및 스타일 */
    .custom-title {
        font-size: 28px;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        padding-bottom: 10px;
    }
    
    /* 문장 버튼 스타일 */
    .stButton>button {
        width: 100%;
        text-align: left;
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #dcdde1;
        border-radius: 10px;
        padding: 14px 18px;
        font-weight: bold;
        line-height: 1.4;
    }
    .stButton>button:hover {
        border-color: #3498db;
        color: #3498db;
    }
    
    /* ➕, ➖ 조절 버튼 및 듣기 버튼 스타일 고정 */
    div[data-testid="stColumn"] .stButton>button {
        padding: 10px 5px;
        text-align: center;
    }
    
    /* 하단 플랫폼 메뉴 완벽 차단 */
    [data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    footer {visibility: hidden !important; height: 0px !important; padding: 0px !important;}
    header {visibility: hidden !important; height: 0px !important;}
    .stAppDeployButton {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important; visibility: hidden !important;}
    [data-testid="stToolbar"] {display: none !important; visibility: hidden !important;}
    </style>
""", unsafe_allow_html=True)

st.title("👑 스피킹 마스터 👑")

# 사용자 선택 메뉴 (타이틀 연동을 위해 위로 배치)
users = ["우진", "동탕"]
selected_user = st.selectbox("👤 학습자를 선택하세요", users)

# 👑 선택한 사용자에 따라 제목이 바뀌도록 설정
st.markdown(f"<div class='custom-title'>👑 {selected_user}의 스피킹 마스터 👑</div>", unsafe_allow_html=True)

st.write(f"💡 **{selected_user}**의 문장 리스트입니다. 문장을 누르면 영어로 변환됩니다.")
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
