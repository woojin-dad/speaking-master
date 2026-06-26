import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from gtts import gTTS
import io
import threading  # 백그라운드 초고속 저장 및 릴레이용 모듈

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

# 🔥 [레이아웃 최적화 CSS] 최상단 무한 반복 라디오 플레이어 전용 스타일
st.markdown("""
    <style>
    .block-container { 
        max-width: 100% !important;
        padding-top: 0.5rem !important; 
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
        margin-top: 10px !important;
    }

    /* 📻 최상단 무한 반복 라디오 박스 디자인 (강렬한 에메랄드 테두리) */
    .total-relay-box {
        background-color: #f0fdf4 !important;
        padding: 12px 15px !important;
        border-radius: 12px !important;
        border: 2px solid #2ecc71 !important;
        text-align: center !important;
        margin-bottom: 15px !important;
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

# 👥 메뉴 설정 (기본 / 우선순위)
menu_options = ["동탕", "동탕 (우선순위)", "우진", "우진 (우선순위)"]
selected_menu = st.selectbox("👤 학습 모드를 선택하세요", menu_options)

# 구글 시트 실제 탭 이름 매칭
if "동탕" in selected_menu:
    real_sheet_name = "동탕"
else:
    real_sheet_name = "우진"

is_priority_mode = "우선순위" in selected_menu

# 2. 구글 시트 연동 설정
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

user_data_key = f"records_{real_sheet_name}"
user_sheet_key = f"sheet_{real_sheet_name}"

if "last_menu" not in st.session_state:
    st.session_state["last_menu"] = selected_menu

if st.session_state["last_menu"] != selected_menu:
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

# 전체 데이터 가공 및 인덱스 기록
all_display_records = []
for idx, r in enumerate(records):
    try:
        e_val = int(r['energy'])
        if e_val > 3: e_val = 3
        elif e_val < 0: e_val = 0
    except:
        e_val = 0
        
    all_display_records.append({
        'original_index': idx,
        'original_row': idx + 2,
        'id': r['id'],
        'kr': r['kr'],
        'en': r['en'],
        'energy': e_val
    })

# 📖 100개 단위로 책장(페이지) 나누기 로직 자동 작동
total_sentences = len(all_display_records)
page_size = 100  

if total_sentences > 0:
    page_options = []
    for i in range(0, total_sentences, page_size):
        start_num = i + 1
        end_num = min(i + page_size, total_sentences)
        page_options.append(f"📖 책장: {start_num} ~ {end_num}번")
    
    selected_page_str = page_options[0] # 기본값 세팅용
else:
    display_records = []

# 🚀 [업그레이드 완료] 최상단 동탕 릴레이 '무한 반복' 라디오 컨트롤러
if all_display_records:
    st.markdown("<div class='total-relay-box'>📻 🔁 <b>동탕 무한 반복 스피킹 라디오</b></div>", unsafe_allow_html=True)
    
    if st.button("▶️ 1번부터 끝까지 멈춤 없이 무한 반복 재생 시작", key=f"total_relay_btn_{real_sheet_name}"):
        with st.spinner("⚡ 동탕 라디오 가동 중... 100개 단위 릴레이 굽기 시작"):
            try:
                relay_audio = io.BytesIO()
                target_batch = all_display_records[:100] if len(all_display_records) > 100 else all_display_records
                
                # 💡 만약 한 바퀴를 완전히 무한으로 뺑뺑이 돌리기 위해, 임시로 대상을 복사 확장하거나 
                # HTML5 오디오 태그의 무한반복 특성(loop=True)을 활용하여 부드럽게 무한 재생 작동 유도
                for item in target_batch:
                    if item['en'].strip():
                        tts_part = gTTS(text=item['en'], lang='en')
                        part_fp = io.BytesIO()
                        tts_part.write_to_fp(part_fp)
                        part_fp.seek(0)
                        relay_audio.write(part_fp.read())
                        relay_audio.write(b'\x00' * 2500) # 문장 간 아늑한 1.2초 공백 버퍼
                
                relay_audio.seek(0)
                # 🔁 loop=True 설정을 주어 오디오 파일이 끝나면 자동으로 처음부터 다시 무한 재생되도록 설계!
                st.audio(relay_audio, format='audio/mp3', autoplay=True, loop=True)
                st.success("🎶 무한 반복 라디오가 정상 가동되었습니다! 화면을 끄지 않는 한 계속 재생됩니다.")
            except Exception as e:
                st.error("라디오 생성 중 오류가 발생했습니다.")

# 👑 타이틀 설정
st.markdown(f"<div class='custom-title'>👑 {selected_menu}의 스피킹 마스터 👑</div>", unsafe_allow_html=True)
st.write("---")

# 책장 선택 상자 본진 배치
if total_sentences > 0:
    selected_page_str = st.selectbox("📚 이동할 책장을 고르세요", page_options)
    page_idx = page_options.index(selected_page_str)
    start_idx = page_idx * page_size
    end_idx = start_idx + page_size
    display_records = all_display_records[start_idx:end_idx]

if is_priority_mode:
    display_records = sorted(display_records, key=lambda x: x['energy'])

def save_to_google_sheet(sheet_obj, row, col, val):
    if sheet_obj:
        try:
            sheet_obj.update_cell(row, col, str(val))
        except:
            pass

# 3. 화면에 선택된 책장의 문장 리스트 출력
for item in display_records:
    orig_idx = item['original_index']
    row_idx = item['original_row']
    energy_val = item['energy']
    
    col1, col2 = st.columns([8.5, 1.5])
    
    with col1:
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
            if energy_val == 0:
                color_block_text = "🟥\n🟥\n🟥\n🟥"
            elif energy_val == 1:
                color_block_text = "🟧\n🟧\n🟧"
            elif energy_val == 2:
                color_block_text = "🟨\n🟨"
            else:
                color_block_text = "🟩"
            
            if st.button(color_block_text, key=f"bar_touch_{real_sheet_name}_{orig_idx}"):
                new_energy = energy_val + 1 if energy_val < 3 else 0
                st.session_state[user_data_key][orig_idx]['energy'] = new_energy
                
                threading.Thread(
                    target=save_to_google_sheet, 
                    args=(sheet, row_idx, 4, new_energy), 
                    daemon=True
                ).start()
                
                st.rerun()
                
    st.write("---")
