import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import json
from gtts import gTTS
import io
import threading
import base64
import time
from datetime import datetime

# 1. 웹페이지 기본 설정
st.set_page_config(
    page_title="스피킹 & 리스닝 마스터",
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

# 🎛️ [최상단 메인 스위치] 서비스 모드 전환
app_mode = st.radio(
    "📱 학습 서비스 선택",
    ["🗣️ 스피킹 마스터", "🎧 리스닝 마스터"],
    key="main_app_mode_switcher",
    horizontal=True
)
st.write("---")

# ==============================================================================
# 🔀 [모드 1] 🗣️ 스피킹 마스터
# ==============================================================================
if app_mode == "🗣️ 스피킹 마스터":

    @st.cache_resource
    def init_gspread():
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = json.loads(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)

    @st.cache_resource
    def get_sheet_titles():
        try:
            client = init_gspread()
            doc = client.open("SpeakingMaster")
            titles = [ws.title for ws in doc.worksheets()]
            return [t for t in titles if t != "ListeningRecord"]
        except:
            return ["동탕"]

    existing_sheets = get_sheet_titles()
    menu_options = []
    for title in existing_sheets:
        menu_options.append(title)
        menu_options.append(f"{title} (우선순위)")

    if "pure_main_menu_box" in st.session_state and st.session_state["pure_main_menu_box"] in menu_options:
        selected_menu = st.session_state["pure_main_menu_box"]
    else:
        selected_menu = menu_options[0]

    st.markdown(f"<div class='custom-title'>👑 {selected_menu}의 스피킹 마스터 👑</div>", unsafe_allow_html=True)
    st.write("---")

    st.selectbox("👤 학습 모드를 선택하세요", menu_options, key="pure_main_menu_box")

    real_sheet_name = selected_menu.replace(" (우선순위)", "").strip()
    is_priority_mode = "우선순위" in selected_menu

    font_size = st.slider("🔤 문장 글자 크기 조절 (기본값: 26px)", min_value=18, max_value=36, value=26, step=1, key="pure_font_slider")

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
        [data-testid="stToolbar"] {{display: none !important; visibility: hidden !important;}}
        button[title="Fork this app"] {{display: none !important; visibility: hidden !important;}}
        </style>
    """, unsafe_allow_html=True)

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

# ==============================================================================
# 🔀 [모드 2] 🎧 리스닝 마스터 (타이틀 변경 반영 완료)
# ==============================================================================
else:
    st.markdown("""
        <style>
        .block-container {
            max-width: 100% !important;
            padding-top: 0.5rem !important;
            padding-bottom: 1rem !important;
            padding-left: 10px !important;
            padding-right: 0px !important;
        }
        
        .custom-title {
            font-size: 26px !important;
            font-weight: bold !important;
            color: #2c3e50 !important;
            text-align: center !important;
            padding-top: 5px;
            margin-top: 10px !important;
        }

        [data-testid="stToolbar"] {display: none !important; visibility: hidden !important;}
        button[title="Fork this app"] {display: none !important; visibility: hidden !important;}
        header {visibility: hidden !important; height: 0px !important;}
        footer {visibility: hidden !important; height: 0px !important;}
        
        .track-title {
            font-size: 17px;
            font-weight: bold;
            color: #1e293b;
        }
        .badge-completed {
            background-color: #dcfce7;
            color: #15803d;
            font-size: 13px;
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 6px;
            display: inline-block;
            margin-top: 4px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 📌 요청하신 타이틀 변경 완료: "👑 리스닝 마스터 👑"
    st.markdown("<div class='custom-title'>👑 리스닝 마스터 👑</div>", unsafe_allow_html=True)
    st.write("---")

    TARGET_FOLDER_ID = "10jn33dgDqiBD_ovj6BYnUD_1Y9BQruwF"

    @st.cache_resource
    def init_gspread_listening():
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = json.loads(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)

    def load_listening_records():
        try:
            client = init_gspread_listening()
            doc = client.open("SpeakingMaster")
            ws = doc.worksheet("ListeningRecord")
            records = ws.get_all_records()
            completed_dict = {}
            notes_dict = {}
            for r in records:
                fname = r.get('filename', '')
                if str(r.get('is_completed', '')).upper() == "TRUE":
                    completed_dict[fname] = r.get('completed_at', '완료')
                if r.get('notes'):
                    notes_dict[fname] = str(r.get('notes'))
            return completed_dict, notes_dict, ws
        except Exception as e:
            return {}, {}, None

    def toggle_track_completed_in_sheet(ws, filename, mark_as_done):
        if not ws:
            return
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M") if mark_as_done else ""
        is_completed_str = "TRUE" if mark_as_done else "FALSE"
        
        try:
            records = ws.get_all_records()
            found_row = None
            for idx, r in enumerate(records, start=2):
                if r.get('filename') == filename:
                    found_row = idx
                    break
            
            if found_row:
                ws.update_cell(found_row, 2, is_completed_str)
                ws.update_cell(found_row, 3, now_str)
            else:
                if mark_as_done:
                    ws.append_row([filename, "TRUE", now_str, ""])
        except Exception as e:
            pass

    def save_track_note_in_sheet(ws, filename, note_text):
        if not ws:
            return
        try:
            records = ws.get_all_records()
            found_row = None
            for idx, r in enumerate(records, start=2):
                if r.get('filename') == filename:
                    found_row = idx
                    break
            
            if found_row:
                ws.update_cell(found_row, 4, note_text)
            else:
                ws.append_row([filename, "FALSE", "", note_text])
        except Exception as e:
            pass

    def build_drive_service():
        creds_dict = json.loads(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            creds_dict, 
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        return build('drive', 'v3', credentials=creds)

    def get_drive_audio_files_safe(folder_id, max_retries=3):
        for attempt in range(max_retries):
            try:
                service = build_drive_service()
                query = f"'{folder_id}' in parents and trashed = false and (mimeType contains 'audio/' or name contains '.mp3' or name contains '.m4a' or name contains '.wav')"
                results = service.files().list(
                    q=query,
                    fields="files(id, name, mimeType)",
                    orderBy="name"
                ).execute()
                return results.get('files', []), None
            except Exception as e:
                time.sleep(1)
                if attempt == max_retries - 1:
                    return [], str(e)

    @st.cache_data(show_spinner=False)
    def download_audio_bytes(file_id):
        try:
            service = build_drive_service()
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            fh.seek(0)
            return fh.read()
        except Exception as e:
            return None

    with st.spinner("⚡ 구글 드라이브, 완독 기록 및 메모 스캔 중..."):
        completed_records, saved_notes, record_ws = load_listening_records()
        audio_files, error_msg = get_drive_audio_files_safe(TARGET_FOLDER_ID)

    if error_msg:
        st.warning("⚠️ 구글 서버와의 연결 지연이 발생했습니다.")
        if st.button("🔄 다시 시도하기", key="retry_ssl_btn"):
            st.rerun()
    elif audio_files:
        col_top1, col_top2 = st.columns([7, 3])
        with col_top1:
            st.success(f"🎶 총 {len(audio_files)}개의 오디오 트랙이 보관되어 있습니다.")
        with col_top2:
            if st.button("🔄 드라이브 새로고침", key="refresh_drive_btn"):
                st.rerun()
        st.write("---")

        for idx, file_info in enumerate(audio_files, start=1):
            fname = file_info['name']
            fid = file_info['id']
            is_done = fname in completed_records
            done_time = completed_records.get(fname, "")
            current_note = saved_notes.get(fname, "")

            play_state_key = f"play_active_{fid}"
            if play_state_key not in st.session_state:
                st.session_state[play_state_key] = False

            c1, c2 = st.columns([7.5, 2.5])
            
            with c1:
                st.markdown(f"<div class='track-title'>🎵 {idx}. {fname}</div>", unsafe_allow_html=True)
                if is_done:
                    st.markdown(f"<div class='badge-completed'>✅ 완독: {done_time}</div>", unsafe_allow_html=True)
            
            with c2:
                btn_label = "❚❚ 닫기" if st.session_state[play_state_key] else "▶ 재생"
                if st.button(btn_label, key=f"btn_toggle_{fid}"):
                    st.session_state[play_state_key] = not st.session_state[play_state_key]
                    st.rerun()

            if st.session_state[play_state_key]:
                with st.spinner(f"📥 [{fname}] 음성 로딩 중..."):
                    audio_bytes = download_audio_bytes(fid)
                
                if audio_bytes:
                    b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
                    player_id = f"custom_audio_{fid}"

                    custom_player_html = f"""
                    <div style="background-color: #f1f5f9; padding: 15px; border-radius: 12px; margin-bottom: 10px;">
                        <audio id="{player_id}" src="data:audio/mp3;base64,{b64_audio}" controls style="width: 100%; margin-bottom: 10px;"></audio>
                        <div style="display: flex; gap: 8px; flex-wrap: wrap; justify-content: center;">
                            <button onclick="skipTime('{player_id}', -10)" style="padding: 8px 12px; background-color: #3b82f6; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">⏪ 10초 뒤로</button>
                            <button onclick="skipTime('{player_id}', 10)" style="padding: 8px 12px; background-color: #3b82f6; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">10초 앞으로 ⏩</button>
                            <button onclick="startLoop3Sec('{player_id}')" style="padding: 8px 12px; background-color: #e11d48; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">🔂 방금 3초 찍찍이 (무한반복)</button>
                            <button onclick="stopLoop3Sec('{player_id}')" style="padding: 8px 12px; background-color: #475569; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">▶ 표준 재생</button>
                        </div>
                    </div>

                    <script>
                    if (typeof window.loopIntervals === 'undefined') {{
                        window.loopIntervals = {{}};
                    }}

                    function skipTime(id, sec) {{
                        var audio = document.getElementById(id);
                        if(audio) {{
                            audio.currentTime = Math.max(0, audio.currentTime + sec);
                        }}
                    }}

                    function startLoop3Sec(id) {{
                        var audio = document.getElementById(id);
                        if(audio) {{
                            if (window.loopIntervals[id]) clearInterval(window.loopIntervals[id]);
                            var start = Math.max(0, audio.currentTime - 3);
                            var end = audio.currentTime;
                            audio.currentTime = start;
                            audio.play();

                            window.loopIntervals[id] = setInterval(function() {{
                                if (audio.currentTime >= end || audio.currentTime < start) {{
                                    audio.currentTime = start;
                                }}
                            }}, 200);
                        }}
                    }}

                    function stopLoop3Sec(id) {{
                        if (window.loopIntervals[id]) {{
                            clearInterval(window.loopIntervals[id]);
                            delete window.loopIntervals[id];
                        }}
                    }}
                    </script>
                    """
                    st.components.v1.html(custom_player_html, height=140)
                    
                    user_note = st.text_area(
                        "📝 나만의 청취 메모 (중요 표현, 구간 적기):",
                        value=current_note,
                        key=f"note_input_{fid}",
                        height=80
                    )
                    
                    col_note_btn, col_blank = st.columns([3, 7])
                    with col_note_btn:
                        if st.button("💾 메모 저장하기", key=f"save_note_btn_{fid}"):
                            threading.Thread(
                                target=save_track_note_in_sheet,
                                args=(record_ws, fname, user_note),
                                daemon=True
                            ).start()
                            saved_notes[fname] = user_note
                            st.success("메모가 구글 시트에 저장되었습니다!")

                    st.write("---")

                    col_act1, col_act2 = st.columns([5, 5])
                    with col_act1:
                        if not is_done:
                            if st.button(f"🎉 완독 완료 도장 찍기", key=f"mark_done_{fid}"):
                                threading.Thread(
                                    target=toggle_track_completed_in_sheet,
                                    args=(record_ws, fname, True),
                                    daemon=True
                                ).start()
                                completed_records[fname] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                st.success("완독 기록 저장 완료!")
                                st.rerun()
                    with col_act2:
                        if is_done:
                            if st.button(f"🗑️ 완독 기록 취소하기", key=f"cancel_done_{fid}"):
                                threading.Thread(
                                    target=toggle_track_completed_in_sheet,
                                    args=(record_ws, fname, False),
                                    daemon=True
                                ).start()
                                if fname in completed_records:
                                    del completed_records[fname]
                                st.info("완독 기록이 취소되었습니다.")
                                st.rerun()
                else:
                    st.error("오디오 로딩 실패")
            
            st.write("---")
            
    else:
        st.warning("구글 드라이브 폴더에 MP3 파일이 없습니다.")
