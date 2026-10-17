let allQuestions = [];       // Toàn bộ 200 câu của đề hiện tại
let filteredQuestions = [];  // Danh sách câu hỏi sau khi lọc theo Part
let currentIndex = 0;
let userAnswers = {};
let isSubmitted = false;
let currentPartFilter = "ALL";
let timeLeft = 120 * 60; // 120 phút

// Các phần tử DOM
const passageCol = document.getElementById("passageCol");
const mediaBox = document.getElementById("mediaBox");
const passageText = document.getElementById("passageText");
const questionCol = document.getElementById("questionCol");
const questionText = document.getElementById("questionText");
const optionsContainer = document.getElementById("optionsContainer");
const partBadge = document.getElementById("partBadge");
const questionCounter = document.getElementById("questionCounter");
const explanationBox = document.getElementById("explanationBox");
const explanationText = document.getElementById("explanationText");
const questionPalette = document.getElementById("questionPalette");
const timerEl = document.getElementById("timer");
const examSelect = document.getElementById("examSelect");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const submitBtn = document.getElementById("submitBtn");

// 1. Nạp đề thi
async function loadExam(fileName = "data.json") {
  try {
    userAnswers = {};
    isSubmitted = false;
    currentPartFilter = "ALL";
    submitBtn.classList.remove("hidden");
    
    // Đặt lại trạng thái nút lọc
    updatePartTabStyles();

    const res = await fetch(fileName);
    if (!res.ok) throw new Error("Không thể tải tệp đề: " + fileName);
    allQuestions = await res.json();
    
    applyPartFilter("ALL");
  } catch (err) {
    console.error(err);
    alert("Lỗi tải đề: " + fileName);
  }
}

// 2. Lọc câu hỏi theo từng Part
function applyPartFilter(partName) {
  currentPartFilter = partName;
  if (partName === "ALL") {
    filteredQuestions = allQuestions;
  } else {
    filteredQuestions = allQuestions.filter(q => q.part === partName);
  }

  updatePartTabStyles();
  buildPalette();
  renderQuestion(0);
}

function updatePartTabStyles() {
  const buttons = document.querySelectorAll("#partFilterContainer .part-tab-btn");
  buttons.forEach(btn => {
    if (btn.getAttribute("data-part") === currentPartFilter) {
      btn.className = "part-tab-btn px-3.5 py-1.5 rounded-full bg-emerald-600 text-white font-bold transition shadow-xs";
    } else {
      btn.className = "part-tab-btn px-3.5 py-1.5 rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200 transition font-medium";
    }
  });
}

// 3. Trích xuất đoạn văn cho Part 6 & 7
function extractPassage(q) {
  if (!q.group_text || q.part === "Part 5") return "";
  const gt = q.group_text;
  if (gt.includes("Question\n")) {
    return gt.split("Question\n")[0].replace("ĐOẠN VĂN\nThu gọn", "").trim();
  }
  if (gt.includes("ĐOẠN VĂN\nThu gọn")) {
    return gt.split("ĐOẠN VĂN\nThu gọn")[1].trim();
  }
  return "";
}

// 4. Trích xuất lời giải thích
function extractExplanation(q) {
  const at = q.article_text || "";
  const keywords = ["DẪN CHỨNG", "SUY LUẬN", "Ngữ pháp", "Từ vựng", "Tìm chi tiết", "Ý chính", "Mục đích", "Đọc bảng biểu"];
  for (const kw of keywords) {
    const idx = at.indexOf(kw);
    if (idx !== -1) return at.substring(idx).trim();
  }
  return at || "Đang cập nhật giải thích cho câu hỏi này.";
}

