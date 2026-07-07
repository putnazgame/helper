# -*- coding: utf-8 -*-
"""
สร้างไฟล์ HTML ที่มีเสียง Google TTS ฝังอยู่ภายใน
ใช้งาน offline ได้ — ไม่ต้องต่อเน็ตเมื่อเปิดโปรแกรม

วิธีใช้:
    python build_html.py

ไฟล์ที่ได้: โปรแกรมช่วยเหลือ_offline.html
"""
import io, base64, json, os, sys

try:
    from gtts import gTTS
except ImportError:
    print("กรุณาติดตั้ง: pip install gtts")
    sys.exit(1)

# ============================================================
# รายการเมนู (อ่านจาก menu_items.json ถ้ามี)
# ============================================================
SAVE_FILE = "menu_items.json"
DEFAULT_ITEMS = [
    "ขอน้ำดื่ม",       "อยากเข้าห้องน้ำ", "ช่วยพยุงหน่อย",
    "เปิดพัดลม",        "ปิดพัดลม",         "เปิดไฟ",
    "ปิดไฟ",            "ปวดหัว",           "หิวข้าว",
    "โทรหาหมอ",         "ขอความช่วยเหลือ",  "อยากนอน",
]

if os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)
    print(f"โหลดรายการจาก {SAVE_FILE} ({len(items)} รายการ)")
else:
    items = DEFAULT_ITEMS[:]
    print(f"ใช้รายการเริ่มต้น ({len(items)} รายการ)")

# เพิ่มเสียงพิเศษ
all_texts = items + ["ใช่", "ไม่", "โปรแกรมพร้อมใช้งาน"]

# ============================================================
# สร้างเสียง
# ============================================================
def to_b64(text: str) -> str:
    tts = gTTS(text=text, lang="th", slow=False)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    return "data:audio/mpeg;base64," + base64.b64encode(buf.getvalue()).decode()

audio_map = {}
total = len(all_texts)
for i, text in enumerate(all_texts, 1):
    print(f"  [{i}/{total}] สร้างเสียง: {text}", end=" ... ", flush=True)
    try:
        audio_map[text] = to_b64(text)
        print("OK")
    except Exception as e:
        print(f"ERROR: {e}")

# ============================================================
# สร้าง HTML
# ============================================================
audio_json = json.dumps(audio_map, ensure_ascii=False)
items_json = json.dumps(items,     ensure_ascii=False)

