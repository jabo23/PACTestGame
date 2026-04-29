import pygame
import random
import math
import json
import os

# ── constants ─────────────────────────────────────────────────────────────────
TARGET_WIDTH  = 40
WIDTH, HEIGHT = 480, 800
SCORES_FILE   = "scores.json"

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
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PAC Games!")
clock  = pygame.time.Clock()
pygame.mouse.set_visible(False)
pygame.font.init()

font_lg = pygame.font.SysFont("consolas", 42, bold=True)
font_md = pygame.font.SysFont("consolas", 28)
font_sm = pygame.font.SysFont("consolas", 20)
font_xs = pygame.font.SysFont("consolas", 15)

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
    pygame.mixer.music.play() 

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

def draw_crosshair(surface, pos, colour=YELLOW, size=16, gap=5, thickness=2):
    """Yellow crosshair, no centre dot."""
    x, y = int(pos.x), int(pos.y)
    pygame.draw.line(surface, colour, (x - size, y), (x - gap, y), thickness)
    pygame.draw.line(surface, colour, (x + gap,  y), (x + size, y), thickness)
    pygame.draw.line(surface, colour, (x, y - size), (x, y - gap), thickness)
    pygame.draw.line(surface, colour, (x, y + gap),  (x, y + size), thickness)

def draw_circle_cursor(surface, pos, colour=YELLOW, radius=7, thickness=2):
    """Simple circle cursor with a dark outline for contrast."""
    x, y = int(pos.x), int(pos.y)
    pygame.draw.circle(surface, DARK_GREY, (x, y), radius + 1)
    pygame.draw.circle(surface, colour,    (x, y), radius, thickness)

# ── helpers ───────────────────────────────────────────────────────────────────

