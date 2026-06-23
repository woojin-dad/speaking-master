import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# 1. 웹페이지 기본 설정
st.set_page_config(
    page_title="스피킹 마스터", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 대시보드 스타일링 (CSS)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        text-align: left;
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #dcdde1;
        border-radius: 8px;
        padding: 10px 15px;
        font-weight: bold;
    }
    .stButton>button:hover {
        border-color: #3498db;
        color: #3498db;
    }
    [data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    footer {visibility: hidden !important; height: 0px !important; padding: 0px !important;}
    header {visibility: hidden !important; height: 0px !important;}
    .stAppDeployButton {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important; visibility: hidden !important;}
    [data-testid="stToolbar"] {display: none !important; visibility: hidden !important;}
    </style>
""", unsafe_allow_html=True)

st.title("👑 스피킹 마스터 👑")

# 👥 [핵심] 사용자 선택 메뉴 추가 (구글 시트 탭 이름과 정확히 일치해야 합니다)
users = ["우진", "동탕"]
selected_user = st.selectbox("👤 학습자를 선택하세요", users)

st.write(f"💡 **{selected_user}**의 문장 리스트입니다. 문장을 누르면 영어로 변환됩니다.")
st.write("---")

# 2. 구글 시트 연동 설정
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# 사용자가 바뀔 때마다 해당 탭의 데이터를 새로 고정하기 위해 세션 구조 변경
user_data_key = f"records_{selected_user}"
user_sheet_key = f"sheet_{selected_user}"

if user_sheet_key not in st.session_state or st.session_state[user_sheet_key] is None:
    try:
        client = init_gspread()
        # 선택된 사용자의 이름과 똑같은 '탭(워크시트)'을 엽니다.
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
    
    col1, col2, col3 = st.columns([5, 3, 2])
    
    with col1:
        # 사용자별로 스위칭 버튼 상태 분리
        state_key = f"show_{selected_user}_{i}"
        if state_key not in st.session_state:
            st.session_state[state_key] = False
            
        btn_label = f"{r['id']}. {r['en']}" if st.session_state[state_key] else f"{r['id']}. {r['kr']}"
        
        if st.button(btn_label, key=f"sentence_{selected_user}_{i}"):
            st.session_state[state_key] = not st.session_state[state_key]
            st.rerun()
            
    with col2:
        energy_val = int(r['energy']) if r['energy'] != "" else 0
        stars = "★" * energy_val + "☆" * (5 - energy_val)
        st.write(f"<span style='color:#f1c40f; font-size:18px;'>{stars}</span>", unsafe_allow_html=True)
        
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
