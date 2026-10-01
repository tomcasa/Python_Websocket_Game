"""Effet Matrix : pluie de caractères qui tombe."""
import random
import unicodedata


_CHARS = (
    "0123456789"
    "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"
    "¥$#@%&*+=-<>|"
)

# Mais si un caractère est full-width (par ex. ア au lieu de ｱ), il fait 2 cases au lieu d'1 → décalage immédiat. Vérifie :
# Règle stricte : ne garde que Na, H. Exclus tout ce qui est W, F, A.

_CHARS = "".join(
    c for c in "AZERTYUIOP0123456789ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ¥$#@%&*+=-<>|"
    if unicodedata.east_asian_width(c) in ("Na")
)

GREEK_UPPER = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
GREEK_LOWER = "αβγδεζηθικλμνξοπρστυφχψω"
HEBREW      = "אבגדהוזחטיכלמנסעפצקרשת"
ARMENIAN_UPPER = "ԱԲԳԴԵԶԷԸԹԺԻԼԽԾԿՀՁՂՃՄՅՆՇՈՉՊՋՌՍՎՏՐՑՒՓՔՕՖ"
ARMENIAN_LOWER = "աբգդեզէըթժիլխծկհձղճմյնշոչպջռսվտրցւփքօֆ"
BRAILLE_SPARSE = "⠁⠂⠃⠄⠅⠆⠇⠈⠉⠊⠋⠌⠍⠎⠏⠐⠑⠒⠓⠔⠕⠖⠗⠘⠙⠚⠛⠜⠝⠞⠟"
GEORGIAN = "აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ"

_CHARS = (
    # ─── Chiffres ───
    "0123456789"
    # ─── Latin ───
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    # ─── Cyrillique (russe) ───
    "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
    "абвгдежзийклмнопрстуфхцчшщъыьэюя"
    # ─── Grec ───
    "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    "αβγδεζηθικλμνξοπρστυφχψω"
    # ─── Arménien ───
    "ԱԲԳԴԵԶԷԸԹԺԻԼԽԾԿՀՁՂՃՄՅՆՇՈՉՊՋՌՍՎՏՐՑՒՓՔՕՖ"
    "աբգդեզէըթժիլխծկհձղճմյնշոչպջռսվտրցւփքօֆ" 
    # ─── Symboles ASCII ───
    "$#@%&*+=-<>|~^`'\"_/\\.,:;!?()[]{}"
    
)


class MatrixRain:
    def __init__(self, rows: int = 25, cols: int = 92,
                 density: float = 0.2, spawn: float =  0.3):
        self.rows = rows
        self.cols = cols
        self.density = density   # probabilité qu'une colonne descende à ce tick
        self.spawn = spawn       # probabilité d'apparition d'un nouveau char en haut
        self.spawn_boost = 0.7     # taux si une goutte est proche
        self.active_window = 2 # combien de lignes du haut on inspecte
        self.disable = True


        # Grille de caractères
        self.grid = [[" "] * cols for _ in range(rows)]

    def _has_drop_above(self, x: int) -> bool:
        """True si une goutte est dans les `active_window` premières lignes."""
        for y in range(self.active_window):
            if self.grid[y][x] != " ":
                return True
        return False

    def tick(self) -> list[str]:
        """Fait tomber la pluie d'un cran, retourne les lignes."""
        for x in range(self.cols):
            # 1) Chaque colonne tombe à son propre rythme
            if random.random() < self.density:
                # Décalage vers le bas : on part du bas pour ne pas écraser
                for y in range(self.rows - 1, 0, -1):

                    self.grid[y][x] = self.grid[y - 1][x]

                # 2) Nouveau caractère en haut (ou espace si rien ne spawn)
                rate = self.spawn_boost if self._has_drop_above(x) else self.spawn
                if random.random() < rate and not self.disable :
                    self.grid[0][x] = random.choice(_CHARS)
                else:
                    self.grid[0][x] = " "

        #return ["".join(row) for row in self.grid]
        #return self.grid 
        return [row[:] for row in self.grid]
