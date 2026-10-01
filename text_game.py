"""Jeu de texte diffusé périodiquement à tous les clients."""
import asyncio
import logging
import random

import logging

from matrix_rain import MatrixRain
from wall import Wall 
from ball import Ball
from bricks import Bricks
import figlet_cmd 


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

log = logging.getLogger(__name__)

TICK_MS = 100
TICK_S = TICK_MS / 1000


# ─── données du jeu (exemple) ───
_WORDS = [
    "coucou", "figlet", "websocket", "python", "asyncio",
    "serveur", "client", "broadcast", "message", "canal",
]


class TextGame:
    """Un seul jeu à la fois, process-wide."""

    def __init__(self, broadcast):
        self._broadcast = broadcast
        self._task: asyncio.Task | None = None
        self._started_by: str | None = None
        self._tick = 0
        self._rain: MatrixRain | None = None
        self._bricks = None
        self._ball = None
        self._winner = "personne"



    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def _skip_player(self,player) : 
        return (not "playing" in player) or (not player["playing"] )

    async def start(self, by_pseudo: str) -> bool:
        """Démarre le jeu. Retourne False s'il tournait déjà."""
        
        if self.running:
            return False

        self._cols = 95 
        self._started_by = by_pseudo
        self._tick = 0
        self._rain = MatrixRain(rows=25, cols=self._cols)
        self._wall = Wall(rows=2, cols=self._cols)  
        self._wall.text_game = self
        self._bricks = Bricks(rows=25, cols=self._cols)
        self._wall.bricks = self._bricks
        self._ready = False

        self._task = asyncio.create_task(self._loop(), name="text_game")
        log.info("text_game démarré par %s", by_pseudo)
        return True

    async def stop(self, by_pseudo: str) -> bool:
        """Arrête le jeu. Retourne False s'il ne tournait pas."""
        if not self.running:
            return False

        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        log.info("text_game arrêté par %s", by_pseudo)
        end_game = 9 
        return True

    async def _loop(self):
        """Boucle principale : broadcast toutes les TICK_S secondes."""
        try:
            end_game = 0 
            while not self._ready : 
                self._tick += 1 
                lines = self._rain.tick()
                self._rain.disable=False
                self._wall.message = "[[ présser flèche droite pour démarrer ]]"
                self._wall.overlay(lines)
                lines = ["".join(row) for row in lines]

                await self._broadcast({
                    "type": "text_game",
                    "tick": self._tick,
                    #"text": random.choice(_WORDS),
                    "text": "\n".join(lines), 
                    "started_by": self._started_by,
                }) 
                await asyncio.sleep(TICK_S)  
            self._rain.disable=True      
            
            count_down = 14
            while count_down >0 : 
                self._tick += 1
                self._wall.message = figlet_cmd.render(f"-f doom {count_down}")    
                self._wall.message += "\n"  
                lines = self._rain.tick()
                
                self._wall.overlay(lines)
                lines = ["".join(row) for row in lines]

                await self._broadcast({
                    "type": "text_game",
                    "tick": self._tick,
                    #"text": random.choice(_WORDS),
                    "text": "\n".join(lines), 
                    "started_by": self._started_by,
                })
                if self._tick % 10 == 0 :
                    count_down -= 1
                await asyncio.sleep(TICK_S)  
        
            while True:


                all_events = {}

                for sid, player in self._wall._players.items():
                    
                    if self._skip_player(player) : 
                        continue 


                    ball = player['ball']
                    # si la balle est morte (explosion finie) → reset + perte de vie
                    if ball.exploding == 0 and player.get("pending_reset", False):
                        player['pending_reset'] = False
                        ball.reset(x=75.0, y=5.0)
                        continue


                    # ─── 2. Faire avancer la balle ───
                    events = ball.step(
                        rows=self._rain.rows,
                        cols=self._rain.cols,
                        bricks=self._bricks,
                        players_dict=self._wall._players,
                    )
                    
                    # score : +1 par brique cassée
                    if events["brick_hits"]: 
                        player['score'] = player.get('score',0) + events["brick_hits"]

                    # balle qui touche le sol → explosion + vie -1
                    if events["floor_hit"]:
                        player['lives'] = player['lives'] - 1
                        if player['lives']  <= 0:
                            player['playing']  = False
                            end_game = 10
                            message = f"{player['pseudo']} LOOSE"
                            
                        else:
                            player['pending_reset']  = True

                    all_events[sid] = events

                  
                
                # ─── 2. Détecter la fin de partie ───
                actifs = [p for p in self._wall._players.values() if 'playing' in p and p['playing']]
                if len(actifs) == 1 :
                    self._winner = actifs[0]['pseudo']

                self._wall.message = None
                if len(actifs) == 1 : # and end_game == 10:                    
                    self._wall.message = figlet_cmd.render(f"-f doom Winner is")    
                    self._wall.message += "\n\n\n"
                    self._wall.message += figlet_cmd.render(f"-f banner {self._winner}")    
                    self._wall.message += "\n\n/text_game start (pour relancer)"  
                    end_game = 9 


                self._tick += 1
                #print(self._tick)
                lines = self._rain.tick()
                self._wall.overlay(lines)
                lines = ["".join(row) for row in lines]

                await self._broadcast({
                    "type": "text_game",
                    "tick": self._tick,
                    #"text": random.choice(_WORDS),
                    "text": "\n".join(lines), 
                    "started_by": self._started_by,
                })
                
                if end_game == 9:                    
                    await self._broadcast({
                        "type": "system",  
                        "text": "Fin du Jeux", 
                    })
                    asyncio.create_task(self.stop("Fin du jeu"))

                await asyncio.sleep(TICK_S)
        except asyncio.CancelledError:
            # nettoyage éventuel, puis on laisse remonter
            log.info("text_game: boucle annulée")
            raise
        except Exception:
            log.exception("text_game: erreur dans la boucle")