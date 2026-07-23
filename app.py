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

# 💡 모바일 스크린 확대 허용 메타 태그 유지
st.markdown("""
    <script>
        var meta = document.createElement('meta');
        meta.name = 'viewport';
        meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
        document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
""", unsafe_allow_html=True)

# 2. 구글 시트 연동 설정
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# ⚡ [초고속 속도 보장] 서버 로딩 시 딱 1번만 구글 시트 탭 목록을 조회하여 메모리에 상주시킵니다.
@st.cache_resource
def get_sheet_titles():
    try:
        client = init_gspread()
        doc = client.open("SpeakingMaster")
        return [ws.title for ws in doc.worksheets()]
    except:
        return ["동탕"] # 통신 장애 발생 시 기본값 안전 장치

# 👥 메뉴 동적 자동 생성 (실제 시트 탭 목록 연동)
existing_sheets = get_sheet_titles()
menu_options = []
for title in existing_sheets:
    menu_options.append(title)
    menu_options.append(f"{title} (우선순위)")

# 🚨 [세션 증발 버그 차단 1단계]
if "pure_main_menu_box" in st.session_state and st.session_state["pure_main_menu_box"] in menu_options:
    selected_menu = st.session_state["pure_main_menu_box"]
else:
    selected_menu = menu_options[0]

# 🥇 [대장님 주문 100% 반영: 1층 최상단 자리에 타이틀 간판 파이썬 직통 배치!]
st.markdown(f"<div class='custom-title'>👑 {selected_menu}의 스피킹 마스터 👑</div>", unsafe_allow_html=True)
st.write("---")

# 🥈 2층: 학습 모드 선택 상자 안착
st.selectbox("👤 학습 모드를 선택하세요", menu_options, key="pure_main_menu_box")

# 🎯 선택된 메뉴에서 실제 구글 시트 탭 이름과 우선순위 여부 자동 추출
real_sheet_name = selected_menu.replace(" (우선순위)", "").strip()
is_priority_mode = "우선순위" in selected_menu

# 🔤 [동탕 커스텀] 실시간 문장 글자 크기 조절 슬라이더
font_size = st.slider("🔤 문장 글자 크기 조절 (기본값: 26px)", min_value=18, max_value=36, value=26, step=1, key="pure_font_slider")

# 🔥 [레이아웃 최적화 CSS]
st.markdown(f"""
    <style>
    .block-container {{
        max-width: 100% !important;
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 10px !important;
        padding-right: 0px !important;
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
   
    .custom-title {{
        font-size: 26px !important;
        font-weight: bold !important;
        color: #2c3e50 !important;
        text-align: center !important;
        padding-top: 5px;
        margin-top: 10px !important;
    }}

    /* 📻 1. 최상단 무한 반복 라디오 단일 버튼 통합 디자인 (초록색 테두리) */
    div.stButton > button[key^="total_relay_btn_"] {{
        background-color: #f0fdf4 !important;
        border: 2px solid #2ecc71 !important;
        border-radius: 12px !important;
        padding: 14px 15px !important;
        width: 100% !important;
        text-align: center !important;
        margin-bottom: 15px !important;
    }}
    div.stButton > button[key^="total_relay_btn_"] p,
    div.stButton > button[key^="total_relay_btn_"] * {{
        color: #15803d !important;
        font-size: 17px !important;
        font-weight: bold !important;
    }}

    /* 🎧 2. 중단 책장별 연속 듣기 단일 버튼 통합 디자인 (파란색 테두리) */
    div.stButton > button[key^="page_relay_btn_"] {{
        background-color: #f0f9ff !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
        padding: 14px 15px !important;
        width: 100% !important;
        text-align: center !important;
        margin-top: 8px !important;
        margin-bottom: 5px !important;
    }}
    div.stButton > button[key^="page_relay_btn_"] p,
    div.stButton > button[key^="page_relay_btn_"] * {{
        color: #1d4ed8 !important;
        font-size: 16px !important;
        font-weight: bold !important;
    }}
   
    /* 🔤 슬라이더 조절에 따라 실시간으로 변하는 문장 버튼 크기 */
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
        text-align: center !important;
        padding: 0px !important;
        margin: 0px !important;
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

# 구글 시트 데이터 로드
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

# 전체 데이터 가공
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

# 📖 100개 단위로 책장 나누기 로직
total_sentences = len(all_display_records)
page_size = 100  

if total_sentences > 0:
    page_options = []
    for i in range(0, total_sentences, page_size):
        start_num = i + 1
        end_num = min(i + page_size, total_sentences)
        page_options.append(f"📖 책장: {start_num} ~ {end_num}번")
else:
    page_options = []

# 🚀 [동탕 통짜 라디오] 단일 통합 초록 버튼
if total_sentences > 0:
    if st.button(f"📻 🔁 {selected_menu} 전체 문장 반복 재생 시작 (1번 ~ 끝까지)", key=f"total_relay_btn_{real_sheet_name}"):
        with st.spinner("⚡ 전체 문장 취합 중..."):
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
                        var player = document.getElementById('total-radio-player');
                        player.play().catch(function(e) {{ console.log(e); }});
                    </script>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
                st.success("🎶 100번 고개를 넘어 시트 마지막 번호까지 무한 반복하는 진짜 라디오가 시작되었습니다!")
            except Exception as e:
                st.error("라디오 플레이어 컴파일 실패")

# 📚 책장 고르기 본진 레이아웃
if total_sentences > 0:
    selected_page_str = st.selectbox("📚 이동할 책장을 고르세요", page_options, key="pure_page_box")
    page_idx = page_options.index(selected_page_str)
    start_idx = page_idx * page_size
    end_idx = start_idx + page_size
    display_records = all_display_records[start_idx:end_idx]
else:
    display_records = []

if is_priority_mode:
    display_records = sorted(display_records, key=lambda x: x['energy'])

# 🚀 [기능 2] 선택된 책장 문장만 연속 듣기 단일 통합 파란 버튼
if display_records:
    if st.button(f"🎧 {selected_page_str} 문장만 연속 듣기 반복 재생 시작", key=f"page_relay_btn_{real_sheet_name}_{page_idx}"):
        with st.spinner("⚡ 현재 책장 100개 음성 결합 중..."):
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
                st.success(f"🎶 {selected_page_str} 범위 무한 반복 재생이 시작되었습니다!")
            except:
                st.error("오디오 생성 오류")
    st.write("---")

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