def distance(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

def text_centre(surface, text, font, colour, cx, cy):
    surf = font.render(text, True, colour)
    surface.blit(surf, surf.get_rect(center=(cx, cy)))

def draw_scanlines(surface, alpha=18):
    ls = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for yy in range(0, HEIGHT, 3):
        pygame.draw.line(ls, (0, 0, 0, alpha), (0, yy), (WIDTH, yy))
    surface.blit(ls, (0, 0))

def draw_button(surface, rect, label, font, active=False, col=None):
    col    = col or YELLOW
    hover  = rect.collidepoint(cursor_pos.x, cursor_pos.y)
    bg     = (60, 60, 40) if (hover or active) else (35, 35, 35)
    border = col          if (hover or active) else (80, 80, 80)
    pygame.draw.rect(surface, bg,     rect, border_radius=6)
    pygame.draw.rect(surface, border, rect, width=2, border_radius=6)
    text_centre(surface, label, font, border, rect.centerx, rect.centery)
    return hover

def draw_grid(surface):
    for x in range(0, WIDTH, 40):
        pygame.draw.line(surface, MID_GREY, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(surface, MID_GREY, (0, y), (WIDTH, y), 1)

# ── HOME button ───────────────────────────────────────────────────────────────

HOME_BTN_RECT = pygame.Rect(10, HEIGHT - 44, 110, 34)

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
        self.score_key  = score_key
        self.new_score  = new_score
        self.on_done    = on_done
        self.board      = sorted(scores_db[score_key],
                                 key=lambda x: x["score"], reverse=True)[:5]

        # qualify for top-5?
        qualifies = (len(self.board) < 5
                     or new_score > (self.board[-1]["score"] if self.board else -1))
        self.entering_name = qualifies
        self.letters       = [0, 0, 0]
        self.confirmed     = False

        if qualifies:
            pygame.mixer.music.stop() 
            SFX["LeaderBoardMusicHIGH"].play()
        else:
            pygame.mixer.music.stop() 
            SFX["LeaderBoardMusicLose"].play()

        # ── layout constants ──
        # Leaderboard rows occupy roughly y=120..350 (5 rows × 44px)
        # Name-entry block sits below that, above the play/menu buttons

        # Play / menu buttons at very bottom
        self.play_btn = pygame.Rect(WIDTH//2 - 90, HEIGHT - 110, 180, 40)
        self.menu_btn = pygame.Rect(WIDTH//2 - 90, HEIGHT - 62,  180, 40)

        # Name-entry widgets: centred above play button
        # Block layout (top→bottom): label, initials row (up / box / dn), confirm
        # Total block height ≈ 20+30+50+30+10+36 = 176 px
        # Place it so confirm sits ~30 px above play_btn
        self._confirm_rect = pygame.Rect(WIDTH//2 - 60, self.play_btn.top - 120, 120, 36)
        # base_y = top of letter boxes
        self._base_y       = self._confirm_rect.top - 100   # letter box h=50
        self._col_w        = 54
        self._start_x      = WIDTH//2 - (3 * self._col_w) // 2

        # Arrow rects
        self.up_rects = []
        self.dn_rects = []
        for i in range(3):
            cx = self._start_x + i * self._col_w
            self.up_rects.append(pygame.Rect(cx, self._base_y - 34, self._col_w - 4, 28))
            self.dn_rects.append(pygame.Rect(cx, self._base_y + 54, self._col_w - 4, 28))

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
                        self._save_score()
                        self.confirmed = True
                else:
                    if self.play_btn.collidepoint(px, py):
                        pygame.mixer.music.play()
                        SFX["Button"].play()
                        self.on_done("play")
                    if self.menu_btn.collidepoint(px, py):
                        SFX["Button"].play()
                        self.on_done("menu")

    def _save_score(self):
        scores_db[self.score_key].append({"name": self._get_name(),
                                          "score": self.new_score})
        scores_db[self.score_key].sort(key=lambda x: x["score"], reverse=True)
        save_scores(scores_db)
        self.board = sorted(scores_db[self.score_key],
                            key=lambda x: x["score"], reverse=True)[:5]

    # ── draw ──────────────────────────────────────────────────────────────────
    def draw(self, surface):
        surface.fill(DARK_GREY)
        draw_grid(surface)

        text_centre(surface, "LEADERBOARD", font_lg, YELLOW, WIDTH//2, 50)

        # column x positions
        col_xs = [60, 200, 360]
        text_centre(surface, "RANK",  font_xs, (100,100,100), col_xs[0], 100)
        text_centre(surface, "NAME",  font_xs, (100,100,100), col_xs[1], 100)
        text_centre(surface, "SCORE", font_xs, (100,100,100), col_xs[2], 100)
        pygame.draw.line(surface, MID_GREY, (30, 112), (WIDTH-30, 112), 1)

        # build preview board (show player's position live while entering)
        preview_board = list(self.board)
        new_row_idx   = -1
        if self.entering_name and not self.confirmed:
            tmp = preview_board + [{"name": self._get_name(), "score": self.new_score}]
            tmp.sort(key=lambda x: x["score"], reverse=True)
            preview_board = tmp[:5]
            for idx, e in enumerate(preview_board):
                if e["score"] == self.new_score and e["name"] == self._get_name():
                    new_row_idx = idx
                    break

        for idx, entry in enumerate(preview_board):
            row_y    = 130 + idx * 44
            is_new   = (idx == new_row_idx)
            is_top   = (idx == 0)
            col      = YELLOW if is_new else (WHITE if is_top else (160,160,160))

            if is_new:
                pygame.draw.rect(surface, (60,55,20),
                                 pygame.Rect(28, row_y-14, WIDTH-56, 28), border_radius=4)

            # rank — draw a star for #1 instead of unicode crown
            if is_top:
                # small gold star drawn as polygon
                cx, cy  = col_xs[0], row_y
                pts     = []
                for k in range(5):
                    angle_out = math.pi/2 + k * 2*math.pi/5
                    angle_in  = angle_out + math.pi/5
                    pts.append((cx + 9*math.cos(angle_out), cy - 9*math.sin(angle_out)))
                    pts.append((cx + 4*math.cos(angle_in),  cy - 4*math.sin(angle_in)))
                pygame.draw.polygon(surface, (255,210,0), pts)
                rank_str = " "
            else:
                rank_str = f"#{idx+1}"

            text_centre(surface, rank_str,            font_sm, col, col_xs[0], row_y)
            text_centre(surface, entry["name"],        font_sm, col, col_xs[1], row_y)
            text_centre(surface, str(entry["score"]),  font_sm, col, col_xs[2], row_y)

        # ── separator line above name-entry zone ──
        sep_y = 360
        pygame.draw.line(surface, MID_GREY, (30, sep_y), (WIDTH-30, sep_y), 1)

        # ── name entry or "too bad" message ──
        if self.entering_name and not self.confirmed:
            label_y    = sep_y + 22
            initials_y = label_y + 26   # small gap label→arrows
            text_centre(surface, "NEW HIGH SCORE! Enter initials:",
                        font_xs, YELLOW, WIDTH//2, label_y)

            for i in range(3):
                cx  = self._start_x + i * self._col_w
                # up arrow
                draw_button(surface, self.up_rects[i], "^", font_sm)
                # letter box
                box = pygame.Rect(cx, self._base_y, self._col_w - 4, 50)
                pygame.draw.rect(surface, (50,50,30), box, border_radius=6)
                pygame.draw.rect(surface, YELLOW,     box, width=2, border_radius=6)
                text_centre(surface, self.ALPHABET[self.letters[i]], font_lg, YELLOW,
                            box.centerx, box.centery)
                # down arrow
                draw_button(surface, self.dn_rects[i], "v", font_sm)

            draw_button(surface, self._confirm_rect, "CONFIRM", font_sm, col=YELLOW)

        else:
            msg_y = sep_y + 30
            if not self.entering_name:
                text_centre(surface, "Too bad!", font_md, (200,80,80), WIDTH//2, msg_y)
                text_centre(surface, "Better luck next time!",
                            font_xs, (160,160,160), WIDTH//2, msg_y + 34)

        # ── play / menu buttons ──
        draw_button(surface, self.play_btn, "PLAY AGAIN", font_sm)
        draw_button(surface, self.menu_btn, "MAIN MENU",  font_sm)

        draw_scanlines(surface)
        draw_circle_cursor(surface, cursor_pos)


# ══════════════════════════════════════════════════════════════════════════════
# GAME 1 – AIM TRAINER
# ══════════════════════════════════════════════════════════════════════════════

class AimTrainer:
    SHRINK_DELAY = 3.0   # seconds before shrink starts
    SHRINK_TIME  = 3.0   # seconds to shrink to zero

    # Hard-mode speed: base + ramp per point
    HARD_SPEED_BASE = 90      # px/s at score 0
    HARD_SPEED_RAMP = 18      # extra px/s per point scored

    def __init__(self):
        self.difficulty        = None
        self.score             = 0
        self.misses            = 0
        self.state             = "difficulty"
        self.leaderboard_screen = None
        self.target_pos        = pygame.Vector2(WIDTH/2, HEIGHT/2)
        self.target_radius     = TARGET_WIDTH
        self.idle_timer        = 0.0
        self.shrinking         = False
        self.vel               = pygame.Vector2(0, 0)
        self._build_diff_rects()

    def _build_diff_rects(self):
        """Two stacked buttons, wide enough for the description text."""
        bw, bh = 300, 110
        gap    = 20
        total_h = bh * 2 + gap
        lx     = WIDTH // 2 - bw // 2
        top_y  = HEIGHT // 2 - total_h // 2
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
            self.difficulty = None
            self.state      = "difficulty"
        else:
            self.state = "playing"
            self._new_target()

    def _current_speed(self):
        base  = self.HARD_SPEED_BASE + self.score * self.HARD_SPEED_RAMP
        return min(base, 500)   # cap so it doesn't get absurd

    def _new_target(self):
        margin = 60
        self.target_pos.x  = random.randint(margin, WIDTH  - margin)
        self.target_pos.y  = random.randint(margin + 60, HEIGHT - margin - 60)
        self.target_radius = TARGET_WIDTH
        self.idle_timer    = 0.0
        self.shrinking     = False
        if self.difficulty == "hard":
            spd   = self._current_speed()
            angle = random.uniform(0, math.tau)
            self.vel = pygame.Vector2(math.cos(angle) * spd,
                                      math.sin(angle) * spd)
        else:
            self.vel = pygame.Vector2(0, 0)

    def _register_miss(self):
        """Count a miss (shrink timeout or bad click). Returns True if game over."""
        SFX["AimMiss"].play()
        self.misses += 1
        if self.score > 0:
            self.score -= 1
        return self.misses >= self.MAX_MISSES

    def update(self, events, dt):
        # ── difficulty select ──
        if self.state == "difficulty":
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    SFX["Button"].play()
                    if self.easy_rect.collidepoint(cursor_pos.x, cursor_pos.y):
                        self.difficulty = "easy"
                        self.state      = "playing"
                        self.MAX_MISSES   = 5     # misses before game over
                        self._new_target()
                    elif self.hard_rect.collidepoint(cursor_pos.x, cursor_pos.y):
                        self.difficulty = "hard"
                        self.state      = "playing"
                        self.MAX_MISSES   = 3     # misses before game over
                        self._new_target()
            return

        if self.state == "gameover":
            if self.leaderboard_screen:
                self.leaderboard_screen.handle_events(events)
            return

        # ── playing ──

        # Hard mode: move & bounce
        if self.difficulty == "hard":
            self.target_pos += self.vel * dt
            r = self.target_radius
            if self.target_pos.x - r < 0:
                self.target_pos.x = r; self.vel.x = abs(self.vel.x)
            if self.target_pos.x + r > WIDTH:
                self.target_pos.x = WIDTH - r; self.vel.x = -abs(self.vel.x)
            if self.target_pos.y - r < 60:
                self.target_pos.y = 60 + r; self.vel.y = abs(self.vel.y)
            if self.target_pos.y + r > HEIGHT - 60:
                self.target_pos.y = HEIGHT - 60 - r; self.vel.y = -abs(self.vel.y)

        # Shrink timer
        self.idle_timer += dt
        if self.idle_timer >= self.SHRINK_DELAY:
            self.shrinking     = True
            progress           = (self.idle_timer - self.SHRINK_DELAY) / self.SHRINK_TIME
            self.target_radius = max(0, TARGET_WIDTH * (1.0 - progress))
            if self.target_radius <= 0:
                    game_over = self._register_miss()

                    if game_over:
                        self.state = "gameover"
                        return
                    else:
                        self._new_target()

        # Mouse clicks
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_BTN_RECT.collidepoint(cursor_pos.x, cursor_pos.y):
                    continue
                if distance(self.target_pos, cursor_pos) <= self.target_radius + 2:
                    self.score += 1
                    SFX["AimHit"].play()
                    self._new_target()
                else:
                    if self._register_miss():
                        self.state = "gameover"
                        return

    def _start_leaderboard(self, on_done):
        key = "aim_easy" if self.difficulty == "easy" else "aim_hard"
        self.leaderboard_screen = LeaderboardScreen(key, self.score, on_done)

    def draw(self, surface):
        surface.fill(DARK_GREY)
        draw_grid(surface)

        # ── difficulty screen ──
        if self.state == "difficulty":
            text_centre(surface, "HIT THE TARGET",  font_lg, YELLOW,        WIDTH//2, 150)
            text_centre(surface, "Select difficulty", font_sm, (120,120,120), WIDTH//2, 200)

            card_data = [
                (self.easy_rect, "EASY",
                 "Go for a high score",
                 "before the target disappears!",
                 (60, 180, 60)),
                (self.hard_rect, "HARD",
                 "Targets move around",
                 "Be careful not to miss!",
                 (200, 60, 60)),
            ]
            for rect, label, desc1, desc2, col in card_data:
                hover = rect.collidepoint(cursor_pos.x, cursor_pos.y)
                if label == "EASY":
                    bg = (40, 50, 40) if hover else (35, 35, 35)
                else:
                    bg = (50, 30, 30) if hover else (35, 35, 35)
                pygame.draw.rect(surface, bg,  rect, border_radius=8)
                pygame.draw.rect(surface, col, rect, width=2, border_radius=8)
                text_centre(surface, label, font_md, col, rect.centerx, rect.y + 26)
                text_centre(surface, desc1, font_xs, (160,160,160), rect.centerx, rect.y + 60)
                text_centre(surface, desc2, font_xs, (160,160,160), rect.centerx, rect.y + 78)

            draw_scanlines(surface)
            draw_home_button(surface)
            draw_circle_cursor(surface, cursor_pos)
            return

        # ── gameover → leaderboard ──
        if self.state == "gameover":
            if self.leaderboard_screen:
                self.leaderboard_screen.draw(surface)
            return

        # ── playing ──
        if self.shrinking:
            t     = min(1.0, (self.idle_timer - self.SHRINK_DELAY) / self.SHRINK_TIME)
            r_col = (int(255*(1-t) + 220*t), int(40*t), int(40*t))
        else:
            r_col = RED

        r = self.target_radius
        if r > 0:
            pygame.draw.circle(surface, r_col,  self.target_pos, r)
            if r > TARGET_WIDTH * 0.75:
                pygame.draw.circle(surface, WHITE, self.target_pos, r * 0.75)
            if r > TARGET_WIDTH * 0.50:
                pygame.draw.circle(surface, r_col, self.target_pos, r * 0.50)
            if r > TARGET_WIDTH * 0.25:
                pygame.draw.circle(surface, WHITE, self.target_pos, r * 0.25)

        draw_scanlines(surface)

        # HUD
        surface.blit(font_md.render(f"SCORE  {self.score:04d}", True, YELLOW), (14, 14))
        diff_lbl = (self.difficulty or "").upper()
        surface.blit(font_xs.render(diff_lbl, True, (100,100,100)), (14, 46))

        # Miss counter (red hearts / X marks)
        miss_x = WIDTH - 14
        for m in range(self.MAX_MISSES):
            filled = m < self.misses
            col    = (180, 40, 40) if filled else (60, 60, 60)
            cx     = miss_x - m * 22
            pygame.draw.circle(surface, col, (cx, 24), 7)

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
        gap = 4
        hw  = WIDTH  // 2
        hh  = HEIGHT // 2
        return [
            pygame.Rect(0,      0,      hw-gap, hh-gap),
            pygame.Rect(hw+gap, 0,      hw-gap, hh-gap),
            pygame.Rect(0,      hh+gap, hw-gap, hh-gap),
            pygame.Rect(hw+gap, hh+gap, hw-gap, hh-gap),
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
        
        # Start the blink timer immediately on click
        self.lit_quad = quad_index
        self.flash_timer = 0.18  
        if quad_index == expected:
            SFX["SimonHit"].play()
            
        if quad_index != expected:
            # We override the timer here because we want the "Wrong!" 
            # message and the red light to stay visible for longer
            self.lit_quad = -1
            SFX["SimonFail"].play()
            self.flash_timer = 3
            self.message = f"Wrong!  Score: {self.score}"
            self.message_colour = (255, 80, 80)
            self.state = "wrong"
        elif len(self.player_input) == len(self.sequence):
                self.message_colour = (80, 255, 121)
                self.score += 1
                self.state = "correct"
                self.flash_timer = 2
                self.message = f"Round {self.score + 1}"
                

    def _start_leaderboard(self, on_done):
        self.leaderboard_screen = LeaderboardScreen("simon", self.score, on_done)
 
    def update(self, events, dt):
        if self.state == "gameover":
            if self.leaderboard_screen:
                self.leaderboard_screen.handle_events(events)
            return

       # --- TIMER HANDLING ---
        if self.flash_timer > 0:
            self.flash_timer -= dt
            
            # VISUAL LOGIC: Turn off the light after 0.18s 
            # (Basically, if the timer has moved 0.18 away from its starting point)
            if self.state == "correct":
                # If we started at 1.0, turn off at 0.82
                if self.flash_timer < (2.0 - 0.18):
                    self.lit_quad = -1
            elif self.state == "waiting":
                # Normal input blinks
                if self.flash_timer <= 0:
                    self.lit_quad = -1
            
            # STATE LOGIC: Transition only when timer hits 0
            if self.flash_timer <= 0:
                self.lit_quad = -1 
                if self.state == "correct":
                    self._start_round()
                elif self.state == "wrong":
                    self.state = "gameover"

        # --- STATE LOGIC ---
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
            
            # This handles the sequence "playback" lighting
            if t < self._SHOW_ON:
                self.lit_quad = self.sequence[slot]
            else:
                self.lit_quad = -1
                
            if self.show_timer >= len(self.sequence) * phase:
                self.state = "waiting"
                self.message = "Your turn!"
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
                    self.lit_quad = -1
                    self._start_round()
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
            pygame.draw.rect(surface, col, rect, border_radius=6)
            lbl = font_sm.render(colour_key.upper(), True, (0,0,0))
            surface.blit(lbl, lbl.get_rect(center=rect.center))
 
        draw_scanlines(surface)
 
        # wider HUD strip (300 px) so text never clips
        hud_w    = 300
        hud_rect = pygame.Rect(WIDTH//2 - hud_w//2, HEIGHT//2 - 22, hud_w, 44)
        pygame.draw.rect(surface, (10,10,10), hud_rect, border_radius=4)
        if self.message:
            text_centre(surface, self.message, font_sm,
                        self.message_colour, WIDTH//2, HEIGHT//2)
 
        surface.blit(font_md.render(f"SCORE  {self.score:04d}", True, WHITE), (14, 14))
 
        draw_home_button(surface)
        draw_circle_cursor(surface, cursor_pos)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ══════════════════════════════════════════════════════════════════════════════

class MainMenu:
    
    CARDS = [
        {"title": "Hit the Target", "desc": ["Click the targets", "as fast as you can"], "colour": (200,0,0)},
        {"title": "Color Memory",   "desc": ["Repeat the colour", "sequence"],           "colour": (180,60,200)},
    ]

    def __init__(self):
        card_w, card_h = 340, 140
        gap     = 24
        total_h = len(self.CARDS) * card_h + (len(self.CARDS)-1) * gap
        start_y = HEIGHT//2 - total_h//2 + 40
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

        text_centre(surface, "PAC GAMES",     font_lg, YELLOW,        WIDTH//2, 110)
        text_centre(surface, "Point the controller to select a game!", font_sm, (100,100,100), WIDTH//2, 155)

        mx, my = int(cursor_pos.x), int(cursor_pos.y)
        for rect, card in zip(self._rects, self.CARDS):
            hover = rect.collidepoint(mx, my)
            col   = card["colour"]
            pygame.draw.rect(surface, (10,10,10), rect.move(4,4), border_radius=8)
            pygame.draw.rect(surface, (55,55,55) if hover else (35,35,35), rect, border_radius=8)
            pygame.draw.rect(surface, col, rect, width=2, border_radius=8)
            pygame.draw.rect(surface, col, pygame.Rect(rect.x, rect.y+8, 4, rect.h-16), border_radius=2)
            surface.blit(font_md.render(card["title"], True, col), (rect.x+22, rect.y+22))
            for j, line in enumerate(card["desc"]):
                surface.blit(font_sm.render(line, True, (160,160,160)), (rect.x+22, rect.y+62+j*24))
            if hover:
                cx = rect.right - 28
                cy = rect.centery
                pygame.draw.polygon(surface, col, [(cx,cy-10),(cx+14,cy),(cx,cy+10)])

        draw_scanlines(surface)
        text_centre(surface, "Team 10!",
                    font_sm, (60,60,60), WIDTH//2, HEIGHT-30)
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
        play_music("MenuMusic")
        nonlocal scene
        scene = "menu"
        aim_game.reset()
        simon_game.reset()

    def aim_done(action):
        nonlocal scene
        if action == "play":
            aim_game.reset(keep_difficulty=True)
            scene = "aim"
        else:
            go_menu()

    def simon_done(action):
        nonlocal scene
        if action == "play":
            simon_game.reset()
            scene = "simon"
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
                        aim_game.reset(); scene = "aim"
                        SFX["Button"].play()
                        play_music("AimMusic")
                    elif choice == 1:
                        simon_game.reset(); scene = "simon"
                        SFX["Button"].play()
                        play_music("SimonMusic")
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