// 5. Hiển thị nội dung câu hỏi
function renderQuestion(index) {
  if (filteredQuestions.length === 0) return;
  currentIndex = index;
  const q = filteredQuestions[index];

  questionCounter.textContent = `Câu ${index + 1}/${filteredQuestions.length} (Gốc: #${q.number})`;
  partBadge.textContent = q.part || "TOEIC";
  
  // Format tên câu
  questionText.textContent = q.question.startsWith(`${q.number}.`) 
    ? q.question 
    : `${q.number || index + 1}. ${q.question}`;

  // Xử lý Cột bên trái: Đoạn văn, Audio, Ảnh
  mediaBox.innerHTML = "";
  const passage = extractPassage(q);
  const hasImages = q.media && q.media.images && q.media.images.length > 0;
  const hasAudio = q.media && q.media.audio && q.media.audio.length > 0;

  if (passage || hasImages || hasAudio) {
    passageCol.classList.remove("hidden");
    questionCol.classList.remove("lg:col-span-12");
    questionCol.classList.add("lg:col-span-6");

    // Audio Player phong cách Đậu TOEIC có chỉnh tốc độ
    if (hasAudio) {
      const audioUrl = q.media.audio[0];
      const audioWrapper = document.createElement("div");
      audioWrapper.className = "p-3 bg-slate-50 rounded-xl border border-slate-200/70 shadow-xs";
      audioWrapper.innerHTML = `
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-bold text-emerald-700 flex items-center space-x-1">
            <span>🎧 Nghe Audio câu ${q.number}</span>
          </span>
          <div class="flex items-center space-x-1 text-[11px] font-semibold text-slate-500">
            <span>Tốc độ:</span>
            <button onclick="changeSpeed(this, 0.8)" class="px-1.5 py-0.5 rounded hover:bg-slate-200">0.8x</button>
            <button onclick="changeSpeed(this, 1.0)" class="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">1.0x</button>
            <button onclick="changeSpeed(this, 1.2)" class="px-1.5 py-0.5 rounded hover:bg-slate-200">1.2x</button>
          </div>
        </div>
        <audio controls src="${audioUrl}" class="w-full h-8"></audio>
      `;
      mediaBox.appendChild(audioWrapper);
    }

    // Ảnh minh họa
    if (hasImages) {
      const imgWrapper = document.createElement("div");
      imgWrapper.className = "text-center";
      imgWrapper.innerHTML = `<img src="${q.media.images[0]}" class="max-h-80 object-contain mx-auto rounded-xl border border-slate-200 shadow-xs" alt="Hình minh họa" />`;
      mediaBox.appendChild(imgWrapper);
    }

    passageText.textContent = passage;
  } else {
    // Part 5: Mở rộng 1 cột toàn màn hình
    passageCol.classList.add("hidden");
    questionCol.classList.remove("lg:col-span-6");
    questionCol.classList.add("lg:col-span-12");
  }

  // Danh sách đáp án A, B, C, D
  optionsContainer.innerHTML = "";
  const choices = q.choices || [];
  
  choices.forEach((choice, i) => {
    const isSelected = userAnswers[q.number] === i;
    const btn = document.createElement("button");
    
    // Style nút chuẩn Đậu TOEIC: Bo góc lớn, viền thanh thoát, đổ bóng nhẹ
    let btnStyle = "w-full text-left p-4 rounded-xl border transition-all flex flex-col space-y-1.5 cursor-pointer ";
    if (isSelected) {
      btnStyle += "border-emerald-600 bg-emerald-50/70 text-emerald-950 ring-2 ring-emerald-500/20 shadow-xs";
    } else {
      btnStyle += "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/60 text-slate-700";
    }

    // Đổi màu khi đã nộp bài
    if (isSubmitted) {
      btn.disabled = true;
      if (choice.correct) {
        btnStyle = "w-full text-left p-4 rounded-xl border-2 !border-emerald-500 !bg-emerald-50 text-emerald-900";
      } else if (isSelected && !choice.correct) {
        btnStyle = "w-full text-left p-4 rounded-xl border-2 !border-rose-400 !bg-rose-50 text-rose-900";
      }
    }
    btn.className = btnStyle;

    const rawText = choice.text || "";
    const match = rawText.match(/^\(([A-D])\)\s*([\s\S]*)$/);
    const label = match ? match[1] : String.fromCharCode(65 + i);
    const content = match ? match[2].trim() : rawText.trim();

    // 1. Kiểm tra: Đối với Part 1 và Part 2 (câu 1 đến 31), khi đang làm bài sẽ ẨN lời thoại
    const isAudioOnlyPart = q.part === "Part 1" || q.part === "Part 2" || (q.number && q.number <= 31);
    const showTranscript = !isAudioOnlyPart || isSubmitted;

    let badgeClass = "w-7 h-7 shrink-0 rounded-full flex items-center justify-center font-bold text-xs border ";
    if (isSelected) {
      badgeClass += "bg-emerald-600 text-white border-emerald-600";
    } else {
      badgeClass += "bg-slate-100 text-slate-500 border-slate-200";
    }

    // 2. Nếu là Part 1 / Part 2 đang làm bài: chỉ hiển thị huy hiệu chữ A, B, C, D
    let innerHtml = `
      <div class="flex items-center space-x-3 w-full">
        <span class="${badgeClass}">${label}</span>
        ${showTranscript ? `<span class="font-medium text-sm leading-snug">${content}</span>` : ""}
      </div>
    `;

    // Dịch nghĩa song ngữ Anh - Việt sau khi nộp bài
    if (isSubmitted && choice.translation) {
      innerHtml += `<div class="text-xs text-slate-500 pl-10 italic">Nghĩa: ${choice.translation}</div>`;
    }

    btn.innerHTML = innerHtml;
    btn.onclick = () => selectAnswer(q.number, i);
    optionsContainer.appendChild(btn);
  });

  // Khung giải thích
  if (isSubmitted) {
    explanationBox.classList.remove("hidden");
    explanationText.textContent = extractExplanation(q);
  } else {
    explanationBox.classList.add("hidden");
  }

  prevBtn.disabled = index === 0;
  nextBtn.disabled = index === filteredQuestions.length - 1;
  updatePaletteActive();
}

// 6. Chọn đáp án
function selectAnswer(questionNumber, choiceIndex) {
  if (isSubmitted) return;
  userAnswers[questionNumber] = choiceIndex;
  renderQuestion(currentIndex);
  buildPalette();
}

