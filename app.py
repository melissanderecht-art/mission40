# -*- coding: utf-8 -*-
"""
🦄 MISSION 40 — Le week-end de Mélissande · Gîtes Le Val d'Or, Saint-Prix (Ardèche)
Lancer avec :  py -V:3.13 -m streamlit run app.py
Dépendances :  streamlit (>= 1.40) et pandas
👉 Tout ce que tu modifies est dans les blocs marqués "✏️".
"""

import base64
import io
import json
import mimetypes
import os
import re
import threading
import unicodedata
from datetime import date, datetime
from html import escape
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st

# =============================================================================
# ✏️ RÉGLAGES GÉNÉRAUX
# =============================================================================
PRENOM = "Mélissande"
DATES = "11-14 juin 2027"
DATE_ARRIVEE = datetime(2027, 6, 11, 18, 0)   # (année, mois, jour, heure, minute)
NOM_LIEU = "Gîtes Le Val d'Or · Saint-Prix (Ardèche)"
ALBUM_PHOTOS = ""            # ✏️ lien de l'album partagé (Google Photos, iCloud…)
CODE_PARCOURS = "ARDECHE40"  # débloque le parcours sport
CODE_DEFIS = "MOLKKYCHAMP"   # débloque Jouer + Classement
AFFICHER_DIAGNOSTIC = True


st.set_page_config(page_title="Mission 40 🦄", page_icon="🦄", layout="centered",
                   initial_sidebar_state="collapsed")


# =============================================================================
# 🖼️ IMAGES LOCALES (dossier Images/Badges à côté de app.py) → Base64 pour le HTML
# =============================================================================
@st.cache_data(show_spinner=False)
def image_en_base64(chemin: str, version: float = 0.0, taille: int = 240) -> str:
    """Lit une image locale et la renvoie encodée en Base64, prête à être collée dans un <img src="...">.
    L'image est réduite (240 px max) pour garder la page légère. 'version' (date du fichier) relance le calcul si tu changes l'image."""
    octets = Path(chemin).read_bytes()
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(octets))
        img.thumbnail((taille, taille))
        tampon = io.BytesIO()
        img.save(tampon, format="PNG", optimize=True)
        octets = tampon.getvalue()
    except Exception:
        pass   # sans Pillow, on garde l'image d'origine
    return "data:image/png;base64," + base64.b64encode(octets).decode()


def _chercher_dossier(chemins):
    """Cherche un dossier à côté de app.py, sans tenir compte des majuscules (ex. Images/Picto ou images/picto)."""
    base = Path(__file__).parent
    for chemin in chemins:
        courant = base
        for nom in chemin:
            courant = next((d for d in courant.iterdir() if d.is_dir() and d.name.lower() == nom), None)
            if courant is None:
                break
        if courant is not None:
            return courant
    return None


def trouver_dossier_badges():
    """Dossier des badges : Images/Badges, sinon 'vignettes' ou 'badges'."""
    return _chercher_dossier((("images", "badges"), ("vignettes",), ("badges",)))


def trouver_dossier_pictos():
    """Dossier des pictos des jauges : Images/Picto (ou Pictos)."""
    return _chercher_dossier((("images", "picto"), ("images", "pictos"), ("picto",), ("pictos",)))


def licorne_html():
    """Illustration d'accueil : première image trouvée dans Images/Accueil (de préférence un fichier dont le nom contient « licorne »).
    Sans image, on garde l'émoji 🦄."""
    dossier = _chercher_dossier((("images", "accueil"), ("accueil",)))
    if dossier is not None:
        fichiers = sorted(f for f in dossier.iterdir() if f.suffix.lower() in (".png", ".webp", ".jpg", ".jpeg"))
        fichier = next((f for f in fichiers if "licorne" in _norm(f.stem)), fichiers[0] if fichiers else None)
        if fichier is not None:
            return f'<div class="licorne-img"><img src="{image_en_base64(str(fichier), fichier.stat().st_mtime, 480)}"></div>'
    if AFFICHER_DIAGNOSTIC:
        st.info("ℹ️ Aucune image trouvée dans Images/Accueil : l'émoji 🦄 est utilisé. (Pour masquer ce message : AFFICHER_DIAGNOSTIC = False)")
    return '<div class="licorne">🦄</div>'


def badge_image(icone, rang):
    """Choisit le PNG d'un animal d'après la colonne Icone (ex. 'chevre' trouve « chèvre badge 1.png »).
    S'il y a plusieurs badges pour l'animal, on les alterne d'un invité à l'autre ('rang' = place dans l'équipe)."""
    dossier = trouver_dossier_badges()
    if dossier is None or not icone:
        return None
    fichiers = sorted((f for f in dossier.iterdir() if f.suffix.lower() == ".png" and _norm(f.stem).startswith(_norm(icone))),
                      key=lambda f: (len(f.stem), f.stem))
    return fichiers[rang % len(fichiers)] if fichiers else None

# =============================================================================
# CSS GLOBAL — fond crème, Playfair Display (titres) + Montserrat (texte)
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,500;1,700&family=Montserrat:wght@400;500;600;700&display=swap');
:root { --nuit:#14315A; --foret:#3C4A3A; --or:#E4A834; --orange:#F08A24;
  --grain:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 .55 0 0 0 0 .42 0 0 0 0 .3 0 0 0 .25 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }

html, body, .stApp, [class*="css"] { font-family:'Montserrat',sans-serif; }
.stApp p, .stApp label, .stApp li, .stApp a, .stApp button, .stApp input, .stApp textarea, .stApp div,
.stApp span:not([data-testid="stIconMaterial"]) { font-family:'Montserrat',sans-serif; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { font-family:'Playfair Display',serif !important; font-weight:700; }
.stApp h2 { text-transform:uppercase; letter-spacing:.08em; text-align:center; font-size:1.45rem; }
[data-testid="stCaptionContainer"] p { text-align:center; }
.stApp .titre-page { font-family:'Playfair Display',serif; font-weight:700; text-transform:uppercase; letter-spacing:.09em;
                     text-align:center; font-size:1.5rem; color:#14315A; margin:.2rem 0 .1rem; }
.stApp .titre-section { font-family:'Playfair Display',serif; font-weight:700; font-size:1.3rem; color:#14315A; margin:.6rem 0 .4rem; }
.stApp .titre-page, .stApp .titre-section, .prog .horaire, .prog .titre, .hero .mission, .hero .prenom
  { font-variant-numeric:lining-nums; font-feature-settings:"lnum" 1; }   /* chiffres alignés : 18h00 et non 18hoo */
html, body { background:#FDFBF7 !important; }
.stApp { background-color:#FDFBF7 !important; background-attachment:fixed;
  background-image:var(--grain), radial-gradient(ellipse 80% 35% at 105% -5%, rgba(240,170,184,.30), transparent 70%),
                   radial-gradient(ellipse 90% 40% at -10% 105%, rgba(150,172,110,.28), transparent 70%) !important; }
[data-testid="stAppViewContainer"], [data-testid="stMain"] { background:transparent !important; }
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stSidebar"],
[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] { display:none !important; }
.block-container { padding:1rem 1rem 7rem; max-width:520px; }
h1, h2, h3 { font-family:'Playfair Display',serif; color:var(--nuit); }

/* ---- Accueil ---- */
.hero { text-align:center; padding:1rem .5rem .2rem; }
.hero .mission { font-family:'Playfair Display',serif; font-style:italic; font-weight:700; font-size:3.3rem; color:var(--nuit); line-height:1; }
.hero .petit { color:var(--foret); margin-top:.5rem; font-size:.95rem; }
.hero .prenom { font-family:'Playfair Display',serif; font-style:italic; font-weight:700; font-size:2.6rem; color:#D95D79; line-height:1.1; }
.hero .licorne { font-size:4.2rem; margin:.3rem 0; }
.hero .licorne-img { margin:.4rem 0 .2rem; }
.hero .licorne-img img { height:160px; width:auto; max-width:75%; mix-blend-mode:multiply; filter:drop-shadow(0 3px 5px rgba(60,50,45,.15)); }
.compte { background:#fff; border-radius:20px; padding:.9rem 1.1rem; margin:.8rem 0 1.2rem;
          border-left:6px solid var(--or); color:var(--nuit); box-shadow:0 2px 12px rgba(20,49,90,.07); }

/* ---- Cartes blanches (programme, copains, missions…) ---- */
.carte { background:#fff; border-radius:20px; padding:1.1rem 1.25rem; margin-bottom:.8rem;
         box-shadow:0 2px 12px rgba(20,49,90,.07); }
.carte .titre { font-family:'Playfair Display',serif; font-weight:700; color:var(--nuit); font-size:1.08rem; }
.carte .sous { color:var(--foret); font-size:.82rem; margin-top:.15rem; }
.ligne { display:flex; gap:1rem; align-items:center; }
.ligne .corps { flex:1; }
.horaire { font-weight:700; color:var(--nuit); font-size:.9rem; min-width:3.2rem; }
.icone { font-size:1.7rem; }
.pts { float:right; background:rgba(255,255,255,.75); border-radius:999px; padding:.1rem .7rem; font-weight:700; font-size:.78rem; }
.tag { display:inline-block; background:#C96F4F; color:#fff; border-radius:999px; padding:.12rem .7rem; margin:.3rem .25rem 0 0;
        font-size:.72rem; font-weight:600; box-shadow:0 2px 4px rgba(150,70,40,.18); }       /* badges terracotta */
.equipe { display:inline-block; background:rgba(126,144,96,.20); color:#4C5E36; border-radius:999px; padding:.08rem .65rem;
          margin:.35rem .3rem 0 0; font-size:.72rem; font-weight:600; }
.slogan { font-family:'Playfair Display',serif; font-style:italic; font-size:.85rem; color:#4F5E4C; margin-top:.35rem; }
.avatar { width:56px; height:56px; border-radius:50%; background:#EFE4D0; display:flex; align-items:center; justify-content:center; font-size:1.7rem; overflow:hidden; flex-shrink:0; }
.avatar img { width:100%; height:100%; object-fit:cover; }
.cadenas { text-align:center; background:#fff; border-radius:24px; padding:1.8rem 1rem; margin:1rem 0; box-shadow:0 2px 12px rgba(20,49,90,.07); }
.cadenas .gros { font-size:3rem; }

/* ---- Sous-titres : Playfair Display en italique ---- */
[data-testid="stCaptionContainer"] p, .hero .petit { font-family:'Playfair Display',serif !important; font-style:italic; font-size:1.05rem !important; color:#4F5E4C; }

/* ---- Cartes du programme : papier crème translucide, grain, bords légèrement irréguliers ---- */
.prog { display:flex; align-items:center; gap:1rem; border-radius:18px 14px 17px 15px; padding:1rem 1.1rem; margin-bottom:.8rem;
        background:var(--grain), radial-gradient(ellipse 70% 120% at 100% 50%, rgba(246,214,190,.45), transparent 70%), rgba(255,251,243,.72);
        border:1px solid rgba(170,145,105,.25); box-shadow:0 4px 12px rgba(120,90,50,.06);
        transition:transform .25s ease, box-shadow .25s ease; }
.prog:hover { transform:translateY(-2px); box-shadow:0 8px 18px rgba(120,90,50,.10); }
.prog .horaire { font-family:'Playfair Display',serif; font-weight:600; color:#14315A; font-size:1rem; min-width:3.1rem;
                 padding-right:.9rem; border-right:1px solid rgba(170,145,105,.35); align-self:stretch; display:flex; align-items:center; }
.prog .corps { flex:1; min-width:0; }
.prog .titre { font-family:'Playfair Display',serif; font-weight:600; color:#14315A; font-size:1.02rem; line-height:1.25; }
.prog .desc { color:#4F555E; font-size:.8rem; font-weight:500; margin-top:.2rem; }
.prog .visuel { width:62px; height:62px; flex-shrink:0; animation:flotte 5s ease-in-out infinite; }
.prog img.visuel { object-fit:contain; mix-blend-mode:multiply; }   /* le fond blanc d'une image disparaît dans la carte */
.prog .visuel.emoji { display:flex; align-items:center; justify-content:center; font-size:1.9rem; border-radius:50%; opacity:.95;
    background:radial-gradient(circle at 40% 40%, rgba(247,214,190,.85), rgba(240,196,170,.35) 65%, transparent 100%);
    filter:saturate(.55) sepia(.25) contrast(.92); }                 /* émoji adouci : couleurs pastel */
@keyframes flotte { 0%,100% { transform:translateY(0); } 50% { transform:translateY(-4px); } }
@media (prefers-reduced-motion:reduce) { .prog .visuel { animation:none; } }

/* ---- Même papier doux pour les autres cartes ---- */
.carte, .cadenas, [data-testid="stCheckbox"] { background-image:var(--grain); background-color:rgba(255,251,243,.75);
    border:1px solid rgba(170,145,105,.22); box-shadow:0 4px 12px rgba(120,90,50,.06); }

/* ---- Boutons génériques ---- */
.stButton > button, .stLinkButton > a { border-radius:999px !important; background:var(--foret) !important; border:none !important; font-weight:700 !important; }
.stButton > button p, .stLinkButton > a p { color:#fff !important; }
.stTextInput input { border-radius:16px; }
[data-testid="stCheckbox"] { background:#fff; border-radius:16px; padding:.55rem .9rem; margin-bottom:.45rem; box-shadow:0 2px 10px rgba(20,49,90,.06); }

/* ---- Lignes de boutons qui restent HORIZONTALES sur smartphone (grille + barre de jours) ---- */
.st-key-grille, [class*="st-key-barre_"] { gap:.6rem !important; }
.st-key-grille [data-testid="stHorizontalBlock"], [class*="st-key-barre_"] [data-testid="stHorizontalBlock"] { flex-wrap:nowrap !important; gap:.6rem !important; }
.st-key-grille [data-testid="stColumn"], [class*="st-key-barre_"] [data-testid="stColumn"] { min-width:0 !important; flex:1 1 0 !important; width:auto !important; }

/* ---- Grosses tuiles de l'accueil : icône blanche AU-DESSUS du texte, coins 24px ---- */
[class*="st-key-nav_"] button { height:6.6rem; border-radius:24px !important; box-shadow:0 4px 14px rgba(20,49,90,.15); }
[class*="st-key-nav_"] button [data-testid="stMarkdownContainer"] p { display:flex; flex-direction:column; align-items:center; gap:.45rem;
    margin:0; font-size:.78rem; font-weight:600; letter-spacing:.09em; line-height:1.2; }
[class*="st-key-nav_"] [data-testid="stIconMaterial"] { font-size:2.1rem !important; color:#fff !important; }
.st-key-nav_jouer button      { background:#D95D79 !important; }   /* rose terracotta */
.st-key-nav_weekend button    { background:#3D737F !important; }   /* bleu canard */
.st-key-nav_copains button    { background:#E4A834 !important; }   /* jaune safran */
.st-key-nav_autour button     { background:#8A9A6B !important; }   /* sauge */
.st-key-nav_classement button { background:#7B5C9E !important; }   /* parme */
.st-key-nav_galerie button    { background:#E8876A !important; }   /* corail */

/* ---- Barre de petits boutons arrondis (jours du programme, parcours) ---- */
[class*="st-key-barre_"] button { min-height:3.1rem; padding:.2rem 0 !important; border:none !important; }
[class*="st-key-barre_"] button p { color:#fff !important; font-size:.72rem !important; font-weight:700 !important; white-space:nowrap;
                                    text-shadow:0 1px 2px rgba(50,35,20,.40); }

/* ---- Bouton retour discret ---- */
.st-key-retour button { background:transparent !important; padding:.2rem .3rem !important; }
.st-key-retour button p { color:var(--nuit) !important; }

/* ---- Bandeau de navigation fixé en bas de l'écran ---- */
.st-key-bandeau { position:fixed; bottom:0; left:50%; transform:translateX(-50%); width:100%; max-width:520px; z-index:1000;
    background:var(--grain), rgba(253,251,247,.95); backdrop-filter:blur(8px); border-top:1px solid rgba(170,145,105,.30);
    border-radius:22px 22px 0 0; box-shadow:0 -4px 14px rgba(120,90,50,.08);
    padding:.35rem .5rem calc(.45rem + env(safe-area-inset-bottom)); gap:0 !important; }
.st-key-bandeau [data-testid="stHorizontalBlock"] { flex-wrap:nowrap !important; gap:.1rem !important; }
.st-key-bandeau [data-testid="stColumn"] { min-width:0 !important; flex:1 1 0 !important; width:auto !important; }
.st-key-bandeau button { background:transparent !important; box-shadow:none !important; border:none !important;
    border-radius:14px !important; height:3.5rem; padding:.15rem 0 !important; }
.st-key-bandeau button p { display:flex; flex-direction:column; align-items:center; gap:.15rem; margin:0; font-size:.62rem !important;
    font-weight:600 !important; line-height:1.1; color:#4F555E !important; }
.st-key-bandeau [data-testid="stIconMaterial"] { font-size:1.6rem !important; color:#4F555E; }

/* ====== PAGE LES COPAINS : coup de crayon / coloriage ====== */
/* Grand encadré d'équipe : contour "fait main" + fine ligne de crayon (la couleur --c est définie équipe par équipe en Python) */
[class*="st-key-equipe_"] { border-radius:255px 15px 225px 15px / 15px 225px 15px 255px; padding:1.5rem 1.2rem !important; margin:0 0 1.8rem; gap:.9rem !important;
    border:2px solid color-mix(in srgb, rgb(var(--c, 240,196,206)) 40%, #3a2f2a); outline:1.2px solid rgba(60,50,45,.22); outline-offset:3px;
    box-shadow:0 5px 14px rgba(var(--c, 240,196,206), .28);
    background:var(--grain), linear-gradient(165deg, rgba(var(--c, 240,196,206), .68), rgba(var(--c, 240,196,206), .34)); }
.stApp .equipe-titre { font-family:'Playfair Display',serif; font-weight:700; font-size:1.9rem; color:#14315A; text-align:center; line-height:1.15;
}
.stApp .equipe-slogan { font-family:'Playfair Display',serif; font-style:italic; font-size:.95rem; color:#4F555E; text-align:center; margin-top:.4rem; }

/* Carte blanche : même contour irrégulier, trait de crayon fin */
[class*="st-key-fiche_"] { background:#fff !important; border-radius:255px 15px 225px 15px / 15px 225px 15px 255px;
    padding:1.2rem 1rem 1.1rem !important; gap:.6rem !important;
    border:1.6px solid rgba(60,50,45,.55); outline:1px solid rgba(60,50,45,.16); outline-offset:3px; box-shadow:0 4px 12px rgba(90,60,40,.08); }
.stApp .fi { text-align:center; padding-bottom:.8rem; margin-bottom:0 !important; display:flow-root; }
.badge-img { width:92px; height:92px; margin:0 auto .5rem; }
.badge-img img { width:100%; height:100%; object-fit:contain; filter:drop-shadow(0 3px 5px rgba(60,50,45,.20)); }
.badge { width:78px; height:78px; margin:0 auto .55rem; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:2.3rem;
    background:var(--grain), radial-gradient(circle at 35% 30%, rgba(var(--c, 240,196,206), .75), rgba(var(--c, 240,196,206), .32));
    box-shadow:0 0 0 2px #fff, 0 0 0 3.5px rgba(60,50,45,.45); }                 /* badge de secours (émoji) */
.stApp .fi .prenom { font-family:'Playfair Display',serif; font-weight:700; font-size:1.25rem; color:#14315A; }
.fi .lien { font-size:.76rem; color:#4F555E; margin-top:.1rem; }
.fi .tags { margin-top:.4rem; }
.signe { font-style:italic; font-size:.82rem; color:#4F555E; margin-top:.55rem; }

/* Mini-jauges : 2 x 2, jamais de retour à la ligne, remplies avec la couleur pastel de l'équipe */
.jauges { display:grid; grid-template-columns:1fr 1fr; gap:.5rem .6rem; margin-top:.85rem; padding-top:.65rem; border-top:1px dashed rgba(60,50,45,.28); }
.jg { display:flex; align-items:center; justify-content:center; gap:.28rem; white-space:nowrap; min-width:0; }
.ico { display:inline-block; width:19px; height:19px; flex-shrink:0; background-size:contain; background-repeat:no-repeat; background-position:center; }
.jg-b { display:block; flex:0 1 38px; min-width:16px; height:4px; border-radius:4px; background:rgba(60,50,45,.12); overflow:hidden; }
.jg-b i { display:block; height:100%; border-radius:4px; background:rgb(var(--c, 240,196,206)); box-shadow:inset 0 0 0 .5px rgba(60,50,45,.18); }
.jg-n { font-size:.64rem; font-weight:600; color:#4F555E; flex-shrink:0; }

/* Lien discret "Voir son secret" + anecdote révélée */
[class*="st-key-anec_"] .stButton { display:flex; justify-content:center; }
[class*="st-key-anec_"] button { background:transparent !important; border:none !important; box-shadow:none !important;
    min-height:0; padding:.1rem .6rem !important; border-radius:10px !important; }
[class*="st-key-anec_"] button p { color:#B8532F !important; font-size:.74rem !important; font-weight:600 !important;
    text-decoration:underline dotted; text-underline-offset:3px; }
[class*="st-key-anec_"] button:hover { background:rgba(201,111,79,.10) !important; }
.secret { background:rgba(246,214,190,.35); border-left:3px solid #C96F4F; border-radius:12px; padding:.6rem .85rem; text-align:left;
          font-style:italic; font-size:.82rem; color:#4F5E4C; line-height:1.4; animation:apparait .4s ease; }
@keyframes apparait { from { opacity:0; transform:translateY(-4px); } to { opacity:1; transform:none; } }

/* ====== LIVRE D'OR : formulaire + anecdotes reçues ====== */
.st-key-nav_livredor button { background:#6E9A93 !important; }
.mot-intro { text-align:center; color:#4F555E; font-size:.88rem; margin-bottom:.8rem; }
[data-testid="stForm"] { background:#fff; border:1.6px solid rgba(60,50,45,.5); outline:1px solid rgba(60,50,45,.16); outline-offset:3px;
    border-radius:255px 15px 225px 15px / 15px 225px 15px 255px; padding:1.4rem 1.3rem; box-shadow:0 4px 12px rgba(90,60,40,.08); }
[data-testid="stFormSubmitButton"] button { border-radius:999px !important; background:var(--foret) !important; border:none !important; }
[data-testid="stFormSubmitButton"] button p { color:#fff !important; font-weight:700 !important; }
.stTextArea textarea { border-radius:14px; }
.mot { background:#fff; border:1.6px solid rgba(60,50,45,.5); outline:1px solid rgba(60,50,45,.16); outline-offset:3px;
    border-radius:255px 15px 225px 15px / 15px 225px 15px 255px; padding:1.2rem 1.3rem; margin:.9rem 0 1.1rem; box-shadow:0 4px 12px rgba(90,60,40,.08); }
.stApp .mot-texte { font-family:'Playfair Display',serif; font-style:italic; font-size:1rem; color:#14315A; line-height:1.5; }
.stApp .mot-auteur { margin-top:.6rem; text-align:right; font-size:.78rem; color:#4F555E; font-weight:600; }
.mot-auteur span { font-weight:400; color:#8C919A; margin-left:.4rem; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# OUTILS
# =============================================================================
st.session_state.setdefault("page", "accueil")


def aller(page):
    st.session_state["page"] = page


def visuel_html(v):
    """Illustration à droite d'une carte. 'v' peut être :
    - une URL d'image            → "https://…/apero.jpg"
    - un nom de fichier image    → "apero.png" (cherché à côté de app.py, puis dans le dossier Images et ses sous-dossiers)
    - un simple émoji            → "🥂" (affiché sur une pastille crème)"""
    if v.startswith("http"):
        return f'<img class="visuel" src="{escape(v)}">'
    if v.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
        fichier = Path(__file__).parent / v
        if not fichier.exists():
            dossier = _chercher_dossier((("images",),))
            fichier = next((f for f in dossier.rglob("*") if f.is_file() and f.name.lower() == Path(v).name.lower()), fichier) if dossier else fichier
        if fichier.exists():
            return f'<img class="visuel" src="{image_en_base64(str(fichier), fichier.stat().st_mtime, 160)}">'
    return f'<div class="visuel emoji">{escape(v)}</div>'


def entete(titre, sous_titre=""):
    """Bouton retour + titre de page."""
    st.button("← Accueil", key="retour", on_click=aller, args=("accueil",))
    st.markdown(f"<div class='titre-page'>{titre}</div>", unsafe_allow_html=True)
    if sous_titre:
        st.caption(sous_titre)


def pinceau(i):
    """Silhouette de coup de pinceau (masque SVG aux bords irréguliers). Une variante par bouton."""
    chemins = ["M10,26 C50,12 120,16 190,22 L188,56 C130,68 60,62 12,64 Z",
               "M12,20 C60,14 130,22 188,16 L190,60 C120,64 70,70 10,60 Z",
               "M8,24 C70,18 140,12 192,24 L186,64 C120,60 60,70 14,58 Z",
               "M14,18 C60,22 140,14 190,20 L188,58 C130,70 60,60 10,66 Z",
               "M10,22 C50,16 130,24 192,18 L190,62 C120,66 60,60 12,62 Z"]
    graines = [3, 8, 14, 21, 5]
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 80' preserveAspectRatio='none'>"
           "<filter id='f' x='-10%' y='-30%' width='120%' height='160%'>"
           f"<feTurbulence type='fractalNoise' baseFrequency='0.035 0.22' numOctaves='3' seed='{graines[i % 5]}' result='n'/>"
           "<feDisplacementMap in='SourceGraphic' in2='n' scale='15' xChannelSelector='R' yChannelSelector='G'/></filter>"
           f"<path d='{chemins[i % 5]}' fill='black' filter='url(#f)'/></svg>")
    return "data:image/svg+xml," + quote(svg)


def barre_boutons(cle, labels):
    """Ligne horizontale de petits boutons colorés. Le bouton choisi passe en jaune doré
    avec un liseré orange. Renvoie le label sélectionné."""
    st.session_state.setdefault(f"sel_{cle}", labels[0])
    choisi = st.session_state[f"sel_{cle}"]
    # ✏️ Couleurs (RVB) des jours non choisis ; le jour choisi est toujours jaune doré
    couleurs = [(112, 168, 184), (226, 132, 156), (150, 172, 112), (170, 148, 205), (232, 160, 120)]
    inclinaisons = [-1.5, 1.0, -0.8, 1.3, -1.0]   # légères rotations pour casser la régularité
    css = ""
    for i, lab in enumerate(labels):
        choisi_ici = lab == choisi
        r, g, b = (232, 160, 40) if choisi_ici else couleurs[i % len(couleurs)]
        fonce = f"rgb({int(r * .82)},{int(g * .82)},{int(b * .82)})"   # pigment qui s'accumule sur les bords
        clair = f"rgb({min(255, int(r * 1.1))},{min(255, int(g * 1.1))},{min(255, int(b * 1.1))})"
        masque = f'url("{pinceau(i)}") center/100% 100% no-repeat'
        css += (f".st-key-barre_{cle}_{i} {{ filter:drop-shadow(0 3px 3px rgba({r},{g},{b},.45)); }} "
                f".st-key-barre_{cle}_{i} button {{ border-radius:0 !important; box-shadow:none !important; "
                f"transform:rotate({inclinaisons[i % 5]}deg) scale({1.08 if choisi_ici else 1}); "
                f"background:var(--grain), radial-gradient(ellipse at 30% 35%, rgba(255,255,255,.22), transparent 60%), "
                f"linear-gradient(95deg, {fonce}, rgb({r},{g},{b}) 38%, {clair} 68%, {fonce}) !important; "
                f"-webkit-mask:{masque}; mask:{masque}; }} ")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)   # CSS dynamique selon le choix
    with st.container(key=f"barre_{cle}"):
        cols = st.columns(len(labels))
        for i, (col, lab) in enumerate(zip(cols, labels)):
            col.button(lab, key=f"barre_{cle}_{i}", width="stretch",
                       on_click=st.session_state.__setitem__, args=(f"sel_{cle}", lab))
    return choisi


def deverrouille(cle, code, titre, indice):
    """Cadenas + champ code. Renvoie True si débloqué (le reste ensuite)."""
    if st.session_state.get(f"ok_{cle}"):
        return True
    st.markdown(f'<div class="cadenas"><div class="gros">🔒</div><div class="titre-section">{titre}</div><p>{indice}</p></div>',
                unsafe_allow_html=True)
    saisie = st.text_input("Code secret", key=f"saisie_{cle}", type="password", placeholder="Tape le code ici…")
    if not saisie.strip():
        st.info("🔐 Verrouillé. Le code te sera donné de vive voix, sois attentif(ve) !")
    elif saisie.strip().upper() == code.upper():
        st.session_state[f"ok_{cle}"] = True
        st.rerun()
    else:
        st.error("🦄 Mauvais code ! Même la licorne a trouvé plus vite… Tends l'oreille et réessaie.")  # ✏️ message drôle
    return False


# =============================================================================
# ACCUEIL
# =============================================================================
def page_accueil():
    st.markdown(f"""<div class="hero">
      <div class="mission">Mission 40</div>
      <div class="petit">Le week-end de</div>
      <div class="prenom">{PRENOM}</div>
      <div class="petit">Ardèche · {DATES}</div>
      {licorne_html()}
      <div class="petit">Un week-end. Des amis. Des défis.<br>Une licorne. Que demander de plus ? ♡</div>
    </div>""", unsafe_allow_html=True)

    reste = DATE_ARRIVEE - datetime.now()
    texte = (f"⏳ Plus que <b>{reste.days} jours</b> et <b>{reste.seconds // 3600} heures</b> avant le départ !"
             if reste.total_seconds() > 0 else "🎉 C'est parti, la mission commence !")
    st.markdown(f'<div class="compte">{texte}</div>', unsafe_allow_html=True)

    st.markdown("<div class='titre-section' style='text-align:center'>Prête pour l'aventure ?</div>", unsafe_allow_html=True)
    # (clé, icône Material, texte) — 2 tuiles par ligne
    tuiles = [("jouer", "sports_esports", "JOUER"), ("weekend", "calendar_month", "LE WEEK-END"),
              ("copains", "groups", "LES COPAINS"), ("autour", "forest", "AUTOUR DE NOUS"),
              ("classement", "emoji_events", "CLASSEMENT"), ("galerie", "photo_camera", "GALERIE")]
    verrous = {"jouer": "defis", "classement": "defis"}   # tuiles qui affichent un cadenas tant que verrouillées
    with st.container(key="grille"):
        for i in range(0, len(tuiles), 2):
            for col, (cle, ico, txt) in zip(st.columns(2), tuiles[i:i + 2]):
                lock = " 🔒" if cle in verrous and not st.session_state.get(f"ok_{verrous[cle]}") else ""
                col.button(f":material/{ico}: {txt}{lock}", key=f"nav_{cle}", width="stretch",
                           on_click=aller, args=(cle,))


# =============================================================================
# JOUER 🔒
# =============================================================================
def page_jouer():
    entete("Jouer", "Les missions du moment")
    if not deverrouille("defis", CODE_DEFIS, "Zone de jeu", "Seuls les vrais compétiteurs connaissent le code…"):
        return
    st.success("🔓 Les missions sont ouvertes. Que le meilleur gagne !")
    # ✏️ Tes 5 missions : (titre, description, points, couleur de fond)
    missions = [
        ("Pyramide humaine", "Selfie d'équipe : 3 étages minimum 🤳", 200, "#E3D8EE"),
        ("Animal sauvage", "Imite un animal de l'Ardèche dans la nature 🦆", 150, "#F8E3B0"),
        ("Saut synchronisé", "Photo de plongeon collectif dans la piscine 🏊", 250, "#C9E0E6"),
        ("Pub de fromage", "Recrée une pub avec les produits locaux 🧀", 150, "#D5E0BE"),
        ("Le défi des 40", "Bougie imaginaire sur un sommet, en tenue de sport 🎂", 500, "#F8CDBE"),
    ]
    total = 0
    for i, (titre, desc, pts, fond) in enumerate(missions):
        st.markdown(f"""<div class="carte" style="background:{fond};margin-bottom:.3rem"><span class="pts">{pts} pts</span>
          <div class="titre">Mission {i + 1:02d} · {titre}</div><div class="sous">{desc}</div></div>""",
                    unsafe_allow_html=True)
        if st.checkbox("Mission accomplie ✅", key=f"mission_{i}"):
            total += pts
    st.markdown(f'<div class="compte">🎯 Points gagnés par ton équipe : <b>{total}</b><br>'
                '<small>Montre tes photos à l\'organisatrice pour les faire valider !</small></div>',
                unsafe_allow_html=True)


# =============================================================================
# LE WEEK-END (programme + valise)
# =============================================================================
# ✏️ PROGRAMME DE SECOURS : affiché seulement si programme.xlsx est introuvable ou illisible
# (heure, titre, description, illustration à droite)
PROGRAMME_SECOURS = {
    "VEN 11": [("18h00", "Arrivée & installation", "Posez vos affaires, prenez un verre !", "🥂"),
               ("19h30", "Apéro d'accueil", "L'aventure commence ici !", "🍹"),
               ("21h00", "Dîner convivial", "On se régale !", "🍽️"),
               ("22h30", "Première mission", "La licorne compte sur vous…", "✨")],
    "SAM 12": [("09h00", "Petit-déjeuner", "En terrasse, au soleil", "☕"),
               ("10h30", "Sport : choisis ton parcours", "Chill, trail ou vélo", "🚴"),
               ("13h00", "Pique-nique", "Au bord de l'eau", "🧺"),
               ("16h00", "Molkky & piscine", "Tournoi par équipes", "🏆"),
               ("20h00", "Grande soirée des 40 ans", "Tenue de fête conseillée !", "🎂")],
    "DIM 13": [("10h00", "Brunch", "Sans se presser", "🥐"),
               ("12h00", "Balade ou baignade", "Au choix", "🏊"),
               ("17h00", "Remise des prix", "Le classement final", "🥇")],
    "LUN 14": [("10h00", "Dernier café", "Et les au revoir", "☕"),
               ("11h00", "Départ", "Merci d'être venus ♡", "👋")],
}


JOURS_ABREGES = ["LUN", "MAR", "MER", "JEU", "VEN", "SAM", "DIM"]
NOMS_JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
# Mots reconnus dans les en-têtes de colonnes de l'onglet « planning » (sans accents ni majuscules)
MOTS_PLANNING = {"jour": ("jour", "date"),
                 "heure": ("heure", "horaire", "debut"),
                 "titre": ("titre", "activite", "evenement", "intitule", "nom", "programme"),
                 "desc": ("description", "detail", "sous titre", "commentaire", "info"),
                 "visuel": ("illustration", "image", "icone", "picto", "emoji", "visuel")}


def trouver_fichier_programme():
    """Cherche programme.xlsx (ou .xlsm, majuscules ou non) dans le dossier de app.py."""
    for f in sorted(Path(__file__).parent.iterdir()):
        if f.name.lower().startswith("programme") and f.suffix.lower() in (".xlsx", ".xlsm"):
            return f
    return None


def etiquette_jour(texte):
    """'Vendredi 11 juin', '2027-06-11' ou 'VEN 11' → 'VEN 11' (étiquette du bouton)."""
    t = texte.strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        d = date(int(m[1]), int(m[2]), int(m[3]))
        return f"{JOURS_ABREGES[d.weekday()]} {d.day}"
    n = _norm(t)
    i = next((i for i, nom in enumerate(NOMS_JOURS) if nom in n or re.search(rf"\b{nom[:3]}\b", n)), None)
    numero = re.search(r"\d+", t)
    if i is not None:
        return f"{JOURS_ABREGES[i]} {numero.group()}" if numero else JOURS_ABREGES[i]
    return t.upper()[:10]


def format_heure(valeur):
    """'18:00', '18h00', '18:00:00' ou une heure Excel (0,75) → '18h00'."""
    t = valeur.strip()
    m = re.search(r"(\d{1,2})[:h](\d{2})", t)
    if m:
        return f"{int(m.group(1)):02d}h{m.group(2)}"
    try:
        f = float(t.replace(",", "."))
        if 0 <= f < 1:
            total = round(f * 1440)
            return f"{total // 60:02d}h{total % 60:02d}"
    except ValueError:
        pass
    return t


def lire_programme():
    """Lit l'onglet « planning » de programme.xlsx avec Pandas. Renvoie (programme, problème) :
    programme = {'VEN 11': [(heure, titre, description, illustration), ...], ...} ; problème = texte si échec."""
    fichier = trouver_fichier_programme()
    if fichier is None:
        return None, "fichier programme.xlsx introuvable à côté de app.py"
    try:
        feuilles = pd.ExcelFile(fichier).sheet_names
        feuille = next((f for f in feuilles if _norm(f) == "planning"), feuilles[0])
        brut = pd.read_excel(fichier, sheet_name=feuille, header=None, dtype=str).fillna("")   # = pd.read_excel("programme.xlsx")
    except Exception as erreur:   # ex. openpyxl non installé, fichier corrompu…
        return None, f"lecture impossible ({erreur})"

    # Ligne d'en-tête : la première qui contient au moins les colonnes Jour, Heure et Titre/Activité
    colonnes, ligne_entete = {}, None
    for i in range(min(len(brut), 20)):
        noms = [_norm(c) for c in brut.iloc[i]]
        trouvees = {}
        for cle, mots in MOTS_PLANNING.items():
            trouvees[cle] = next((j for j, nom in enumerate(noms) if j not in trouvees.values() and any(nom.startswith(m) for m in mots)), None)
        if all(trouvees[c] is not None for c in ("jour", "heure", "titre")):
            colonnes, ligne_entete = trouvees, i
            break
    if ligne_entete is None:
        return None, "colonnes introuvables dans l'onglet « " + feuille + " » (attendu : Jour, Heure, Titre, Description, Illustration)"

    def cellule(i, cle):
        j = colonnes.get(cle)
        return str(brut.iat[i, j]).strip() if j is not None else ""

    programme, jour = {}, ""
    for i in range(ligne_entete + 1, len(brut)):
        jour = cellule(i, "jour") or jour           # jour laissé vide (cellules fusionnées) = même jour que la ligne du dessus
        titre = cellule(i, "titre")
        if not titre or not jour:
            continue
        programme.setdefault(etiquette_jour(jour), []).append(
            (format_heure(cellule(i, "heure")), titre, cellule(i, "desc"), cellule(i, "visuel") or "✨"))
    if not programme:
        return None, "aucune ligne de planning lisible"
    return programme, None


def page_weekend():
    entete("Le week-end", "Le programme des festivités")
    programme, probleme = lire_programme()
    if probleme and AFFICHER_DIAGNOSTIC:
        st.info(f"ℹ️ Programme d'exemple affiché : {probleme}. (Pour masquer ce message : AFFICHER_DIAGNOSTIC = False)")
    programme = programme or PROGRAMME_SECOURS
    jours = list(programme) + ["VALISE"]
    if st.session_state.get("sel_jours") not in jours:
        st.session_state["sel_jours"] = jours[0]
    choix = barre_boutons("jours", jours)
    st.write("")
    if choix in programme:
        for heure, titre, sous, visuel in programme[choix]:
            st.markdown(f"""<div class="prog"><div class="horaire">{escape(heure)}</div>
              <div class="corps"><div class="titre">{escape(titre)}</div><div class="desc">{escape(sous)}</div></div>
              {visuel_html(visuel)}</div>""", unsafe_allow_html=True)
    else:
        # ✏️ Liste "Dans ma valise"
        valise = ["👟 Baskets de trail", "🚴 Vélo (ou location sur place)", "🩱 Maillot de bain", "💧 Gourde",
                  "🦟 Anti-moustique", "🧴 Crème solaire", "🧢 Casquette", "🧥 Petite polaire pour le soir",
                  "🦄 Ta bonne humeur (obligatoire)"]
        cochees = [st.checkbox(o, key=f"valise_{i}") for i, o in enumerate(valise)]
        st.progress(sum(cochees) / len(valise), text=f"{sum(cochees)}/{len(valise)} objets prêts")


# =============================================================================
# LES COPAINS
# =============================================================================
# ✏️ ICÔNES D'ÉQUIPE : colonne "Icone" de l'Excel → image affichée à gauche du prénom.
# Colle un lien ("https://…") ou le chemin d'un fichier ("images/renard.png") entre les guillemets.
# Tant que c'est vide, un émoji de secours s'affiche. Les clés doivent être écrites comme dans l'Excel, en minuscules.
ICONES = {
    "chevre": "",
    "renard": "",
    "chouette": "",
    "loutre": "",
}
EMOJIS_SECOURS = {"chevre": "🐐", "renard": "🦊", "chouette": "🦉", "loutre": "🦦"}
AFFICHER_ABSENTS = False   # ✏️ True = afficher aussi les invités marqués "Absent" dans l'Excel


def trouver_fichier_excel():
    """Cherche copains.xlsx (ou .xlsm, majuscules ou non) dans le dossier de app.py."""
    for f in sorted(Path(__file__).parent.iterdir()):
        if f.name.lower().startswith("copains") and f.suffix.lower() in (".xlsx", ".xlsm"):
            return f
    return None


def liste_tags(texte):
    """'#A, #B' → ['#A', '#B']. Ignore les tags vides et ajoute le # s'il manque."""
    tags = []
    for t in texte.split(","):
        t = t.strip().lstrip("#").strip()
        if t:
            tags.append("#" + t)
    return tags


def _norm(texte):
    """Texte simplifié pour comparer les noms de colonnes : sans accents, sans emoji, sans ponctuation, en minuscules."""
    t = unicodedata.normalize("NFKD", str(texte)).encode("ascii", "ignore").decode().lower()
    return " ".join("".join(c if c.isalnum() else " " for c in t).split())


def champ(ligne, debut):
    """Valeur de la colonne dont le nom commence par 'debut' (ex. 'esprit de comp' trouve « Esprit de compèt' »)."""
    for nom in ligne.index:
        if nom.startswith(debut):
            return str(ligne[nom]).strip()
    return ""


def note(valeur):
    """'4' → 4.0 ; case vide ou texte → None. La note est limitée entre 0 et 5."""
    try:
        return max(0.0, min(5.0, float(str(valeur).replace(",", ".").strip())))
    except ValueError:
        return None


def charger_copains(fichier):
    """Lit l'Excel avec Pandas (pd.read_excel) et renvoie une liste de dictionnaires, un par invité.
    La ligne d'en-tête est repérée automatiquement (celle qui contient « Prénom »), même s'il y a des lignes de titre au-dessus."""
    brut = pd.read_excel(fichier, header=None, dtype=str).fillna("")
    entete = next((i for i in range(len(brut)) if "prenom" in [_norm(c) for c in brut.iloc[i]]), None)
    if entete is None:
        raise ValueError("colonne « Prénom » introuvable dans l'Excel")
    df = brut.iloc[entete + 1:].reset_index(drop=True)
    df.columns = [_norm(c) for c in brut.iloc[entete]]
    invites = []
    for _, ligne in df.iterrows():
        prenom = champ(ligne, "prenom")
        if not prenom:
            continue
        equipe = champ(ligne, "equipe")
        invites.append({
            "prenom": prenom,
            "lien": champ(ligne, "lien"),
            "equipe": equipe[:1].upper() + equipe[1:],          # "les hulottes" → "Les hulottes"
            "icone": _norm(champ(ligne, "icone")),
            "slogan": champ(ligne, "slogan"),
            "tags": liste_tags(champ(ligne, "tags")),           # le .split(',') est dans liste_tags
            "absent": champ(ligne, "absent").lower().startswith("absent"),
            "anecdote": champ(ligne, "anecdote"),
            "signe": champ(ligne, "signe particulier"),
            "notes": {"compet": note(champ(ligne, "esprit de comp")), "strat": note(champ(ligne, "esprit strat")),
                      "sport": note(champ(ligne, "niveau sportif")), "demon": note(champ(ligne, "potentiel demon")),
                      "adresse": note(champ(ligne, "adresse"))},
        })
    return invites


def icone_html(icone):
    """Image de l'icône (lien ou fichier du dictionnaire ICONES), sinon émoji de secours."""
    v = ICONES.get(icone, "")
    if v.startswith("http"):
        return f'<img src="{escape(v)}">'
    if v:
        fichier = Path(__file__).parent / v
        if fichier.exists():
            donnees = base64.b64encode(fichier.read_bytes()).decode()
            return f'<img src="data:{mimetypes.guess_type(fichier.name)[0]};base64,{donnees}">'
    return EMOJIS_SECOURS.get(icone, "🦄")


# ✏️ ANECDOTE SECRÈTE (bouton en bas de chaque fiche)
TEXTE_BOUTON = "🕵️‍♂️ Voir son secret"
INTRO_SECRET = "🤫 Le secret de {prenom} :"      # {prenom} est remplacé automatiquement


def basculer_secret(cle):
    """Affiche ou cache l'anecdote à chaque clic sur le bouton."""
    st.session_state[cle] = not st.session_state.get(cle, False)


# ✏️ JAUGES : (clé de l'Excel, nom complet affiché au survol). Pour la colonne Adresse : décommente la ligne "adresse".
STATS = [("compet", "Esprit de compét"), ("strat", "Stratège"), ("sport", "Physique / Sport"), ("demon", "Démon de minuit"),
         # ("adresse", "Adresse"),
         ]

# Icônes "coup de crayon" : une forme coloriée (légèrement décalée, comme un coloriage) + un contour à main levée.
# Coupe = esprit de compét, pion d'échecs = stratège, montagnes = sport, lune = démon de minuit, cible = adresse.
FORMES_ICONES = {
    "compet": ("M7 4.2h10v5a5 5 0 0 1-10 0z",
               "M7 6.2H4.6c-.3 2.2.9 3.8 2.6 4.2M17 6.2h2.4c.3 2.2-.9 3.8-2.6 4.2M12 14.3v3.7M8.2 20.3c1.2-.9 6.4-.9 7.6 0"),
    "strat": ("M12 3.6a3 3 0 1 0 .1 0zM10.4 11.6c.1 3-1.6 4.2-2.7 6.6h8.6c-1.1-2.4-2.8-3.6-2.7-6.6z", "M9.1 11.7h5.8M6.9 20.2h10.2"),
    "sport": ("M2.6 19.4 9.2 7l4.1 7.2 2.4-3.6 5.7 8.8z", "M7.3 10.6l1.8 1.9 1.5-1.7"),
    "demon": ("M15.8 3.2C8 3.6 3.6 10.6 6.6 16.6c2.4 4.2 8.2 5.2 12.2 3.2C12.2 18.8 9.6 12 12.2 7.6c.9-1.8 2.2-3.3 3.6-4.4z",
              "M19.3 4.4v3.6M17.5 6.2h3.6"),
    "adresse": ("M12 3.4a8.6 8.6 0 1 0 .1 0z", "M12 7.6a4.4 4.4 0 1 0 .1 0zM12 11.4a.6.6 0 1 0 .1 0z"),
}


# ✏️ TES PICTOS (dossier Images/Picto). Chaque picto est retrouvé grâce à un mot présent dans son nom de fichier
# (sans accents ni majuscules). Si la détection se trompe, écris le nom exact du fichier dans PICTOS.
MOTS_PICTOS = {"compet": ("compet", "coupe", "trophee", "medaille", "victoire"),
               "strat": ("strat", "echec", "pion", "plan", "cerveau"),
               "sport": ("sport", "physique", "course", "basket", "montagne", "velo"),
               "demon": ("demon", "minuit", "lune", "diable", "nuit"),
               "adresse": ("adresse", "cible", "fleche")}
PICTOS = {"compet": "", "strat": "", "sport": "", "demon": "", "adresse": ""}   # ex. "strat": "mon picto 2.png"
AFFICHER_DIAGNOSTIC = True   # ✏️ True = un petit message t'aide si un picto n'est pas trouvé (mets False avant de partager l'appli)


def trouver_pictos():
    """Renvoie {clé de stat: fichier PNG} pour les pictos trouvés dans Images/Picto."""
    dossier = trouver_dossier_pictos()
    if dossier is None:
        return {}
    fichiers = sorted(f for f in dossier.iterdir() if f.suffix.lower() in (".png", ".webp", ".jpg", ".jpeg"))
    trouves = {}
    for cle, mots in MOTS_PICTOS.items():
        voulu = PICTOS.get(cle, "")
        if voulu:
            fichier = next((f for f in fichiers if f.name.lower() == voulu.lower()), None)
        else:
            fichier = next((f for f in fichiers if any(m in _norm(f.stem) for m in mots)), None)
        if fichier is not None:
            trouves[cle] = fichier
    return trouves


def diagnostic_pictos():
    """Petit message, visible seulement s'il y a un souci, pour t'aider à nommer tes pictos."""
    if not AFFICHER_DIAGNOSTIC:
        return
    dossier = trouver_dossier_pictos()
    if dossier is None:
        st.info("ℹ️ Dossier Images/Picto introuvable à côté de app.py : les icônes de secours sont utilisées. "
                "(Pour masquer ce message : AFFICHER_DIAGNOSTIC = False)")
        return
    trouves = trouver_pictos()
    manquants = [cle for cle, _ in STATS if cle not in trouves]
    if manquants:
        st.info(f"ℹ️ Picto non reconnu pour : {', '.join(manquants)}. Fichiers présents : "
                f"{', '.join(sorted(f.name for f in dossier.iterdir()))}. Indique les bons noms dans le dictionnaire PICTOS.")


def icone_crayon(nom, rgb):
    """Icône SVG (data URI) coloriée avec la couleur pastel de l'équipe."""
    forme, traits = FORMES_ICONES[nom]
    r, g, b = rgb
    contour = "stroke='#5b4a3f' stroke-width='1.4' stroke-linecap='round' stroke-linejoin='round' fill='none'"
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>"
           f"<path d='{forme}' fill='rgb({r},{g},{b})' fill-opacity='.9' transform='translate(.9 .7)'/>"
           f"<path d='{forme}' {contour}/><path d='{traits}' {contour}/>"
           f"<path d='{forme}' stroke='#5b4a3f' stroke-opacity='.28' stroke-width='.8' fill='none' transform='translate(.5 .4)'/></svg>")
    return "data:image/svg+xml," + quote(svg)


def jauges_html(notes):
    """4 minuscules jauges HTML (4 px de haut), en grille 2 x 2. La couleur vient de l'équipe (variable CSS --c)."""
    if all(notes.get(cle) is None for cle, _ in STATS):
        return ""
    cellules = ""
    for cle, nom in STATS:
        n = notes.get(cle)
        texte = f"{n:g}/5" if n is not None else "–"
        largeur = 0 if n is None else n / 5 * 100
        cellules += (f'<div class="jg" title="{nom} : {texte}"><span class="ico ico-{cle}"></span>'
                     f'<span class="jg-b"><i style="width:{largeur:.0f}%"></i></span><span class="jg-n">{texte}</span></div>')
    return f'<div class="jauges">{cellules}</div>'


# ✏️ COULEURS DES SECTIONS (RVB). Le mot-clé est cherché dans le NOM de l'équipe et dans son Icone (sans accents).
COULEURS_EQUIPES = {"biquette": (176, 198, 146), "chevre": (176, 198, 146),   # Les biquettes → vert sauge
                    "goupil": (246, 170, 145), "renard": (246, 170, 145),     # Les goupils   → corail
                    "hulotte": (205, 185, 232), "chouette": (205, 185, 232),  # Les hulottes  → lilas
                    "loutre": (160, 196, 212)}                                # Les loutres   → bleu-gris
# Si aucun mot-clé ne correspond (équipe renommée…), chaque équipe reçoit tour à tour une de ces couleurs :
PALETTE_SECOURS = [(176, 198, 146), (246, 170, 145), (205, 185, 232), (160, 196, 212), (238, 206, 140)]
COULEUR_DEFAUT = (242, 198, 208)                   # rose poudré : uniquement pour « Hors équipe »


def couleur_equipe(equipe, icone, rang):
    """Couleur (RVB) d'une section d'équipe."""
    texte = f"{_norm(equipe)} {icone}"
    for mot, rgb in COULEURS_EQUIPES.items():
        if mot in texte:
            return rgb
    return PALETTE_SECOURS[rang % len(PALETTE_SECOURS)]


def badge_html(icone, rang):
    """Badge de l'invité : 1) lien/fichier choisi dans ICONES, 2) PNG du dossier Images/Badges, 3) émoji de secours."""
    if ICONES.get(icone):
        h = icone_html(icone)
        if h.startswith("<img"):
            return f'<div class="badge-img">{h}</div>'
    fichier = badge_image(icone, rang)
    if fichier is not None:
        return f'<div class="badge-img"><img src="{image_en_base64(str(fichier), fichier.stat().st_mtime)}"></div>'
    return f'<div class="badge">{icone_html(icone)}</div>'


def carte_copain(inv, n, rang):
    """Une carte blanche : badge, prénom, lien, tags terracotta, signe particulier, mini-jauges, lien « Voir son secret »."""
    lien = f'<div class="lien">{escape(inv["lien"])}</div>' if inv["lien"] else ""
    absent = '<div style="margin-top:.3rem"><span class="equipe" style="background:#eee;color:#777">Absent(e)</span></div>' if inv["absent"] else ""
    tags = ('<div class="tags">' + "".join(f'<span class="tag">{escape(t)}</span>' for t in inv["tags"]) + '</div>') if inv["tags"] else ""
    signe = f'<div class="signe">💡 Signe particulier : {escape(inv["signe"])}</div>' if inv["signe"] else ""
    with st.container(key=f"fiche_{n}"):
        st.markdown(f"""<div class="fi">{badge_html(inv['icone'], rang)}<div class="prenom">{escape(inv['prenom'])}</div>{lien}{absent}{tags}{signe}{jauges_html(inv['notes'])}</div>""",
                    unsafe_allow_html=True)
        # Lien discret : uniquement pour les invités qui ont une anecdote dans l'Excel
        if inv["anecdote"] and not inv["absent"]:
            cle = f"secret_{inv['prenom']}"
            st.button(TEXTE_BOUTON, key=f"anec_{n}", on_click=basculer_secret, args=(cle,))
            if st.session_state.get(cle):
                intro = INTRO_SECRET.replace("{prenom}", inv["prenom"])
                st.markdown(f'<div class="secret">{escape(intro)} « {escape(inv["anecdote"])} »</div>', unsafe_allow_html=True)


def page_copains():
    entete("Les copains", "La dream team")
    fichier = trouver_fichier_excel()
    if fichier is None:
        st.error("📄 Fichier Excel introuvable : place « copains.xlsx » dans le même dossier que app.py.")
        return
    try:
        invites = charger_copains(fichier)
    except Exception as erreur:   # ex. openpyxl non installé, fichier corrompu…
        st.error(f"Impossible de lire l'Excel : {erreur}")
        st.caption("Si le message parle d'openpyxl : py -V:3.13 -m pip install openpyxl")
        return
    if not AFFICHER_ABSENTS:
        invites = [i for i in invites if not i["absent"]]

    diagnostic_pictos()

    # Regroupement par équipe (ordre d'apparition dans l'Excel ; les invités sans équipe à la fin)
    groupes = {}
    for inv in invites:
        groupes.setdefault(inv["equipe"], []).append(inv)
    ordre = [e for e in groupes if e] + ([""] if "" in groupes else [])

    # CSS dynamique : une couleur par section + de très légères inclinaisons "posées à la main" sur les cartes
    pictos = {cle: image_en_base64(str(f), f.stat().st_mtime, 64) for cle, f in trouver_pictos().items()}   # tes dessins, réduits
    css = ""
    for k, equipe in enumerate(ordre):
        icone = next((m["icone"] for m in groupes[equipe] if m["icone"]), "")
        r, g, b = couleur_equipe(equipe, icone, k) if equipe else COULEUR_DEFAUT
        css += f".st-key-equipe_{k} {{ --c:{r},{g},{b}; }} "
        for nom in FORMES_ICONES:   # ton picto s'il existe, sinon l'icône dessinée de secours (coloriée aux couleurs de l'équipe)
            css += f'.st-key-equipe_{k} .ico-{nom} {{ background-image:url("{pictos.get(nom) or icone_crayon(nom, (r, g, b))}"); }} '
    for n in range(len(invites)):
        css += f".st-key-fiche_{n} {{ transform:rotate({[-0.5, 0.4, -0.3, 0.5][n % 4]}deg); }} "
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    n = 0
    for k, equipe in enumerate(ordre):
        membres = groupes[equipe]
        slogan = next((m["slogan"] for m in membres if m["slogan"]), "")
        slogan_html = f'<div class="equipe-slogan">{escape(slogan)}</div>' if slogan else ""
        with st.container(key=f"equipe_{k}"):
            st.markdown(f'<div class="equipe-titre">{escape(equipe or "Hors équipe")}</div>{slogan_html}', unsafe_allow_html=True)
            for debut in range(0, len(membres), 2):                       # grille de 2 cartes par ligne
                for col, (rang, inv) in zip(st.columns(2, gap="small"), enumerate(membres[debut:debut + 2], start=debut)):
                    with col:
                        carte_copain(inv, n, rang)
                        n += 1
    st.button(f"💌 Écrire une anecdote sur {PRENOM}", key="vers_livredor", on_click=aller, args=("livredor",))


# =============================================================================
# AUTOUR DE NOUS (infos + parcours sport 🔒)
# =============================================================================
def page_autour():
    entete("Autour de nous", "À découvrir en Ardèche")
    st.markdown(f"""<div class="carte"><div class="titre">📍 {NOM_LIEU}</div>
      <div class="sous">✏️ Adresse, digicode, horaires d'arrivée… à compléter ici.</div></div>""",
                unsafe_allow_html=True)
    st.markdown("<div class='titre-section'>Parcours sport 🔒</div>", unsafe_allow_html=True)
    if not deverrouille("parcours", CODE_PARCOURS, "Les tracés secrets", "Les parcours se méritent. Demande le code !"):
        return
    # ✏️ Descriptions et liens Strava / Komoot / GPX ("" = pas encore prêt)
    parcours = {
        "CHILL": ("🌿 Dolce Via", "Ancienne voie ferrée aménagée, plate et ombragée. Idéale pour discuter et finir par une glace.",
                  "≈ 15 km · quasi plat · 2 h tranquille", ""),
        "TRAIL": ("🏃 Trail du Val d'Or", "Sentiers, racines et vues sur la vallée depuis le gîte.",
                  "≈ 12 km · 500 m D+ · 2 h 30", ""),
        "VÉLO": ("🚴 L'Ardéchoise", "Un morceau du mythique parcours cyclo : cols, lacets, paysages sublimes.",
                 "≈ 60 km · 1 100 m D+ · 3 h 30", ""),
    }
    nom, desc, infos, lien = parcours[barre_boutons("parcours", list(parcours))]
    st.markdown(f'<div class="carte" style="margin-top:.8rem"><div class="titre">{nom}</div>'
                f'<div class="sous">{desc}<br><b>{infos}</b></div></div>', unsafe_allow_html=True)
    if lien:
        st.link_button("📍 Ouvrir le tracé (GPX)", lien)
    else:
        st.info("🛠️ Lien GPX à venir (Strava / Komoot).")


# =============================================================================
# CLASSEMENT 🔒
# =============================================================================
def equipes_depuis_excel():
    """Équipes du classement = équipes de l'Excel (colonne Equipe), avec l'émoji de leur icône."""
    equipes = []
    fichier = trouver_fichier_excel()
    if fichier:
        try:
            for inv in charger_copains(fichier):
                if inv["equipe"]:
                    nom = f"{EMOJIS_SECOURS.get(inv['icone'], '🦄')} {inv['equipe']}"
                    if nom not in equipes:
                        equipes.append(nom)
        except Exception:
            pass
    # ✏️ Équipes de secours si l'Excel est introuvable
    return equipes or ["🐐 Les biquettes", "🦊 Les goupils", "🦉 Les hulottes", "🦦 Les loutres"]


def page_classement():
    entete("Classement", "Les équipes se battent pour la gloire !")
    if not deverrouille("defis", CODE_DEFIS, "Le classement secret", "Seuls les champions connaissent le code…"):
        return
    if "scores" not in st.session_state:   # les équipes viennent de l'Excel ; tout le monde démarre à 0 point
        equipes = equipes_depuis_excel()
        st.session_state["scores"] = pd.DataFrame({"Équipe": equipes, "Points": [0] * len(equipes)})
    classement = st.session_state["scores"].sort_values("Points", ascending=False).reset_index(drop=True)
    fonds = ["#F8E3B0", "#F8CDBE", "#C9E0E6", "#E3D8EE"]
    for rang, ligne in classement.iterrows():
        st.markdown(f"""<div class="carte" style="background:{fonds[rang % len(fonds)]}"><span class="pts">{ligne['Points']} pts</span>
          <div class="titre">{rang + 1} · {ligne['Équipe']}</div></div>""", unsafe_allow_html=True)
    with st.expander("✏️ Modifier les scores (organisatrice)"):
        modifie = st.data_editor(st.session_state["scores"], hide_index=True, width="stretch",
                                 disabled=["Équipe"], key="editeur_scores",
                                 column_config={"Points": st.column_config.NumberColumn(min_value=0, step=10)})
        if not modifie.equals(st.session_state["scores"]):
            st.session_state["scores"] = modifie
            st.rerun()
    st.caption("⚠️ Les scores repartent à zéro si la page est rechargée : garde-les aussi de côté.")


# =============================================================================
# GALERIE
# =============================================================================
def page_galerie():
    entete("Galerie", "Les souvenirs du week-end")
    st.write("Déposez vos plus belles photos (et les preuves des défis !) dans l'album partagé.")
    if ALBUM_PHOTOS:
        st.link_button("📷 Ouvrir l'album partagé", ALBUM_PHOTOS)
    else:
        st.info("🛠️ Le lien de l'album arrive bientôt.")


# =============================================================================
# LIVRE D'OR : les invités écrivent des anecdotes sur toi
# =============================================================================
CODE_LECTURE = "SOUVENIRS"   # ✏️ code pour LIRE les anecdotes (garde-le pour toi, ou donne-le à la fin du week-end)
LECTURE_LIBRE = False        # ✏️ True = tout le monde peut lire les anecdotes sans code
LONGUEUR_MAX = 600           # ✏️ nombre de caractères maximum par anecdote
FICHIER_ANECDOTES = Path(__file__).parent / "anecdotes_livre_dor.json"   # fichier créé automatiquement sur le serveur


@st.cache_resource
def verrou_fichier():
    """Évite que deux invités qui envoient en même temps ne s'écrasent mutuellement."""
    return threading.Lock()


def lire_anecdotes():
    try:
        return json.loads(FICHIER_ANECDOTES.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return []


def ajouter_anecdote(auteur, texte):
    """Ajoute une anecdote dans le fichier JSON (écriture sécurisée via un fichier temporaire)."""
    with verrou_fichier():
        liste = lire_anecdotes()
        liste.append({"date": datetime.now().strftime("%d/%m/%Y %H:%M"), "auteur": auteur, "texte": texte})
        temporaire = FICHIER_ANECDOTES.with_suffix(".tmp")
        temporaire.write_text(json.dumps(liste, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporaire, FICHIER_ANECDOTES)


def envoyer_anecdote():
    """Appelée au clic sur « Envoyer » : vérifie, enregistre, puis vide le formulaire (sauf en cas d'erreur)."""
    auteur = st.session_state.get("la_auteur", "").strip()
    anonyme = st.session_state.get("la_anonyme", False)
    texte = st.session_state.get("la_texte", "").strip()
    if len(texte) < 5:
        st.session_state["la_msg"] = ("warn", "Ton anecdote est un peu courte… raconte-nous en plus ! ✍️")
    elif not auteur and not anonyme:
        st.session_state["la_msg"] = ("warn", "Indique ton prénom, ou coche « anonyme ».")
    else:
        try:
            ajouter_anecdote("" if anonyme else auteur, texte)
        except OSError:
            st.session_state["la_msg"] = ("error", "Impossible d'enregistrer pour le moment, réessaie un peu plus tard.")
            return
        st.session_state["la_msg"] = ("ok", f"Merci ! Ton anecdote est bien arrivée jusqu'à {PRENOM} 💌")
        st.session_state["la_auteur"], st.session_state["la_texte"], st.session_state["la_anonyme"] = "", "", False


def page_livredor():
    entete("Livre d'or", f"Une anecdote sur {PRENOM} ?")
    st.markdown(f'<div class="mot-intro">Un souvenir, une blague, un moment gênant… Écris-le ici : '
                f'{escape(PRENOM)} le découvrira plus tard 🤫</div>', unsafe_allow_html=True)
    with st.form("form_anecdote", border=False):
        st.text_input("Ton prénom", max_chars=40, key="la_auteur")
        st.checkbox("Je préfère rester anonyme", key="la_anonyme")
        st.text_area(f"Ton anecdote sur {PRENOM}", max_chars=LONGUEUR_MAX, height=160, key="la_texte",
                     placeholder="Notre première rencontre, un fou rire, un moment gênant…")
        st.form_submit_button("💌 Envoyer", on_click=envoyer_anecdote)
    message = st.session_state.pop("la_msg", None)
    if message:
        {"ok": st.success, "warn": st.warning, "error": st.error}[message[0]](message[1])
        if message[0] == "ok":
            st.balloons()

    anecdotes = lire_anecdotes()
    st.caption(f"{len(anecdotes)} anecdote{'s' if len(anecdotes) > 1 else ''} déjà reçue{'s' if len(anecdotes) > 1 else ''}")

    # Lecture : verrouillée par un code (surprise !) sauf si LECTURE_LIBRE = True
    if not LECTURE_LIBRE and not deverrouille("anecdotes", CODE_LECTURE, "Les anecdotes reçues",
                                              f"Réservé à {PRENOM}… la lecture se fera au moment venu."):
        return
    if not anecdotes:
        st.info("Aucune anecdote pour l'instant.")
        return
    for n, a in enumerate(reversed(anecdotes)):                        # les plus récentes en premier
        auteur = escape(a["auteur"]) if a["auteur"] else "Un(e) ami(e) mystère 🤫"
        texte = escape(a["texte"]).replace("\r", "").replace("\n", "<br>")
        st.markdown(f"""<div class="mot" style="transform:rotate({[-0.5, 0.4, -0.3, 0.5][n % 4]}deg)"><div class="mot-texte">« {texte} »</div><div class="mot-auteur">— {auteur}<span>{escape(a["date"])}</span></div></div>""",
                    unsafe_allow_html=True)
    # Sauvegarde : à télécharger de temps en temps (le fichier du serveur peut être effacé quand l'appli redémarre)
    st.download_button("⬇️ Télécharger toutes les anecdotes (CSV)", data=pd.DataFrame(anecdotes).to_csv(index=False).encode("utf-8-sig"),
                       file_name="anecdotes.csv", mime="text/csv")


# =============================================================================
# PLUS (les sections qui ne sont pas dans le bandeau du bas)
# =============================================================================
def page_plus():
    entete("Plus", "Toutes les autres sections")
    tuiles = [("autour", "forest", "AUTOUR DE NOUS"), ("classement", "emoji_events", "CLASSEMENT"),
              ("galerie", "photo_camera", "GALERIE"), ("livredor", "menu_book", "LIVRE D'OR")]
    with st.container(key="grille"):
        for i in range(0, len(tuiles), 2):
            for col, (cle, ico, txt) in zip(st.columns(2), tuiles[i:i + 2]):
                lock = " 🔒" if cle == "classement" and not st.session_state.get("ok_defis") else ""
                col.button(f":material/{ico}: {txt}{lock}", key=f"nav_{cle}", width="stretch",
                           on_click=aller, args=(cle,))


# =============================================================================
# BANDEAU DU BAS (visible sur toutes les pages)
# =============================================================================
def bandeau_bas():
    """Barre de navigation fixée en bas de l'écran. L'onglet actif est en rose."""
    onglets = [("accueil", "home", "Accueil"), ("jouer", "sports_esports", "Jouer"),
               ("weekend", "calendar_month", "Week-end"), ("copains", "groups", "Copains"),
               ("plus", "more_horiz", "Plus")]            # ✏️ icônes : noms Material (fonts.google.com/icons)
    page = st.session_state["page"]
    actif = page if page in ("accueil", "jouer", "weekend", "copains") else "plus"
    st.markdown(f"<style>.st-key-bandeau .st-key-bas_{actif} button p, "
                f".st-key-bandeau .st-key-bas_{actif} [data-testid='stIconMaterial'] "
                f"{{ color:#D95D79 !important; }}</style>", unsafe_allow_html=True)
    with st.container(key="bandeau"):
        for col, (cle, ico, txt) in zip(st.columns(len(onglets)), onglets):
            col.button(f":material/{ico}: {txt}", key=f"bas_{cle}", width="stretch",
                       on_click=aller, args=(cle,))


PAGES = {"accueil": page_accueil, "jouer": page_jouer, "weekend": page_weekend, "copains": page_copains,
         "plus": page_plus, "livredor": page_livredor, "autour": page_autour, "classement": page_classement, "galerie": page_galerie}
PAGES[st.session_state["page"]]()
bandeau_bas()