html = f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#12121e">
<title>โปรแกรมช่วยเหลือ</title>
<style>
:root {{
  --bg:     #12121e;
  --card-n: #2a2c44;
  --card-s: #1c62d0;
  --card-b: #5088ff;
  --text:   #f0f0f0;
  --title:  #64beff;
  --yes:    #1a7840;
  --no:     #992222;
  --stat:   #8cff8c;
  --panel:  #1c1c34;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }}
body {{
  background: var(--bg);
  color: var(--text);
  font-family: 'Sarabun','Tahoma',sans-serif;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  user-select: none;
}}
header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 18px;
  flex-shrink: 0;
  min-height: 64px;
}}
header h1 {{ font-size: clamp(24px,4vw,40px); color: var(--title); }}
#editBtn {{
  background: rgba(80,136,255,.15);
  border: 2px solid var(--card-b);
  color: var(--title);
  padding: 8px 18px;
  border-radius: 12px;
  font-size: clamp(16px,2.5vw,24px);
  cursor: pointer;
  font-family: inherit;
}}
#addBar {{
  display: none;
  gap: 10px;
  padding: 8px 16px;
  flex-shrink: 0;
  background: rgba(80,136,255,.08);
  border-bottom: 1px solid #334;
}}
#addBar.show {{ display: flex; }}
#newInput {{
  flex: 1;
  background: #34345a;
  border: 2px solid var(--card-b);
  border-radius: 12px;
  color: white;
  font-size: clamp(18px,2.5vw,26px);
  padding: 10px 14px;
  font-family: inherit;
  outline: none;
}}
#addBtn {{
  background: #1a7840;
  border: none;
  border-radius: 12px;
  color: white;
  font-size: clamp(18px,2.5vw,26px);
  padding: 10px 20px;
  cursor: pointer;
  font-family: inherit;
  white-space: nowrap;
}}
#grid {{
  flex: 1;
  display: grid;
  grid-template-columns: repeat(3,1fr);
  gap: 12px;
  padding: 10px 16px;
  overflow-y: auto;
  align-content: start;
}}
@media (max-width: 480px) {{ #grid {{ grid-template-columns: repeat(2,1fr); }} }}
.card {{
  background: var(--card-n);
  border-radius: 18px;
  border: 3px solid transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: clamp(20px,3.2vw,38px);
  padding: 14px 10px;
  min-height: clamp(90px,14vh,140px);
  cursor: pointer;
  position: relative;
  transition: background .12s, border-color .12s, transform .08s;
  word-break: break-word;
  line-height: 1.35;
}}
.card:active {{ transform: scale(.96); }}
.card.active  {{ background: var(--card-s); border-color: var(--card-b); }}
.edit-mode .card {{
  background: #4a1a1a;
  border-color: #cc3333;
}}
.edit-mode .card::after {{
  content: "✕ แตะเพื่อลบ";
  position: absolute;
  bottom: 6px; right: 10px;
  font-size: clamp(12px,1.8vw,18px);
  color: #ff8888;
  opacity: .85;
}}
#yesno {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 10px 16px;
  flex-shrink: 0;
}}
.yn {{
  border: none;
  border-radius: 16px;
  font-size: clamp(22px,3.8vw,42px);
  padding: 18px;
  cursor: pointer;
  color: white;
  font-family: inherit;
  transition: opacity .1s, transform .08s;
}}
.yn:active {{ transform: scale(.96); opacity: .85; }}
#yesBtn {{ background: var(--yes); }}
#noBtn  {{ background: var(--no);  }}
#status {{
  background: rgba(0,0,0,.35);
  padding: 8px 18px;
  font-size: clamp(14px,2vw,24px);
  color: var(--stat);
  flex-shrink: 0;
  min-height: 40px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
</style>
</head>
<body>
<header>
  <h1>โปรแกรมช่วยเหลือ</h1>
  <button id="editBtn" onclick="toggleEdit()">✏ แก้ไข</button>
</header>
<div id="addBar">
  <input id="newInput" type="text" placeholder="พิมพ์รายการใหม่แล้วกด เพิ่ม">
  <button id="addBtn" onclick="addItem()">+ เพิ่ม</button>
</div>
<div id="grid"></div>
<div id="yesno">
  <button class="yn" id="yesBtn" onclick="say('ใช่')">✓&nbsp; ใช่</button>
  <button class="yn" id="noBtn"  onclick="say('ไม่')">✗&nbsp; ไม่</button>
</div>
<div id="status">กำลังโหลด...</div>
<script>
// ── เสียงที่ฝังไว้ล่วงหน้า (Google TTS, ใช้ offline) ────────
const AUDIO = {audio_json};

// ── รายการเมนู ───────────────────────────────────────────────
const DEFAULT = {items_json};
let items    = JSON.parse(localStorage.getItem("items") || "null") || DEFAULT.slice();
let editMode = false;
let speaking = false;
let selIdx   = 0;
let lastSpeak  = 0;
let lastScroll = 0;

function save() {{ localStorage.setItem("items", JSON.stringify(items)); }}

// ── Render ───────────────────────────────────────────────────
function render() {{
  const grid = document.getElementById("grid");
  grid.innerHTML = "";
  grid.className = editMode ? "edit-mode" : "";
  items.forEach((item, i) => {{
    const card = document.createElement("div");
    card.className = "card" + (i === selIdx ? " active" : "");
    card.textContent = item;
    card.addEventListener("click", () => {{
      if (editMode) {{
        if (confirm('ลบ "' + item + '" ใช่ไหม?')) deleteItem(i);
      }} else {{
        selIdx = i; highlight(); say(item);
      }}
    }});
    grid.appendChild(card);
  }});
}}

