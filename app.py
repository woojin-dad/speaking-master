import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# 1. 웹페이지 기본 설정
st.set_page_config(page_title="스피킹 마스터", layout="centered")

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
    </style>
""", unsafe_allow_html=True)

st.title("👑 스피킹 마스터 👑")
st.write("💡 문장을 누르면 영어로 변환됩니다. 잘 안 외워지면 에너지를 조절하세요!")
st.write("---")

# 2. 구글 시트 연동 (스트림릿 보안 비밀번호 기능 활용)
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # 스트림릿 서버에 숨겨둔 json 보안 데이터를 읽어옵니다.
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

try:
    client = init_gspread()
    # 구글 시트 이름을 동탕님의 시트 이름으로 정확히 적어주세요.
    # 만약 시트 이름이 다르면 아래 "SpeakingMaster"를 수정하시면 됩니다.
    sheet = client.open("SpeakingMaster").sheet1
    records = sheet.get_all_records()
except Exception as e:
    st.error(f"구글 시트 연결에 실패했습니다. 설정을 확인해주세요. 에러: {e}")
    records = []

# 3. 화면에 문장 리스트 출력
for i, r in enumerate(records):
    row_idx = i + 2
    
    # 3개의 칸으로 나누기 (문장 칸, 에너지 칸, 조절 버튼 칸)
    col1, col2, col3 = st.columns([5, 3, 2])
    
    with col1:
        # 각 문장별로 토글(열고 닫기) 상태를 기억하기 위한 설정
        if f"show_{i}" not in st.session_state:
            st.session_state[f"show_{i}"] = False
            
        # 버튼 텍스트 설정 (토글 상태에 따라 한글 또는 영어 표시)
        btn_label = f"{r['id']}. {r['en']}" if st.session_state[f"show_{i}"] else f"{r['id']}. {r['kr']}"
        
        if st.button(btn_label, key=f"sentence_{i}"):
            st.session_state[f"show_{i}"] = not st.session_state[f"show_{i}"]
            st.rerun()
            
    with col2:
        # 에너지 수치만큼 별(★) 표시
        energy_val = int(r['energy']) if r['energy'] != "" else 0
        stars = "★" * energy_val + "☆" * (5 - energy_val)
        st.write(f"<span style='color:#f1c40f; font-size:18px;'>{stars}</span>", unsafe_allow_html=True)
        
    with col3:
        # + / - 버튼을 한 줄에 배치
        b1, b2 = st.columns(2)
        with b1:
            if st.button("➕", key=f"plus_{i}"):
                current_energy = int(r['energy']) if r['energy'] != "" else 0
                if current_energy < 5:
                    sheet.update_cell(row_idx, 4, current_energy + 1)
                    st.rerun()
        with b2:
            if st.button("➖", key=f"minus_{i}"):
                current_energy = int(r['energy']) if r['energy'] != "" else 0
                if current_energy > 0:
                    sheet.update_cell(row_idx, 4, current_energy - 1)
                    st.rerun()
    st.write("") # 한 줄 띄우기
