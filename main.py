import pygame
import random
import math
import json
import os

# ── resolution & scale ────────────────────────────────────────────────────────
BASE_W, BASE_H = 480, 800
WIDTH,  HEIGHT = 1080, 2000
SX = WIDTH  / BASE_W   
SY = HEIGHT / BASE_H   
S  = min(SX, SY)      

def sx(v):  return int(v * SX)
def sy(v):  return int(v * SY)
def sc(v):  return int(v * S)   

TARGET_WIDTH = sc(40)
SCORES_FILE  = "scores.json"

# colours
BLACK     = (0,   0,   0)
WHITE     = (255, 255, 255)
DARK_GREY = (20,  20,  20)
MID_GREY  = (45,  45,  45)
YELLOW    = (255, 230, 80)
RED       = (220, 40,  40)

SIMON_COLOURS = {
    "red":    ((140, 20,  20),  (255, 60,  60)),
    "blue":   ((20,  20,  140), (60,  60,  255)),
    "yellow": ((140, 120, 0),   (255, 230, 0)),
    "green":  ((20,  120, 20),  (60,  220, 60)),
}

# ── pygame setup ──────────────────────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), display=1)
pygame.display.set_caption("PAC Games!")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)
pygame.font.init()


font_lg = pygame.font.SysFont("consolas", sc(42), bold=True)
font_md = pygame.font.SysFont("consolas", sc(28))
font_sm = pygame.font.SysFont("consolas", sc(20))
font_xs = pygame.font.SysFont("consolas", sc(15))

cursor_pos = pygame.Vector2(WIDTH / 2, HEIGHT / 2)

pygame.mixer.init()

SFX = {
    "MenuMusic":            "Sounds/freesound_community-8-bit-melody-loop-37872 (1).mp3",
    "SimonMusic":           "Sounds/freesound_community-chase-8-bit-73312.mp3",
    "AimMusic":             "Sounds/freesound_community-8bit-music-for-game-68698.mp3",
    "Button":               pygame.mixer.Sound("Sounds/freesound_community-famikick-92712.mp3"),
    "AimHit":               pygame.mixer.Sound("Sounds/driken5482-retro-click-236673.mp3"),
    "AimMiss":              pygame.mixer.Sound("Sounds/freesound_community-skip-sfx-38509.mp3"),
    "SimonHit":             pygame.mixer.Sound("Sounds/dammafra-virtual-pet-happy-458154.mp3"),
    "SimonFail":            pygame.mixer.Sound("Sounds/freesound_community-8-bit-fireball-81148.mp3"),
    "LeaderBoardMusicLose": pygame.mixer.Sound("Sounds/make_more_sound-8-bit-video-game-lose-sound-version-1-145828.mp3"),
    "LeaderBoardMusicHIGH": pygame.mixer.Sound("Sounds/freesound_community-winsquare-6993.mp3"),
}

def play_music(key):
    pygame.mixer.music.load(SFX[key])
    pygame.mixer.music.play(-1)

# ── scores I/O ────────────────────────────────────────────────────────────────

def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"aim_easy": [], "aim_hard": [], "simon": []}

def save_scores(data):
    with open(SCORES_FILE, "w") as f:
        json.dump(data, f, indent=2)

scores_db = load_scores()
for key in ("aim_easy", "aim_hard", "simon"):
    if key not in scores_db:
        scores_db[key] = []

# ── cursors ───────────────────────────────────────────────────────────────────

def draw_crosshair(surface, pos, colour=YELLOW):
    size = sc(16); gap = sc(5); thickness = max(2, sc(2))
    x, y = int(pos.x), int(pos.y)
    pygame.draw.line(surface, colour, (x-size, y), (x-gap, y), thickness)
    pygame.draw.line(surface, colour, (x+gap,  y), (x+size, y), thickness)
    pygame.draw.line(surface, colour, (x, y-size), (x, y-gap), thickness)
    pygame.draw.line(surface, colour, (x, y+gap),  (x, y+size), thickness)