function highlight() {{
  document.querySelectorAll(".card").forEach((c,i) =>
    c.classList.toggle("active", i === selIdx));
  document.querySelectorAll(".card")[selIdx]?.scrollIntoView({{block:"nearest"}});
}}

// ── Audio cache (localStorage) สำหรับรายการที่เพิ่มใหม่ ─────
function getCached(text) {{
  return localStorage.getItem("gtts_" + text) || null;
}}
function setCached(text, b64) {{
  try {{ localStorage.setItem("gtts_" + text, b64); }} catch(e) {{}}
}}

// ── ดึงเสียง Google TTS ────────────────────────────────────────
async function fetchGoogleAudio(text) {{
  const url = "https://translate.googleapis.com/translate_tts?ie=UTF-8&q="
    + encodeURIComponent(text) + "&tl=th&client=gtx&sl=th";
  const resp = await fetch(url);
  if (!resp.ok) throw new Error("HTTP " + resp.status);
  const blob = await resp.blob();
  return new Promise((res, rej) => {{
    const r = new FileReader();
    r.onload  = () => res(r.result);
    r.onerror = rej;
    r.readAsDataURL(blob);
  }});
}}

// ── TTS หลัก ─────────────────────────────────────────────────
function say(text) {{
  if (speaking) return;
  const now = Date.now();
  if (now - lastSpeak < 900) return;
  lastSpeak = now;
  speaking  = true;
  setStatus("กำลังพูด: " + text);

  // 1) เสียงฝังไว้  2) localStorage cache  3) fallback
  const src = AUDIO[text] || getCached(text);
  if (src) {{
    playB64(src, text);
  }} else {{
    fallbackTTS(text);
  }}
}}

function playB64(src, text) {{
  const audio = new Audio(src);
  audio.onended = () => {{ speaking = false; setStatus("เลือก: " + text); }};
  audio.onerror = () => {{ speaking = false; fallbackTTS(text); }};
  audio.play().catch(() => {{ speaking = false; fallbackTTS(text); }});
}}

function fallbackTTS(text) {{
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "th-TH"; u.rate = 0.92; u.volume = 1;
  u.onend  = () => {{ speaking = false; setStatus("เลือก: " + text); }};
  u.onerror = () => {{ speaking = false; setStatus("เสียงผิดพลาด: " + text); }};
  window.speechSynthesis.speak(u);
}}

function setStatus(msg) {{ document.getElementById("status").textContent = msg; }}

// ── โหมดแก้ไข ────────────────────────────────────────────────
function toggleEdit() {{
  editMode = !editMode;
  document.getElementById("editBtn").textContent = editMode ? "✓ เสร็จ" : "✏ แก้ไข";
  document.getElementById("addBar").className    = editMode ? "show" : "";
  setStatus(editMode
    ? "โหมดแก้ไข — แตะการ์ดเพื่อลบ | พิมพ์ด้านบนเพื่อเพิ่ม"
    : "พร้อมใช้งาน — แตะการ์ดเพื่อพูด");
  render();
}}

async function addItem() {{
  const inp  = document.getElementById("newInput");
  const text = inp.value.trim();
  if (!text) return;
  items.push(text);
  save();
  inp.value = "";
  selIdx = items.length - 1;
  render();

  // ดึงเสียง Google แล้วเก็บใน localStorage
  setStatus("กำลังดาวน์โหลดเสียง Google: " + text + " ...");
  try {{
    const b64 = await fetchGoogleAudio(text);
    setCached(text, b64);
    setStatus("เพิ่มแล้ว: " + text + " ✓ เสียง Google (offline แล้ว)");
  }} catch(e) {{
    setStatus("เพิ่มแล้ว: " + text + " (ไม่มีเน็ต — ใช้เสียง browser)");
  }}
}}

