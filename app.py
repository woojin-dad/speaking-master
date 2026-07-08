import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from gtts import gTTS
import io
import threading
import base64

# 1. 웹페이지 기본 설정
st.set_page_config(
    page_title="스피킹 마스터",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 💡 모바일 스크린 확대 허용 메타 태그 (원본 유지)
st.markdown("""
    <script>
        var meta = document.createElement('meta');
        meta.name = 'viewport';
        meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
        document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
""", unsafe_allow_html=True)

# 2. 구글 시트 연동 및 실시간 탭 목록 마스터 로직
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

# 👥 메뉴 자동 동적 리스트업 생성
menu_options = []
for name in all_sheet_names:
    menu_options.append(name)
    menu_options.append(f"{name} (우선순위)")

if "selected_menu" not in st.session_state:
    st.session_state["selected_menu"] = menu_options[0]

title_text = f"👑 {st.session_state['selected_menu']}의 스피킹 마스터 👑"
font_size = st.session_state.get("dynamic_font_size", 26)

# 🔥 [레이아웃 및 원본 스타일 CSS]
st.markdown(f"""
    <style>
    /* 앱 전체 가로 스크롤을 방지하기 위한 타이트한 핏 설정 */
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

    div[data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 20px !important;
        width: 100% !important;
    }}
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) {{ flex: 8.5 1 0% !important; min-width: 0 !important; }}
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) {{ flex: 1.5 1 0% !important; min-width: 0 !important; }}
   
    /* 👑 최상단 완벽 밀착 유연 타이틀 */
    .custom-title-container {{
        width: 100% !important;
        text-align: center !important;
        margin-top: 0px !important;
        margin-bottom: 5px !important;
        padding: 6px 0px !important;
        background-color: #f8fafc !important;
        border-radius: 10px !important;
        container-type: inline-size !important;
        overflow: hidden !important;
    }}
    .custom-title {{
        font-size: calc(98vw / ({len(title_text)} * 0.85)) !important;
        font-weight: bold !important;
        color: #2c3e50 !important;
        white-space: nowrap !important;
        display: inline-block !important;
    }}
    @media (min-width: 600px) {{
        .custom-title {{ font-size: 28px !important; }}
    }}

    /* 📻 통합 1. 최상단 전체 무한 라디오 버튼 전용 CSS */
    div.stButton > button[key^="total_relay_btn_"] {{
        background-color: #f0fdf4 !important;
        border: 2px solid #2ecc71 !important;
        border-radius: 12px !important;
        padding: 14px 15px !important;
        width: 100% !important;
        text-align: center !important;
    }}
    div.stButton > button[key^="total_relay_btn_"] p,
    div.stButton > button[key^="total_relay_btn_"] * {{
        color: #15803d !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }}

    /* 🎧 통합 2. 중단 책장별 연속 재생 버튼 전용 CSS */
    div.stButton > button[key^="page_relay_btn_"] {{
        background-color: #f0f9ff !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
        padding: 12px 14px !important;
        width: 100% !important;
        text-align: center !important;
        margin-top: 5px !important;
    }}
    div.stButton > button[key^="page_relay_btn_"] p,
    div.stButton > button[key^="page_relay_btn_"] * {{
        color: #1d4ed8 !important;
        font-size: 17px !important;
        font-weight: bold !important;
    }}
   
    /* 🔤 본문 영어/한국어 문장 버튼 스타일 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button {{
        width: 100% !important;
        text-align: left !important;
        background-color: #2c3e50 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 10px !important;
    }}
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button p,
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button div,
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button span,
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button * {{
        font-size: {font_size}px !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        line-height: 1.2 !important;
    }}
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button:hover * {{
        color: #f1c40f !important;
    }}
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton {{
        text-align: right !important;
        width: 100% !important;
        display: flex !important;
        justify-content: flex-end !important;
    }}
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button {{
        background-color: #ffffff !important;
        border: none !important;
        padding: 0px !important;
        margin: 0px !important;
        width: auto !important;
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
    }}
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button p,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button div,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button span,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button * {{
        font-size: 16px !important;
        white-space: pre-line !important;
        line-height: 1.0 !important;
    }}
   
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button[help="audio-btn"] * {{
        font-size: 16px !important;
        color: #2c3e50 !important;
        font-weight: bold !important;
        line-height: 1.2 !important;
    }}
   
    hr {{ margin: 6px 0px !important; padding: 0px !important; }}
    [data-testid="stStatusWidget"] {{display: none !important; visibility: hidden !important;}}
    footer {{visibility: hidden !important; height: 0px !important; padding: 0px !important;}}
    header {{visibility: hidden !important; height: 0px !important;}}
    .stAppDeployButton {{display: none !important;}}
    </style>
""", unsafe_allow_html=True)

# 🥇 1층: 메인 타이틀
st.markdown(f"<div class='custom-title-container'><div class='custom-title'>{title_text}</div></div>", unsafe_allow_html=True)

# 🥈 2층: [학습 모드 선택 드롭박스 전환] 가로 탭을 제거하여 흔들림 원천 차단
selected_menu = st.selectbox(
    "👤 학습 모드 선택",
    menu_options,
    index=menu_options.index(st.session_state["selected_menu"])
)

if selected_menu != st.session_state["selected_menu"]:
    st.session_state["selected_menu"] = selected_menu
    st.rerun()

real_sheet_name = selected_menu.replace(" (우선순위)", "")
is_priority_mode = "우선순위" in selected_menu

user_data_key = f"records_{real_sheet_name}"
user_sheet_key = f"sheet_{real_sheet_name}"

try:
    st.session_state[user_sheet_key] = spreadsheet.worksheet(real_sheet_name)
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
        'id': r['id'],
        'kr': r['kr'],
        'en': r['en'],
        'energy': e_val
    })

