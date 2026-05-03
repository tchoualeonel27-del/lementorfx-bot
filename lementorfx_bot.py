import logging, json, os, re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)

import os
TOKEN    = os.environ.get("BOT_TOKEN", "7575039426:AAEoTVawvW6uLOZf3b9C5xMcxjfy8GXbBmk")
ADMIN_ID = 7412212489

EXNESS_LINK       = "https://one.exnessonelink.com/a/do7n4lz3on"
CANAL_VIP_SIGNAUX = "https://t.me/+HJ9qJhRZ7mg0MmFk"
CANAL_VIP_ROBOTS  = "https://t.me/+N-Atm_7qeHMxZTM8"
CANAL_PUB_SIGNAUX = "https://t.me/lementorforexgroup"
CANAL_PUB_ROBOTS  = "https://t.me/robotradingratuit"
DB_FILE           = "membres.json"

LIENS_VIP = (
    "1 — LeMentor Signal\n"
    "Education de base en trading FR/EN + copier les signaux\n"
    "https://t.me/+HJ9qJhRZ7mg0MmFk\n\n"
    "2 — Forex Master Mind\n"
    "Signaux scalper\n"
    "https://t.me/+O-qp8FFqU3M2YzU0\n\n"
    "3 — Forex Manipulation\n"
    "Signaux swing trading\n"
    "https://t.me/+nmaRfODrkkJhNTJk\n\n"
    "4 — Supply and Demand Intraday\n"
    "Signaux Gold et BTC + gros R/R intraday\n"
    "https://t.me/+PNPC0O0teFhiMGY0\n\n"
    "5 — Sadeeq FX\n"
    "Signaux Forex intraday\n"
    "https://t.me/+RM5QY9P10mM1ODRk\n\n"
    "6 — ShadTrading Premium\n"
    "Signaux intraday Gold et BTC\n"
    "https://t.me/+Tn3gEe_HOediN2M0"
)

# ── ÉTATS ──────────────────────────────────────────────
(S_LANG, S_MENU,
 S_NOM, S_PRENOM, S_PAYS, S_VILLE,
 S_TEL, S_EMAIL, S_NIVEAU, S_OBJECTIF,
 S_EXQ, S_EXID, S_CONFIRM,
 S_ATTENTE_PAIEMENT) = range(14)

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════
# BASE DE DONNÉES
# ══════════════════════════════════════════════════════

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {"valides": {}, "attente": {}, "attente_paiement": {},
            "rejetes": {}, "exness_ids": [], "emails": [], "bloques": []}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def eid_used(e):     return e in load_db().get("exness_ids", [])
def mail_used(e):    return e.lower() in [x.lower() for x in load_db().get("emails", [])]
def is_blocked(u):   return u in load_db().get("bloques", [])
def is_validated(u): return str(u) in load_db().get("valides", {})

def save_pending(uid, d):
    db = load_db()
    db["attente"][str(uid)] = {**d, "date": datetime.now().isoformat()}
    save_db(db)

def save_pending_payment(uid, d):
    db = load_db()
    db["attente_paiement"][str(uid)] = {**d, "date": datetime.now().isoformat()}
    save_db(db)

def approve_signal(uid):
    db = load_db(); k = str(uid)
    if k not in db["attente"]: return None
    d = db["attente"].pop(k); d["statut"] = "valide_signaux"
    db["valides"][k] = d
    if d.get("exness_id"): db["exness_ids"].append(d["exness_id"])
    if d.get("email"):     db["emails"].append(d["email"].lower())
    save_db(db); return d

def reject_member(uid):
    db = load_db(); k = str(uid)
    if k not in db["attente"]: return None
    d = db["attente"].pop(k); d["statut"] = "rejete"
    db["rejetes"][k] = d; save_db(db); return d

def approve_robot(uid):
    db = load_db(); k = str(uid)
    if k not in db["attente_paiement"]: return None
    d = db["attente_paiement"].pop(k); d["statut"] = "valide_robots"
    db["valides"][k + "_robot"] = d; save_db(db); return d

def reject_payment(uid):
    db = load_db(); k = str(uid)
    if k not in db["attente_paiement"]: return None
    d = db["attente_paiement"].pop(k); d["statut"] = "paiement_rejete"
    db["rejetes"][k + "_pay"] = d; save_db(db); return d

# ══════════════════════════════════════════════════════
# TEXTES
# ══════════════════════════════════════════════════════

