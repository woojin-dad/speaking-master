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

# 💡 모바일 확대 허용 메타 태그
st.markdown("""
    <script>
        var meta = document.createElement('meta');
        meta.name = 'viewport';
        meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
        document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
""", unsafe_allow_html=True)

# 2. 구글 시트 연동
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

# 🔥 [속도 최적화 및 레이아웃 CSS]
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
        padding: 6px 0px !important;
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
    
    /* ⚡ 초고속 반응형 문장판 템플릿 CSS */
    .sentence-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #e2e8f0;
        gap: 15px;
    }}
    .sentence-btn-box {{
        flex: 8.5;
        min-width: 0;
    }}
    .sentence-click-btn {{
        width: 100%;
        text-align: left;
        background-color: #2c3e50;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 15px;
        font-size: {font_size}px;
        font-weight: 900;
        line-height: 1.3;
        cursor: pointer;
        user-select: none;
        -webkit-tap-highlight-color: transparent;
    }}
    .sentence-click-btn:active {{
        background-color: #34495e;
    }}
    .action-box {{
        flex: 1.5;
        display: flex;
        justify-content: flex-end;
        align-items: center;
    }}
    .energy-btn {{
        background: none;
        border: none;
        font-size: 16px;
        cursor: pointer;
        text-align: right;
        white-space: pre-line;
        line-height: 1.1;
        font-weight: bold;
        -webkit-tap-highlight-color: transparent;
    }}
    
    /* 기존 스트림릿 기본 버튼 커스텀 */
    div.stButton > button[key^="total_relay_btn_"] {{
        background-color: #f0fdf4 !important; border: 2px solid #2ecc71 !important; border-radius: 12px !important; padding: 14px 15px !important; width: 100% !important;
    }}
    div.stButton > button[key^="total_relay_btn_"] * {{ color: #15803d !important; font-size: 18px !important; font-weight: bold !important; }}
    div.stButton > button[key^="page_relay_btn_"] {{
        background-color: #f0f9ff !important; border: 2px solid #3b82f6 !important; border-radius: 12px !important; padding: 12px 14px !important; width: 100% !important; margin-top: 5px !important;
    }}
    div.stButton > button[key^="page_relay_btn_"] * {{ color: #1d4ed8 !important; font-size: 17px !important; font-weight: bold !important; }}
    
    [data-testid="stStatusWidget"] {{display: none !important; visibility: hidden !important;}}
    footer, header, .stAppDeployButton {{display: none !important; visibility: hidden !important; height: 0px !important;}}
    </style>
""", unsafe_allow_html=True)

# 🥇 1층: 메인 타이틀 (최상단 고정)
st.markdown(f"<div class='custom-title-container'><div class='custom-title'>{title_text}</div></div>", unsafe_allow_html=True)

# 🥈 2층: 학습 모드 선택
selected_menu = st.selectbox(
    "👤 학습 모드 선택", 
    menu_options, 
    index=menu_options.index(st.session_state["selected_menu"])
)

if selected_menu != st.session_state["selected_menu"]:
    st.session_state["selected_menu"] = selected_menu
    # 메뉴 변경 시 가공 캐시 삭제
    for k in list(st.session_state.keys()):
        if "cached_display_" in k:
            del st.session_state[k]
    st.rerun()

real_sheet_name = st.session_state["selected_menu"].replace(" (우선순위)", "")
is_priority_mode = "우선순위" in st.session_state["selected_menu"]

user_data_key = f"records_{real_sheet_name}"
user_sheet_key = f"sheet_{real_sheet_name}"

if user_sheet_key not in st.session_state or st.session_state[user_sheet_key] is None:
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

# 데이터 메모리 캐시화
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
            'kr': str(r['kr']).replace("'", "\\'").replace('"', '\\"'),
            'en': str(r['en']).replace("'", "\\'").replace('"', '\\"'),
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

# 🥉 3층: 무한 반복 스피킹 라디오
if total_sentences > 0:
    if st.button(f"📻 🔁 {real_sheet_name} 무한 반복 스피킹 라디오", key=f"total_relay_btn_{real_sheet_name}"):
        with st.spinner("⚡ 라디오 튜닝 중..."):
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
            except: st.error("라디오 실패")

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
            except: st.error("오디오 실패")

# 5층: 글자 크기 조절 슬라이더
new_font_size = st.slider("🔤 문장 글자 크기 조절 (기본값: 26px)", min_value=18, max_value=40, value=font_size, step=1, key="font_slider")
if new_font_size != font_size:
    st.session_state["dynamic_font_size"] = new_font_size
    st.rerun()

st.write("---")

# ⚡ [백그라운드 저장용 쿼리 핸들러]
# 사용자가 스마트폰 화면에서 변경한 에너지를 비밀리에 구글 시트에 업데이트하는 창구 역할
query_params = st.query_params
if "action" in query_params and query_params["action"] == "save_energy":
    r_idx = int(query_params.get("row", 0))
    n_eng = int(query_params.get("val", 0))
    if sheet and r_idx > 0:
        try: sheet.update_cell(r_idx, 4, str(n_eng))
        except: pass
    st.query_params.clear()

# ⚡ [초고속 코어] JavaScript 기반 즉시 반응형 문장 렌더러 빌드
html_buffer = []
for item in display_records:
    r_idx = item['original_row']
    o_idx = item['original_index']
    e_val = item['energy']
    
    # 에너지 수치별 초기 텍스트 설정
    if e_val == 0: e_text = "🟥\\n🟥\\n🟥\\n🟥"
    elif e_val == 1: e_text = "🟧\\n🟧\\n🟧"
    elif e_val == 2: e_text = "🟨\\n🟨"
    else: e_text = "🟩"

    html_buffer.append(f"""
    <div class="sentence-row">
        <div class="sentence-btn-box">
            <button class="sentence-click-btn" 
                    id="txt_{o_idx}" 
                    data-state="kr" 
                    onclick="toggleSentence('{o_idx}', '{item['id']}', '{item['kr']}', '{item['en']}')">
                {item['id']}. {item['kr']}
            </button>
        </div>
        <div class="action-box">
            <button class="energy-btn" 
                    id="eng_{o_idx}" 
                    data-energy="{e_val}" 
                    onclick="cycleEnergy('{o_idx}', '{r_idx}')">{e_text}</button>
        </div>
    </div>
    """)

# 웹브라우저에서 직접 돌아가는 초고속 JavaScript 엔진 주입
js_script = """
<script>
function toggleSentence(oIdx, id, kr, en) {
    var btn = document.getElementById('txt_' + oIdx);
    if (btn.getAttribute('data-state') === 'kr') {
        btn.innerHTML = id + '. ' + en;
        btn.setAttribute('data-state', 'en');
        btn.style.color = '#f1c40f'; // 영어 상태일 때 노란색 포인트 강조
    } else {
        btn.innerHTML = id + '. ' + kr;
        btn.setAttribute('data-state', 'kr');
        btn.style.color = '#ffffff';
    }
}

function cycleEnergy(oIdx, rowIdx) {
    var btn = document.getElementById('eng_' + oIdx);
    var currentEnergy = parseInt(btn.getAttribute('data-energy'));
    var nextEnergy = currentEnergy + 1;
    if (nextEnergy > 3) { nextEnergy = 0; }
    
    btn.setAttribute('data-energy', nextEnergy);
    
    // 즉각적인 프론트엔드 아이콘 변경
    if (nextEnergy === 0) { btn.innerHTML = "🟥\\n🟥\\n🟥\\n🟥"; }
    else if (nextEnergy === 1) { btn.innerHTML = "🟧\\n🟧\\n🟧"; }
    else if (nextEnergy === 2) { btn.innerHTML = "🟨\\n🟨"; }
    else { btn.innerHTML = "🟩"; }
    
    // 사용자가 눈치채지 못하게 조용히 서버를 통해 구글 시트에 업데이트 요청 전달 (화면 새로고침 없음!)
    fetch('/?action=save_energy&row=' + rowIdx + '&val=' + nextEnergy);
}
</script>
"""

# 완성된 초고속 보드를 화면에 일괄 렌더링
st.markdown("".join(html_buffer) + js_script, unsafe_allow_html=True)
