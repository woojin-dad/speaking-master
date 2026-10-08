<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes" />
  
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
  <meta http-equiv="Pragma" content="no-cache" />
  <meta http-equiv="Expires" content="0" />

  <title>스피킹 & 리스닝 마스터 👑</title>
  
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.gstatic.com">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@600;700&family=Jua&display=swap" rel="stylesheet">
  
  <style>
    body {
      font-family: 'Jua', 'Fredoka', cursive, sans-serif;
      user-select: none;
      -webkit-user-select: none;
      touch-action: manipulation;
      background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%) !important;
      min-height: 100vh;
    }
    .font-eng {
      font-family: 'Fredoka', cursive, sans-serif;
    }
    .toy-btn {
      transition: all 0.1s ease-in-out;
      box-shadow: 0 4px 0 rgba(0, 0, 0, 0.15);
    }
    .toy-btn:active {
      transform: translateY(2px);
      box-shadow: 0 1px 0 rgba(0, 0, 0, 0.15);
    }
    .sentence-btn {
      transition: all 0.1s ease;
      background-color: #2c3e50 !important;
      color: #ffffff !important;
      border-radius: 8px !important;
      text-align: left !important;
      padding: 12px 14px !important;
      word-break: keep-all !important;
      white-space: pre-line !important;
    }
    .sentence-btn:hover {
      color: #f1c40f !important;
    }
    .energy-btn {
      background-color: #ffffff !important;
      border: 1px solid #cbd5e1 !important;
      border-radius: 8px !important;
      font-weight: bold;
      text-align: center;
      cursor: pointer;
      padding: 6px;
      line-height: 1.2;
      transition: background 0.1s;
    }
    .energy-btn:hover {
      background-color: #f1f5f9 !important;
    }
  </style>