def txt(lang, key, **kw):
    T = {
    "fr": {
    "accueil": (
        "Bienvenue chez LeMentorFx !\n\n"
        "Je suis ton assistant officiel, gere par @lementorfx\n"
        "Partenaire IB Exness - Signaux XAU/USD\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Ce que nous proposons :\n\n"
        "OPTION 1 — GRATUIT\n"
        "Formation de base en trading\n"
        "Comment lire et appliquer un signal\n"
        "Acces au salon de signaux VIP XAU/USD\n"
        "6 groupes VIP de signaux inclus\n\n"
        "OPTION 2 — 200 USD a vie\n"
        "Acces illimite au VIP Robots MT4/MT5\n"
        "Telechargement gratuit de tous les robots\n"
        "Mises a jour incluses a vie\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Choisis ton option ci-dessous"
    ),
    "menu_publics": (
        "Avant de t'inscrire, rejoins nos groupes publics gratuits\n"
        "pour voir ce qui se passe dans le VIP :\n\n"
        "Signaux & Education (public) :\n"
        f"{CANAL_PUB_SIGNAUX}\n\n"
        "Robots de trading (public) :\n"
        f"{CANAL_PUB_ROBOTS}\n\n"
        "Quand tu es pret, reviens choisir ton option !"
    ),
    "choix_signaux": (
        "ACCES VIP SIGNAUX & EDUCATION - 100% GRATUIT\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Ce que tu obtiens :\n\n"
        "Formation de base en trading (FR et EN)\n"
        "Comment lire et appliquer un signal correctement\n"
        "Acces Google Drive avec formation complete\n"
        "6 groupes VIP de signaux :\n"
        "  - Scalping, Swing, Intraday Gold, BTC, Forex\n\n"
        "Condition : etre filleul Exness de @lementorfx\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Appuie sur Commencer l'inscription pour continuer"
    ),
    "choix_robots": (
        "ACCES VIP ROBOTS MT4/MT5 - 200 USD a vie\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Ce que tu obtiens :\n\n"
        "Telechargement illimite de tous les robots\n"
        "Martingale, Hedging, One Shot, Grid, Scalping\n"
        "Mises a jour gratuites a vie\n"
        "Compatible MT4 et MT5\n"
        "Support technique inclus\n\n"
        "Methodes de paiement :\n"
        "Binance Pay - Binance USDT TRC20 - PayPal\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Appuie sur Voir les details de paiement pour continuer"
    ),

    # ── INSCRIPTION ──
    "nom":     "ETAPE 1/9 — Nom\n\nQuel est ton nom de famille ?",
    "prenom":  "ETAPE 2/9 — Prenom\n\nQuel est ton prenom ?",
    "pays":    "ETAPE 3/9 — Pays\n\nDans quel pays es-tu ? (ex: Cameroun, France...)",
    "ville":   "ETAPE 4/9 — Ville\n\nDans quelle ville es-tu ? (ex: Yaounde, Paris...)",
    "tel":     "ETAPE 5/9 — Telephone\n\nTon numero WhatsApp / telephone ?\n(ex: +237 6XX XXX XXX)",
    "email":   "ETAPE 6/9 — Email\n\nTon adresse email ?\n\nCet email sera verifie pour confirmer ton parrainage Exness.",
    "niveau":  "ETAPE 7/9 — Niveau\n\nQuel est ton niveau actuel en trading ?",
    "objectif":"ETAPE 8/9 — Objectif\n\nQuel est ton objectif principal avec le trading ?\n(ex: revenus complementaires, liberte financiere, apprendre...)",
    "exq":     "ETAPE 9/9 — Compte Exness\n\nAs-tu un compte Exness ?",
    "noex": (
        "Pas encore de compte Exness ?\n\n"
        "C'est gratuit et ca prend 3 minutes !\n\n"
        f"Lien officiel de parrainage :\n{EXNESS_LINK}\n\n"
        "Une fois inscrit, reviens ici et tape /start"
    ),
    "exid": (
        "Ton ID Exness (7 a 9 chiffres)\n\n"
        "Comment trouver ton ID :\n"
        "1. Va sur exness.com et connecte-toi\n"
        "2. Clique sur ton Profil (haut a droite)\n"
        "3. L'ID s'affiche sur le tableau de bord\n\n"
        "Entre ton ID Exness :"
    ),
    "ebad":  "Email invalide. Entre une adresse correcte (ex: nom@gmail.com) :",
    "edup":  "Cet email est deja enregistre. Contacte @lementorfx si c'est une erreur.",
    "idbad": "ID invalide. L'ID Exness contient 7 a 9 chiffres. Reessaie :",
    "iddup": "Cet ID Exness est deja utilise. Contacte @lementorfx si c'est une erreur.",

    "recap": (
        "RECAPITULATIF DE TA FICHE\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Nom : {nom} {prenom}\n"
        "Pays / Ville : {pays}, {ville}\n"
        "Telephone : {tel}\n"
        "Email : {email}\n"
        "Niveau : {niveau}\n"
        "Objectif : {objectif}\n"
        "ID Exness : {exid}\n"
        "Telegram : @{user}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Tout est correct ?"
    ),

    "attente": (
        "Demande envoyee avec succes !\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Ta fiche a ete transmise a @lementorfx\n"
        "pour verification de ton parrainage Exness.\n\n"
        "Prochaines etapes :\n\n"
        "1. @lementorfx verifie ton ID Exness\n"
        "2. Si valide — tu recois les 6 liens VIP ici\n"
        "3. Si non — tu recois un message explicatif\n\n"
        "Delai : quelques heures maximum\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "En attendant, rejoins nos groupes publics :\n\n"
        f"Signaux & Education (public) :\n{CANAL_PUB_SIGNAUX}\n\n"
        f"Robots de trading (public) :\n{CANAL_PUB_ROBOTS}\n\n"
        "Questions ? @lementorfx"
    ),

    "valide": (
        "ACCES VIP ACCORDE !\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Ton parrainage Exness est verifie et valide !\n\n"
        "Bienvenue dans la communaute LeMentorFx !\n\n"
        "Voici tes 6 acces VIP :\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{LIENS_VIP}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Pour chaque groupe :\n"
        "Clique le lien et rejoins\n"
        "Active les notifications\n"
        "Lis les regles epinglees\n\n"
        "Bon trading ! @lementorfx"
    ),

    "rejete": (
        "Acces non accorde\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "L'ID Exness {exid} n'a pas ete trouve\n"
        "dans les filleuls de @lementorfx.\n\n"
        "Solutions :\n\n"
        f"Pas de compte Exness ? Cree-en un :\n{EXNESS_LINK}\n\n"
        "Compte existant mais pas via notre lien ?\n"
        "Contacte @lementorfx pour regulariser\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Tape /start pour recommencer."
    ),

    "paiement_info": (
        "PAIEMENT — VIP ROBOTS MT4/MT5\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Binance Pay\n"
        "ID : 556807688\n\n"
        "Binance USDT TRC20\n"
        "TEWKJtPsn4RsrEt2kiLNCDMUVKLGQ6RLJb\n\n"
        "PayPal\n"
        "capor51@gmail.com\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Montant exact : 200 USD\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Apres le paiement :\n"
        "Envoie ici une capture d'ecran de\n"
        "ta confirmation de paiement.\n\n"
        "@lementorfx verifie et t'envoie l'acces.\n\n"
        "Attention : seuls les vrais paiements sont acceptes."
    ),

    "capture_recue": (
        "Capture recue !\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Ta preuve de paiement a ete envoyee\n"
        "a @lementorfx pour verification.\n\n"
        "Si le paiement est confirme,\n"
        "tu recevras l'acces VIP Robots ici.\n\n"
        "Delai : quelques heures maximum\n\n"
        "Questions ? @lementorfx"
    ),

    "valide_robot": (
        "PAIEMENT CONFIRME !\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Ton acces VIP Robots est active a vie !\n\n"
        "Ton acces VIP Robots MT4/MT5 :\n\n"
        f"{CANAL_VIP_ROBOTS}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Dans ce canal :\n"
        "Telechargement illimite de tous les robots\n"
        "Martingale, Hedging, One Shot, Grid, Scalping\n"
        "Mises a jour gratuites a vie\n"
        "Support technique\n\n"
        "Rejoins et active les notifications !\n\n"
        "Merci pour ta confiance ! @lementorfx"
    ),

    "paiement_rejete": (
        "Paiement non confirme\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "La capture envoyee n'a pas pu etre\n"
        "verifiee par @lementorfx.\n\n"
        "Que faire ?\n"
        "Verifie le montant envoye (200 USD)\n"
        "Verifie les coordonnees de paiement\n"
        "Contacte @lementorfx directement\n\n"
        "Tape /robots pour reessayer."
    ),

    "cancel": "Inscription annulee. Tape /start pour recommencer.",
    "deja":   "Tu es deja inscrit et valide ! Questions ? @lementorfx",
    "trop_court": "Reponse trop courte. Reessaie :",
    },

    # ────────────────────────────────────────────────
    "en": {
    "accueil": (
        "Welcome to LeMentorFx!\n\n"
        "I'm your official assistant, managed by @lementorfx\n"
        "Exness IB Partner - XAU/USD Signals\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "What we offer:\n\n"
        "OPTION 1 — FREE\n"
        "Basic trading education\n"
        "How to read and apply a signal\n"
        "Access to VIP XAU/USD signals channel\n"
        "6 VIP signal groups included\n\n"
        "OPTION 2 — 200 USD lifetime\n"
        "Unlimited VIP MT4/MT5 Robots access\n"
        "Free download of all robots\n"
        "Lifetime updates included\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Choose your option below"
    ),
    "menu_publics": (
        "Before registering, join our free public groups\n"
        "to see what happens in the VIP:\n\n"
        f"Signals & Education (public):\n{CANAL_PUB_SIGNAUX}\n\n"
        f"Trading Robots (public):\n{CANAL_PUB_ROBOTS}\n\n"
        "When you're ready, come back and choose your option!"
    ),
    "choix_signaux": (
        "VIP SIGNALS & EDUCATION ACCESS - 100% FREE\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "What you get:\n\n"
        "Basic trading education (FR and EN)\n"
        "How to read and apply a signal correctly\n"
        "Google Drive access with full training\n"
        "6 VIP signal groups:\n"
        "  - Scalping, Swing, Intraday Gold, BTC, Forex\n\n"
        "Condition: be an Exness referral of @lementorfx\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Press Start Registration to continue"
    ),
    "choix_robots": (
        "VIP MT4/MT5 ROBOTS ACCESS - 200 USD lifetime\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "What you get:\n\n"
        "Unlimited download of all robots\n"
        "Martingale, Hedging, One Shot, Grid, Scalping\n"
        "Free lifetime updates\n"
        "Compatible MT4 and MT5\n"
        "Technical support included\n\n"
        "Payment methods:\n"
        "Binance Pay - Binance USDT TRC20 - PayPal\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Press View Payment Details to continue"
    ),

    "nom":     "STEP 1/9 — Last Name\n\nWhat is your last name?",
    "prenom":  "STEP 2/9 — First Name\n\nWhat is your first name?",
    "pays":    "STEP 3/9 — Country\n\nWhich country are you in? (ex: Nigeria, UK...)",
    "ville":   "STEP 4/9 — City\n\nWhich city are you in? (ex: Lagos, London...)",
    "tel":     "STEP 5/9 — Phone\n\nYour WhatsApp / phone number?\n(ex: +234 XXX XXX XXXX)",
    "email":   "STEP 6/9 — Email\n\nYour email address?\n\nThis email will be verified to confirm your Exness referral.",
    "niveau":  "STEP 7/9 — Level\n\nWhat is your current trading level?",
    "objectif":"STEP 8/9 — Goal\n\nWhat is your main goal with trading?\n(ex: extra income, financial freedom, learning...)",
    "exq":     "STEP 9/9 — Exness Account\n\nDo you have an Exness account?",
    "noex": (
        "No Exness account yet?\n\n"
        "It's free and takes 3 minutes!\n\n"
        f"Official referral link:\n{EXNESS_LINK}\n\n"
        "Once registered, come back and type /start"
    ),
    "exid": (
        "Your Exness ID (7 to 9 digits)\n\n"
        "How to find your ID:\n"
        "1. Go to exness.com and log in\n"
        "2. Click your Profile (top right)\n"
        "3. ID appears on the dashboard\n\n"
        "Enter your Exness ID:"
    ),
    "ebad":  "Invalid email. Enter a valid address (ex: name@gmail.com):",
    "edup":  "This email is already registered. Contact @lementorfx if this is an error.",
    "idbad": "Invalid ID. Exness ID contains 7 to 9 digits. Try again:",
    "iddup": "This Exness ID is already used. Contact @lementorfx if this is an error.",

    "recap": (
        "YOUR REGISTRATION SUMMARY\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Name: {nom} {prenom}\n"
        "Country / City: {pays}, {ville}\n"
        "Phone: {tel}\n"
        "Email: {email}\n"
        "Level: {niveau}\n"
        "Goal: {objectif}\n"
        "Exness ID: {exid}\n"
        "Telegram: @{user}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Is everything correct?"
    ),

    "attente": (
        "Request submitted successfully!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Your registration has been sent to @lementorfx\n"
        "for Exness referral verification.\n\n"
        "Next steps:\n\n"
        "1. @lementorfx verifies your Exness ID\n"
        "2. If validated — you receive 6 VIP links here\n"
        "3. If not — you receive an explanatory message\n\n"
        "Delay: a few hours maximum\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "While waiting, join our public groups:\n\n"
        f"Signals & Education (public):\n{CANAL_PUB_SIGNAUX}\n\n"
        f"Trading Robots (public):\n{CANAL_PUB_ROBOTS}\n\n"
        "Questions? @lementorfx"
    ),

    "valide": (
        "VIP ACCESS GRANTED!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Your Exness referral is verified and validated!\n\n"
        "Welcome to the LeMentorFx community!\n\n"
        "Here are your 6 VIP accesses:\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{LIENS_VIP}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "For each group:\n"
        "Click the link and join\n"
        "Enable notifications\n"
        "Read the pinned rules\n\n"
        "Happy trading! @lementorfx"
    ),

    "rejete": (
        "Access not approved\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Exness ID {exid} was not found\n"
        "in @lementorfx's referrals.\n\n"
        "Solutions:\n\n"
        f"No Exness account? Create one:\n{EXNESS_LINK}\n\n"
        "Account exists but not via our link?\n"
        "Contact @lementorfx to regularize\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Type /start to try again."
    ),

    "paiement_info": (
        "PAYMENT — VIP ROBOTS MT4/MT5\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Binance Pay\n"
        "ID: 556807688\n\n"
        "Binance USDT TRC20\n"
        "TEWKJtPsn4RsrEt2kiLNCDMUVKLGQ6RLJb\n\n"
        "PayPal\n"
        "capor51@gmail.com\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Exact amount: 200 USD\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "After payment:\n"
        "Send a screenshot of your payment\n"
        "confirmation right here in the bot.\n\n"
        "@lementorfx verifies and sends your access.\n\n"
        "Warning: only real payments are accepted."
    ),

    "capture_recue": (
        "Screenshot received!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Your payment proof has been sent\n"
        "to @lementorfx for verification.\n\n"
        "If confirmed, you will receive\n"
        "your VIP Robots access here.\n\n"
        "Delay: a few hours maximum\n\n"
        "Questions? @lementorfx"
    ),

    "valide_robot": (
        "PAYMENT CONFIRMED!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Your VIP Robots access is activated for life!\n\n"
        "Your VIP MT4/MT5 Robots access:\n\n"
        f"{CANAL_VIP_ROBOTS}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "In this channel:\n"
        "Unlimited download of all robots\n"
        "Martingale, Hedging, One Shot, Grid, Scalping\n"
        "Free lifetime updates\n"
        "Technical support\n\n"
        "Join and enable notifications!\n\n"
        "Thank you for your trust! @lementorfx"
    ),

    "paiement_rejete": (
        "Payment not confirmed\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "The screenshot sent could not be\n"
        "verified by @lementorfx.\n\n"
        "What to do?\n"
        "Check the amount sent (200 USD)\n"
        "Check payment details\n"
        "Contact @lementorfx directly\n\n"
        "Type /robots to try again."
    ),

    "cancel": "Registration cancelled. Type /start to restart.",
    "deja":   "You are already registered and validated! Questions? @lementorfx",
    "trop_court": "Answer too short. Try again:",
    }}
    s = T.get(lang, T["fr"]).get(key, "")
    return s.format(**kw) if kw else s

