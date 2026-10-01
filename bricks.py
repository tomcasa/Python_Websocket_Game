"""Grille de briques destructibles."""


class Bricks:
    # Lignes où sont dessinées les briques (index dans la grille)
    LINES = (3, 5, 7)

    # Motif d'une brique complète : 3 colonnes
    BRICK_PATTERN = "[_]"
    BRICK_WIDTH = 3

    def __init__(self, rows: int = 10, cols: int = 150):
        self.rows = rows
        self.cols = cols
        # une brique tous les 3 chars sur chaque ligne
        self._bricks = {}
        for y in self.LINES:
            self._bricks[y] = [True] * (cols // self.BRICK_WIDTH)

    def brique_restante(self):
        return sum(sum(row) for row in self._bricks.values())

    def alive_at(self, y: int, x: int) -> bool:
        """Une brique existe-t-elle à cette cellule (y, x) de la grille ?"""
        if y not in self._bricks:
            return False
        brick_col = x // self.BRICK_WIDTH
        if 0 <= brick_col < len(self._bricks[y]):
            return self._bricks[y][brick_col]
        return False

    def hit(self, y: int, x: int) -> bool:
        """Détruit la brique à (y, x). Retourne True si une brique existait."""
        if y not in self._bricks:
            return False
        brick_col = x // self.BRICK_WIDTH
        if 0 <= brick_col < len(self._bricks[y]) and self._bricks[y][brick_col]:
            self._bricks[y][brick_col] = False
            return True
        return False

    def line_of(self, y: int) -> str:
        """Retourne la ligne y sous forme de string (avec les briques restantes)."""
        if y not in self._bricks:
            return ""
        out = []
        for alive in self._bricks[y]:
            out.append(self.BRICK_PATTERN if alive else "   ")
        return "".join(out)

    def reset(self):
        for y in self.LINES:
            self._bricks[y] = [True] * (self.cols // self.BRICK_WIDTH)