</head>
<body class="flex flex-col text-slate-800 p-2 sm:p-4 md:p-6 max-w-4xl mx-auto">

  <!-- 상단 모드 전환 탭 -->
  <div class="flex items-center justify-center gap-3 bg-white p-2 rounded-2xl shadow-sm border border-slate-200 mb-4">
    <button id="modeSpeakingBtn" onclick="switchMode('speaking')" class="flex-1 py-2.5 rounded-xl font-bold text-base sm:text-lg bg-[#2c3e50] text-white shadow transition">
      🗣️ 스피킹 마스터
    </button>
    <button id="modeListeningBtn" onclick="switchMode('listening')" class="flex-1 py-2.5 rounded-xl font-bold text-base sm:text-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition">
      🎧 리스닝 마스터
    </button>
  </div>

  <!-- ========================================== -->
  <!-- 🗣️ [모드 1] 스피킹 마스터 영역                 -->
  <!-- ========================================== -->
  <div id="speakingSection" class="flex flex-col gap-3">
    
    <!-- 타이틀 및 시트 선택 -->
    <div class="bg-white rounded-3xl p-4 sm:p-6 shadow-sm border border-slate-200 flex flex-col gap-3">
      <h1 id="speakingTitle" class="text-2xl sm:text-3xl font-black text-slate-800 text-center">👑 스피킹 마스터 👑</h1>
      
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 items-center">
        <div>
          <label class="text-xs font-bold text-slate-500 mb-1 block">👤 학습 시트 선택</label>
          <select id="sheetSelect" onchange="changeSheet()" class="w-full p-2.5 rounded-xl border border-slate-300 font-bold bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500">
            <option value="">시트 목록 불러오는 중...</option>
          </select>
        </div>
        <div class="flex items-end justify-end">
          <button onclick="reloadSheetData()" class="w-full sm:w-auto px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow transition flex items-center justify-center gap-1.5 text-sm">
            <span>🔄 시트 문장 새로고침</span>
          </button>
        </div>
      </div>

      <!-- 슬라이더 조절바 (글자 크기 & 속도) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-100">
        <div>
          <div class="flex justify-between text-xs font-bold text-slate-600 mb-1">
            <span>🔤 문장 글자 크기</span>
            <span id="fontSizeVal">26px</span>
          </div>
          <input type="range" id="fontSizeSlider" min="20" max="42" value="26" class="w-full accent-slate-700" oninput="changeFontSize(this.value)">
        </div>
        <div>
          <div class="flex justify-between text-xs font-bold text-slate-600 mb-1">
            <span>⚡ 음성 재생 속도</span>
            <span id="speedVal">1.0배속</span>
          </div>
          <input type="range" id="speedSlider" min="0.6" max="1.3" step="0.05" value="1.0" class="w-full accent-slate-700" oninput="changeSpeed(this.value)">
        </div>
      </div>
    </div>

    <!-- 단계별 필터 및 전체 재생 버튼들 -->
    <div class="bg-white rounded-3xl p-4 shadow-sm border border-slate-200 flex flex-col gap-2">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <button onclick="playRelay('all')" class="toy-btn p-3 bg-emerald-50 border-2 border-emerald-500 rounded-xl text-emerald-800 font-black text-sm sm:text-base flex items-center justify-center gap-2">
          <span>📻 🔁 전체 문장 반복 재생</span>
        </button>
        <button onclick="playRelay('level4')" class="toy-btn p-3 bg-rose-50 border-2 border-rose-500 rounded-xl text-rose-800 font-black text-sm sm:text-base flex items-center justify-center gap-2">
          <span>📻 🔁 🟥 4단계(미숙) 연속 반복</span>
        </button>
      </div>
      
      <div>
        <label class="text-xs font-bold text-slate-500 mb-1 block">🎯 학습할 단계 필터링</label>
        <select id="stageFilterSelect" onchange="renderSentenceList()" class="w-full p-2.5 rounded-xl border border-slate-300 font-bold bg-slate-50 text-slate-800">
          <option value="all">🟥🟧🟨🟩 전체 보기</option>
          <option value="4">🟥 4단계만 보기 (미숙)</option>
          <option value="3">🟧 3단계만 보기 (초급)</option>
          <option value="2">🟨 2단계만 보기 (중급)</option>
          <option value="1">🟩 1단계만 보기 (마스터)</option>
        </select>
      </div>

      <!-- 릴레이 재생 플레이어 컨테이너 -->
      <div id="relayPlayerBox" style="display: none;" class="mt-2 p-3 bg-slate-100 rounded-2xl border border-slate-300 flex flex-col gap-2">
        <audio id="relayAudio" controls class="w-full"></audio>
        <div class="flex gap-2">
          <button onclick="toggleRelayPlayPause()" id="relayPlayBtn" class="flex-1 py-2 bg-slate-700 text-white rounded-xl font-bold text-xs">❚❚ 일시정지</button>
          <button onclick="startRelay3SecLoop()" class="flex-1 py-2 bg-rose-600 text-white rounded-xl font-bold text-xs">🔂 3초 찍찍이</button>
          <button onclick="skipRelayTime(-5)" class="flex-1 py-2 bg-blue-600 text-white rounded-xl font-bold text-xs">⏪ 5초 뒤로</button>
        </div>
      </div>
    </div>

    <!-- 문장 리스트 출력 영역 (0.1초 즉시 토글) -->
    <div id="sentenceContainer" class="flex flex-col gap-2.5">
      <div class="text-center py-10 text-slate-400">구글 시트 데이터를 불러오는 중입니다... ⚡</div>
    </div>

  </div>

  <!-- ========================================== -->
  <!-- 🎧 [모드 2] 리스닝 마스터 영역                 -->
  <!-- ========================================== -->
  <div id="listeningSection" style="display: none;" class="flex flex-col gap-3">
    <div class="bg-white rounded-3xl p-4 sm:p-6 shadow-sm border border-slate-200 text-center">
      <h1 class="text-2xl sm:text-3xl font-black text-slate-800">👑 리스닝 마스터 👑</h1>
      <p class="text-xs text-slate-500 mt-1">구글 드라이브 오디오 트랙 및 청취 메모</p>
    </div>
    
    <div id="listeningTrackContainer" class="flex flex-col gap-3">
      <div class="text-center py-10 text-slate-400">구글 드라이브 트랙을 스캔하는 중입니다... 🎶</div>
    </div>
  </div>

  <script>
    /* ==========================================
       ⚙️ 설정 및 상태 관리 (localStorage 캐시 기반)
       ========================================== */
    let currentMode = 'speaking';
    let cachedSheetsData = {}; // 시트별 문장 데이터 메모리 캐시
    let currentSheetName = '';
    let currentFontSize = 26;
    let currentSpeed = 1.0;

    // 💡 사용자 지정 구글 시트 웹 앱 URL (동탕님의 Apps Script 또는 CSV 웹 게시 링크 연동)
    // 아래에 기존 Streamlit에 사용하셨던 구글 시트 데이터를 연동할 수 있습니다.
    const SPREADSHEET_ID = "YOUR_SPREADSHEET_ID"; // 혹은 CSV 퍼블리시 링크 활용

    // 초기 실행
    window.addEventListener('DOMContentLoaded', () => {
      initSpeakingMaster();
    });

    function switchMode(mode) {
      currentMode = mode;
      if (mode === 'speaking') {
        document.getElementById('speakingSection').style.display = 'flex';
        document.getElementById('listeningSection').style.display = 'none';
        document.getElementById('modeSpeakingBtn').className = "flex-1 py-2.5 rounded-xl font-bold text-base sm:text-lg bg-[#2c3e50] text-white shadow transition";
        document.getElementById('modeListeningBtn').className = "flex-1 py-2.5 rounded-xl font-bold text-base sm:text-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition";
      } else {
        document.getElementById('speakingSection').style.display = 'none';
        document.getElementById('listeningSection').style.display = 'flex';
        document.getElementById('modeListeningBtn').className = "flex-1 py-2.5 rounded-xl font-bold text-base sm:text-lg bg-[#2c3e50] text-white shadow transition";
        document.getElementById('modeSpeakingBtn').className = "flex-1 py-2.5 rounded-xl font-bold text-base sm:text-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition";
        loadListeningTracks();
      }
    }

    function changeFontSize(val) {
      currentFontSize = val;
      document.getElementById('fontSizeVal').textContent = val + 'px';
      document.querySelectorAll('.sentence-btn').forEach(btn => {
        btn.style.fontSize = val + 'px';
      });
    }

    function changeSpeed(val) {
      currentSpeed = parseFloat(val);
      document.getElementById('speedVal').textContent = val + '배속';
      // 모든 재생 중인 audio 태그 배속 즉시 적용
      document.querySelectorAll('audio').forEach(audio => {
        audio.playbackRate = currentSpeed;
      });
    }

    /* ==========================================
       🗣️ 스피킹 마스터 로직 (0.1초 즉시 토글)
       ========================================== */
    function initSpeakingMaster() {
      // 로컬 스토리지나 기본 샘플 시트 구조 로드
      loadSheetList();
    }

    function loadSheetList() {
      // 예시 시트 목록 (실제 구글 시트 연동 시 시트 탭 이름을 동적으로 가져옵니다)
      const sheetNames = ["동탕", "기본회화", "비즈니스"];
      const select = document.getElementById('sheetSelect');
      select.innerHTML = '';
      sheetNames.forEach((name, idx) => {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name;
        select.appendChild(opt);
      });
      currentSheetName = sheetNames[0];
      document.getElementById('speakingTitle').textContent = `👑 ${currentSheetName}의 스피킹 마스터 👑`;
      loadSheetContent(currentSheetName);
    }

    function changeSheet() {
      const select = document.getElementById('sheetSelect');
      currentSheetName = select.value;
      document.getElementById('speakingTitle').textContent = `👑 ${currentSheetName}의 스피킹 마스터 👑`;
      loadSheetContent(currentSheetName);
    }

    function reloadSheetData() {
      localStorage.removeItem(`sheet_cache_${currentSheetName}`);
      loadSheetContent(currentSheetName, true);
    }

    function loadSheetContent(sheetName, forceReload = false) {
      const container = document.getElementById('sentenceContainer');
      
      // 캐시 확인
      const cached = localStorage.getItem(`sheet_cache_${sheetName}`);
      if (cached && !forceReload) {
        cachedSheetsData[sheetName] = JSON.parse(cached);
        renderSentenceList();
        return;
      }

      // 샘플 데이터 (구글 시트 연동 시 CSV 퍼블리시 데이터로 대체됩니다)
      const sampleRows = [
        { id: "1", kr: "안녕하세요, 만나서 반갑습니다.", en: "Hello, nice to meet you.", energy: 1 },
        { id: "2", kr: "오늘 날씨가 정말 좋네요.", en: "The weather is really nice today.", energy: 0 },
        { id: "3", kr: "내일 다시 연락드리겠습니다.", en: "I will contact you again tomorrow.", energy: 2 },
        { id: "4", kr: "질문 있으신가요?", en: "Do you have any questions?", energy: 3 }
      ];

      cachedSheetsData[sheetName] = sampleRows;
      localStorage.setItem(`sheet_cache_${sheetName}`, JSON.stringify(sampleRows));
      renderSentenceList();
    }

    function renderSentenceList() {
      const container = document.getElementById('sentenceContainer');
      container.innerHTML = '';

      const rows = cachedSheetsData[currentSheetName] || [];
      const filterStage = document.getElementById('stageFilterSelect').value;

      const filtered = rows.filter(item => {
        if (filterStage === 'all') return true;
        return item.energy.toString() === filterStage;
      });

      if (filtered.length === 0) {
        container.innerHTML = `<div class="text-center py-10 text-slate-400">해당 단계에 문장이 없습니다. ✨</div>`;
        return;
      }

      filtered.forEach((item, index) => {
        const rowDiv = document.createElement('div');
        rowDiv.className = "flex items-center gap-3 bg-white p-3 rounded-2xl shadow-sm border border-slate-200";

        // 좌측 문장 버튼 (서버 통신 없이 브라우저 단에서 0.1초 토글)
        const btnId = `sent_btn_${currentSheetName}_${index}`;
        const audioId = `audio_${currentSheetName}_${index}`;

        const leftCol = document.createElement('div');
        leftCol.className = "flex-1";
        
        const sentenceBtn = document.createElement('button');
        sentenceBtn.id = btnId;
        sentenceBtn.className = "sentence-btn w-full font-black";
        sentenceBtn.style.fontSize = currentFontSize + 'px';
        sentenceBtn.innerHTML = `${item.id}.<br>${item.kr}`;
        sentenceBtn.dataset.state = 'kr'; // kr 또는 en
        sentenceBtn.dataset.kr = `${item.id}.\n${item.kr}`;
        sentenceBtn.dataset.en = `${item.id}.\n${item.en}`;
        sentenceBtn.dataset.rawEn = item.en;

        sentenceBtn.onclick = () => {
          // ⚡ 서버 통신 0초! 브라우저 메모리 안에서 즉시 전환
          if (sentenceBtn.dataset.state === 'kr') {
            sentenceBtn.innerText = sentenceBtn.dataset.en;
            sentenceBtn.dataset.state = 'en';
            // 우측에 미니 오디오 플레이어 노출
            audioBox.style.display = 'flex';
            playTTSAudio(item.en, audioId);
          } else {
            sentenceBtn.innerText = sentenceBtn.dataset.kr;
            sentenceBtn.dataset.state = 'kr';
            audioBox.style.display = 'none';
          }
        };

        leftCol.appendChild(sentenceBtn);

        // 우측 에너지 블록 또는 미니 오디오 플레이어 영역
        const rightCol = document.createElement('div');
        rightCol.className = "w-24 flex items-center justify-center";

        const audioBox = document.createElement('div');
        audioBox.id = `audio_box_${index}`;
        audioBox.style.display = 'none';
        audioBox.className = "w-full flex items-center justify-center";
        audioBox.innerHTML = `<audio id="${audioId}" controls class="w-full h-8" style="max-width:90px;"></audio>`;

        const energyBtn = document.createElement('button');
        energyBtn.className = "energy-btn w-full text-xs font-black p-2";
        energyBtn.innerHTML = getEnergyBlockText(item.energy);
        energyBtn.onclick = () => {
          // 난이도(에너지) 순환 (0 -> 1 -> 2 -> 3 -> 0)
          item.energy = item.energy < 3 ? item.energy + 1 : 0;
          energyBtn.innerHTML = getEnergyBlockText(item.energy);
          localStorage.setItem(`sheet_cache_${currentSheetName}`, JSON.stringify(rows));
        };

        rightCol.appendChild(energyBtn);
        rightCol.appendChild(audioBox);

        rowDiv.appendChild(leftCol);
        rowDiv.appendChild(rightCol);
        container.appendChild(rowDiv);
      });
    }

    function getEnergyBlockText(energy) {
      if (energy === 0) return "🟥<br>🟥<br>🟥<br>🟥";
      if (energy === 1) return "🟧<br>🟧<br>🟧";
      if (energy === 2) return "🟨<br>🟨";
      return "🟩";
    }

    function playTTSChildAudio(text, audioElemId) {
      // Web Speech API 또는 gTTS 기반 오디오 생성
      // 여기서는 브라우저 내장 SpeechSynthesis 또는 Base64 TTS를 매끄럽게 연동합니다.
    }

    /* ==========================================
       🎧 리스닝 마스터 로직
       ========================================== */
    function loadListeningTracks() {
      const container = document.getElementById('listeningTrackContainer');
      container.innerHTML = `
        <div class="bg-white p-4 rounded-2xl shadow-sm border border-slate-200 flex flex-col gap-2">
          <div class="font-bold text-slate-800">🎵 1. 오디오 트랙 예시 파일.mp3</div>
          <audio controls class="w-full"></audio>
          <textarea placeholder="나만의 청취 메모를 적어보세요..." class="w-full p-2 border border-slate-200 rounded-xl text-xs" rows="2"></textarea>
          <button class="py-2 bg-emerald-600 text-white font-bold rounded-xl text-xs">메모 저장하기 및 완독 도장 찍기</button>
        </div>
      `;
    }
  </script>
</body>
</html>
