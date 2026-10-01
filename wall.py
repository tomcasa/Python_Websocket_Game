"""Mur Arkanoid qui se dessine par-dessus la pluie."""
import json , random 

from ball import Ball


class Wall:
    def __init__(self, rows: int = 2, cols: int = 150):
        self.rows = rows
        self.cols = cols
        self._players = {}
        self.bricks = None      # injecté depuis TextGame
        self.ball = None        # injecté depuis TextGame
        self.message = None 
        self.text_game = None 


    # ─── API ───
    def set_player(self, players):
        self._players = players
        for p in players.values() :
            p["ball"] = Ball(
                x=4.0, y=8.0,
                vx=0.7 if random.random() < 0.5 else -0.7,
                vy=0.5,
            )
            p['lives'] = 3
            p['playing'] = True
            



    # ─── LE POINT CLÉ : overlay sur la grille de pluie ───
    def overlay(self, rain: list[list[str]]) -> list[list[str]]:
        """Dessine le mur PAR-DESSUS la grille de pluie.

        rain : liste de ROWS listes de COLS caractères (modifiée en place).
        Retourne la grille modifiée.
        """
        rows = len(rain)
        cols = len(rain[0]) if rows else 0

        # ─── 1. BRIQUES (depuis l'état persistant) ───
        if not self.message : 
            if self.bricks is not None:
                for y in self.bricks.LINES:
                    if 0 <= y < rows:
                        line = self.bricks.line_of(y)
                        for x in range(min(len(line), cols)):
                            rain[y][x] = line[x]
        
        # ─── 1. Peindre la ligne des pseudos (en haut du mur) ───
         
        pi = 0 
        # ─── 2. Score et vies en haut à gauche ───
        score_x = 2
        score_y = 0

        #print(json.dumps(self._players))  
        for player in self._players.values(): 
            pseudo = player["pseudo"]
            score = player.get("score",0)
            lives = player.get("lives",3)
            hud = f"{pseudo}: {score} ♥{lives}"
            for i, c in enumerate(hud):
                x = score_x + i
                if 0 <= x < cols:
                    rain[score_y][x] = c
            score_x += len(hud) + 4   # espace entre HUD


            pi += 1 
            player_y = rows - pi

            if player["pos_x"] < 0: 
                player["pos_x"] = 0 
                
            label = f"=={pseudo[:5]}=="
            player["wall_length"] = len(label)

            if player["pos_x"] > cols-len(label): 
                player["pos_x"] = cols-len(label)

            # centrage dans le slot

            for i, c in enumerate(label):
                x = player["pos_x"] + i
                if 0 <= x < cols:
                    rain[player_y][x] = c      # ← écrit PAR-DESSUS

                
        pi = 0 
        # ─── 4. Balles (une par joueur, par-dessus tout) ───
        for player in self._players.values():                
            if (self.text_game._skip_player(player)) :
                continue
            
            pi += 1
            ball = player["ball"]
            if ball is None:
                continue
            bx = int(ball.x)
            by = int(ball.y)
            if 0 <= bx < cols and 0 <= by < rows:
                rain[by][bx] = ball.render_cell(pi)

 
        if self.message : 
            #print(self.message) 
            start = 3
            y = 2             
            for line in self.message.split("\n"): 
                #print(line) 
                y += 1                 
                for i, c in enumerate(line):                    
                    x = start + i 
                    if 0 <= x < cols and 0 <= y < rows :
                        rain[y][x] = c
                        

        return rain