function deleteItem(i) {{
  items.splice(i, 1);
  save();
  selIdx = Math.min(selIdx, Math.max(0, items.length - 1));
  render();
}}

// ── Gamepad (F710) ────────────────────────────────────────────
let gpLoop = null;
let gpState = {{ lt: false, lb: false, back: false }};
const COLS_GP = window.innerWidth < 480 ? 2 : 3;

function gpTick() {{
  const gp = [...(navigator.getGamepads?.() ?? [])].find(g => g);
  if (!gp) return;
  const now = Date.now();
  const SC = 300, SEL = 1100;

  if (gp.buttons[12]?.pressed && now-lastScroll>SC) {{ selIdx=Math.max(0,selIdx-COLS_GP); highlight(); lastScroll=now; }}
  if (gp.buttons[13]?.pressed && now-lastScroll>SC) {{ selIdx=Math.min(items.length-1,selIdx+COLS_GP); highlight(); lastScroll=now; }}
  if (gp.buttons[14]?.pressed && now-lastScroll>SC) {{ if(selIdx%COLS_GP>0){{ selIdx--; highlight(); }} lastScroll=now; }}
  if (gp.buttons[15]?.pressed && now-lastScroll>SC) {{ if(selIdx%COLS_GP<COLS_GP-1&&selIdx+1<items.length){{ selIdx++; highlight(); }} lastScroll=now; }}

  const ay = gp.axes[1] ?? 0;
  if (ay > 0.45 && now-lastScroll>SC) {{ selIdx=Math.min(items.length-1,selIdx+COLS_GP); highlight(); lastScroll=now; }}
  else if (ay < -0.45 && now-lastScroll>SC) {{ selIdx=Math.max(0,selIdx-COLS_GP); highlight(); lastScroll=now; }}
  const ax = gp.axes[0] ?? 0;
  if (ax > 0.45 && now-lastScroll>SC) {{ if(selIdx%COLS_GP<COLS_GP-1&&selIdx+1<items.length){{ selIdx++; highlight(); }} lastScroll=now; }}
  else if (ax < -0.45 && now-lastScroll>SC) {{ if(selIdx%COLS_GP>0){{ selIdx--; highlight(); }} lastScroll=now; }}

  const lb = gp.buttons[4]?.pressed || gp.buttons[10]?.pressed;
  if (lb && !gpState.lb && now-lastSpeak>SEL) say(items[selIdx]);
  gpState.lb = lb;

  const lt = gp.buttons[6]?.pressed;
  if (lt && !gpState.lt) say("ใช่");
  gpState.lt = lt;

  const back = gp.buttons[8]?.pressed;
  if (back && !gpState.back && now-lastSpeak>SEL) say("ไม่");
  gpState.back = back;
}}

window.addEventListener("gamepadconnected", e => {{
  setStatus("เชื่อมต่อจอย: " + e.gamepad.id);
  gpLoop = gpLoop || setInterval(gpTick, 50);
}});
window.addEventListener("gamepaddisconnected", () => {{
  clearInterval(gpLoop); gpLoop = null;
}});

document.getElementById("newInput").addEventListener("keydown", e => {{
  if (e.key === "Enter") addItem();
}});

// เริ่มต้น
render();
say("โปรแกรมพร้อมใช้งาน");
setStatus("พร้อมใช้งาน — แตะการ์ดเพื่อพูด (เสียง Google offline)");
</script>
</body>
</html>"""

# ============================================================
# บันทึกไฟล์
# ============================================================
out = "โปรแกรมช่วยเหลือ_offline.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

size_kb = os.path.getsize(out) // 1024
print(f"\nสร้างสำเร็จ: {out}  ({size_kb} KB)")
print("เปิดด้วย Chrome ได้เลย — ใช้งาน offline ได้ทันที")