def g(lang, key, **kw): return txt(lang, key, **kw)

# ══════════════════════════════════════════════════════
# HELPERS CLAVIERS
# ══════════════════════════════════════════════════════

def kb_lang():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Francais", callback_data="L_fr"),
        InlineKeyboardButton("English",  callback_data="L_en"),
    ]])

def kb_menu(lang):
    s = "Voir les groupes publics" if lang=="fr" else "View public groups"
    a = "VIP Signaux & Education — GRATUIT" if lang=="fr" else "VIP Signals & Education — FREE"
    b = "VIP Robots MT4/MT5 — 200 USD"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👀 {s}", callback_data="M_publics")],
        [InlineKeyboardButton(f"📚 {a}", callback_data="M_signaux")],
        [InlineKeyboardButton(f"🤖 {b}", callback_data="M_robots")],
    ])

def kb_back(lang):
    s = "Retour" if lang=="fr" else "Back"
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"← {s}", callback_data="M_back")]])

def kb_exq(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Oui / Yes",               callback_data="EX_oui")],
        [InlineKeyboardButton("En cours / In progress",  callback_data="EX_oui")],
        [InlineKeyboardButton("Pas encore / Not yet",    callback_data="EX_non")],
    ])

def kb_niveau(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌱 Debutant / Beginner",              callback_data="NIV_debutant")],
        [InlineKeyboardButton("📈 Intermediaire / Intermediate",     callback_data="NIV_intermediaire")],
        [InlineKeyboardButton("🔥 Avance / Advanced",                callback_data="NIV_avance")],
        [InlineKeyboardButton("💎 Expert",                           callback_data="NIV_expert")],
    ])

