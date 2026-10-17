let questions = [];
let currentIndex = 0;
let userAnswers = {};
let isSubmitted = false;
let timeLeft = 120 * 60; // 120 phút cho toàn bộ 200 câu

const passageCol = document.getElementById("passageCol");
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

// Đổi tên initApp thành loadExam có nhận tham số fileName
async function loadExam(fileName = "data.json") {
  try {
    // Đặt lại trạng thái bài làm khi đổi đề
    userAnswers = {};
    isSubmitted = false;
    timeLeft = 120 * 60;
    document.getElementById("submitBtn").classList.remove("hidden");

    const res = await fetch(fileName);
    if (!res.ok) throw new Error("Network response was not ok");
    questions = await res.json();

    questionPalette.className = "flex space-x-1.5 overflow-x-auto max-w-sm sm:max-w-md py-1 px-1";
    buildPalette();
    renderQuestion(0);
  } catch (err) {
    console.error(err);
    alert("Không tìm thấy tệp đề thi: " + fileName);
  }
}

// 2. Trích xuất đoạn văn từ group_text cho các phần có bài đọc (Part 6, 7)
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

// 3. Trích xuất lời giải thích chi tiết
function extractExplanation(q) {
  const at = q.article_text || "";
  const keywords = ["DẪN CHỨNG", "SUY LUẬN", "Ngữ pháp", "Từ vựng", "Tìm chi tiết", "Ý chính", "Mục đích", "Đọc bảng biểu"];
  for (const kw of keywords) {
    const idx = at.indexOf(kw);
    if (idx !== -1) return at.substring(idx).trim();
  }
  return at || "Không có giải thích chi tiết cho câu hỏi này.";
}

// 4. Hiển thị nội dung từng câu hỏi
function renderQuestion(index) {
  currentIndex = index;
  const q = questions[index];
  if (!q) return;

  questionCounter.textContent = `Câu ${index + 1}/${questions.length}`;
  partBadge.textContent = q.part || "TOEIC";
  
  // Tránh lặp số thứ tự câu hỏi
  questionText.textContent = q.question.startsWith(`${q.number}.`) 
    ? q.question 
    : `${q.number || index + 1}. ${q.question}`;

  // Dọn dẹp các thẻ ảnh/âm thanh cũ tạo ra ở câu trước
  const oldMedia = passageCol.querySelector(".dynamic-media");
  if (oldMedia) oldMedia.remove();

  const passage = extractPassage(q);
  const hasImages = q.media && q.media.images && q.media.images.length > 0;
  const hasAudio = q.media && q.media.audio && q.media.audio.length > 0;

  // Hiển thị cột trái nếu có bài đọc, hình ảnh minh họa hoặc file nghe
  if (passage || hasImages || hasAudio) {
    passageCol.classList.remove("hidden");
    questionCol.classList.remove("lg:col-span-12");
    questionCol.classList.add("lg:col-span-6");

    const mediaContainer = document.createElement("div");
    mediaContainer.className = "dynamic-media mb-4 space-y-3";

    if (hasAudio) {
      mediaContainer.innerHTML += `
        <div class="bg-slate-50 p-2 rounded border border-slate-200">
          <span class="text-xs font-semibold text-slate-500 block mb-1">🎧 Đoạn nghe Audio:</span>
          <audio controls src="${q.media.audio[0]}" class="w-full h-8"></audio>
        </div>`;
    }
    if (hasImages) {
      mediaContainer.innerHTML += `
        <div class="text-center">
          <img src="${q.media.images[0]}" class="max-h-72 object-contain mx-auto rounded border border-slate-200 shadow-sm" alt="TOEIC Graphic" />
        </div>`;
    }

    passageCol.insertBefore(mediaContainer, passageText);
    passageText.textContent = passage;
  } else {
    // Tự động thu gọn giao diện thành 1 cột cho Part 5
    passageCol.classList.add("hidden");
    questionCol.classList.remove("lg:col-span-6");
    questionCol.classList.add("lg:col-span-12");
  }

  // Hiển thị danh sách lựa chọn A, B, C, D
  optionsContainer.innerHTML = "";
  const choices = q.choices || [];
  
  choices.forEach((choice, i) => {
    const isSelected = userAnswers[q.number] === i;
    const btn = document.createElement("button");
    btn.className = `w-full text-left p-3.5 rounded-lg border text-sm font-medium transition flex flex-col space-y-1 ${
      isSelected
        ? "border-blue-600 bg-blue-50 text-blue-900 ring-1 ring-blue-500"
        : "border-slate-200 hover:bg-slate-50 text-slate-700"
    }`;

    // Tô màu kết quả đúng/sai sau khi nộp bài
    if (isSubmitted) {
      btn.disabled = true;
      if (choice.correct) {
        btn.classList.add("!border-emerald-500", "!bg-emerald-50", "!text-emerald-900");
      } else if (isSelected && !choice.correct) {
        btn.classList.add("!border-red-500", "!bg-red-50", "!text-red-900");
      }
    }

    // Tách ký tự (A), (B) và nội dung văn bản
    const rawText = choice.text || "";
    const match = rawText.match(/^\(([A-D])\)\s*([\s\S]*)$/);
    const label = match ? match[1] : String.fromCharCode(65 + i);
    const content = match ? match[2].trim() : rawText.trim();

    let innerHtml = `
      <div class="flex items-center space-x-3 w-full">
        <span class="w-7 h-7 shrink-0 rounded-full flex items-center justify-center font-bold border ${
          isSelected 
            ? "bg-blue-600 text-white border-blue-600" 
            : "bg-white text-slate-500 border-slate-300"
        }">${label}</span>
        <span class="font-normal text-slate-800">${content}</span>
      </div>
    `;

    // Hiển thị thêm bản dịch tiếng Việt sau khi nộp bài
    if (isSubmitted && choice.translation) {
      innerHtml += `<div class="text-xs text-slate-500 pl-10 italic">Nghĩa: ${choice.translation}</div>`;
    }

    btn.innerHTML = innerHtml;
    btn.onclick = () => {
      if (!isSubmitted) {
        userAnswers[q.number] = i;
        renderQuestion(currentIndex);
        buildPalette();
      }
    };
    optionsContainer.appendChild(btn);
  });

  // Hiển thị giải thích sau khi hoàn thành bài
  if (isSubmitted) {
    explanationBox.classList.remove("hidden");
    explanationText.textContent = extractExplanation(q);
  } else {
    explanationBox.classList.add("hidden");
  }

  document.getElementById("prevBtn").disabled = index === 0;
  document.getElementById("nextBtn").disabled = index === questions.length - 1;
}