total_sentences = len(all_display_records)
page_size = 100  

if total_sentences > 0:
    page_options = []
    for i in range(0, total_sentences, page_size):
        start_num = i + 1
        end_num = min(i + page_size, total_sentences)
        page_options.append(f"📖 {start_num}~{end_num}번")
else:
    page_options = []

# 🥉 3층: 전체 재생 무한 라디오 버튼
if total_sentences > 0:
    if st.button(f"📻 🔁 {real_sheet_name} 무한 반복 스피킹 라디오", key=f"total_relay_btn_{real_sheet_name}"):
        with st.spinner("⚡ 음성 파일 생성 중..."):
            try:
                relay_audio = io.BytesIO()
                for item in all_display_records:
                    english_sentence = str(item['en']).strip()
                    if english_sentence:
                        tts_part = gTTS(text=english_sentence, lang='en')
                        part_fp = io.BytesIO()
                        tts_part.write_to_fp(part_fp)
                        part_fp.seek(0)
                        relay_audio.write(part_fp.read())
                        relay_audio.write(b'\x00' * 2500)
               
                relay_audio.seek(0)
                audio_base64 = base64.b64encode(relay_audio.read()).decode('utf-8')
               
                audio_html = f"""
                    <audio id="total-radio-player" src="data:audio/mp3;base64,{audio_base64}" controls loop style="width: 100%; margin-top: 10px;"></audio>
                    <script>
                        document.getElementById('total-radio-player').play();
                    </script>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
            except:
                st.error("라디오 컴파일 실패")

# 🏾 4층: [이동할 책장 선택 드롭박스 전환] 가로 탭을 제거하여 흔들림 완전 방지
if total_sentences > 0:
    selected_page_str = st.selectbox("📚 이동할 책장 선택", page_options, key="page_select_drop")
    page_idx = page_options.index(selected_page_str)
    start_idx = page_idx * page_size
    end_idx = start_idx + page_size
    display_records = all_display_records[start_idx:end_idx]
else:
    display_records = []

if is_priority_mode:
    display_records = sorted(display_records, key=lambda x: x['energy'])

if display_records:
    if st.button(f"🎧 선택된 {selected_page_str} 문장 연속 재생 시작", key=f"page_relay_btn_{real_sheet_name}_{page_idx}"):
        with st.spinner("⚡ 음성 결합 중..."):
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
                page_audio_html = f"""
                    <audio id="page-radio-player" src="data:audio/mp3;base64,{page_base64}" controls loop style="width: 100%; margin-top: 10px;"></audio>
                    <script>
                        document.getElementById('page-radio-player').play();
                    </script>
                """
                st.markdown(page_audio_html, unsafe_allow_html=True)
            except:
                st.error("오디오 생성 오류")

# 5층: 글자 크기 조절 슬라이더
new_font_size = st.slider("🔤 문장 글자 크기 조절 (기본값: 26px)", min_value=18, max_value=40, value=font_size, step=1, key="slider_placement")
if new_font_size != font_size:
    st.session_state["dynamic_font_size"] = new_font_size
    st.rerun()

st.write("---")

def save_to_google_sheet(sheet_obj, row, col, val):
    if sheet_obj:
        try:
            sheet_obj.update_cell(row, col, str(val))
        except:
            pass

# 3. 문장 리스트 출력
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
