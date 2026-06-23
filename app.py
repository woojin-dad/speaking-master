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

# 2. 구글 시트 연동
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

try:
    client = init_gspread()
    # 구글 시트 이름을 동탕님의 시트 이름으로 정확히 적어주세요. (대소문자 공백 일치 필수)
    workbook = client.open("SpeakingMaster")
    sheet = workbook.sheet1
    records = sheet.get_all_records()
except Exception as e:
    st.error(f"구글 시트 연결에 실패했습니다. 설정을 확인해주세요. 에러: {e}")
    records = []

# 3. 화면에 문장 리스트 출력
for i, r in enumerate(records):
    row_idx = i + 2
    
    col1, col2, col3 = st.columns([5, 3, 2])
    
    with col1:
        if f"show_{i}" not in st.session_state:
            st.session_state[f"show_{i}"] = False
            
        btn_label = f"{r['id']}. {r['en']}" if st.session_state[f"show_{i}"] else f"{r['id']}. {r['kr']}"
        
        if st.button(btn_label, key=f"sentence_{i}"):
            st.session_state[f"show_{i}"] = not st.session_state[f"show_{i}"]
            st.rerun()
            
    with col2:
        energy_val = int(r['energy']) if r['energy'] != "" else 0
        stars = "★" * energy_val + "☆" * (5 - energy_val)
        st.write(f"<span style='color:#f1c40f; font-size:18px;'>{stars}</span>", unsafe_allow_html=True)
        
    with col3:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("➕", key=f"plus_{i}"):
                current_energy = int(r['energy']) if r['energy'] != "" else 0
                if current_energy < 5:
                    # 최신 표준 문법(update_cell)으로 안정성 확보
                    sheet.update_cell(row_idx, 4, str(current_energy + 1))
                    st.rerun()
        with b2:
            if st.button("➖", key=f"minus_{i}"):
                current_energy = int(r['energy']) if r['energy'] != "" else 0
                if current_energy > 0:
                    sheet.update_cell(row_idx, 4, str(current_energy - 1))
                    st.rerun()
    st.write("")