def kb_confirm(lang):
    c = "Confirmer / Confirm"
    e = "Corriger / Edit"
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"✅ {c}", callback_data="C_ok"),
        InlineKeyboardButton(f"✏️ {e}", callback_data="C_edit"),
    ]])

def kb_start(lang):
    s = "Commencer l'inscription" if lang=="fr" else "Start Registration"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🚀 {s}", callback_data="GO")],
        [InlineKeyboardButton("← Retour / Back", callback_data="M_back")],
    ])

def kb_paiement(lang):
    s = "Voir les details de paiement" if lang=="fr" else "View Payment Details"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💳 {s}", callback_data="GO_ROBOT")],
        [InlineKeyboardButton("← Retour / Back", callback_data="M_back")],
    ])

# ══════════════════════════════════════════════════════
# FICHE ADMIN — formatage complet
# ══════════════════════════════════════════════════════

def fiche_admin(d, uid):
    return (
        f"NOUVELLE INSCRIPTION — LeMentorFx\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"IDENTITE\n"
        f"Nom complet : {d.get('nom','')} {d.get('prenom','')}\n"
        f"Pays / Ville : {d.get('pays','')}, {d.get('ville','')}\n"
        f"Telephone : {d.get('tel','')}\n"
        f"Email : {d.get('email','')}\n"
        f"Telegram : @{d.get('username','')}\n"
        f"User ID : {uid}\n\n"
        f"TRADING\n"
        f"Niveau : {d.get('niveau','')}\n"
        f"Objectif : {d.get('objectif','')}\n\n"
        f"EXNESS\n"
        f"Compte Exness : Oui\n"
        f"ID Exness : {d.get('exness_id','')}\n"
        f"Email Exness : {d.get('email','')}\n\n"
        f"OFFRE DEMANDEE : {d.get('offre','').upper()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Date : {datetime.now().strftime('%d/%m/%Y a %H:%M')}\n\n"
        f"Verifie sur ton espace Exness Partner\n"
        f"que cet email/ID est bien ton filleul.\n\n"
        f"Puis clique :"
    )

