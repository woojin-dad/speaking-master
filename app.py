# ==============================================================================
# 🔀 [모드 2] 🎧 리스닝 마스터 (구글 드라이브 주소 + 제목 직접 입력 지원)
# ==============================================================================
else:
    # 상단 Fork 및 툴바 차단 스타일 적용
    st.markdown("""
        <style>
        [data-testid="stToolbar"] {display: none !important; visibility: hidden !important;}
        button[title="Fork this app"] {display: none !important; visibility: hidden !important;}
        header {visibility: hidden !important; height: 0px !important;}
        footer {visibility: hidden !important; height: 0px !important;}
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='custom-title'>👑 리스닝 마스터 👑</div>", unsafe_allow_html=True)
    st.write("---")
    
    st.subheader("🔗 구글 드라이브 오디오 연결")
    st.caption("💡 구글 드라이브 파일의 공유 권한을 '링크가 있는 모든 사용자에게 공개'로 설정한 후 링크를 붙여넣으세요.")
    
    # 1. 링크 입력창
    gdrive_url = st.text_input("구글 드라이브 공유 링크를 붙여넣으세요:", placeholder="https://drive.google.com/file/d/...", key="gdrive_link_input")
    
    # 2. 제목 입력창 (선택 사항)
    track_title = st.text_input("📝 파일 제목을 입력해 주세요 (선택 사항):", placeholder="예: 시니어 오디오북 1강", key="gdrive_title_input")
    
    if gdrive_url:
        # 구글 드라이브 URL에서 File ID 추출하기
        file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', gdrive_url) or re.search(r'id=([a-zA-Z0-9_-]+)', gdrive_url)
        
        if file_id_match:
            file_id = file_id_match.group(1)
            direct_audio_url = f"https://docs.google.com/uc?export=download&id={file_id}"
            
            st.write("---")
            # 제목이 입력되어 있으면 제목을 띄우고, 없으면 기본 문구 표시
            display_title = track_title if track_title.strip() else "구글 드라이브 오디오 파일"
            st.subheader(f"▶️ 현재 재생 중: {display_title}")
            
            # 오디오 플레이어 출력
            st.audio(direct_audio_url)
            st.success("🎶 음성이 성공적으로 연결되었습니다!")
        else:
            st.error("올바른 구글 드라이브 링크 형식이 아닙니다. 링크를 다시 확인해 주세요.")
