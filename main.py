# -*- coding: utf-8 -*-
"""
ระบบช่วยเหลือ
- Grid การ์ด 3 คอลัมน์ (ไม่ต้องเลื่อนเยอะ)
- ปุ่มใช่ / ไม่ กดได้ตลอดเวลา
- เพิ่ม / ลบ รายการได้
"""
import pygame, pyttsx3, time, threading, io, os, sys, json

# ============================================================
# ตั้งค่าหน้าจอ
# ============================================================
SCREEN_W, SCREEN_H, FPS = 0, 0, 30   # จะอ่านจากหน้าจอจริงตอน init

# ============================================================
# สี
# ============================================================
BG        = (18,  18,  30)
CARD_N    = (42,  44,  68)
CARD_S    = (28,  98, 208)
CARD_BOR  = (80, 140, 255)
TEXT_W    = (240, 240, 240)
TITLE_C   = (100, 190, 255)
YES_C     = (28, 130,  72)
NO_C      = (165,  42,  42)
STAT_C    = (140, 255, 140)
STAT_E    = (255, 110, 110)
PANEL_BG  = (28,  28,  52)
INPUT_BG  = (52,  52,  84)
INPUT_BOR = (100, 155, 255)

# ============================================================
# ไฟล์บันทึกรายการ & ค่าเริ่มต้น
# ============================================================
SAVE_FILE     = "menu_items.json"
DEFAULT_ITEMS = [
    "ขอน้ำดื่ม",       "อยากเข้าห้องน้ำ", "ช่วยพยุงหน่อย",
    "เปิดพัดลม",        "ปิดพัดลม",         "เปิดไฟ",
    "ปิดไฟ",            "ปวดหัว",           "หิวข้าว",
    "โทรหาหมอ",         "ขอความช่วยเหลือ",  "อยากนอน",
]

# ============================================================
# ปุ่ม Joystick — Logitech F710 (XInput mode)
# LB=4  LT=axis2  L3=8  Back=6  Start=7
# ============================================================
CONFIRM_BTNS = {4, 8}    # LB / L3         →  เลือกการ์ด
NO_BTNS      = {6}       # Back            →  ไม่
YES_BTNS     = set()     # LT เป็น axis ดูข้างล่าง

LT_AXIS      = 4         # axis ของ LT บน F710 (ปล่อย=-1.0, กดสุด=+1.0)
LT_THR       = -0.7      # กดเบาๆ นิดเดียวก็ trigger (ยิ่งต่ำยิ่งไวขึ้น)

# ============================================================
# Debounce
# ============================================================
SCROLL_CD  = 0.27
SELECT_CD  = 1.10
AXIS_THR   = 0.45

# Layout
COLS      = 3
TITLE_H   = 90
YESNO_H   = 110
STATUS_H  = 56
GRID_PAD  = 22
CARD_GAP  = 14