# ══════════════════════════════════════════════════════
# HANDLERS — CONVERSATION
# ══════════════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_blocked(uid):
        await update.message.reply_text("Acces refuse."); return ConversationHandler.END
    if is_validated(uid):
        await update.message.reply_text(g(ctx.user_data.get("l","fr"),"deja"))
        return ConversationHandler.END
    ctx.user_data.clear()
    ctx.user_data["u"] = update.effective_user.username or str(uid)
    await update.message.reply_text(
        "Choisis ta langue / Choose your language:",
        reply_markup=kb_lang())
    return S_LANG

async def cb_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = "fr" if q.data == "L_fr" else "en"
    ctx.user_data["l"] = lang
    await q.edit_message_text(g(lang,"accueil"), reply_markup=kb_menu(lang))
    return S_MENU

async def cb_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = ctx.user_data.get("l","fr")
    action = q.data

    if action == "M_publics":
        await q.edit_message_text(g(lang,"menu_publics"), reply_markup=kb_back(lang),
                                  disable_web_page_preview=True)
        return S_MENU
    elif action == "M_back":
        await q.edit_message_text(g(lang,"accueil"), reply_markup=kb_menu(lang))
        return S_MENU
    elif action == "M_signaux":
        ctx.user_data["offre"] = "signaux"
        await q.edit_message_text(g(lang,"choix_signaux"), reply_markup=kb_start(lang))
        return S_MENU
    elif action == "M_robots":
        ctx.user_data["offre"] = "robots"
        await q.edit_message_text(g(lang,"choix_robots"), reply_markup=kb_paiement(lang))
        return S_MENU
    elif action == "GO":
        await q.edit_message_text(g(lang,"nom"))
        return S_NOM
    elif action == "GO_ROBOT":
        uid  = update.effective_user.id
        user = ctx.user_data.get("u","—")
        save_pending_payment(uid, {"username":user,"lang":lang,"user_id":uid,"offre":"robots"})
        await q.edit_message_text(g(lang,"paiement_info"), disable_web_page_preview=True)
        return S_ATTENTE_PAIEMENT
    return S_MENU

