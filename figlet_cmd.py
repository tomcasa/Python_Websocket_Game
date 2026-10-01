"""Génération d'ASCII art via pyfiglet."""
import logging
import shlex

import pyfiglet
from pyfiglet import Figlet, FigletFont, FigletError

log = logging.getLogger(__name__)

# Polices qu'on expose aux utilisateurs — liste blanche volontaire
# (pyfiglet en a ~600, mais beaucoup sont illisibles ou trop larges)
ALLOWED_FONTS = {
    "standard", "big", "small", "mini", "banner", "slant",
    "block", "bubble", "digital", "doom", "larry3d",
    "ogre", "rectangles", "shadow", "smscript", "smshadow",
    "starwars", "stop", "sub-zero", "thin", "univers",
}
DEFAULT_FONT = "standard"

MAX_LEN = 40           # longueur max du texte à transformer
MAX_LINES = 50         # sécurité si une police génère trop de lignes
MAX_LINE_LEN = 200     # sécurité largeur


class FigletError_(Exception):
    """Erreur utilisateur (message clair, à afficher tel quel)."""


def _parse_args(raw: str) -> tuple[str, str]:
    """Parse la ligne après '/figlet'.

    Formats acceptés :
        /figlet coucou
        /figlet -f big coucou
        /figlet --font=big coucou tom
    Retourne (font, text).
    """
    try:
        parts = shlex.split(raw)
    except ValueError as e:
        raise FigletError_(f"Syntaxe invalide : {e}")

    font = DEFAULT_FONT
    text_parts = []
    i = 0
    while i < len(parts):
        p = parts[i]
        if p in ("-f", "--font"):
            if i + 1 >= len(parts):
                raise FigletError_("Il manque le nom de la police après -f")
            font = parts[i + 1]
            i += 2
        elif p.startswith("--font="):
            font = p.split("=", 1)[1]
            i += 1
        else:
            text_parts.append(p)
            i += 1

    text = " ".join(text_parts).strip()
    if not text:
        raise FigletError_("Aucun texte à transformer. Usage : /figlet [-f police] <texte>")
    return font, text


def _sanitize_text(text: str) -> str:
    # On limite et on enlève les sauts de ligne (un figlet multi-lignes,
    # c'est possible mais ça complique l'affichage)
    text = text.replace("\r", " ").replace("\n", " ")
    if len(text) > MAX_LEN:
        raise FigletError_(f"Texte trop long (max {MAX_LEN} caractères).")
    return text


def render_all(raw_args: str) -> str:
    font, text = _parse_args(raw_args)
    ret = []
    if font == "ALL":  
        for font in ALLOWED_FONTS:
            ret.append(font)
            ret.append(render(raw_args.replace("ALL",font)))

        return "\n".join(ret)
    else :
        return render(raw_args)


def render(raw_args: str) -> str:
    """Génère l'ASCII art. Lève FigletError_ si entrée invalide."""
    font, text = _parse_args(raw_args)

    if font not in ALLOWED_FONTS:
        raise FigletError_(
            f"Police inconnue : '{font}'. "
            f"Disponibles : {', '.join(sorted(ALLOWED_FONTS))}"
        )

    text = _sanitize_text(text)

    try:
        # Vérifie que la police existe vraiment dans pyfiglet
        FigletFont.preloadFont(font)
        fig = Figlet(font=font, width=200)
        art = fig.renderText(text)
    except (FigletError, OSError) as e:
        log.warning("figlet: erreur police %s : %s", font, e)
        raise FigletError_(f"Impossible de générer avec la police '{font}'.")

    # Nettoyage : retirer les lignes vides de fin, espaces de droite
    lines = [line.rstrip() for line in art.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    while lines and not lines[0]:
        lines.pop(0)

    if not lines:
        raise FigletError_("Rendu vide.")
    if len(lines) > MAX_LINES:
        raise FigletError_("Rendu trop grand, réduis le texte.")

    # Sécurité largeur : on tronque proprement les lignes trop longues
    lines = [ln[:MAX_LINE_LEN] for ln in lines]

    return "\n".join(lines)