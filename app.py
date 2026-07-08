import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from gtts import gTTS
import io
import threading

# 1. 웹페이지 기본 설정 (가장 최상단에 위치)
st.set_page_config(
    page_title="스피킹 마스터",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 💡 모바일 스크린 확대 허용 메타 태그
st.markdown("""
    <script>
        var meta = document.createElement('meta');
        meta.name = 'viewport';
        meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
        document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
""", unsafe_allow_html=True)

# 2. 구글 시트 연동 및 강력한 데이터 캐싱(속도 대폭 향상)
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

try:
    client = init_gspread()
    spreadsheet = client.open("SpeakingMaster")
    all_sheet_names = [ws.title for ws in spreadsheet.worksheets()]
except Exception as e:
    all_sheet_names = ["동탕"]

menu_options = []
for name in all_sheet_names:
    menu_options.append(name)
    menu_options.append(f"{name} (우선순위)")

if "selected_menu" not in st.session_state:
    st.session_state["selected_menu"] = menu_options[0]

title_text = f"👑 {st.session_state['selected_menu']}의 스피킹 마스터 👑"
font_size = st.session_state.get("dynamic_font_size", 26)

# 🔥 [클린 순정 스타일 및 버튼 크기 고정 CSS]
st.markdown(f"""
    <style>
    html, body, [data-testid="stAppViewContainer"], .stApp {{
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }}
    .block-container {{
        max-width: 100% !important;
        padding-top: 0.2rem !important;  
        padding-bottom: 1rem !important;
        padding-left: 10px !important;
        padding-right: 10px !important;
    }}
    .custom-title-container {{
        width: 100% !important;
        text-align: center !important;
        margin-top: 0px !important;
        margin-bottom: 5px !important;
        padding: 8px 0px !important;
        background-color: #f8fafc !important;
        border-radius: 10px !important;
    }}
    .custom-title {{
        font-size: 24px !important;
        font-weight: bold !important;
        color: #2c3e50 !important;
    }}
    @media (min-width: 600px) {{
        .custom-title {{ font-size: 28px !important; }}
    }}
    
    /* 전체 라디오 및 책장 연속 재생 버튼 디자인 */
    div.stButton > button[key^="total_relay_btn_"] {{
        background-color: #f0fdf4 !important; border: 2px solid #2ecc71 !important; border-radius: 12px !important; padding: 14px 15px !important; width: 100% !important;
    }}
    div.stButton > button[key^="total_relay_btn_"] * {{ color: #15803d !important; font-size: 18px !important; font-weight: bold !important; }}
    div.stButton > button[key^="page_relay_btn_"] {{
        background-color: #f0f9ff !important; border: 2px solid #3b82f6 !important; border-radius: 12px !important; padding: 12px 14px !important; width: 100% !important; margin-top: 5px !important;
    }}
    div.stButton > button[key^="page_relay_btn_"] * {{ color: #1d4ed8 !important; font-size: 17px !important; font-weight: bold !important; }}
    
    /* ⚡ 순정 문장 버튼 초고속 전용 커스텀 스타일 */
    div[data-testid="stHorizontalBlock"] {{
        align-items: center !important;
        gap: 10px !important;
    }}
    div[data-testid="stHorizontalBlock"] div.stButton > button {{
        width: 100% !important;
        text-align: left !important;
        background-color: #2c3e50 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 15px !important;
    }}
    div[data-testid="stHorizontalBlock"] div.stButton > button p,
    div[data-testid="stHorizontalBlock"] div.stButton > button * {{
        font-size: {font_size}px !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        line-height: 1.3 !important;
    }}
    /* 에너지 박스 고정 스타일 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button {{
        background-color: transparent !important;
        text-align: right !important;
        padding: 0px !important;
    }}
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button p,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button * {{
        font-size: 16px !important;
        color: #2c3e50 !important;
        font-weight: bold !important;
        white-space: pre-line !important;
        line-height: 1.1 !important;
    }}
    
    [data-testid="stStatusWidget"] {{display: none !important; visibility: hidden !important;}}
    footer, header, .stAppDeployButton {{display: none !important; visibility: hidden !important; height: 0px !important;}}
    </style>
""", unsafe_allow_html=True)

# 🥇 1층: 타이틀 고정
st.markdown(f"<div class='custom-title-container'><div class='custom-title'>{title_text}</div></div>", unsafe_allow_html=True)

# 🥈 2층: 학습 모드 선택
selected_menu = st.selectbox(
    "👤 학습 모드 선택", 
    menu_options, 
    index=menu_options.index(st.session_state["selected_menu"])
)

if selected_menu != st.session_state["selected_menu"]:
    st.session_state["selected_menu"] = selected_menu
    for k in list(st.session_state.keys()):
        if "cached_display_" in k:
            del st.session_state[k]
    st.rerun()

real_sheet_name = st.session_state["selected_menu"].replace(" (우선순위)", "")
is_priority_mode = "우선순위" in st.session_state["selected_menu"]

user_data_key = f"records_{real_sheet_name}"
user_sheet_key = f"sheet_{real_sheet_name}"

if user_sheet_key not in st.session_state or st.session_state[user_sheet_key] is None:
    try: st.session_state[user_sheet_key] = spreadsheet.worksheet(real_sheet_name)
    except: st.session_state[user_sheet_key] = None

if user_data_key not in st.session_state:
    if st.session_state[user_sheet_key]:
        try: st.session_state[user_data_key] = st.session_state[user_sheet_key].get_all_records()
        except: st.session_state[user_data_key] = []
    else:
        st.session_state[user_data_key] = []

records = st.session_state[user_data_key]
sheet = st.session_state[user_sheet_key]

# ⚡ 고속 데이터 캐시 매핑
display_records_cache_key = f"cached_display_{real_sheet_name}"
if display_records_cache_key not in st.session_state:
    all_display_records = []
    for idx, r in enumerate(records):
        if 'id' not in r or 'kr' not in r or 'en' not in r:
            continue
        try:
            e_val = int(r.get('energy', 0))
            if e_val > 3: e_val = 3
            elif e_val < 0: e_val = 0
        except:
            e_val = 0
            
        all_display_records.append({
            'original_index': idx,
            'original_row': idx + 2,
            'id': str(r['id']),
            'kr': str(r['kr']),
            'en': str(r['en']),
            'energy': e_val
        })
    st.session_state[display_records_cache_key] = all_display_records

all_display_records = st.session_state[display_records_cache_key]
total_sentences = len(all_display_records)
page_size = 100  

page_options = []
if total_sentences > 0:
    for i in range(0, total_sentences, page_size):
        page_options.append(f"📖 {i+1}~{min(i+page_size, total_sentences)}번")

# 🥉 3층: 무한 반복 라디오
if total_sentences > 0:
    if st.button(f"📻 🔁 {real_sheet_name} 무한 반복 스피킹 라디오", key=f"total_relay_btn_{real_sheet_name}"):
        with st.spinner("⚡ 라디오 준비 중..."):
            try:
                relay_audio = io.BytesIO()
                for item in all_display_records:
                    en_text = item['en'].strip()
                    if en_text:
                        tts_part = gTTS(text=en_text, lang='en')
                        part_fp = io.BytesIO()
                        tts_part.write_to_fp(part_fp)
                        part_fp.seek(0)
                        relay_audio.write(part_fp.read())
                        relay_audio.write(b'\x00' * 2500)
                relay_audio.seek(0)
                audio_base64 = base64.b64encode(relay_audio.read()).decode('utf-8')
                st.markdown(f'<audio id="total-radio-player" src="data:audio/mp3;base64,{audio_base64}" controls loop style="width: 100%; margin-top: 10px;"></audio><script>document.getElementById("total-radio-player").play();</script>', unsafe_allow_html=True)
            except: st.error("라디오 재생 실패")

# 🏾 4층: 이동할 책장 선택
if total_sentences > 0:
    selected_page_str = st.selectbox("📚 이동할 책장 선택", page_options, key="page_select_drop")
    page_idx = page_options.index(selected_page_str)
    display_records = all_display_records[page_idx*page_size : (page_idx+1)*page_size]
else:
    display_records = []

if is_priority_mode:
    display_records = sorted(display_records, key=lambda x: x['energy'])

# 책장 연속 재생
if display_records:
    if st.button(f"🎧 선택된 {selected_page_str} 문장 연속 재생 시작", key=f"page_relay_btn_{real_sheet_name}_{page_idx}"):
        with st.spinner("⚡ 오디오 합성 중..."):
            try:
                page_audio = io.BytesIO()
                for item in display_records:
                    if item['en'].strip():
                        tts_part = gTTS(text=item['en'], lang='en')
                        part_fp = io.BytesIO()
                        tts_part.write_to_fp(part_fp)
                        part_fp.seek(0)
                        page_audio.write(part_fp.read())
                        page_audio.write(b'\x00' * 2000)
                page_audio.seek(0)
                page_base64 = base64.b64encode(page_audio.read()).decode('utf-8')
                st.markdown(f'<audio id="page-radio-player" src="data:audio/mp3;base64,{page_base64}" controls loop style="width: 100%; margin-top: 10px;"></audio><script>document.getElementById("page-radio-player").play();</script>', unsafe_allow_html=True)
            except: st.error("오디오 재생 실패")

# 5층: 글자 크기 조절
new_font_size = st.slider("🔤 문장 글자 크기 조절 (기본값: 26px)", min_value=18, max_value=40, value=font_size, step=1, key="font_slider")
if new_font_size != font_size:
    st.session_state["dynamic_font_size"] = new_font_size
    st.rerun()

st.write("---")

# ⚡ [백그라운드 비동기 저장 함수] 구글 시트 저장 딜레이를 완벽하게 은닉
def save_to_google_sheet(sheet_obj, row, col, val):
    if sheet_obj:
        try: sheet_obj.update_cell(row, col, str(val))
        except: pass

# 👑 6층: 대망의 100% 무결점 초고속 문장 보드 출력 (스트림릿 100% 순정 정공법)
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
        
        # 문장 버튼 터치 시 즉시 변환
        if st.button(btn_label, key=f"btn_snt_{real_sheet_name}_{orig_idx}"):
            st.session_state[state_key] = not st.session_state[state_key]
            st.rerun()
            
    with col2:
        if is_english:
            # 영어 상태일 때는 오디오 재생 버튼 노출
            if st.button("🔊", key=f"audio_{real_sheet_name}_{orig_idx}"):
                tts = gTTS(text=item['en'], lang='en')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                st.audio(fp, format='audio/mp3', autoplay=True)
        else:
            # 한글 상태일 때는 고속 에너지 게이지 노출
            if energy_val == 0: e_text = "🟥\n🟥\n🟥\n🟥"
            elif energy_val == 1: e_text = "🟧\n🟧\n🟧"
            elif energy_val == 2: e_text = "🟨\n🟨"
            else: e_text = "🟩"
            
            if st.button(e_text, key=f"btn_eng_{real_sheet_name}_{orig_idx}"):
                new_energy = energy_val + 1 if energy_val < 3 else 0
                # 화면 메모리에 즉시 수치 반영 (체감 속도 극대화)
                st.session_state[user_data_key][orig_idx]['energy'] = new_energy
                st.session_state[display_records_cache_key][orig_idx]['energy'] = new_energy
                
                # 구글 시트 저장 명령은 백그라운드 쓰레드로 던져 대기 시간 제거
                threading.Thread(
                    target=save_to_google_sheet, 
                    args=(sheet, row_idx, 4, new_energy), 
                    daemon=True
                ).start()
                st.rerun()
    st.write("---")