# ── CHAMPS D'INSCRIPTION ─────────────────────────────

async def h_nom(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    v = update.message.text.strip()
    if len(v) < 2: await update.message.reply_text(g(lang,"trop_court")); return S_NOM
    ctx.user_data["nom"] = v
    await update.message.reply_text(g(lang,"prenom"))
    return S_PRENOM

async def h_prenom(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    v = update.message.text.strip()
    if len(v) < 2: await update.message.reply_text(g(lang,"trop_court")); return S_PRENOM
    ctx.user_data["prenom"] = v
    await update.message.reply_text(g(lang,"pays"))
    return S_PAYS

async def h_pays(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    ctx.user_data["pays"] = update.message.text.strip()
    await update.message.reply_text(g(lang,"ville"))
    return S_VILLE

async def h_ville(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    ctx.user_data["ville"] = update.message.text.strip()
    await update.message.reply_text(g(lang,"tel"))
    return S_TEL

async def h_tel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    ctx.user_data["tel"] = update.message.text.strip()
    await update.message.reply_text(g(lang,"email"))
    return S_EMAIL

async def h_email(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    v = update.message.text.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
        await update.message.reply_text(g(lang,"ebad")); return S_EMAIL
    if mail_used(v):
        await update.message.reply_text(g(lang,"edup")); return ConversationHandler.END
    ctx.user_data["email"] = v
    await update.message.reply_text(g(lang,"niveau"), reply_markup=kb_niveau(lang))
    return S_NIVEAU

async def cb_niveau(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = ctx.user_data.get("l","fr")
    niveaux = {
        "NIV_debutant":      "Debutant / Beginner",
        "NIV_intermediaire": "Intermediaire / Intermediate",
        "NIV_avance":        "Avance / Advanced",
        "NIV_expert":        "Expert",
    }
    ctx.user_data["niveau"] = niveaux.get(q.data, q.data)
    await q.edit_message_text(g(lang,"objectif"))
    return S_OBJECTIF

async def h_objectif(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    v = update.message.text.strip()
    if len(v) < 3: await update.message.reply_text(g(lang,"trop_court")); return S_OBJECTIF
    ctx.user_data["objectif"] = v
    await update.message.reply_text(g(lang,"exq"), reply_markup=kb_exq(lang))
    return S_EXQ

async def cb_exq(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = ctx.user_data.get("l","fr")
    if q.data == "EX_non":
        await q.edit_message_text(g(lang,"noex"), disable_web_page_preview=True)
        return ConversationHandler.END
    await q.edit_message_text(g(lang,"exid"))
    return S_EXID

async def h_exid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    v = update.message.text.strip().replace(" ","")
    if not re.match(r"^\d{7,9}$", v):
        await update.message.reply_text(g(lang,"idbad")); return S_EXID
    if eid_used(v):
        await update.message.reply_text(g(lang,"iddup")); return ConversationHandler.END
    ctx.user_data["exid"] = v
    await update.message.reply_text(
        g(lang,"recap",
          nom=ctx.user_data.get("nom",""), prenom=ctx.user_data.get("prenom",""),
          pays=ctx.user_data.get("pays",""), ville=ctx.user_data.get("ville",""),
          tel=ctx.user_data.get("tel",""), email=ctx.user_data.get("email",""),
          niveau=ctx.user_data.get("niveau",""), objectif=ctx.user_data.get("objectif",""),
          exid=v, user=ctx.user_data.get("u","")
        ),
        reply_markup=kb_confirm(lang)
    )
    return S_CONFIRM

async def cb_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = ctx.user_data.get("l","fr")
    if q.data == "C_edit":
        await q.edit_message_text(g(lang,"nom")); return S_NOM

    uid = update.effective_user.id
    d = {
        "nom":       ctx.user_data.get("nom",""),
        "prenom":    ctx.user_data.get("prenom",""),
        "pays":      ctx.user_data.get("pays",""),
        "ville":     ctx.user_data.get("ville",""),
        "tel":       ctx.user_data.get("tel",""),
        "email":     ctx.user_data.get("email",""),
        "niveau":    ctx.user_data.get("niveau",""),
        "objectif":  ctx.user_data.get("objectif",""),
        "exness_id": ctx.user_data.get("exid",""),
        "username":  ctx.user_data.get("u",""),
        "lang":      lang,
        "user_id":   uid,
        "offre":     ctx.user_data.get("offre","signaux"),
    }
    save_pending(uid, d)

    await q.edit_message_text(g(lang,"attente"), disable_web_page_preview=True)

    # ── Notification admin avec fiche complète ──
    kb_admin = InlineKeyboardMarkup([[
        InlineKeyboardButton("VALIDER ACCES VIP", callback_data=f"A_ok_{uid}"),
        InlineKeyboardButton("REJETER",            callback_data=f"A_no_{uid}"),
    ]])
    try:
        await ctx.bot.send_message(
            chat_id=ADMIN_ID,
            text=fiche_admin(d, uid),
            reply_markup=kb_admin
        )
        log.info(f"Fiche envoyee a l'admin pour {d['nom']} {d['prenom']} ({uid})")
    except Exception as e:
        log.error(f"Erreur notif admin: {e}")

    return ConversationHandler.END

# ── PAIEMENT ROBOTS ──────────────────────────────────

async def h_capture(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    uid  = update.effective_user.id
    user = ctx.user_data.get("u","—")
    await update.message.reply_text(g(lang,"capture_recue"))
    kb_admin = InlineKeyboardMarkup([[
        InlineKeyboardButton("CONFIRMER PAIEMENT", callback_data=f"P_ok_{uid}"),
        InlineKeyboardButton("REJETER PAIEMENT",   callback_data=f"P_no_{uid}"),
    ]])
    try:
        await ctx.bot.send_message(chat_id=ADMIN_ID,
            text=f"PREUVE DE PAIEMENT RECUE\n\n@{user} | ID: {uid}\n{datetime.now().strftime('%d/%m/%Y a %H:%M')}\nMontant attendu : 200 USD — VIP Robots\n\nVoici la capture :")
        if update.message.photo:
            await ctx.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, reply_markup=kb_admin)
        elif update.message.document:
            await ctx.bot.send_document(chat_id=ADMIN_ID, document=update.message.document.file_id, reply_markup=kb_admin)
        else:
            await ctx.bot.send_message(chat_id=ADMIN_ID, text="Pas d'image recue.", reply_markup=kb_admin)
    except Exception as e: log.error(f"Capture admin: {e}")
    return ConversationHandler.END

# ══════════════════════════════════════════════════════
# ADMIN — VALIDER / REJETER
# ══════════════════════════════════════════════════════

async def cb_admin_signal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("Acces refuse.", show_alert=True); return
    await q.answer()
    parts = q.data.split("_"); action = parts[1]; uid = int(parts[2])

    if action == "ok":
        d = approve_signal(uid)
        if not d: await q.edit_message_text("Introuvable. Deja traite ?"); return
        lang = d.get("lang","fr")
        try:
            await ctx.bot.send_message(chat_id=uid, text=g(lang,"valide"),
                                       disable_web_page_preview=True)
            await q.edit_message_text(
                f"VALIDE !\n\n{d.get('nom','')} {d.get('prenom','')} (@{d.get('username','')})\n"
                f"Email: {d.get('email','')}\nID Exness: {d.get('exness_id','')}\n\nLiens VIP envoyes.")
        except Exception as e: await q.edit_message_text(f"Erreur envoi : {e}")

    elif action == "no":
        d = reject_member(uid)
        if not d: await q.edit_message_text("Introuvable. Deja traite ?"); return
        lang = d.get("lang","fr")
        try:
            await ctx.bot.send_message(chat_id=uid,
                                       text=g(lang,"rejete", exid=d.get("exness_id","?")),
                                       disable_web_page_preview=True)
            await q.edit_message_text(
                f"REJETE\n\n{d.get('nom','')} {d.get('prenom','')} (@{d.get('username','')})\nClient informe.")
        except Exception as e: await q.edit_message_text(f"Erreur : {e}")

async def cb_admin_paiement(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("Acces refuse.", show_alert=True); return
    await q.answer()
    parts = q.data.split("_"); action = parts[1]; uid = int(parts[2])

    if action == "ok":
        d = approve_robot(uid)
        lang = d.get("lang","fr") if d else "fr"
        try:
            await ctx.bot.send_message(chat_id=uid, text=g(lang,"valide_robot"),
                                       disable_web_page_preview=True)
            await q.edit_message_text(f"PAIEMENT CONFIRME — Acces VIP Robots envoye ! ID: {uid}")
        except Exception as e: await q.edit_message_text(f"Erreur : {e}")

    elif action == "no":
        d = reject_payment(uid)
        lang = d.get("lang","fr") if d else "fr"
        try:
            await ctx.bot.send_message(chat_id=uid, text=g(lang,"paiement_rejete"))
            await q.edit_message_text(f"Paiement rejete. ID: {uid}")
        except Exception as e: await q.edit_message_text(f"Erreur : {e}")

# ══════════════════════════════════════════════════════
# COMMANDES ADMIN
# ══════════════════════════════════════════════════════

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    sig = len([x for x in db.get("valides",{}).values() if "signal" in x.get("statut","")])
    rob = len([x for x in db.get("valides",{}).values() if "robot" in x.get("statut","")])
    await update.message.reply_text(
        f"STATS LeMentorFx Bot\n\n"
        f"VIP Signaux valides : {sig}\n"
        f"VIP Robots valides : {rob}\n"
        f"En attente signaux : {len(db.get('attente',{}))}\n"
        f"En attente paiement : {len(db.get('attente_paiement',{}))}\n"
        f"Rejetes : {len(db.get('rejetes',{}))}\n"
        f"IDs Exness enregistres : {len(db.get('exness_ids',[]))}")

async def cmd_attente(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    items = list(db.get("attente",{}).values())
    if not items: await update.message.reply_text("Aucune demande en attente."); return
    lines = []
    for x in items:
        lines.append(
            f"• {x.get('nom','')} {x.get('prenom','')} | {x.get('pays','')} {x.get('ville','')}\n"
            f"  Email: {x.get('email','')} | ID: {x.get('exness_id','')}\n"
            f"  @{x.get('username','')} | {x.get('user_id','')}"
        )
    await update.message.reply_text(f"{len(items)} demande(s) en attente :\n\n" + "\n\n".join(lines))

async def cmd_liste(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    items = list(db.get("valides",{}).values())[-15:]
    if not items: await update.message.reply_text("Aucun membre encore."); return
    lines = [
        f"• {x.get('nom','')} {x.get('prenom','')} | {x.get('pays','')} | {x.get('email','')} | {x.get('exness_id','')} | {x.get('statut','')}"
        for x in items
    ]
    await update.message.reply_text("Membres valides :\n\n" + "\n".join(lines))

async def cmd_bloquer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not ctx.args: await update.message.reply_text("Usage: /bloquer [user_id]"); return
    try:
        uid=int(ctx.args[0]); db=load_db()
        if uid not in db["bloques"]: db["bloques"].append(uid); save_db(db)
        await update.message.reply_text(f"User {uid} bloque.")
    except: await update.message.reply_text("ID invalide.")

async def cmd_fiche(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Affiche la fiche complète d'un membre par user_id"""
    if update.effective_user.id != ADMIN_ID: return
    if not ctx.args: await update.message.reply_text("Usage: /fiche [user_id]"); return
    try:
        uid = ctx.args[0]; db = load_db()
        d = db.get("valides",{}).get(uid) or db.get("attente",{}).get(uid) or db.get("rejetes",{}).get(uid)
        if not d: await update.message.reply_text("Membre introuvable."); return
        await update.message.reply_text(fiche_admin(d, uid))
    except Exception as e: await update.message.reply_text(f"Erreur: {e}")

async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    await update.message.reply_text(g(lang,"cancel"))
    return ConversationHandler.END

async def msg_other(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("Demarrer / Start", callback_data="RESTART")
    ]])
    await update.message.reply_text(
        "Tape /start ou appuie sur le bouton.\nType /start or press the button.",
        reply_markup=kb)

async def cb_restart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear()
    ctx.user_data["u"] = update.effective_user.username or str(update.effective_user.id)
    await q.edit_message_text("Choisis ta langue / Choose your language:", reply_markup=kb_lang())
    return S_LANG

async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start",   "Demarrer l'inscription"),
        BotCommand("robots",  "VIP Robots MT4/MT5 - 200 USD"),
        BotCommand("attente", "Demandes en attente (admin)"),
        BotCommand("stats",   "Statistiques (admin)"),
        BotCommand("liste",   "Liste membres (admin)"),
        BotCommand("fiche",   "Fiche membre (admin)"),
        BotCommand("annuler", "Annuler"),
    ])

# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start",  cmd_start),
            CallbackQueryHandler(cb_restart, pattern="^RESTART$"),
        ],
        states={
            S_LANG:             [CallbackQueryHandler(cb_lang,    pattern="^L_")],
            S_MENU:             [CallbackQueryHandler(cb_menu,    pattern="^(M_|GO)")],
            S_NOM:              [MessageHandler(filters.TEXT & ~filters.COMMAND, h_nom)],
            S_PRENOM:           [MessageHandler(filters.TEXT & ~filters.COMMAND, h_prenom)],
            S_PAYS:             [MessageHandler(filters.TEXT & ~filters.COMMAND, h_pays)],
            S_VILLE:            [MessageHandler(filters.TEXT & ~filters.COMMAND, h_ville)],
            S_TEL:              [MessageHandler(filters.TEXT & ~filters.COMMAND, h_tel)],
            S_EMAIL:            [MessageHandler(filters.TEXT & ~filters.COMMAND, h_email)],
            S_NIVEAU:           [CallbackQueryHandler(cb_niveau,  pattern="^NIV_")],
            S_OBJECTIF:         [MessageHandler(filters.TEXT & ~filters.COMMAND, h_objectif)],
            S_EXQ:              [CallbackQueryHandler(cb_exq,     pattern="^EX_")],
            S_EXID:             [MessageHandler(filters.TEXT & ~filters.COMMAND, h_exid)],
            S_CONFIRM:          [CallbackQueryHandler(cb_confirm, pattern="^C_")],
            S_ATTENTE_PAIEMENT: [MessageHandler(filters.PHOTO | filters.Document.ALL, h_capture)],
        },
        fallbacks=[CommandHandler("annuler", cmd_cancel), CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(cb_admin_signal,   pattern="^A_(ok|no)_"))
    app.add_handler(CallbackQueryHandler(cb_admin_paiement, pattern="^P_(ok|no)_"))
    app.add_handler(CommandHandler("stats",   cmd_stats))
    app.add_handler(CommandHandler("liste",   cmd_liste))
    app.add_handler(CommandHandler("attente", cmd_attente))
    app.add_handler(CommandHandler("fiche",   cmd_fiche))
    app.add_handler(CommandHandler("bloquer", cmd_bloquer))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_other))

    print("LeMentorFx Bot V4 demarre")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
