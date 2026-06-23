import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from gtts import gTTS
import io
import threading  # 백그라운드 초고속 저장 모듈 유지

# 1. 웹페이지 기본 설정
st.set_page_config(
    page_title="스피킹 마스터",
    layout="wide",  # 가로 100% 와이드 모드 유지
    initial_sidebar_state="collapsed"
)

# 💡 모바일 스크린 확대 허용 메타 태그 유지
st.markdown("""
    <script>
        var meta = document.createElement('meta');
        meta.name = 'viewport';
        meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
        document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
""", unsafe_allow_html=True)

# 🔥 [레이아웃 최적화 CSS] 아이폰 액정 끝 벽면 강제 밀착 스타일 유지
st.markdown("""
    <style>
    .block-container { 
        max-width: 100% !important;
        padding-top: 1rem !important; 
        padding-bottom: 1rem !important;
        padding-left: 10px !important;
        padding-right: 0px !important;
    }

    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 20px !important; 
        width: 100% !important;
    }
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) { flex: 8.5 1 0% !important; min-width: 0 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) { flex: 1.5 1 0% !important; min-width: 0 !important; }
   
    .custom-title {
        font-size: 26px !important;
        font-weight: bold !important;
        color: #2c3e50 !important;
        text-align: center !important;
        padding-top: 5px;
    }
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button {
        width: 100% !important;
        text-align: left !important;
        background-color: #2c3e50 !important; 
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 10px !important;
    }
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button p,
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button div,
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button span,
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button * {
        font-size: 22px !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        line-height: 1.2 !important;
    }
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button:hover * {
        color: #f1c40f !important;
    }
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton {
        text-align: right !important;
        width: 100% !important;
        display: flex !important;
        justify-content: flex-end !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button {
        background-color: #ffffff !important;
        border: none !important;
        padding: 0px !important;
        margin: 0px !important;
        width: auto !important;
        display: flex !important;
        justify-content: flex-end !important; 
        align-items: center !important;
    }
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button p,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button div,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button span,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button * {
        font-size: 16px !important;
        white-space: pre-line !important;
        line-height: 1.0 !important;
        text-align: center !important;
        padding: 0px !important;
        margin: 0px !important;
    }
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button[help="audio-btn"] * {
        font-size: 16px !important;
        color: #2c3e50 !important;
        font-weight: bold !important;
        line-height: 1.2 !important;
    }
   
    hr { margin: 6px 0px !important; padding: 0px !important; }
    [data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    footer {visibility: hidden !important; height: 0px !important; padding: 0px !important;}
    header {visibility: hidden !important; height: 0px !important;}
    .stAppDeployButton {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# 👥 [메뉴 확장] 순서대로 기본 탭과 우선순위 탭을 선택할 수 있도록 구성
menu_options = ["동탕", "동탕 (우선순위)", "우진", "우진 (우선순위)"]
selected_menu = st.selectbox("👤 학습 모드를 선택하세요", menu_options)

# 💡 선택된 메뉴에 따라 실제 구글 시트 탭 이름 매칭 (우선순위도 원본 탭에서 데이터를 가져옴)
if "동탕" in selected_menu:
    real_sheet_name = "동탕"
else:
    real_sheet_name = "우진"

# 우선순위 모드 켜짐 여부 확인
is_priority_mode = "우선순위" in selected_menu

# 👑 제목 설정
st.markdown(f"<div class='custom-title'>👑 {selected_menu}의 스피킹 마스터 👑</div>", unsafe_allow_html=True)
st.write("---")

# 2. 구글 시트 연동 설정
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# 캐시 키는 실제 구글 시트 이름("동탕" 또는 "우진") 기준으로 관리
user_data_key = f"records_{real_sheet_name}"
user_sheet_key = f"sheet_{real_sheet_name}"

if "last_menu" not in st.session_state:
    st.session_state["last_menu"] = selected_menu

# 메뉴가 완전히 바뀌었을 때 데이터를 새로고침하도록 설정
if st.session_state["last_menu"] != selected_menu:
    if "우선순위" in st.session_state["last_menu"] or "우선순위" in selected_menu:
        # 우선순위 모드 진입/이탈 시 화면을 깨끗하게 새로 그리기 위해 캐시 초기화 유도
        pass
    st.session_state["last_menu"] = selected_menu

if user_sheet_key not in st.session_state or st.session_state[user_sheet_key] is None:
    try:
        client = init_gspread()
        st.session_state[user_sheet_key] = client.open("SpeakingMaster").worksheet(real_sheet_name)
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

# 🔍 [구조 혁신] 화면에 뿌려줄 리스트 생성 및 정렬 로직
# 구글 시트 원본 행 번호(original_row_idx)를 기록해두어 정렬되더라도 저장은 구글 시트의 제자리에 정확히 박히게 합니다.
display_records = []
for idx, r in enumerate(records):
    # 각 레코드의 무결성 검사 및 정수 변환
    try:
        e_val = int(r['energy'])
        if e_val > 3: e_val = 3
        elif e_val < 0: e_val = 0
    except:
        e_val = 0
        
    display_records.append({
        'original_index': idx,       # 원본 리스트 내의 위치
        'original_row': idx + 2,     # 구글 시트 실제 행 (Row) 번호
        'id': r['id'],
        'kr': r['kr'],
        'en': r['en'],
        'energy': e_val
    })

# 💡 만약 '우선순위' 메뉴를 선택했다면? 에너지 점수가 낮은 순(0점 빨강 ➡️ 1점 주황...)으로 정렬!
if is_priority_mode:
    display_records = sorted(display_records, key=lambda x: x['energy'])

# 백그라운드 구글 시트 업데이트 함수
def save_to_google_sheet(sheet_obj, row, col, val):
    if sheet_obj:
        try:
            sheet_obj.update_cell(row, col, str(val))
        except:
            pass

# 3. 화면에 문장 리스트 출력
for item in display_records:
    orig_idx = item['original_index']
    row_idx = item['original_row']
    energy_val = item['energy']
    
    col1, col2 = st.columns([8.5, 1.5])
    
    with col1:
        # 고유 키는 원본 데이터의 인덱스를 활용하여 정렬 후에도 상태가 꼬이지 않게 보호
        state_key = f"show_{real_sheet_name}_{orig_idx}"
        if state_key not in st.session_state:
            st.session_state[state_key] = False
            
        is_english = st.session_state[state_key]
        text_content = item['en'] if is_english else item['kr']
        btn_label = f"{item['id']}. {text_content}"
        
        if st.button(btn_label, key=f"sentence_{real_sheet_name}_{orig_idx}"):
            st.session_state[state_key] = not st.session_state[state_key]
            st.rerun()
            
    with col2:
        if is_english:
            if st.button("🔊", key=f"audio_{real_sheet_name}_{orig_idx}", help="audio-btn"):
                tts = gTTS(text=item['en'], lang='en')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                st.audio(fp, format='audio/mp3', autoplay=True)
        else:
            # 수직 이모지 빌딩 구성
            if energy_val == 0:
                color_block_text = "🟥\n🟥\n🟥\n🟥"  # 0점: 미암기 (빨강 4층)
            elif energy_val == 1:
                color_block_text = "🟧\n🟧\n🟧"      # 1점: 위험 (주황 3층)
            elif energy_val == 2:
                color_block_text = "🟨\n🟨"          # 2점: 보통 (노랑 2층)
            else:
                color_block_text = "🟩"              # 3점: 안심 (초록 1층)
            
            if st.button(color_block_text, key=f"bar_touch_{real_sheet_name}_{orig_idx}"):
                new_energy = energy_val + 1 if energy_val < 3 else 0
                
                # 원본 세션 상태 데이터에 즉시 업데이트
                st.session_state[user_data_key][orig_idx]['energy'] = new_energy
                
                # 비동기 백그라운드로 구글 시트 제자리에 정확하게 기록 던지기
                threading.Thread(
                    target=save_to_google_sheet, 
                    args=(sheet, row_idx, 4, new_energy), 
                    daemon=True
                ).start()
                
                st.rerun()
                
    st.write("---")