// 7. Chuyển đổi tốc độ phát Audio
window.changeSpeed = function(btn, speed) {
  const audio = btn.closest(".p-3").querySelector("audio");
  if (audio) {
    audio.playbackRate = speed;
    btn.parentElement.querySelectorAll("button").forEach(b => b.className = "px-1.5 py-0.5 rounded hover:bg-slate-200");
    btn.className = "px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold";
  }
};

// 8. Question Palette (Bảng câu hỏi dưới đáy)
function buildPalette() {
  questionPalette.innerHTML = "";
  filteredQuestions.forEach((q, idx) => {
    const pBtn = document.createElement("button");
    pBtn.textContent = q.number;
    
    let stateClass = "w-8 h-8 shrink-0 rounded-lg text-xs font-bold transition flex items-center justify-center border ";
    
    if (userAnswers[q.number] !== undefined) {
      if (isSubmitted) {
        const isRight = q.choices && q.choices[userAnswers[q.number]]?.correct;
        stateClass += isRight 
          ? "bg-emerald-500 text-white border-emerald-600 " 
          : "bg-rose-500 text-white border-rose-600 ";
      } else {
        stateClass += "bg-emerald-600 text-white border-emerald-600 shadow-xs ";
      }
    } else {
      stateClass += "bg-white text-slate-600 border-slate-200 hover:bg-slate-100 ";
    }

    if (currentIndex === idx) {
      stateClass += "ring-2 ring-emerald-500 ring-offset-1 ";
    }

    pBtn.className = stateClass;
    pBtn.onclick = () => renderQuestion(idx);
    questionPalette.appendChild(pBtn);
  });
  updatePaletteActive();
}

function updatePaletteActive() {
  const btns = questionPalette.querySelectorAll("button");
  btns.forEach((b, i) => {
    if (i === currentIndex) {
      b.classList.add("ring-2", "ring-emerald-500", "ring-offset-1");
      b.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
    } else {
      b.classList.remove("ring-2", "ring-emerald-500", "ring-offset-1");
    }
  });
}

// 9. Đồng hồ đếm ngược
function startTimer() {
  const timer = setInterval(() => {
    if (isSubmitted || timeLeft <= 0) {
      clearInterval(timer);
      if (timeLeft <= 0 && !isSubmitted) submitQuiz();
      return;
    }
    timeLeft--;
    const min = String(Math.floor(timeLeft / 60)).padStart(2, "0");
    const sec = String(timeLeft % 60).padStart(2, "0");
    timerEl.textContent = `${min}:${sec}`;
  }, 1000);
}

// 10. Chấm điểm bài thi thang điểm chuẩn
function submitQuiz() {
  isSubmitted = true;
  let correctCount = 0;
  
  allQuestions.forEach(q => {
    const sel = userAnswers[q.number];
    if (sel !== undefined && q.choices && q.choices[sel]?.correct) {
      correctCount++;
    }
  });

  alert(`🎉 Bạn đã nộp bài thành công!\nSố câu đúng: ${correctCount}/${allQuestions.length}\nHãy xem lại lời giải chi tiết và bản dịch từng câu.`);
  submitBtn.classList.add("hidden");
  renderQuestion(currentIndex);
  buildPalette();
}

// 11. Bắt sự kiện phím tắt (A, B, C, D và Phím Mũi tên)
document.addEventListener("keydown", (e) => {
  if (isSubmitted) return;
  const key = e.key.toUpperCase();
  
  // Phím chọn đáp án
  if (['A', '1'].includes(key)) selectAnswer(filteredQuestions[currentIndex].number, 0);
  if (['B', '2'].includes(key)) selectAnswer(filteredQuestions[currentIndex].number, 1);
  if (['C', '3'].includes(key)) selectAnswer(filteredQuestions[currentIndex].number, 2);
  if (['D', '4'].includes(key)) selectAnswer(filteredQuestions[currentIndex].number, 3);
  
  // Phím chuyển câu
  if (e.key === "ArrowLeft" && currentIndex > 0) renderQuestion(currentIndex - 1);
  if (e.key === "ArrowRight" && currentIndex < filteredQuestions.length - 1) renderQuestion(currentIndex + 1);
});

// Sự kiện nút bấm
prevBtn.onclick = () => currentIndex > 0 && renderQuestion(currentIndex - 1);
nextBtn.onclick = () => currentIndex < filteredQuestions.length - 1 && renderQuestion(currentIndex + 1);
submitBtn.onclick = () => confirm("Bạn có chắc chắn muốn nộp bài thi?") && submitQuiz();
if (examSelect) examSelect.onchange = (e) => loadExam(e.target.value);

// Lắng nghe click các tab Part 1 -> Part 7
document.querySelectorAll("#partFilterContainer .part-tab-btn").forEach(btn => {
  btn.onclick = () => applyPartFilter(btn.getAttribute("data-part"));
});

// Khởi chạy ứng dụng
loadExam("data.json");
startTimer();