def draw_circle_cursor(surface, pos, colour=YELLOW):
    radius = sc(7); thickness = max(2, sc(2))
    x, y = int(pos.x), int(pos.y)
    pygame.draw.circle(surface, DARK_GREY, (x, y), radius+sc(1))
    pygame.draw.circle(surface, colour,    (x, y), radius, thickness)

# ── helpers ───────────────────────────────────────────────────────────────────

def distance(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

def text_centre(surface, text, font, colour, cx, cy):
    surf = font.render(text, True, colour)
    surface.blit(surf, surf.get_rect(center=(cx, cy)))

def draw_scanlines(surface, alpha=18):
    ls = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for yy in range(0, HEIGHT, sc(3)):
        pygame.draw.line(ls, (0, 0, 0, alpha), (0, yy), (WIDTH, yy))
    surface.blit(ls, (0, 0))

def draw_button(surface, rect, label, font, active=False, col=None):
    col   = col or YELLOW
    hover = rect.collidepoint(cursor_pos.x, cursor_pos.y)
    bg    = (60, 60, 40) if (hover or active) else (35, 35, 35)
    bord  = col          if (hover or active) else (80, 80, 80)
    pygame.draw.rect(surface, bg,   rect, border_radius=sc(6))
    pygame.draw.rect(surface, bord, rect, width=max(2,sc(2)), border_radius=sc(6))
    text_centre(surface, label, font, bord, rect.centerx, rect.centery)
    return hover

def draw_grid(surface):
    step = sc(40)
    for x in range(0, WIDTH, step):
        pygame.draw.line(surface, MID_GREY, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, step):
        pygame.draw.line(surface, MID_GREY, (0, y), (WIDTH, y), 1)

# ── HOME button  (scaled, bottom-left) ───────────────────────────────────────

_HBW = sx(110); _HBH = sy(34); _HBX = sx(10); _HBY = HEIGHT - sy(60)
HOME_BTN_RECT = pygame.Rect(_HBX, _HBY, _HBW, _HBH)

def draw_home_button(surface):
    draw_button(surface, HOME_BTN_RECT, "HOME", font_sm)

def home_button_clicked(events):
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if HOME_BTN_RECT.collidepoint(cursor_pos.x, cursor_pos.y):
                SFX["Button"].play()
                return True
    return False

# ══════════════════════════════════════════════════════════════════════════════
# LEADERBOARD / NAME-ENTRY SCREEN
# ══════════════════════════════════════════════════════════════════════════════

class LeaderboardScreen:
    ALPHABET = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    def __init__(self, score_key, new_score, on_done):
        self.score_key     = score_key
        self.new_score     = new_score
        self.on_done       = on_done
        self.board         = sorted(scores_db[score_key],
                                    key=lambda x: x["score"], reverse=True)[:5]
        qualifies          = (len(self.board) < 5
                              or new_score > (self.board[-1]["score"] if self.board else -1))
        self.entering_name = qualifies
        self.letters       = [0, 0, 0]
        self.confirmed     = False

        if qualifies:
            pygame.mixer.music.stop(); SFX["LeaderBoardMusicHIGH"].play()
        else:
            pygame.mixer.music.stop(); SFX["LeaderBoardMusicLose"].play()

       
        btn_w  = sx(180);  btn_h  = sy(44)
        btn_x  = WIDTH//2 - btn_w//2
        self.menu_btn = pygame.Rect(btn_x, HEIGHT - sy(70),  btn_w, btn_h)
        self.play_btn = pygame.Rect(btn_x, HEIGHT - sy(125), btn_w, btn_h)

        self._col_w   = sx(60)
        self._box_h   = sy(60)
        self._start_x = WIDTH//2 - (3 * self._col_w) // 2

        arr_h  = sy(32); arr_w = self._col_w - sc(4)
        self._confirm_rect = pygame.Rect(
            WIDTH//2 - sx(70), self.play_btn.top - sy(52), sx(140), sy(40))
        self._base_y = self._confirm_rect.top - sy(85) - self._box_h
        self.up_rects = []
        self.dn_rects = []
        for i in range(3):
            cx = self._start_x + i * self._col_w
            self.up_rects.append(pygame.Rect(cx, self._base_y - arr_h - sc(4), arr_w, arr_h))
            self.dn_rects.append(pygame.Rect(cx, self._base_y + self._box_h + sc(4), arr_w, arr_h))

    def _get_name(self):
        return "".join(self.ALPHABET[i] for i in self.letters)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                px, py = cursor_pos.x, cursor_pos.y
                SFX["Button"].play()
                if self.entering_name and not self.confirmed:
                    for i in range(3):
                        if self.up_rects[i].collidepoint(px, py):
                            self.letters[i] = (self.letters[i] - 1) % 26
                        if self.dn_rects[i].collidepoint(px, py):
                            self.letters[i] = (self.letters[i] + 1) % 26
                    if self._confirm_rect.collidepoint(px, py):
                        self._save_score(); self.confirmed = True
                else:
                    if self.play_btn.collidepoint(px, py):
                        pygame.mixer.music.play(); self.on_done("play")
                    if self.menu_btn.collidepoint(px, py):
                        self.on_done("menu")

    def _save_score(self):
        scores_db[self.score_key].append({"name": self._get_name(), "score": self.new_score})
        scores_db[self.score_key].sort(key=lambda x: x["score"], reverse=True)
        save_scores(scores_db)
        self.board = sorted(scores_db[self.score_key],
                            key=lambda x: x["score"], reverse=True)[:5]

    def draw(self, surface):
        surface.fill(DARK_GREY)
        draw_grid(surface)

        title_y = sy(70)
        text_centre(surface, "LEADERBOARD", font_lg, YELLOW, WIDTH//2, title_y)

        col_xs = [sx(60), WIDTH//2, sx(400)]
        hdr_y  = sy(110)
        text_centre(surface, "RANK",  font_xs, (100,100,100), col_xs[0], hdr_y)
        text_centre(surface, "NAME",  font_xs, (100,100,100), col_xs[1], hdr_y)
        text_centre(surface, "SCORE", font_xs, (100,100,100), col_xs[2], hdr_y)
        sep1_y = hdr_y + sy(18)
        pygame.draw.line(surface, MID_GREY, (sx(30), sep1_y), (WIDTH-sx(30), sep1_y), 1)

        preview_board = list(self.board)
        new_row_idx   = -1
        if self.entering_name and not self.confirmed:
            tmp = preview_board + [{"name": self._get_name(), "score": self.new_score}]
            tmp.sort(key=lambda x: x["score"], reverse=True)
            preview_board = tmp[:5]
            for idx, e in enumerate(preview_board):
                if e["score"] == self.new_score and e["name"] == self._get_name():
                    new_row_idx = idx; break

        row_start = sep1_y + sy(16)
        row_step  = sy(50)
        for idx, entry in enumerate(preview_board):
            row_y  = row_start + idx * row_step
            is_new = (idx == new_row_idx)
            is_top = (idx == 0)
            col    = YELLOW if is_new else (WHITE if is_top else (160,160,160))

            if is_new:
                pygame.draw.rect(surface, (60,55,20),
                    pygame.Rect(sx(28), row_y - sy(16), WIDTH - sx(56), sy(34)),
                    border_radius=sc(4))

            if is_top:
                cx, cy = col_xs[0], row_y
                pts = []
                for k in range(5):
                    ao = math.pi/2 + k*2*math.pi/5
                    ai = ao + math.pi/5
                    pts.append((cx + sc(11)*math.cos(ao), cy - sc(11)*math.sin(ao)))
                    pts.append((cx + sc(5) *math.cos(ai), cy - sc(5) *math.sin(ai)))
                pygame.draw.polygon(surface, (255,210,0), pts)
                rank_str = " "
            else:
                rank_str = f"#{idx+1}"

            text_centre(surface, rank_str,            font_sm, col, col_xs[0], row_y)
            text_centre(surface, entry["name"],        font_sm, col, col_xs[1], row_y)
            text_centre(surface, str(entry["score"]),  font_sm, col, col_xs[2], row_y)

        sep2_y = row_start + 5 * row_step + sy(10)
        pygame.draw.line(surface, MID_GREY, (sx(30), sep2_y), (WIDTH-sx(30), sep2_y), 1)

        if self.entering_name and not self.confirmed:
            lbl_y = sep2_y + sy(0)
            text_centre(surface, "NEW HIGH SCORE!  Enter initials:",
                        font_xs, YELLOW, WIDTH//2, lbl_y)
            for i in range(3):
                cx  = self._start_x + i * self._col_w
                draw_button(surface, self.up_rects[i], "^", font_sm)
                box = pygame.Rect(cx, self._base_y, self._col_w - sc(4), self._box_h)
                pygame.draw.rect(surface, (50,30,30), box, border_radius=sc(6))
                pygame.draw.rect(surface, YELLOW,     box, width=max(2,sc(2)), border_radius=sc(6))
                text_centre(surface, self.ALPHABET[self.letters[i]], font_lg, YELLOW,
                            box.centerx, box.centery)
                draw_button(surface, self.dn_rects[i], "v", font_sm)
            draw_button(surface, self._confirm_rect, "CONFIRM", font_sm, col=YELLOW)
        else:
            msg_y = sep2_y + sy(3)
            if not self.entering_name:
                text_centre(surface, "Too bad!", font_md, (200,80,80), WIDTH//2, msg_y)
                text_centre(surface, "Better luck next time!",
                            font_xs, (160,160,160), WIDTH//2, msg_y + sy(36))

        draw_button(surface, self.play_btn, "PLAY AGAIN", font_sm)
        draw_button(surface, self.menu_btn, "MAIN MENU",  font_sm)
        draw_scanlines(surface)
        draw_circle_cursor(surface, cursor_pos)


# ══════════════════════════════════════════════════════════════════════════════
# GAME 1 – AIM TRAINER
# ══════════════════════════════════════════════════════════════════════════════

class AimTrainer:
    SHRINK_DELAY    = 3.0
    SHRINK_TIME     = 3.0
    HARD_SPEED_BASE = 90 * S   
    HARD_SPEED_RAMP = 18 * S

    def __init__(self):
        self.difficulty         = None
        self.score              = 0
        self.misses             = 0
        self.MAX_MISSES         = 5
        self.state              = "difficulty"
        self.leaderboard_screen = None
        self.target_pos         = pygame.Vector2(WIDTH/2, HEIGHT/2)
        self.target_radius      = TARGET_WIDTH
        self.idle_timer         = 0.0
        self.shrinking          = False
        self.vel                = pygame.Vector2(0, 0)
        self._build_diff_rects()

    def _build_diff_rects(self):
        bw = sx(300); bh = sy(120); gap = sy(20)
        lx = WIDTH//2 - bw//2
        top_y = HEIGHT//2 - (bh*2 + gap)//2
        self.easy_rect = pygame.Rect(lx, top_y,          bw, bh)
        self.hard_rect = pygame.Rect(lx, top_y + bh + gap, bw, bh)

    def reset(self, keep_difficulty=False):
        self.score          = 0
        self.misses         = 0
        self.idle_timer     = 0.0
        self.shrinking      = False
        self.target_radius  = TARGET_WIDTH
        self.leaderboard_screen = None
        if not keep_difficulty:
            self.difficulty = None; self.state = "difficulty"
        else:
            self.state = "playing"; self._new_target()

    def _current_speed(self):
        return min(self.HARD_SPEED_BASE + self.score * self.HARD_SPEED_RAMP, 500 * S)

    def _new_target(self):
        margin = sc(60)
        self.target_pos.x  = random.randint(margin, WIDTH  - margin)
        self.target_pos.y  = random.randint(margin + sy(60), HEIGHT - margin - sy(60))
        self.target_radius = TARGET_WIDTH
        self.idle_timer    = 0.0
        self.shrinking     = False
        if self.difficulty == "hard":
            spd   = self._current_speed()
            angle = random.uniform(0, math.tau)
            self.vel = pygame.Vector2(math.cos(angle)*spd, math.sin(angle)*spd)
        else:
            self.vel = pygame.Vector2(0, 0)

    def _register_miss(self):
        SFX["AimMiss"].play()
        self.misses += 1
        if self.score > 0:
            self.score -= 1
        return self.misses >= self.MAX_MISSES

    def update(self, events, dt):
        if self.state == "difficulty":
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    SFX["Button"].play()
                    if self.easy_rect.collidepoint(cursor_pos.x, cursor_pos.y):
                        self.difficulty = "easy"; self.MAX_MISSES = 5
                        self.state = "playing"; self._new_target()
                    elif self.hard_rect.collidepoint(cursor_pos.x, cursor_pos.y):
                        self.difficulty = "hard"; self.MAX_MISSES = 3
                        self.state = "playing"; self._new_target()
            return

        if self.state == "gameover":
            if self.leaderboard_screen:
                self.leaderboard_screen.handle_events(events)
            return

        if self.difficulty == "hard":
            self.target_pos += self.vel * dt
            r = self.target_radius
            if self.target_pos.x - r < 0:
                self.target_pos.x = r;          self.vel.x =  abs(self.vel.x)
            if self.target_pos.x + r > WIDTH:
                self.target_pos.x = WIDTH - r;  self.vel.x = -abs(self.vel.x)
            if self.target_pos.y - r < sy(60):
                self.target_pos.y = sy(60) + r; self.vel.y =  abs(self.vel.y)
            if self.target_pos.y + r > HEIGHT - sy(60):
                self.target_pos.y = HEIGHT - sy(60) - r; self.vel.y = -abs(self.vel.y)

        self.idle_timer += dt
        if self.idle_timer >= self.SHRINK_DELAY:
            self.shrinking     = True
            progress           = (self.idle_timer - self.SHRINK_DELAY) / self.SHRINK_TIME
            self.target_radius = max(0, TARGET_WIDTH * (1.0 - progress))
            if self.target_radius <= 0:
                if self._register_miss():
                    self.state = "gameover"; return
                else:
                    self._new_target()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_BTN_RECT.collidepoint(cursor_pos.x, cursor_pos.y):
                    continue
                if distance(self.target_pos, cursor_pos) <= self.target_radius + sc(2):
                    self.score += 1; SFX["AimHit"].play(); self._new_target()
                else:
                    if self._register_miss():
                        self.state = "gameover"; return

    def _start_leaderboard(self, on_done):
        key = "aim_easy" if self.difficulty == "easy" else "aim_hard"
        self.leaderboard_screen = LeaderboardScreen(key, self.score, on_done)

    def draw(self, surface):
        surface.fill(DARK_GREY)
        draw_grid(surface)

        if self.state == "difficulty":
            text_centre(surface, "HIT THE TARGET",   font_lg, YELLOW,        WIDTH//2, sy(150))
            text_centre(surface, "Select difficulty", font_sm, (120,120,120), WIDTH//2, sy(210))
            card_data = [
                (self.easy_rect, "EASY", "Go for a high score",
                 "before the target disappears!", (60,180,60)),
                (self.hard_rect, "HARD", "Targets move around,",
                 "Be careful not to miss!",       (200,60,60)),
            ]
            for rect, label, d1, d2, col in card_data:
                hover = rect.collidepoint(cursor_pos.x, cursor_pos.y)
                bg    = ((40,50,40) if label=="EASY" else (50,30,30)) if hover else (35,35,35)
                pygame.draw.rect(surface, bg,  rect, border_radius=sc(8))
                pygame.draw.rect(surface, col, rect, width=max(2,sc(2)), border_radius=sc(8))
                text_centre(surface, label, font_md, col, rect.centerx, rect.y + sy(28))
                text_centre(surface, d1,   font_xs, (160,160,160), rect.centerx, rect.y + sy(62))
                text_centre(surface, d2,   font_xs, (160,160,160), rect.centerx, rect.y + sy(84))
            draw_scanlines(surface)
            draw_home_button(surface)
            draw_circle_cursor(surface, cursor_pos)
            return

        if self.state == "gameover":
            if self.leaderboard_screen:
                self.leaderboard_screen.draw(surface)
            return

        if self.shrinking:
            t     = min(1.0, (self.idle_timer - self.SHRINK_DELAY) / self.SHRINK_TIME)
            r_col = (int(255*(1-t)+220*t), int(40*t), int(40*t))
        else:
            r_col = RED

        r = int(self.target_radius)
        if r > 0:
            pygame.draw.circle(surface, r_col, self.target_pos, r)
            if r > TARGET_WIDTH * 0.75:
                pygame.draw.circle(surface, WHITE, self.target_pos, int(r*0.75))
            if r > TARGET_WIDTH * 0.50:
                pygame.draw.circle(surface, r_col, self.target_pos, int(r*0.50))
            if r > TARGET_WIDTH * 0.25:
                pygame.draw.circle(surface, WHITE, self.target_pos, int(r*0.25))

        draw_scanlines(surface)

        surface.blit(font_md.render(f"SCORE  {self.score:04d}", True, YELLOW), (sx(14), sy(50)))
        surface.blit(font_xs.render((self.difficulty or "").upper(), True, (100,100,100)), (sx(14), sy(74)))

        dot_r   = sc(9)
        dot_gap = sc(22)
        dot_y   = sy(63)
        for m in range(self.MAX_MISSES):
            col = (180,40,40) if m < self.misses else (60,60,60)
            cx  = WIDTH - sx(14) - dot_r - m * dot_gap
            pygame.draw.circle(surface, col, (cx, dot_y), dot_r)

        draw_home_button(surface)
        draw_crosshair(surface, cursor_pos)


# ══════════════════════════════════════════════════════════════════════════════
# GAME 2 – SIMON
# ══════════════════════════════════════════════════════════════════════════════

class SimonGame:
    QUADRANT_COLOURS = ["red", "blue", "yellow", "green"]

    def __init__(self):
        self.reset()

    @staticmethod
    def quad_rect(index):
        gap = sc(4)
        hw  = WIDTH  // 2
        hh  = HEIGHT // 2
        return [
            pygame.Rect(0,       0,       hw-gap, hh-gap),
            pygame.Rect(hw+gap,  0,       hw-gap, hh-gap),
            pygame.Rect(0,       hh+gap,  hw-gap, hh-gap),
            pygame.Rect(hw+gap,  hh+gap,  hw-gap, hh-gap),
        ][index]

    @staticmethod
    def pos_to_quad(pos):
        for i in range(4):
            if SimonGame.quad_rect(i).collidepoint(pos.x, pos.y):
                return i
        return -1

    def reset(self):
        self.sequence        = []
        self.player_input    = []
        self.state           = "idle"
        self.lit_quad        = -1
        self.score           = 0
        self.show_timer      = 0.0
        self.show_index      = 0
        self.flash_timer     = 0.0
        self.message         = "Click anywhere to start"
        self.message_colour  = WHITE
        self._SHOW_ON        = 0.55
        self._SHOW_OFF       = 0.25
        self.leaderboard_screen = None

    def _start_round(self):
        self.sequence.append(random.randint(0, 3))
        self.player_input = []
        self.show_index   = 0
        self.show_timer   = 0.0
        self.lit_quad     = -1
        self.state        = "showing"
        self.message      = ""

    def _check_input(self, quad_index):
        expected = self.sequence[len(self.player_input)]
        self.player_input.append(quad_index)
        self.lit_quad    = quad_index
        self.flash_timer = 0.18
        if quad_index == expected:
            SFX["SimonHit"].play()
        if quad_index != expected:
            self.lit_quad       = -1
            SFX["SimonFail"].play()
            self.flash_timer    = 3
            self.message        = f"Wrong!  Score: {self.score}"
            self.message_colour = (255, 80, 80)
            self.state          = "wrong"
        elif len(self.player_input) == len(self.sequence):
            self.message_colour = (80, 255, 121)
            self.score         += 1
            self.state          = "correct"
            self.flash_timer    = 2
            self.message        = f"Round {self.score + 1}"

    def _start_leaderboard(self, on_done):
        self.leaderboard_screen = LeaderboardScreen("simon", self.score, on_done)

    def update(self, events, dt):
        if self.state == "gameover":
            if self.leaderboard_screen:
                self.leaderboard_screen.handle_events(events)
            return

        if self.flash_timer > 0:
            self.flash_timer -= dt
            if self.state == "correct" and self.flash_timer < (2.0 - 0.18):
                self.lit_quad = -1
            elif self.state == "waiting" and self.flash_timer <= 0:
                self.lit_quad = -1
            if self.flash_timer <= 0:
                self.lit_quad = -1
                if self.state == "correct":
                    self._start_round()
                elif self.state == "wrong":
                    self.state = "gameover"

        if self.state == "idle":
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not HOME_BTN_RECT.collidepoint(cursor_pos.x, cursor_pos.y):
                        self._start_round()

        elif self.state == "showing":
            self.show_timer += dt
            phase = self._SHOW_ON + self._SHOW_OFF
            slot  = self.show_index
            t     = self.show_timer - slot * phase
            self.lit_quad = self.sequence[slot] if t < self._SHOW_ON else -1
            if self.show_timer >= len(self.sequence) * phase:
                self.state          = "waiting"
                self.message        = "Your turn!"
                self.message_colour = WHITE
            elif t >= phase:
                self.show_index += 1

        elif self.state == "waiting":
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if HOME_BTN_RECT.collidepoint(cursor_pos.x, cursor_pos.y):
                        continue
                    quad = self.pos_to_quad(cursor_pos)
                    if quad != -1:
                        self._check_input(quad)

        elif self.state in ("correct", "wrong"):
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                if self.state == "correct":
                    self.lit_quad = -1; self._start_round()
                else:
                    self.state = "gameover"
                self.lit_quad = -1

    def draw(self, surface):
        if self.state == "gameover":
            if self.leaderboard_screen:
                self.leaderboard_screen.draw(surface)
            return

        surface.fill(BLACK)

        for i, colour_key in enumerate(self.QUADRANT_COLOURS):
            rect        = self.quad_rect(i)
            dim, bright = SIMON_COLOURS[colour_key]
            col         = bright if self.lit_quad == i else dim
            pygame.draw.rect(surface, col, rect, border_radius=sc(6))
            lbl = font_sm.render(colour_key.upper(), True, (0,0,0))
            surface.blit(lbl, lbl.get_rect(center=rect.center))

        draw_scanlines(surface)

        hud_w    = sx(320)
        hud_rect = pygame.Rect(WIDTH//2 - hud_w//2, HEIGHT//2 - sy(26), hud_w, sy(52))
        pygame.draw.rect(surface, (10,10,10), hud_rect, border_radius=sc(4))
        if self.message:
            text_centre(surface, self.message, font_sm,
                        self.message_colour, WIDTH//2, HEIGHT//2)

        surface.blit(font_md.render(f"SCORE  {self.score:04d}", True, WHITE), (sx(14), sy(50)))

        draw_home_button(surface)
        draw_circle_cursor(surface, cursor_pos)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ══════════════════════════════════════════════════════════════════════════════

class MainMenu:
    CARDS = [
        {"title": "Hit the Target", "desc": ["Click the targets", "before they disappear"], "colour": (200,0,0)},
        {"title": "Color Memory",   "desc": ["Repeat the color", "sequence"],           "colour": (180,60,200)},
    ]

    def __init__(self):
        card_w = sx(340); card_h = sy(140); gap = sy(24)
        total_h = len(self.CARDS) * card_h + (len(self.CARDS)-1) * gap
        start_y = HEIGHT//2 - total_h//2 + sy(40)
        self._rects = [
            pygame.Rect(WIDTH//2 - card_w//2, start_y + i*(card_h+gap), card_w, card_h)
            for i in range(len(self.CARDS))
        ]

    def handle_click(self):
        for i, rect in enumerate(self._rects):
            if rect.collidepoint(cursor_pos.x, cursor_pos.y):
                return i
        return -1

    def draw(self, surface):
        surface.fill(DARK_GREY)
        draw_grid(surface)

        text_centre(surface, "PAC GAMES",     font_lg, YELLOW,        WIDTH//2, sy(110))
        text_centre(surface, "Point the controller to select a game!",
                    font_sm, (100,100,100), WIDTH//2, sy(162))

        mx, my = int(cursor_pos.x), int(cursor_pos.y)
        for rect, card in zip(self._rects, self.CARDS):
            hover = rect.collidepoint(mx, my)
            col   = card["colour"]
            pygame.draw.rect(surface, (10,10,10), rect.move(sc(4),sc(4)), border_radius=sc(8))
            pygame.draw.rect(surface, (55,55,55) if hover else (35,35,35), rect, border_radius=sc(8))
            pygame.draw.rect(surface, col, rect, width=max(2,sc(2)), border_radius=sc(8))
            pygame.draw.rect(surface, col,
                             pygame.Rect(rect.x, rect.y+sc(8), sc(4), rect.h-sc(16)),
                             border_radius=sc(2))
            surface.blit(font_md.render(card["title"], True, col),
                         (rect.x + sx(22), rect.y + sy(22)))
            for j, line in enumerate(card["desc"]):
                surface.blit(font_sm.render(line, True, (160,160,160)),
                             (rect.x + sx(22), rect.y + sy(70) + j*sy(28)))
            if hover:
                cx = rect.right - sx(28)
                cy = rect.centery
                pygame.draw.polygon(surface, col,
                    [(cx, cy-sc(10)), (cx+sc(14), cy), (cx, cy+sc(10))])

        draw_scanlines(surface)
        text_centre(surface, "A KnockOnWood© Product!", font_sm, (60,60,60), WIDTH//2, HEIGHT - sy(30))
        draw_circle_cursor(surface, cursor_pos)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ══════════════════════════════════════════════════════════════════════════════

def main():
    play_music("MenuMusic")
    global cursor_pos

    menu       = MainMenu()
    aim_game   = AimTrainer()
    simon_game = SimonGame()
    scene      = "menu"
    running    = True

    def go_menu():
        nonlocal scene
        play_music("MenuMusic")
        scene = "menu"
        aim_game.reset()
        simon_game.reset()

    def aim_done(action):
        nonlocal scene
        if action == "play":
            aim_game.reset(keep_difficulty=True); scene = "aim"
        else:
            go_menu()

    def simon_done(action):
        nonlocal scene
        if action == "play":
            simon_game.reset(); scene = "simon"
        else:
            go_menu()

    while running:
        dt     = clock.tick(60) / 1000.0
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEMOTION:
                cursor_pos.x, cursor_pos.y = event.pos
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if scene != "menu":
                    go_menu()

        if scene != "menu" and home_button_clicked(events):
            
            go_menu()

        if scene == "menu":
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    choice = menu.handle_click()
                    if choice == 0:
                        SFX["Button"].play(); play_music("AimMusic")
                        aim_game.reset(); scene = "aim"
                    elif choice == 1:
                        SFX["Button"].play(); play_music("SimonMusic")
                        simon_game.reset(); scene = "simon"
            menu.draw(screen)

        elif scene == "aim":
            aim_game.update(events, dt)
            if aim_game.state == "gameover" and aim_game.leaderboard_screen is None:
                aim_game._start_leaderboard(aim_done)
            aim_game.draw(screen)

        elif scene == "simon":
            simon_game.update(events, dt)
            if simon_game.state == "gameover" and simon_game.leaderboard_screen is None:
                simon_game._start_leaderboard(simon_done)
            simon_game.draw(screen)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