# ============================================================
# ฟังก์ชันช่วย
# ============================================================
def find_thai_font():
    for p in [
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\leelawadee.ttf",
        r"C:\Windows\Fonts\leelawui.ttf",
        r"C:\Windows\Fonts\THSarabunNew.ttf",
        r"C:\Windows\Fonts\cordia.ttf",
        "/usr/share/fonts/truetype/thai/tlwg/Loma.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ]:
        if os.path.exists(p):
            return p
    return None


def _audio_dir() -> str:
    """คืน path ของโฟลเดอร์ audio (รองรับทั้ง .py และ EXE)"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "audio")


def speak_gtts(text: str) -> bool:
    # 1) เล่นจากไฟล์ MP3 ที่เตรียมไว้ (offline)
    mp3 = os.path.join(_audio_dir(), text + ".mp3")
    if os.path.exists(mp3):
        try:
            pygame.mixer.music.load(mp3)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            return True
        except Exception:
            pass

    # 2) fallback — ดึงจาก gTTS (ต้องการ internet)
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="th", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        pygame.mixer.music.load(buf, "mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
        return True
    except Exception:
        return False


def load_items():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return data
        except Exception:
            pass
    return DEFAULT_ITEMS[:]


def save_items(items):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


# ============================================================
# คลาสหลัก
# ============================================================
class HemiInterface:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("โปรแกรมช่วยเหลือ")
        self.clock = pygame.time.Clock()

        # อ่านขนาดหน้าจอจริง (เต็มจอ)
        global SCREEN_W, SCREEN_H
        SCREEN_W, SCREEN_H = self.screen.get_size()

        # โหลดฟอนต์ (ขนาดใหญ่ขึ้น)
        fp = find_thai_font()
        mk = lambda s: (pygame.font.Font(fp, s) if fp
                        else pygame.font.SysFont("tahoma", s, bold=True))
        self.f_title  = mk(52)
        self.f_card   = mk(46)
        self.f_small  = mk(34)
        self.f_input  = mk(40)
        self.f_yesno  = mk(44)

        # โหลดรายการ
        self.items   = load_items()
        self.sel_idx = 0
        self.row_off = 0

        # Debounce
        self.t_scroll = 0.0
        self.t_select = 0.0
        self.ax_moved = False   # axis Y
        self.ax_x_mv  = False   # axis X
        self.lt_held  = False   # LT กำลังถูกกดอยู่ (ป้องกัน repeat)

        # สถานะ
        self.status_text = "พร้อมใช้งาน"
        self.status_ok   = True
        self.speaking    = False

        # โหมดแก้ไข
        self.edit_mode    = False
        self.input_text   = ""
        self.input_active = False

        # คำนวณกริด
        self._calc_grid()

        # Joystick
        pygame.joystick.init()
        self.js = None
        if pygame.joystick.get_count() > 0:
            self.js = pygame.joystick.Joystick(0)
            self.status_text = f"จอย: {self.js.get_name()}"
        else:
            self.status_text = "ไม่พบจอย — ใช้ ↑↓←→ Enter Y N E"

        self._say("ระบบพร้อมใช้งาน")

    # ----------------------------------------------------------
    def _calc_grid(self):
        grid_h = SCREEN_H - TITLE_H - YESNO_H - STATUS_H - GRID_PAD * 2
        rows_vis = max(1, grid_h // 120)
        self.card_h    = (grid_h - CARD_GAP * (rows_vis - 1)) // rows_vis
        self.card_w    = (SCREEN_W - GRID_PAD * 2 - CARD_GAP * (COLS - 1)) // COLS
        self.rows_vis  = rows_vis
        self.grid_top  = TITLE_H + GRID_PAD

    # ----------------------------------------------------------
    # TTS
    # ----------------------------------------------------------
    def _say(self, text: str):
        if self.speaking:
            return
        self.speaking    = True
        self.status_text = f"กำลังพูด: {text}"
        self.status_ok   = True

        def worker():
            ok = speak_gtts(text)
            self.speaking    = False
            self.status_text = f"{'เลือก' if ok else 'เสียงผิดพลาด'}: {text}"
            self.status_ok   = ok

        threading.Thread(target=worker, daemon=True).start()

    # ----------------------------------------------------------
    # การเลื่อน / เลือก
    # ----------------------------------------------------------
    def _can(self, t_attr, cd):
        return (time.monotonic() - getattr(self, t_attr)) >= cd

    def move(self, dr, dc):
        if not self._can("t_scroll", SCROLL_CD):
            return
        self.t_scroll = time.monotonic()
        row = self.sel_idx // COLS + dr
        col = self.sel_idx % COLS + dc
        max_row = (len(self.items) - 1) // COLS
        row = max(0, min(row, max_row))
        col = max(0, min(col, COLS - 1))
        idx = row * COLS + col
        self.sel_idx = min(idx, len(self.items) - 1)
        # เลื่อน scroll
        if row < self.row_off:
            self.row_off = row
        elif row >= self.row_off + self.rows_vis:
            self.row_off = row - self.rows_vis + 1

    def select_item(self):
        if not self._can("t_select", SELECT_CD) or self.speaking or not self.items:
            return
        self.t_select = time.monotonic()
        self._say(self.items[self.sel_idx])

    def say_yes(self):
        self._say("ใช่")

    def say_no(self):
        self._say("ไม่")

    # ----------------------------------------------------------
    # โหมดแก้ไข
    # ----------------------------------------------------------
    def toggle_edit(self):
        self.edit_mode    = not self.edit_mode
        self.input_active = False
        self.input_text   = ""
        pygame.key.stop_text_input()
        self.status_text = ("โหมดแก้ไข — [Delete]=ลบ  [A]=เพิ่ม  [E]=ออก"
                            if self.edit_mode else "พร้อมใช้งาน")

    def delete_selected(self):
        if not self.items:
            return
        name = self.items.pop(self.sel_idx)
        self.sel_idx = min(self.sel_idx, max(0, len(self.items) - 1))
        save_items(self.items)
        self.status_text = f"ลบแล้ว: {name}"

    def start_input(self):
        self.input_text   = ""
        self.input_active = True
        pygame.key.start_text_input()
        self.status_text = "พิมพ์รายการใหม่ แล้วกด Enter"

    def confirm_input(self):
        text = self.input_text.strip()
        if text:
            self.items.append(text)
            save_items(self.items)
            self.sel_idx     = len(self.items) - 1
            self.status_text = f"เพิ่มแล้ว: {text}"
        self.input_text   = ""
        self.input_active = False
        pygame.key.stop_text_input()

    # ----------------------------------------------------------
    # Events
    # ----------------------------------------------------------
    def handle_events(self) -> bool:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False

            # ---- Keyboard ----
            if ev.type == pygame.KEYDOWN:
                if self.input_active:
                    if ev.key == pygame.K_RETURN:      self.confirm_input()
                    elif ev.key == pygame.K_ESCAPE:
                        self.input_active = False
                        self.input_text   = ""
                        pygame.key.stop_text_input()
                    elif ev.key == pygame.K_BACKSPACE:  self.input_text = self.input_text[:-1]

                elif self.edit_mode:
                    if ev.key in (pygame.K_e, pygame.K_ESCAPE): self.toggle_edit()
                    elif ev.key in (pygame.K_DELETE, pygame.K_BACKSPACE): self.delete_selected()
                    elif ev.key == pygame.K_a:     self.start_input()
                    elif ev.key == pygame.K_UP:    self.move(-1, 0)
                    elif ev.key == pygame.K_DOWN:  self.move(1, 0)
                    elif ev.key == pygame.K_LEFT:  self.move(0, -1)
                    elif ev.key == pygame.K_RIGHT: self.move(0, 1)

                else:
                    if ev.key == pygame.K_ESCAPE:      return False
                    elif ev.key == pygame.K_e:         self.toggle_edit()
                    elif ev.key == pygame.K_UP:        self.move(-1, 0)
                    elif ev.key == pygame.K_DOWN:      self.move(1, 0)
                    elif ev.key == pygame.K_LEFT:      self.move(0, -1)
                    elif ev.key == pygame.K_RIGHT:     self.move(0, 1)
                    elif ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                        self.select_item()
                    elif ev.key == pygame.K_y:         self.say_yes()
                    elif ev.key == pygame.K_n:         self.say_no()

            # ---- Text Input (Thai IME) ----
            elif ev.type == pygame.TEXTINPUT and self.input_active:
                self.input_text += ev.text

            # ---- D-pad ----
            elif ev.type == pygame.JOYHATMOTION:
                hx, hy = ev.value
                if hy == 1:    self.move(-1, 0)
                elif hy == -1: self.move(1, 0)
                elif hx == -1: self.move(0, -1)
                elif hx == 1:  self.move(0, 1)

            # ---- Analog Stick ----
            elif ev.type == pygame.JOYAXISMOTION:
                if ev.axis == 1:   # Y axis
                    if ev.value > AXIS_THR and not self.ax_moved:
                        self.ax_moved = True;  self.move(1, 0)
                    elif ev.value < -AXIS_THR and not self.ax_moved:
                        self.ax_moved = True;  self.move(-1, 0)
                    elif abs(ev.value) < AXIS_THR * 0.5:
                        self.ax_moved = False
                elif ev.axis == 0: # X axis
                    if ev.value > AXIS_THR and not self.ax_x_mv:
                        self.ax_x_mv = True;   self.move(0, 1)
                    elif ev.value < -AXIS_THR and not self.ax_x_mv:
                        self.ax_x_mv = True;   self.move(0, -1)
                    elif abs(ev.value) < AXIS_THR * 0.5:
                        self.ax_x_mv = False
                elif ev.axis == LT_AXIS:  # LT → ใช่ (ปล่อย=-1.0, กด=+1.0)
                    if ev.value > LT_THR and not self.lt_held:
                        self.lt_held = True
                        self.say_yes()
                    elif ev.value < 0.0:
                        self.lt_held = False

            # ---- Buttons ----
            elif ev.type == pygame.JOYBUTTONDOWN:
                if ev.button in NO_BTNS:           self.say_no()
                elif ev.button in CONFIRM_BTNS and not self.edit_mode:
                    self.select_item()

        return True

    # ----------------------------------------------------------
    # วาดหน้าจอ
    # ----------------------------------------------------------
    def draw(self):
        self.screen.fill(BG)
        self._draw_title()
        self._draw_grid()
        self._draw_yesno()
        self._draw_status()
        if self.edit_mode:
            self._draw_edit_panel()
        pygame.display.flip()

    def _draw_title(self):
        surf = self.f_title.render("โปรแกรมช่วยเหลือ", True, TITLE_C)
        self.screen.blit(surf, surf.get_rect(midleft=(18, TITLE_H // 2)))
        hint = "[E] โหมดแก้ไข" if not self.edit_mode else "[E] ออกจากแก้ไข"
        h = self.f_small.render(hint, True, (150, 150, 200))
        self.screen.blit(h, h.get_rect(midright=(SCREEN_W - 14, TITLE_H // 2)))

    def _card_rect(self, idx: int) -> pygame.Rect:
        row = idx // COLS - self.row_off
        col = idx % COLS
        x   = GRID_PAD + col * (self.card_w + CARD_GAP)
        y   = self.grid_top + row * (self.card_h + CARD_GAP)
        return pygame.Rect(x, y, self.card_w, self.card_h)

    def _draw_grid(self):
        for i, item in enumerate(self.items):
            row = i // COLS
            if row < self.row_off or row >= self.row_off + self.rows_vis:
                continue
            rect   = self._card_rect(i)
            is_sel = (i == self.sel_idx)

            pygame.draw.rect(self.screen, CARD_S if is_sel else CARD_N,
                             rect, border_radius=16)
            if is_sel:
                pygame.draw.rect(self.screen, CARD_BOR, rect, width=3, border_radius=16)

            # ข้อความการ์ด (clip ไม่ให้ล้นขอบ)
            text = self.f_card.render(item, True, TEXT_W)
            tr   = text.get_rect(center=rect.center)
            self.screen.set_clip(rect.inflate(-10, -6))
            self.screen.blit(text, tr)
            self.screen.set_clip(None)

            # ไอคอน X บนการ์ดที่เลือกในโหมดแก้ไข
            if self.edit_mode and is_sel:
                cr = pygame.Rect(rect.right - 28, rect.top + 4, 24, 24)
                pygame.draw.circle(self.screen, (190, 40, 40), cr.center, 12)
                xs = self.f_small.render("✕", True, TEXT_W)
                self.screen.blit(xs, xs.get_rect(center=cr.center))

    def _draw_yesno(self):
        y0  = SCREEN_H - YESNO_H - STATUS_H
        pad = 14
        mid = SCREEN_W // 2
        yr  = pygame.Rect(pad,        y0 + 8, mid - pad * 2, YESNO_H - 16)
        nr  = pygame.Rect(mid + pad,  y0 + 8, mid - pad * 2, YESNO_H - 16)
        pygame.draw.rect(self.screen, YES_C, yr, border_radius=14)
        pygame.draw.rect(self.screen, NO_C,  nr, border_radius=14)
        yt = self.f_yesno.render("✓  ใช่   [ LT ]", True, TEXT_W)
        nt = self.f_yesno.render("✗  ไม่   [ Back ]", True, TEXT_W)
        self.screen.blit(yt, yt.get_rect(center=yr.center))
        self.screen.blit(nt, nt.get_rect(center=nr.center))

    def _draw_status(self):
        y = SCREEN_H - STATUS_H
        pygame.draw.rect(self.screen, (22, 22, 42), (0, y, SCREEN_W, STATUS_H))
        c = STAT_C if self.status_ok else STAT_E
        s = self.f_small.render(self.status_text, True, c)
        self.screen.blit(s, s.get_rect(midleft=(14, y + STATUS_H // 2)))

    def _draw_edit_panel(self):
        # overlay กึ่งโปร่งใส
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        self.screen.blit(ov, (0, 0))

        # Panel กลาง
        pw, ph = 580, 270
        px, py = (SCREEN_W - pw) // 2, (SCREEN_H - ph) // 2
        panel  = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(self.screen, PANEL_BG, panel, border_radius=20)
        pygame.draw.rect(self.screen, INPUT_BOR, panel, width=2, border_radius=20)

        # หัวข้อ
        t = self.f_input.render("โหมดแก้ไขเมนู", True, TITLE_C)
        self.screen.blit(t, t.get_rect(midtop=(SCREEN_W // 2, py + 14)))

        # ปุ่มลบ
        dr = pygame.Rect(px + 18, py + 60, pw // 2 - 28, 54)
        pygame.draw.rect(self.screen, (155, 38, 38), dr, border_radius=12)
        label = self.items[self.sel_idx] if self.items else "-"
        dt = self.f_small.render(f"[Delete]  ลบ:  {label}", True, TEXT_W)
        self.screen.set_clip(dr.inflate(-8, 0))
        self.screen.blit(dt, dt.get_rect(center=dr.center))
        self.screen.set_clip(None)

        # ปุ่มเพิ่ม
        ar = pygame.Rect(px + pw // 2 + 10, py + 60, pw // 2 - 28, 54)
        pygame.draw.rect(self.screen, (28, 115, 55), ar, border_radius=12)
        at = self.f_small.render("[A]  เพิ่มรายการใหม่", True, TEXT_W)
        self.screen.blit(at, at.get_rect(center=ar.center))

        # Text input
        ir = pygame.Rect(px + 18, py + 130, pw - 36, 52)
        bc = INPUT_BOR if self.input_active else (75, 75, 108)
        pygame.draw.rect(self.screen, INPUT_BG, ir, border_radius=10)
        pygame.draw.rect(self.screen, bc, ir, width=2, border_radius=10)
        disp = (self.input_text + "|") if self.input_active else (
            self.input_text or "กด [A] แล้วพิมพ์ข้อความ...")
        ic = TEXT_W if self.input_active else (115, 115, 148)
        it = self.f_input.render(disp, True, ic)
        self.screen.set_clip(ir.inflate(-8, 0))
        self.screen.blit(it, it.get_rect(midleft=(ir.left + 10, ir.centery)))
        self.screen.set_clip(None)

        # คำแนะนำ
        hint = self.f_small.render(
            "↑↓←→ เลือก | Delete ลบ | A เพิ่ม | Enter ยืนยัน | E ปิด", True, (135, 135, 175))
        self.screen.blit(hint, hint.get_rect(midbottom=(SCREEN_W // 2, py + ph - 10)))

    # ----------------------------------------------------------
    def run(self):
        while self.handle_events():
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    HemiInterface().run()