// 5. Tạo danh sách nút bấm số câu hỏi
function buildPalette() {
  questionPalette.innerHTML = "";
  questions.forEach((q, idx) => {
    const pBtn = document.createElement("button");
    pBtn.textContent = q.number || (idx + 1);
    pBtn.className = `w-7 h-7 shrink-0 rounded text-xs font-semibold border ${
      currentIndex === idx ? "ring-2 ring-blue-500 " : ""
    } ${
      userAnswers[q.number] !== undefined
        ? "bg-blue-600 text-white border-blue-600"
        : "bg-white text-slate-600 border-slate-200 hover:bg-slate-100"
    }`;
    pBtn.onclick = () => {
      renderQuestion(idx);
      buildPalette();
    };
    questionPalette.appendChild(pBtn);
  });
}

// 6. Đồng hồ đếm ngược
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

// 7. Chấm điểm bài thi
function submitQuiz() {
  isSubmitted = true;
  let correctCount = 0;
  questions.forEach(q => {
    const selectedIdx = userAnswers[q.number];
    if (selectedIdx !== undefined && q.choices && q.choices[selectedIdx]?.correct) {
      correctCount++;
    }
  });

  alert(`Hoàn thành bài thi ETS 2024 Test 1!\nKết quả: ${correctCount}/${questions.length} câu đúng.`);
  document.getElementById("submitBtn").classList.add("hidden");
  renderQuestion(currentIndex);
}

document.getElementById("prevBtn").onclick = () => currentIndex > 0 && renderQuestion(currentIndex - 1);
document.getElementById("nextBtn").onclick = () => currentIndex < questions.length - 1 && renderQuestion(currentIndex + 1);
document.getElementById("submitBtn").onclick = () => confirm("Bạn có chắc chắn muốn nộp bài thi?") && submitQuiz();

const examSelect = document.getElementById("examSelect");
if (examSelect) {
  examSelect.onchange = (e) => loadExam(e.target.value);
}

// Bắt đầu với đề thi mặc định
loadExam("data.json");
startTimer();