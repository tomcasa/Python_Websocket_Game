"""Balle rebondissante, avec état d'explosion."""


EXPLOSION_FRAMES = [
    # 3 frames d'explosion, de plus en plus large
    ["·"],
    ["*", "·", "*"],
    ["✳", "✴", "✳", "✴", "✳"],
]


class Ball:
    EXPLOSION_TICKS = len(EXPLOSION_FRAMES)   # 3 ticks d'animation

    def __init__(self, x: float, y: float, vx: float = 0.7, vy: float = 0.5):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.exploding = 0      # 0 = normale, >0 = en train d'exploser

    def reset(self, x: float, y: float):
        """Relance la balle après une explosion ou un point."""
        self.x = x
        self.y = y
        self.vx = 0.7 if self.vx >= 0 else -0.7
        self.vy = abs(self.vy) or 0.5
        self.exploding = 0

    def explode(self):
        """Démarre une explosion."""
        self.exploding = self.EXPLOSION_TICKS

    @property
    def is_alive(self) -> bool:
        return self.exploding == 0

    def step(self, rows: int, cols: int, bricks, players_dict) -> dict:
        """Avance d'un tick. Retourne les événements."""
        events = {
            "brick_hits": 0,
            "wall_hit": False,
            "paddle_hit": False,
            "floor_hit": False,
        }

        # ─── Si en explosion, on décompte et on ne bouge pas ───
        if self.exploding > 0:
            self.exploding -= 1
            return events

        # ─── Déplacement ───
        self.x += self.vx
        self.y += self.vy

        # ─── Rebonds murs ───
        if self.x <= 0:
            self.x = 0
            self.vx = abs(self.vx)
            events["wall_hit"] = True
        elif self.x >= cols - 1:
            self.x = cols - 1
            self.vx = -abs(self.vx)
            events["wall_hit"] = True

        if self.y <= 0:
            self.y = 0
            self.vy = abs(self.vy)
            events["wall_hit"] = True

        # ─── Briques ───
        ix, iy = int(self.x), int(self.y)
        if bricks.alive_at(iy, ix):
            bricks.hit(iy, ix)
            events["brick_hits"] += 1
            nbb = bricks.brique_restante()
            print(nbb)
            if ( nbb < 20 ): 
                self.vx = 1.3 if self.vx >= 0 else -1.3
                self.vy = 1
            if ( nbb < 10 ): 
                self.vx = 2 if self.vx >= 0 else -2
                self.vy = 2.2
                    
            self.vy = -self.vy
            self.y += self.vy * 0.6

        # ─── Pseudos ───
        for player in players_dict.values(): 
            try :
                pseudo = player["pseudo"]
                pos_x = player["pos_x"]
                if int(self.y) >= rows - 2:
                    label_len = player["wall_length"] 

                    if pos_x <= int(self.x) < pos_x + label_len:
                        self.y = rows - 3
                        self.vy = -abs(self.vy)
                        center = pos_x + label_len / 2
                        self.vx = (self.x - center) * 0.3
                        events["paddle_hit"] = True
                        break
            except:
                pass 

        # ─── Sol (sous les pseudos) ───
        if self.y >= rows - 0.5:
            events["floor_hit"] = True
            self.explode()

        return events

    def render_cell(self,i) -> str:
        """Retourne le caractère à dessiner pour cette balle."""
        if self.exploding == 0:
            return str(i)
        # frame d'explosion : 0 → la plus grande, EXPLOSION_TICKS-1 → la plus petite
        # (on joue l'animation à l'envers : ça commence large, ça se dissipe)
        idx = self.EXPLOSION_TICKS - self.exploding
        idx = min(idx, len(EXPLOSION_FRAMES) - 1)
        # on prend un char au hasard dans la frame (positions multiples)
        import random
        return random.choice(EXPLOSION_FRAMES[idx])