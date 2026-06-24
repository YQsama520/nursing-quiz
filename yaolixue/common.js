/* ═══════════════════════════════════════════════════════════════════════════
   COMMON — shared by all pages
   ═══════════════════════════════════════════════════════════════════════════ */

/* ─── 1. DATA & STATE ─── */
const DATA = QUESTION_DATA.subjects;
const LS_KEY = 'nursing_quiz_progress';

function loadState() {
  try { return JSON.parse(localStorage.getItem(LS_KEY)) || {} } catch (e) { return {} }
}
function saveState() { localStorage.setItem(LS_KEY, JSON.stringify(state)) }

var state = loadState();

function getSubjectState(subjId) {
  if (!state[subjId]) {
    state[subjId] = { done:0, correct:0, wrong:0, wrongIds:[], choices:{}, results:{} };
  }
  var p = state[subjId];
  if (!p.choices) p.choices = {};
  if (!p.results) p.results = {};
  if (!p.wrongIds) p.wrongIds = [];
  return p;
}

/* ─── 2. Question key helpers ─── */
function qKey(q) {
  return q.section ? q.section + '::' + q.id : String(q.id);
}
function findQ(subj, key) {
  var sep = key.indexOf('::');
  if (sep === -1) return subj.questions.find(function(x) { return String(x.id) === key; });
  var section = key.slice(0, sep);
  var id = key.slice(sep + 2);
  return subj.questions.find(function(x) { return x.section === section && String(x.id) === id; });
}
function findSubject(q) {
  for (var i = 0; i < DATA.length; i++) {
    if (DATA[i].questions.indexOf(q) !== -1) return DATA[i];
  }
  return null;
}

/* ─── 3. Utility ─── */
function shuffle(arr) {
  for (var i = arr.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp;
  }
  return arr;
}

function highlightMatch(text, kw) {
  if (!kw) return text;
  var esc = kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  var parts = esc.split(' ');
  var re = new RegExp('(' + parts.join('|') + ')', 'gi');
  return text.replace(re, '<span class="src-match">$1</span>');
}

/* ─── 4. Booksmarks ─── */
function countBookmarks() {
  return state.bookmarks ? Object.keys(state.bookmarks).length : 0;
}

/* ─── 5. ENCOURAGEMENT ─── */
var ENC_MSGS = {
  yc_总论: { icon: '💪', msg: '总论满分通过！对药理学基础掌握得真扎实！' },
  yc_传出神经: { icon: '🧠', msg: '传出神经系统全对！宝宝太厉害了！' },
  yc_中枢神经: { icon: '✨', msg: '中枢神经全部拿下！宝宝真聪明！' },
  yc_心血管: { icon: '❤️', msg: '心血管系统全通关！宝宝太棒了！' },
  yc_血液: { icon: '🩸', msg: '血液系统全对！状态拉满！' },
  yc_化学治疗: { icon: '🎯', msg: '化疗药物全部答对！宝宝无敌了！' },
  yc_内脏药理: { icon: '🌟', msg: '内脏药理全掌握！宝宝好厉害！' },
  yc_综合题库: { icon: '👑', msg: '综合题库全对！宝宝是最棒的！' },
  waike: { icon: '🏆', msg: '外科护理全通关！大神级别！' },
  infect: { icon: '📚', msg: '传染病全部拿下！学霸本霸！' },
  ped: { icon: '👶', msg: '儿科满分！超有爱！' },
  emerg: { icon: '🚀', msg: '急危重症全部攻克！太强了！' },
};

var ALL_DONE_MSGS = [
  { icon: '🌟', msg: '所有错题全部攻克！宝宝是天才吗！' },
  { icon: '🎉', msg: '完美通关！没有什么能难倒我家宝宝！' },
  { icon: '👸', msg: '错题清零！宝宝最棒了！奖励一朵小红花🌺' },
  { icon: '🌈', msg: '全部答对！今晚加鸡腿！🍗' },
  { icon: '🏅', msg: '学霸认证！错题本已清空！' },
];

function showEnc(icon, title, text) {
  document.getElementById('encIcon').textContent = icon;
  document.getElementById('encTitle').textContent = title;
  document.getElementById('encText').textContent = text;
  document.getElementById('encPopup').classList.add('show');
}

function closeEnc() {
  document.getElementById('encPopup').classList.remove('show');
}

/* ─── 6. SPARKLES ─── */
var SPARKLES = ['🌸','💗','✨','🦋','🌷','💕','🫧','🎀'];

function startSparkles() {
  var layer = document.getElementById('sparkleLayer');
  if (!layer) return;
  layer.innerHTML = '';
  for (var i = 0; i < 12; i++) {
    var s = document.createElement('div');
    s.className = 'sparkle';
    s.textContent = SPARKLES[Math.floor(Math.random() * SPARKLES.length)];
    s.style.left = Math.random() * 100 + '%';
    s.style.animationDuration = (8 + Math.random() * 12) + 's';
    s.style.animationDelay = (Math.random() * 12) + 's';
    s.style.fontSize = (12 + Math.random() * 14) + 'px';
    layer.appendChild(s);
  }
}

function stopSparkles() {
  var l = document.getElementById('sparkleLayer');
  if (l) l.innerHTML = '';
}

/* ─── 7. CUTE MODE / EASTER EGG ─── */
var EGG_KEY = 'yaoli_egg_shown';
var CUTE_KEY = 'yaoli_cute_mode';

function checkEasterEgg() {
  var total = 0;
  DATA.forEach(function(s) {
    var p = state[s.id];
    if (p) total += p.done || 0;
  });
  if (total >= 52 && !localStorage.getItem(EGG_KEY) && !localStorage.getItem(CUTE_KEY)) {
    setTimeout(function() { document.getElementById('eggModal').classList.add('show'); }, 500);
  }
}

function closeEggModal() {
  document.getElementById('eggModal').classList.remove('show');
  localStorage.setItem(EGG_KEY, '1');
  var btn = document.getElementById('styleToggle');
  if (btn) btn.style.display = 'inline-block';
}

function enableCuteMode() {
  localStorage.setItem(CUTE_KEY, '1');
  localStorage.setItem(EGG_KEY, '1');
  document.getElementById('eggModal').classList.remove('show');
  applyCuteMode();
}

function applyCuteMode() {
  if (localStorage.getItem(CUTE_KEY)) {
    document.body.classList.add('cute-mode');
    startSparkles();
    var btn = document.getElementById('styleToggle');
    if (btn) { btn.textContent = '😎 暗色'; btn.style.display = 'inline-block'; }
  }
}

function toggleStyle() {
  if (document.body.classList.contains('cute-mode')) {
    document.body.classList.remove('cute-mode');
    localStorage.removeItem(CUTE_KEY);
    document.getElementById('styleToggle').textContent = '🎀 可爱';
    stopSparkles();
  } else {
    document.body.classList.add('cute-mode');
    localStorage.setItem(CUTE_KEY, '1');
    document.getElementById('styleToggle').textContent = '😎 暗色';
    startSparkles();
  }
}

/* ─── 8. Overlay click handlers for closing modals ─── */
document.addEventListener('click', function(e) {
  if (e.target.id === 'settingsModal') closeSettingsModal();
  if (e.target.id === 'eggModal' && !e.target.closest('.modal')) closeEggModal();
});

/* ─── 9. Init: applyCuteMode on every page load ─── */
document.addEventListener('DOMContentLoaded', function() {
  applyCuteMode();
});
