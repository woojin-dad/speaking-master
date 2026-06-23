import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# 1. 웹페이지 기본 설정
st.set_page_config(page_title="스피킹 마스터", layout="centered")

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

# 2. 구글 시트 연동 설정 (최초 1회만 실행하도록 강력 캐싱)
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# 세션 상태에 구글 시트 연결 객체 저장 (매번 재연결 방지)
if "gspread_sheet" not in st.session_state:
    try:
        client = init_gspread()
        st.session_state["gspread_sheet"] = client.open("SpeakingMaster").sheet1
    except:
        st.session_state["gspread_sheet"] = None

# 최초 1회만 구글 시트에서 전체 데이터를 긁어와 메모리에 저장
if "records_data" not in st.session_state:
    if st.session_state["gspread_sheet"]:
        try:
            st.session_state["records_data"] = st.session_state["gspread_sheet"].get_all_records()
        except:
            st.session_state["records_data"] = []
    else:
        st.session_state["records_data"] = []

records = st.session_state["records_data"]
sheet = st.session_state["gspread_sheet"]

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
        # 메모리(세션)에 저장된 현재 에너지를 즉시 가져와서 화면에 출력
        energy_val = int(r['energy']) if r['energy'] != "" else 0
        stars = "★" * energy_val + "☆" * (5 - energy_val)
        st.write(f"<span style='color:#f1c40f; font-size:18px;'>{stars}</span>", unsafe_allow_html=True)
        
    with col3:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("➕", key=f"plus_{i}"):
                current_energy = int(r['energy']) if r['energy'] != "" else 0
                if current_energy < 5:
                    new_energy = current_energy + 1
                    # [핵심] 화면 데이터를 '즉시' 업데이트하여 지연 시간 0초로 만듦
                    st.session_state["records_data"][i]['energy'] = new_energy
                    
                    # 구글 시트 저장은 화면 갱신 후에 뒤에서 처리하도록 예외 처리 형태로 던짐
                    if sheet:
                        try:
                            sheet.update_cell(row_idx, 4, str(new_energy))
                        except:
                            pass
                    st.rerun()
        with b2:
            if st.button("➖", key=f"minus_{i}"):
                current_energy = int(r['energy']) if r['energy'] != "" else 0
                if current_energy > 0:
                    new_energy = current_energy - 1
                    # [핵심] 화면 데이터를 '즉시' 업데이트
                    st.session_state["records_data"][i]['energy'] = new_energy
                    
                    if sheet:
                        try:
                            sheet.update_cell(row_idx, 4, str(new_energy))
                        except:
                            pass
                    st.rerun()
    st.write("---")
