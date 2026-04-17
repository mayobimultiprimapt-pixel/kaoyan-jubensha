/* 故事模式 · 视觉小说引擎
   读取 STORY 对象驱动 UI：背景 + 立绘 + 对话框 + 选项。
   特性：打字机动画 / 逐点推进 / 分支选择 / 结局统计 / localStorage 进度。
*/

const BG_CLASSES = {
  "modern-library": "bg-modern",
  "warp": "bg-warp",
  "lyon-street": "bg-lyon",
  "silk-workshop": "bg-silk",
  "uprising": "bg-uprising",
  "fog": "bg-fog",
  "london-rain": "bg-london",
  "silesia-night": "bg-silesia",
  "paris-study": "bg-paris"
};

const SAVE_KEY = "story_progress_m1";
const state = {
  scene: STORY.scene,
  tags: new Set(),
  history: [],
  typing: false,
  full: "",
  typingTimer: null
};

const $ = id => document.getElementById(id);
const setClass = (el, cls) => { el.className = cls; };

function bgClass(key) {
  return BG_CLASSES[key] || "bg-modern";
}

function save() {
  try {
    localStorage.setItem(SAVE_KEY, JSON.stringify({
      scene: state.scene,
      tags: [...state.tags],
      history: state.history.slice(-30)
    }));
  } catch (e) {}
}

function load() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return false;
    const d = JSON.parse(raw);
    if (d.scene && STORY.scenes[d.scene]) {
      state.scene = d.scene;
      state.tags = new Set(d.tags || []);
      state.history = d.history || [];
      return true;
    }
  } catch (e) {}
  return false;
}

function resetSave() {
  try { localStorage.removeItem(SAVE_KEY); } catch (e) {}
  state.scene = STORY.scene;
  state.tags = new Set();
  state.history = [];
  render();
}

function typeWriter(text, cb) {
  const box = $("dialog-text");
  box.textContent = "";
  state.typing = true;
  state.full = text;
  let i = 0;
  const step = () => {
    if (!state.typing) { box.textContent = text; cb && cb(); return; }
    if (i >= text.length) { state.typing = false; cb && cb(); return; }
    box.textContent += text[i++];
    state.typingTimer = setTimeout(step, 28);
  };
  step();
}

function skipTyping() {
  if (state.typing) {
    state.typing = false;
    clearTimeout(state.typingTimer);
    $("dialog-text").textContent = state.full;
    return true;
  }
  return false;
}

function render() {
  const sc = STORY.scenes[state.scene];
  if (!sc) { console.error("missing scene", state.scene); return; }
  save();

  // 背景
  const stage = $("stage");
  setClass(stage, "stage " + bgClass(sc.bg));

  // 立绘
  const leftEl = $("char-left");
  const rightEl = $("char-right");
  leftEl.textContent = ""; rightEl.textContent = "";
  leftEl.className = "char-slot left"; rightEl.className = "char-slot right";
  if (sc.face) {
    const slot = sc.pos === "right" ? rightEl : leftEl;
    slot.textContent = sc.face;
    slot.classList.add("visible");
  }

  // 结局
  if (sc.end) {
    renderEnding(sc);
    return;
  }

  // 对话框
  $("name-tag").textContent = sc.name || "";
  $("name-tag").style.display = sc.name ? "inline-block" : "none";

  // 清空选项
  const choicesBox = $("choices");
  choicesBox.innerHTML = "";
  choicesBox.style.display = "none";

  // 继续提示
  $("continue-hint").style.display = "none";

  // 标签记录
  if (sc.get) state.tags.add(sc.get);

  // 打字机动画
  typeWriter(sc.text, () => {
    if (sc.choices && sc.choices.length) {
      choicesBox.innerHTML = "";
      sc.choices.forEach((ch, i) => {
        const btn = document.createElement("button");
        btn.className = "choice-btn";
        btn.textContent = (i + 1) + ". " + ch.text;
        btn.onclick = () => pickChoice(ch);
        choicesBox.appendChild(btn);
      });
      choicesBox.style.display = "flex";
    } else if (sc.next) {
      $("continue-hint").style.display = "block";
    }
  });
}

function pickChoice(ch) {
  if (state.typing) { skipTyping(); return; }
  if (ch.tag) state.tags.add(ch.tag);
  state.history.push({ from: state.scene, choice: ch.text });
  state.scene = ch.next;
  render();
}

function advance() {
  if (skipTyping()) return;
  const sc = STORY.scenes[state.scene];
  if (sc.choices && sc.choices.length) return;
  if (sc.next) {
    state.history.push({ from: state.scene });
    state.scene = sc.next;
    render();
  }
}

function renderEnding(sc) {
  $("name-tag").style.display = "none";
  const choicesBox = $("choices");
  $("continue-hint").style.display = "none";
  $("dialog-text").textContent = "";
  typeWriter(sc.text, () => {
    choicesBox.innerHTML = "";
    const b1 = document.createElement("button");
    b1.className = "choice-btn";
    b1.textContent = "↺ 重新开始";
    b1.onclick = resetSave;
    choicesBox.appendChild(b1);
    const b2 = document.createElement("button");
    b2.className = "choice-btn";
    b2.textContent = "← 返回启动器";
    b2.onclick = () => { window.location.href = "../考研剧本杀合集/"; };
    choicesBox.appendChild(b2);
    choicesBox.style.display = "flex";
  });
}

// 点击舞台推进
document.addEventListener("click", e => {
  // 排除按钮区点击
  if (e.target.closest("#choices") || e.target.closest(".topbar")) return;
  advance();
});

// 快捷键：Space / Enter 推进；1-9 选项；R 重开；Esc 返回
document.addEventListener("keydown", e => {
  const sc = STORY.scenes[state.scene];
  if (!sc) return;
  if (e.key === " " || e.key === "Enter") {
    e.preventDefault();
    if (sc.choices) {
      // 不默认选第 1 项，避免误触
      return;
    }
    advance();
  } else if (/^[1-9]$/.test(e.key) && sc.choices) {
    const idx = parseInt(e.key) - 1;
    if (idx < sc.choices.length) pickChoice(sc.choices[idx]);
  } else if (e.key.toLowerCase() === "r") {
    if (confirm("重新开始本故事？")) resetSave();
  } else if (e.key === "Escape") {
    window.location.href = "../考研剧本杀合集/";
  }
});

// 启动：优先读存档，否则从头开始
(function() {
  document.getElementById("story-title").textContent = STORY.title;
  document.getElementById("story-subject").textContent = STORY.subject;
  load();
  render();
})();
