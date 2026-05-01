import logging, json, os, re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)

TOKEN       = "7575039426:AAEoTVawvW6uLOZf3b9C5xMcxjfy8GXbBmk"
ADMIN_ID    = 7412212489
EXNESS_LINK = "https://one.exnessonelink.com/a/do7n4lz3on"
DB_FILE     = "membres.json"

# ── CANAUX ──────────────────────────────────────────────
CANAL_VIP_SIGNAUX  = "https://t.me/+HJ9qJhRZ7mg0MmFk"
CANAL_VIP_ROBOTS   = "https://t.me/+N-Atm_7qeHMxZTM8"
CANAL_PUB_SIGNAUX  = "https://t.me/lementorforexgroup"
CANAL_PUB_ROBOTS   = "https://t.me/robotradingratuit"

# ── PAIEMENT ROBOTS ─────────────────────────────────────
PRIX_ROBOTS = "200 USD"
PAIEMENT_INFO = (
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "💳 *MÉTHODES DE PAIEMENT*\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "🟡 *Binance Pay*\n"
    "   ID : `556807688`\n\n"
    "🔵 *Binance USDT TRC20*\n"
    "   `TEWKJtPsn4RsrEt2kiLNCDMUVKLGQ6RLJb`\n\n"
    "🔵 *PayPal*\n"
    "   `capor51@gmail.com`\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "⚠️ *Montant exact :* `200 USD`\n\n"
    "📸 *Après paiement :*\n"
    "Envoie une capture d'écran de ta confirmation\n"
    "de paiement directement ici dans le bot.\n\n"
    "✅ @lementorfx vérifie et te donne l'accès."
)

# ── ÉTATS ───────────────────────────────────────────────
(S_LANG, S_MENU, S_NOM, S_PAYS, S_EMAIL,
 S_EXQ, S_EXID, S_CONFIRM,
 S_ATTENTE_PAIEMENT) = range(9)

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
# BASE DE DONNÉES
# ═══════════════════════════════════════════════════════

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE,"r",encoding="utf-8") as f: return json.load(f)
    return {"valides":{},"attente":{},"attente_paiement":{},"rejetes":{},
            "exness_ids":[],"emails":[],"bloques":[]}

def save_db(db):
    with open(DB_FILE,"w",encoding="utf-8") as f: json.dump(db,f,ensure_ascii=False,indent=2)

def eid_used(e):     return e in load_db().get("exness_ids",[])
def mail_used(e):    return e.lower() in [x.lower() for x in load_db().get("emails",[])]
def is_blocked(u):   return u in load_db().get("bloques",[])
def is_validated(u): return str(u) in load_db().get("valides",{})

def save_pending(uid, d):
    db = load_db(); db["attente"][str(uid)] = {**d,"date":datetime.now().isoformat()}; save_db(db)

def save_pending_payment(uid, d):
    db = load_db(); db["attente_paiement"][str(uid)] = {**d,"date":datetime.now().isoformat()}; save_db(db)

def approve_signal(uid):
    db = load_db(); k = str(uid)
    if k not in db["attente"]: return None
    d = db["attente"].pop(k); d["statut"] = "validé_signaux"
    db["valides"][k] = d
    if d.get("exness_id"): db["exness_ids"].append(d["exness_id"])
    if d.get("email"):     db["emails"].append(d["email"].lower())
    save_db(db); return d

def reject_member(uid):
    db = load_db(); k = str(uid)
    if k not in db["attente"]: return None
    d = db["attente"].pop(k); d["statut"] = "rejeté"; db["rejetes"][k] = d; save_db(db); return d

def approve_robot(uid):
    db = load_db(); k = str(uid)
    if k not in db["attente_paiement"]: return None
    d = db["attente_paiement"].pop(k); d["statut"] = "validé_robots"; save_db(db); return d

def reject_payment(uid):
    db = load_db(); k = str(uid)
    if k not in db["attente_paiement"]: return None
    d = db["attente_paiement"].pop(k); d["statut"] = "paiement_rejeté"
    db["rejetes"][k+"_pay"] = d; save_db(db); return d

# ═══════════════════════════════════════════════════════
# TEXTES FR / EN
# ═══════════════════════════════════════════════════════

T = {
"fr": {

"accueil": (
    "👋 *Bienvenue chez LeMentorFx !*\n\n"
    "Je suis ton assistant officiel 🤖\n"
    "Géré par *@lementorfx* — Partenaire IB Exness\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🎓 *Ce que nous proposons :*\n\n"
    "📚 *Option 1 — GRATUIT*\n"
    "Formation de base en trading\n"
    "Comment lire et appliquer un signal\n"
    "Accès au salon de signaux VIP XAU/USD\n\n"
    "🤖 *Option 2 — 200 USD à vie*\n"
    "Accès illimité au VIP Robots MT4/MT5\n"
    "Téléchargement gratuit de tous les robots\n"
    "Mises à jour incluses à vie\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "👇 *Choisis ton option ci-dessous*"
),

"menu": (
    "🔽 *Que souhaites-tu faire ?*\n\n"
    "📢 Tu peux d'abord *rejoindre nos groupes publics gratuits*\n"
    "pour avoir une idée de ce qui se passe dans le VIP 👇"
),

"publics": (
    "👀 *Avant de t'inscrire, rejoins nos groupes publics :*\n\n"
    "📡 Groupe signaux & éducation *(public)* :\n"
    f"{CANAL_PUB_SIGNAUX}\n\n"
    "🤖 Groupe robots de trading *(public)* :\n"
    f"{CANAL_PUB_ROBOTS}\n\n"
    "Tu peux voir ce qui s'y passe et décider ensuite.\n"
    "Quand tu es prêt → reviens et choisis ton option !"
),

"choix_signaux": (
    "📚 *ACCÈS VIP SIGNAUX & ÉDUCATION*\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "*100% GRATUIT* ✅\n\n"
    "Ce que tu obtiens :\n"
    "• 🎓 Formation de base en trading\n"
    "• 📈 Comment appliquer un signal correctement\n"
    "• 📡 Signaux XAU/USD en temps réel *(PHANTOM TRAP)*\n"
    "• 🔗 Accès au Google Drive avec la formation complète\n"
    "• 🌍 Disponible en Français et English\n\n"
    "*Condition :* être filleul Exness de @lementorfx\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Clique *Commencer l'inscription* pour continuer 👇"
),

"choix_robots": (
    "🤖 *ACCÈS VIP ROBOTS MT4/MT5*\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "*200 USD — Accès à vie* 💎\n\n"
    "Ce que tu obtiens :\n"
    "• 🤖 Téléchargement illimité de tous les robots\n"
    "• 📊 Robots Martingale, Hedging, One Shot, Grid, Scalping\n"
    "• 🔄 Mises à jour gratuites à vie\n"
    "• 📱 Compatible MT4 & MT5\n"
    "• 💬 Support technique inclus\n\n"
    "*Méthodes de paiement :*\n"
    "Binance Pay • Binance USDT TRC20 • PayPal\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Clique *Voir les détails de paiement* pour continuer 👇"
),

"nom":   "━━━━━━━━━━━━━━━━━━━━━\n👤 *ÉTAPE 1 / 5 — Identité*\n━━━━━━━━━━━━━━━━━━━━━\n\nQuel est ton *nom complet* ?\n\n_Ex : Jean-Pierre Mvogo_",
"pays":  "━━━━━━━━━━━━━━━━━━━━━\n🌍 *ÉTAPE 2 / 5 — Pays*\n━━━━━━━━━━━━━━━━━━━━━\n\nDans quel pays es-tu situé ?\n\n_Ex : Cameroun, Sénégal, France..._",
"email": "━━━━━━━━━━━━━━━━━━━━━\n📧 *ÉTAPE 3 / 5 — Email Exness*\n━━━━━━━━━━━━━━━━━━━━━\n\nEntre l'adresse email de ton compte Exness.\n\n⚠️ Cet email sera vérifié pour confirmer ton parrainage.\n\n_Ex : tonnom@gmail.com_",
"ebad":  "❌ *Email invalide.* Entre une adresse correcte :\n_Ex : tonnom@gmail.com_",
"edup":  "❌ *Email déjà enregistré.*\nContacte @lementorfx si c'est une erreur.",
"exq":   "━━━━━━━━━━━━━━━━━━━━━\n🏦 *ÉTAPE 4 / 5 — Compte Exness*\n━━━━━━━━━━━━━━━━━━━━━\n\nAs-tu un compte Exness ?\n\n💡 L'accès VIP signaux est *gratuit*.\nCondition : être inscrit via le lien de @lementorfx.",
"noex":  f"⚠️ *Pas encore de compte Exness ?*\n\nC'est *gratuit* et rapide !\n\n🔗 Lien officiel :\n{EXNESS_LINK}\n\n✅ Une fois inscrit, reviens taper /start",
"exid":  "━━━━━━━━━━━━━━━━━━━━━\n🔢 *ÉTAPE 5 / 5 — ID Exness*\n━━━━━━━━━━━━━━━━━━━━━\n\nEntre ton *ID Exness* _(7 à 9 chiffres)_\n\n📌 *Comment trouver :*\n1️⃣ exness.com → connecte-toi\n2️⃣ Clique *Profil* _(haut à droite)_\n3️⃣ L'ID s'affiche sur le tableau de bord\n\n👇 Entre ton ID :",
"idbad": "❌ *ID invalide.* L'ID Exness = 7 à 9 chiffres.\nRéessaie :",
"iddup": "❌ *Cet ID est déjà utilisé.*\nContacte @lementorfx si c'est une erreur.",
"recap": "━━━━━━━━━━━━━━━━━━━━━\n📋 *RÉCAPITULATIF*\n━━━━━━━━━━━━━━━━━━━━━\n\n👤 Nom : *{nom}*\n🌍 Pays : *{pays}*\n📧 Email : *{email}*\n🏦 ID Exness : *{exid}*\n📱 Telegram : @{user}\n\nTout est correct ?",

"attente_signal": (
    "⏳ *Demande envoyée !*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Tes infos ont été transmises à *@lementorfx*\n"
    "pour vérification de ton parrainage Exness.\n\n"
    "📋 *Prochaines étapes :*\n\n"
    "1️⃣ @lementorfx vérifie ton ID Exness\n"
    "2️⃣ Si validé ✅ → tu reçois le lien VIP ici\n"
    "3️⃣ Si non ❌ → tu reçois un message explicatif\n\n"
    "⏱ Délai : *quelques heures maximum*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "⬇️ *En attendant, rejoins nos groupes publics :*\n\n"
    f"📡 Signaux & Éducation *(public)* :\n{CANAL_PUB_SIGNAUX}\n\n"
    f"🤖 Robots Trading *(public)* :\n{CANAL_PUB_ROBOTS}\n\n"
    "Questions → @lementorfx 💬"
),

"valide_signal": (
    "\U0001f389 ACCES VIP ACCORDE !\n\n"
    "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
    "Ton parrainage Exness est verifie et valide \u2705\n\n"
    "Bienvenue dans la communaute LeMentorFx ! \U0001f525\n\n"
    "Voici tous tes acces VIP :\n\n"
    "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
    "\U0001f4da 1 — LeMentor Signal\n"
    "Education de base en trading FR/EN\n"
    "Comment copier et appliquer les signaux\n"
    "https://t.me/+HJ9qJhRZ7mg0MmFk\n\n"
    "\U0001f9e0 2 — Forex Master Mind\n"
    "Signaux scalper\n"
    "https://t.me/+O-qp8FFqU3M2YzU0\n\n"
    "\U0001f3af 3 — Forex Manipulation\n"
    "Signaux swing trading\n"
    "https://t.me/+nmaRfODrkkJhNTJk\n\n"
    "\U0001f4ca 4 — Supply and Demand Intraday\n"
    "Signaux Gold et BTC + gros R/R intraday\n"
    "https://t.me/+PNPC0O0teFhiMGY0\n\n"
    "\U0001f48e 5 — Sadeeq FX\n"
    "Signaux Forex intraday\n"
    "https://t.me/+RM5QY9P10mM1ODRk\n\n"
    "\U0001f525 6 — ShadTrading Premium\n"
    "Signaux intraday Gold et BTC\n"
    "https://t.me/+Tn3gEe_HOediN2M0\n\n"
    "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
    "Pour chaque groupe :\n"
    "Clique le lien et rejoins\n"
    "Active les notifications\n"
    "Lis les regles epinglees\n\n"
    "Bon trading ! @lementorfx"
),

"rejete": (
    "❌ *Accès non accordé*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "L'ID Exness *{exid}* n'a pas été trouvé\n"
    "dans les filleuls de @lementorfx.\n\n"
    "💡 *Solutions :*\n\n"
    f"▸ Pas de compte Exness ?\n  → {EXNESS_LINK}\n\n"
    "▸ Compte existant mais pas via notre lien ?\n"
    "  → Contacte @lementorfx pour régulariser\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Tape /start pour recommencer."
),

"paiement_instructions": (
    "💳 *PAIEMENT — ACCÈS VIP ROBOTS*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🟡 *Binance Pay*\n"
    "   ID : `556807688`\n\n"
    "🔵 *Binance USDT TRC20*\n"
    "   `TEWKJtPsn4RsrEt2kiLNCDMUVKLGQ6RLJb`\n\n"
    "🔵 *PayPal*\n"
    "   `capor51@gmail.com`\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "💰 *Montant exact :* `200 USD`\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "📸 *Étape suivante :*\n"
    "Une fois le paiement effectué,\n"
    "*envoie ici une capture d'écran*\n"
    "de ta confirmation de paiement.\n\n"
    "✅ @lementorfx vérifie et t'envoie l'accès.\n\n"
    "_⚠️ Envoie uniquement une vraie capture._\n"
    "_Tout faux paiement sera rejeté._"
),

"capture_recue": (
    "📸 *Capture reçue !*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Ta preuve de paiement a été transmise\n"
    "à *@lementorfx* pour vérification.\n\n"
    "✅ Si le paiement est confirmé,\n"
    "tu recevras l'accès au VIP Robots ici.\n\n"
    "⏱ Délai : *quelques heures maximum*\n\n"
    "Questions → @lementorfx 💬"
),

"valide_robot": (
    "🎉 *PAIEMENT CONFIRMÉ !*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Ton accès VIP Robots est *activé à vie* ✅\n\n"
    "🤖 *Ton accès VIP Robots MT4/MT5 :*\n\n"
    f"🔐 *Canal VIP Robots* :\n{CANAL_VIP_ROBOTS}\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "📌 *Dans ce canal :*\n"
    "• Téléchargement illimité de tous les robots\n"
    "• Martingale, Hedging, One Shot, Grid, Scalping\n"
    "• Mises à jour gratuites à vie\n"
    "• Support technique\n\n"
    "✅ Rejoins et active les notifications 🔔\n\n"
    "Merci pour ta confiance ! 🚀 @lementorfx"
),

"paiement_rejete": (
    "❌ *Paiement non confirmé*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "La capture envoyée n'a pas pu être\n"
    "vérifiée par @lementorfx.\n\n"
    "💡 *Que faire ?*\n"
    "▸ Vérifie que tu as envoyé le bon montant *(200 USD)*\n"
    "▸ Vérifie les coordonnées de paiement\n"
    "▸ Contacte @lementorfx directement\n\n"
    "Tape /robots pour réessayer."
),

"cancel": "❌ Annulé. Tape /start pour recommencer.",
"deja":   "✅ Tu es déjà inscrit !\nDes questions → @lementorfx",
},

"en": {

"accueil": (
    "👋 *Welcome to LeMentorFx!*\n\n"
    "I'm your official assistant 🤖\n"
    "Managed by *@lementorfx* — Exness IB Partner\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🎓 *What we offer:*\n\n"
    "📚 *Option 1 — FREE*\n"
    "Basic trading education\n"
    "How to read and apply a signal\n"
    "Access to VIP XAU/USD signals channel\n\n"
    "🤖 *Option 2 — 200 USD lifetime*\n"
    "Unlimited VIP MT4/MT5 Robots access\n"
    "Free download of all robots\n"
    "Lifetime updates included\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "👇 *Choose your option below*"
),

"menu": "🔽 *What would you like to do?*\n\n📢 You can first *join our free public groups*\nto see what happens in the VIP 👇",

"publics": (
    "👀 *Before registering, join our public groups:*\n\n"
    f"📡 Signals & Education *(public)*:\n{CANAL_PUB_SIGNAUX}\n\n"
    f"🤖 Trading Robots *(public)*:\n{CANAL_PUB_ROBOTS}\n\n"
    "See what's happening there, then decide.\nReady? Come back and choose your option!"
),

"choix_signaux": (
    "📚 *VIP SIGNALS & EDUCATION ACCESS*\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "*100% FREE* ✅\n\n"
    "What you get:\n"
    "• 🎓 Basic trading education\n"
    "• 📈 How to apply a signal correctly\n"
    "• 📡 Real-time XAU/USD signals *(PHANTOM TRAP)*\n"
    "• 🔗 Google Drive access with full training\n"
    "• 🌍 Available in French and English\n\n"
    "*Condition:* be an Exness referral of @lementorfx\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Click *Start Registration* to continue 👇"
),

"choix_robots": (
    "🤖 *VIP MT4/MT5 ROBOTS ACCESS*\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "*200 USD — Lifetime Access* 💎\n\n"
    "What you get:\n"
    "• 🤖 Unlimited download of all robots\n"
    "• 📊 Martingale, Hedging, One Shot, Grid, Scalping\n"
    "• 🔄 Free lifetime updates\n"
    "• 📱 Compatible MT4 & MT5\n"
    "• 💬 Technical support included\n\n"
    "*Payment methods:*\n"
    "Binance Pay • Binance USDT TRC20 • PayPal\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Click *View Payment Details* to continue 👇"
),

"nom":   "━━━━━━━━━━━━━━━━━━━━━\n👤 *STEP 1 / 5 — Identity*\n━━━━━━━━━━━━━━━━━━━━━\n\nWhat is your *full name*?\n\n_Ex: John Smith_",
"pays":  "━━━━━━━━━━━━━━━━━━━━━\n🌍 *STEP 2 / 5 — Country*\n━━━━━━━━━━━━━━━━━━━━━\n\nWhich country are you in?\n\n_Ex: Nigeria, UK, USA..._",
"email": "━━━━━━━━━━━━━━━━━━━━━\n📧 *STEP 3 / 5 — Exness Email*\n━━━━━━━━━━━━━━━━━━━━━\n\nEnter the email of your Exness account.\n\n⚠️ This will be verified to confirm your referral.\n\n_Ex: yourname@gmail.com_",
"ebad":  "❌ *Invalid email.* Enter a valid address:\n_Ex: yourname@gmail.com_",
"edup":  "❌ *Email already registered.*\nContact @lementorfx if this is an error.",
"exq":   "━━━━━━━━━━━━━━━━━━━━━\n🏦 *STEP 4 / 5 — Exness Account*\n━━━━━━━━━━━━━━━━━━━━━\n\nDo you have an Exness account?\n\n💡 VIP signals access is *free*.\nCondition: registered via @lementorfx's link.",
"noex":  f"⚠️ *No Exness account yet?*\n\nIt's free and fast!\n\n🔗 Official link:\n{EXNESS_LINK}\n\n✅ Once registered, come back and type /start",
"exid":  "━━━━━━━━━━━━━━━━━━━━━\n🔢 *STEP 5 / 5 — Exness ID*\n━━━━━━━━━━━━━━━━━━━━━\n\nEnter your *Exness ID* _(7 to 9 digits)_\n\n📌 *How to find it:*\n1️⃣ exness.com → log in\n2️⃣ Click *Profile* _(top right)_\n3️⃣ ID appears on dashboard\n\n👇 Enter your ID:",
"idbad": "❌ *Invalid ID.* Exness ID = 7 to 9 digits.\nTry again:",
"iddup": "❌ *This ID is already used.*\nContact @lementorfx if this is an error.",
"recap": "━━━━━━━━━━━━━━━━━━━━━\n📋 *SUMMARY*\n━━━━━━━━━━━━━━━━━━━━━\n\n👤 Name: *{nom}*\n🌍 Country: *{pays}*\n📧 Email: *{email}*\n🏦 Exness ID: *{exid}*\n📱 Telegram: @{user}\n\nIs everything correct?",

"attente_signal": (
    "⏳ *Request submitted!*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Your info has been sent to *@lementorfx*\n"
    "for Exness referral verification.\n\n"
    "📋 *Next steps:*\n\n"
    "1️⃣ @lementorfx verifies your Exness ID\n"
    "2️⃣ If validated ✅ → you receive the VIP link here\n"
    "3️⃣ If not ❌ → you receive an explanatory message\n\n"
    "⏱ Delay: *a few hours maximum*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "⬇️ *While waiting, join our public groups:*\n\n"
    f"📡 Signals & Education *(public)*:\n{CANAL_PUB_SIGNAUX}\n\n"
    f"🤖 Trading Robots *(public)*:\n{CANAL_PUB_ROBOTS}\n\n"
    "Questions → @lementorfx 💬"
),

"valide_signal": (
    "\U0001f389 VIP ACCESS GRANTED!\n\n"
    "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
    "Your Exness referral is verified and validated \u2705\n\n"
    "Welcome to LeMentorFx community! \U0001f525\n\n"
    "Here are all your VIP accesses:\n\n"
    "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
    "\U0001f4da 1 — LeMentor Signal\n"
    "Basic trading education FR/EN\n"
    "How to copy and apply signals\n"
    "https://t.me/+HJ9qJhRZ7mg0MmFk\n\n"
    "\U0001f9e0 2 — Forex Master Mind\n"
    "Scalper signals\n"
    "https://t.me/+O-qp8FFqU3M2YzU0\n\n"
    "\U0001f3af 3 — Forex Manipulation\n"
    "Swing trading signals\n"
    "https://t.me/+nmaRfODrkkJhNTJk\n\n"
    "\U0001f4ca 4 — Supply and Demand Intraday\n"
    "Gold and BTC signals + high R/R intraday\n"
    "https://t.me/+PNPC0O0teFhiMGY0\n\n"
    "\U0001f48e 5 — Sadeeq FX\n"
    "Forex intraday signals\n"
    "https://t.me/+RM5QY9P10mM1ODRk\n\n"
    "\U0001f525 6 — ShadTrading Premium\n"
    "Intraday Gold and BTC signals\n"
    "https://t.me/+Tn3gEe_HOediN2M0\n\n"
    "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
    "For each group:\n"
    "Click the link and join\n"
    "Enable notifications\n"
    "Read the pinned rules\n\n"
    "Happy trading! @lementorfx"
),

"rejete": (
    "❌ *Access Not Approved*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Exness ID *{exid}* was not found\n"
    "in @lementorfx's referrals.\n\n"
    "💡 *Solutions:*\n\n"
    f"▸ No Exness account?\n  → {EXNESS_LINK}\n\n"
    "▸ Account exists but not via our link?\n"
    "  → Contact @lementorfx\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Type /start to try again."
),

"paiement_instructions": (
    "💳 *PAYMENT — VIP ROBOTS ACCESS*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🟡 *Binance Pay*\n"
    "   ID: `556807688`\n\n"
    "🔵 *Binance USDT TRC20*\n"
    "   `TEWKJtPsn4RsrEt2kiLNCDMUVKLGQ6RLJb`\n\n"
    "🔵 *PayPal*\n"
    "   `capor51@gmail.com`\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "💰 *Exact amount:* `200 USD`\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "📸 *Next step:*\n"
    "Once payment is done,\n"
    "*send a screenshot* of your payment\n"
    "confirmation right here in the bot.\n\n"
    "✅ @lementorfx verifies and sends your access.\n\n"
    "_⚠️ Only send a real screenshot._\n"
    "_Fake payments will be rejected._"
),

"capture_recue": (
    "📸 *Screenshot received!*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Your payment proof has been sent\n"
    "to *@lementorfx* for verification.\n\n"
    "✅ If confirmed, you'll receive\n"
    "your VIP Robots access here.\n\n"
    "⏱ Delay: *a few hours maximum*\n\n"
    "Questions → @lementorfx 💬"
),

"valide_robot": (
    "🎉 *PAYMENT CONFIRMED!*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Your VIP Robots access is *activated for life* ✅\n\n"
    "🤖 *Your VIP MT4/MT5 Robots access:*\n\n"
    f"🔐 *VIP Robots Channel*:\n{CANAL_VIP_ROBOTS}\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "📌 *In this channel:*\n"
    "• Unlimited download of all robots\n"
    "• Martingale, Hedging, One Shot, Grid, Scalping\n"
    "• Free lifetime updates\n"
    "• Technical support\n\n"
    "✅ Join and enable notifications 🔔\n\n"
    "Thank you for your trust! 🚀 @lementorfx"
),

"paiement_rejete": (
    "❌ *Payment Not Confirmed*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "The screenshot sent could not be\n"
    "verified by @lementorfx.\n\n"
    "💡 *What to do?*\n"
    "▸ Check you sent the right amount *(200 USD)*\n"
    "▸ Check payment details\n"
    "▸ Contact @lementorfx directly\n\n"
    "Type /robots to try again."
),

"cancel": "❌ Cancelled. Type /start to restart.",
"deja":   "✅ You are already registered!\nQuestions → @lementorfx",
}}

def g(lang, key, **kw):
    s = T.get(lang, T["fr"]).get(key, "")
    return s.format(**kw) if kw else s

# ═══════════════════════════════════════════════════════
# CONVERSATION PRINCIPALE
# ═══════════════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_blocked(uid):
        await update.message.reply_text("⛔ Accès refusé. / Access denied."); return ConversationHandler.END
    if is_validated(uid):
        await update.message.reply_text(g(ctx.user_data.get("l","fr"),"deja"), parse_mode="Markdown")
        return ConversationHandler.END
    ctx.user_data.clear()
    ctx.user_data["u"] = update.effective_user.username or str(uid)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🇫🇷 Français", callback_data="L_fr"),
        InlineKeyboardButton("🇬🇧 English",  callback_data="L_en"),
    ]])
    await update.message.reply_text(
        "🌍 *Choisis ta langue / Choose your language:*",
        parse_mode="Markdown", reply_markup=kb)
    return S_LANG

async def cb_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = "fr" if q.data == "L_fr" else "en"
    ctx.user_data["l"] = lang

    btn_fr = "Voir les groupes publics 👀" if lang=="fr" else "View public groups 👀"
    btn_s  = "📚 VIP Signaux & Éducation — GRATUIT" if lang=="fr" else "📚 VIP Signals & Education — FREE"
    btn_r  = "🤖 VIP Robots MT4/MT5 — 200 USD" if lang=="fr" else "🤖 VIP Robots MT4/MT5 — 200 USD"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👀 {btn_fr}", callback_data="M_publics")],
        [InlineKeyboardButton(btn_s, callback_data="M_signaux")],
        [InlineKeyboardButton(btn_r, callback_data="M_robots")],
    ])
    await q.edit_message_text(g(lang,"accueil"), parse_mode="Markdown", reply_markup=kb)
    return S_MENU

async def cb_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = ctx.user_data.get("l","fr")
    action = q.data

    if action == "M_publics":
        btn_back = "⬅️ Retour / Back" 
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(btn_back, callback_data="M_back")]])
        await q.edit_message_text(g(lang,"publics"), parse_mode="Markdown",
                                  reply_markup=kb, disable_web_page_preview=True)
        return S_MENU

    elif action == "M_back":
        btn_s = "📚 VIP Signaux & Éducation — GRATUIT" if lang=="fr" else "📚 VIP Signals & Education — FREE"
        btn_r = "🤖 VIP Robots MT4/MT5 — 200 USD"
        btn_p = "Voir les groupes publics 👀"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"👀 {btn_p}", callback_data="M_publics")],
            [InlineKeyboardButton(btn_s, callback_data="M_signaux")],
            [InlineKeyboardButton(btn_r, callback_data="M_robots")],
        ])
        await q.edit_message_text(g(lang,"accueil"), parse_mode="Markdown", reply_markup=kb)
        return S_MENU

    elif action == "M_signaux":
        ctx.user_data["offre"] = "signaux"
        btn = "🚀 Commencer l'inscription →" if lang=="fr" else "🚀 Start Registration →"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(btn, callback_data="GO")],
            [InlineKeyboardButton("⬅️ Retour / Back", callback_data="M_back")],
        ])
        await q.edit_message_text(g(lang,"choix_signaux"), parse_mode="Markdown", reply_markup=kb)
        return S_MENU

    elif action == "M_robots":
        ctx.user_data["offre"] = "robots"
        btn = "💳 Voir les détails de paiement →" if lang=="fr" else "💳 View Payment Details →"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(btn, callback_data="GO_ROBOT")],
            [InlineKeyboardButton("⬅️ Retour / Back", callback_data="M_back")],
        ])
        await q.edit_message_text(g(lang,"choix_robots"), parse_mode="Markdown", reply_markup=kb)
        return S_MENU

    elif action == "GO":
        await q.edit_message_text(g(lang,"nom"), parse_mode="Markdown")
        return S_NOM

    elif action == "GO_ROBOT":
        uid  = update.effective_user.id
        user = ctx.user_data.get("u","—")
        # Sauvegarde infos basiques pour retrouver qui envoie la capture
        save_pending_payment(uid, {
            "username": user, "lang": lang,
            "user_id": uid, "offre": "robots"
        })
        await q.edit_message_text(g(lang,"paiement_instructions"), parse_mode="Markdown")
        return S_ATTENTE_PAIEMENT

    return S_MENU

# ── INSCRIPTION SIGNAUX ──────────────────────────────────

async def h_nom(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    v = update.message.text.strip()
    if len(v) < 2: await update.message.reply_text("❌ Nom trop court. Réessaie."); return S_NOM
    ctx.user_data["nom"] = v
    await update.message.reply_text(g(lang,"pays"), parse_mode="Markdown")
    return S_PAYS

async def h_pays(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    ctx.user_data["pays"] = update.message.text.strip()
    await update.message.reply_text(g(lang,"email"), parse_mode="Markdown")
    return S_EMAIL

async def h_email(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    v = update.message.text.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
        await update.message.reply_text(g(lang,"ebad"), parse_mode="Markdown"); return S_EMAIL
    if mail_used(v):
        await update.message.reply_text(g(lang,"edup"), parse_mode="Markdown"); return ConversationHandler.END
    ctx.user_data["email"] = v
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Oui / Yes",               callback_data="EX_oui")],
        [InlineKeyboardButton("🔄 En cours / In progress",  callback_data="EX_oui")],
        [InlineKeyboardButton("❌ Pas encore / Not yet",    callback_data="EX_non")],
    ])
    await update.message.reply_text(g(lang,"exq"), parse_mode="Markdown", reply_markup=kb)
    return S_EXQ

async def cb_exq(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = ctx.user_data.get("l","fr")
    if q.data == "EX_non":
        await q.edit_message_text(g(lang,"noex"), parse_mode="Markdown"); return ConversationHandler.END
    await q.edit_message_text(g(lang,"exid"), parse_mode="Markdown")
    return S_EXID

async def h_exid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    v = update.message.text.strip().replace(" ","")
    if not re.match(r"^\d{7,9}$", v):
        await update.message.reply_text(g(lang,"idbad"), parse_mode="Markdown"); return S_EXID
    if eid_used(v):
        await update.message.reply_text(g(lang,"iddup"), parse_mode="Markdown"); return ConversationHandler.END
    ctx.user_data["exid"] = v
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Confirmer / Confirm", callback_data="C_ok"),
        InlineKeyboardButton("✏️ Corriger / Edit",     callback_data="C_edit"),
    ]])
    await update.message.reply_text(
        g(lang,"recap", nom=ctx.user_data.get("nom","—"), pays=ctx.user_data.get("pays","—"),
          email=ctx.user_data.get("email","—"), exid=v, user=ctx.user_data.get("u","—")),
        parse_mode="Markdown", reply_markup=kb)
    return S_CONFIRM

async def cb_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = ctx.user_data.get("l","fr")
    if q.data == "C_edit":
        await q.edit_message_text(g(lang,"exid"), parse_mode="Markdown"); return S_EXID

    uid   = update.effective_user.id
    nom   = ctx.user_data.get("nom","—")
    pays  = ctx.user_data.get("pays","—")
    email = ctx.user_data.get("email","—")
    exid  = ctx.user_data.get("exid","—")
    user  = ctx.user_data.get("u","—")

    save_pending(uid, {"nom":nom,"pays":pays,"email":email,"exness_id":exid,
                       "username":user,"lang":lang,"user_id":uid,"offre":"signaux"})

    await q.edit_message_text(g(lang,"attente_signal"), parse_mode="Markdown",
                              disable_web_page_preview=True)

    kb_admin = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ VALIDER ACCÈS VIP",  callback_data=f"A_ok_{uid}"),
        InlineKeyboardButton("❌ REJETER",             callback_data=f"A_no_{uid}"),
    ]])
    notif = (
        f"🆕 *NOUVELLE DEMANDE VIP SIGNAUX*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *{nom}*\n🌍 {pays}\n📧 `{email}`\n"
        f"🏦 ID Exness : `{exid}`\n📱 @{user}\n🆔 `{uid}`\n"
        f"📅 {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 Vérifie sur ton espace Exness Partner\n"
        f"que cet email/ID est bien ton filleul.\n\n"
        f"👇 Puis clique :"
    )
    try:
        await ctx.bot.send_message(chat_id=ADMIN_ID, text=notif,
                                   parse_mode="Markdown", reply_markup=kb_admin)
    except Exception as e:
        log.error(f"Notif admin: {e}")
    return ConversationHandler.END

# ── PAIEMENT ROBOTS ──────────────────────────────────────

async def h_capture_paiement(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Reçoit la capture d'écran de paiement"""
    lang = ctx.user_data.get("l","fr")
    uid  = update.effective_user.id
    user = ctx.user_data.get("u","—")

    await update.message.reply_text(g(lang,"capture_recue"), parse_mode="Markdown")

    # Transférer la capture à l'admin avec boutons
    kb_admin = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ CONFIRMER PAIEMENT",  callback_data=f"P_ok_{uid}"),
        InlineKeyboardButton("❌ REJETER PAIEMENT",    callback_data=f"P_no_{uid}"),
    ]])
    try:
        await ctx.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"💳 *PREUVE DE PAIEMENT REÇUE*\n\n"
                f"📱 @{user} | 🆔 `{uid}`\n"
                f"📅 {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n"
                f"💰 Montant attendu : *200 USD — VIP Robots*\n\n"
                f"📸 Capture ci-dessous ↓\n\n"
                f"👇 Confirme ou rejette :"
            ),
            parse_mode="Markdown"
        )
        # Transférer la photo/document
        if update.message.photo:
            await ctx.bot.send_photo(chat_id=ADMIN_ID,
                                     photo=update.message.photo[-1].file_id,
                                     reply_markup=kb_admin)
        elif update.message.document:
            await ctx.bot.send_document(chat_id=ADMIN_ID,
                                        document=update.message.document.file_id,
                                        reply_markup=kb_admin)
        else:
            await ctx.bot.send_message(chat_id=ADMIN_ID,
                                       text="⚠️ Pas d'image reçue.",
                                       reply_markup=kb_admin)
    except Exception as e:
        log.error(f"Transfert capture admin: {e}")

    return ConversationHandler.END

# ═══════════════════════════════════════════════════════
# ADMIN — VALIDER / REJETER
# ═══════════════════════════════════════════════════════

async def cb_admin_signal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("⛔ Non autorisé.", show_alert=True); return
    await q.answer()
    parts = q.data.split("_"); action = parts[1]; uid = int(parts[2])

    if action == "ok":
        d = approve_signal(uid)
        if not d: await q.edit_message_text("⚠️ Introuvable. Déjà traité ?"); return
        lang = d.get("lang","fr")
        try:
            await ctx.bot.send_message(chat_id=uid, text=g(lang,"valide_signal"),
                                       parse_mode=None, disable_web_page_preview=False)
            await q.edit_message_text(
                f"✅ *Accès VIP accordé !*\n\n👤 {d.get('nom')} (@{d.get('username')})\n"
                f"🏦 {d.get('exness_id')}\nLien VIP Signaux envoyé ✅",
                parse_mode="Markdown")
        except Exception as e: await q.edit_message_text(f"⚠️ Erreur envoi : {e}")

    elif action == "no":
        d = reject_member(uid)
        if not d: await q.edit_message_text("⚠️ Introuvable. Déjà traité ?"); return
        lang = d.get("lang","fr")
        try:
            await ctx.bot.send_message(chat_id=uid,
                                       text=g(lang,"rejete", exid=d.get("exness_id","?")),
                                       parse_mode="Markdown", disable_web_page_preview=True)
            await q.edit_message_text(
                f"❌ *Rejeté*\n\n👤 {d.get('nom')} (@{d.get('username')})\nClient informé.",
                parse_mode="Markdown")
        except Exception as e: await q.edit_message_text(f"⚠️ Erreur envoi : {e}")

async def cb_admin_paiement(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("⛔ Non autorisé.", show_alert=True); return
    await q.answer()
    parts = q.data.split("_"); action = parts[1]; uid = int(parts[2])

    if action == "ok":
        d = approve_robot(uid)
        lang = d.get("lang","fr") if d else "fr"
        try:
            await ctx.bot.send_message(chat_id=uid, text=g(lang,"valide_robot"),
                                       parse_mode="Markdown", disable_web_page_preview=True)
            await q.edit_message_text(
                f"✅ *Paiement confirmé — Accès VIP Robots accordé !*\n🆔 {uid}", parse_mode="Markdown")
        except Exception as e: await q.edit_message_text(f"⚠️ Erreur : {e}")

    elif action == "no":
        d = reject_payment(uid)
        lang = d.get("lang","fr") if d else "fr"
        try:
            await ctx.bot.send_message(chat_id=uid, text=g(lang,"paiement_rejete"),
                                       parse_mode="Markdown")
            await q.edit_message_text(f"❌ *Paiement rejeté*\n🆔 {uid}", parse_mode="Markdown")
        except Exception as e: await q.edit_message_text(f"⚠️ Erreur : {e}")

# ═══════════════════════════════════════════════════════
# COMMANDES ADMIN
# ═══════════════════════════════════════════════════════

async def cmd_robots(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Commande pour accéder directement à l'option robots"""
    uid = update.effective_user.id
    lang = ctx.user_data.get("l","fr")
    ctx.user_data["offre"] = "robots"
    ctx.user_data["u"] = update.effective_user.username or str(uid)
    save_pending_payment(uid, {"username": ctx.user_data["u"], "lang": lang,
                               "user_id": uid, "offre": "robots"})
    await update.message.reply_text(g(lang,"paiement_instructions"), parse_mode="Markdown")
    return S_ATTENTE_PAIEMENT

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    await update.message.reply_text(
        f"📊 *Stats LeMentorFx Bot*\n\n"
        f"✅ VIP Signaux validés : *{len([x for x in db.get('valides',{}).values() if x.get('statut')=='validé_signaux'])}*\n"
        f"🤖 VIP Robots validés : *{len([x for x in db.get('valides',{}).values() if x.get('statut')=='validé_robots'])}*\n"
        f"⏳ En attente signaux : *{len(db.get('attente',{}))}*\n"
        f"💳 En attente paiement : *{len(db.get('attente_paiement',{}))}*\n"
        f"❌ Rejetés : *{len(db.get('rejetes',{}))}*\n"
        f"🏦 IDs Exness enregistrés : *{len(db.get('exness_ids',[]))}*",
        parse_mode="Markdown")

async def cmd_attente(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    items = list(db.get("attente",{}).values())
    if not items: await update.message.reply_text("✅ Aucune demande en attente."); return
    lines = [f"• *{x.get('nom','?')}* | {x.get('pays','?')} | `{x.get('email','?')}` | ID:{x.get('exness_id','?')} | @{x.get('username','?')}" for x in items]
    await update.message.reply_text(f"⏳ *{len(items)} demande(s) :*\n\n"+"\n".join(lines), parse_mode="Markdown")

async def cmd_liste(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    items = list(db.get("valides",{}).values())[-15:]
    if not items: await update.message.reply_text("Aucun membre encore."); return
    lines = [f"• *{x.get('nom','?')}* | {x.get('pays','?')} | {x.get('exness_id','?')} | _{x.get('statut','?')}_" for x in items]
    await update.message.reply_text("📋 *Membres :*\n\n"+"\n".join(lines), parse_mode="Markdown")

async def cmd_bloquer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not ctx.args: await update.message.reply_text("Usage: /bloquer [user_id]"); return
    try:
        uid=int(ctx.args[0]); db=load_db()
        if uid not in db["bloques"]: db["bloques"].append(uid); save_db(db)
        await update.message.reply_text(f"✅ User {uid} bloqué.")
    except: await update.message.reply_text("❌ ID invalide.")

async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    await update.message.reply_text(g(lang,"cancel"), parse_mode="Markdown")
    return ConversationHandler.END

async def msg_other(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 S'inscrire / Register", callback_data="RESTART")]])
    await update.message.reply_text(
        "👋 Tape /start ou appuie sur le bouton ci-dessous.\nType /start or press the button below.",
        reply_markup=kb)

async def cb_restart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear()
    ctx.user_data["u"] = update.effective_user.username or str(update.effective_user.id)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🇫🇷 Français", callback_data="L_fr"),
        InlineKeyboardButton("🇬🇧 English",  callback_data="L_en"),
    ]])
    await q.edit_message_text("🌍 *Choisis ta langue / Choose your language:*",
                              parse_mode="Markdown", reply_markup=kb)
    return S_LANG

async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start",   "🚀 Démarrer"),
        BotCommand("robots",  "🤖 Accès VIP Robots — 200 USD"),
        BotCommand("annuler", "❌ Annuler"),
    ])

# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start",   cmd_start),
            CommandHandler("robots",  cmd_robots),
            CallbackQueryHandler(cb_restart, pattern="^RESTART$"),
        ],
        states={
            S_LANG:             [CallbackQueryHandler(cb_lang,    pattern="^L_")],
            S_MENU:             [CallbackQueryHandler(cb_menu,    pattern="^(M_|GO)")],
            S_NOM:              [MessageHandler(filters.TEXT & ~filters.COMMAND, h_nom)],
            S_PAYS:             [MessageHandler(filters.TEXT & ~filters.COMMAND, h_pays)],
            S_EMAIL:            [MessageHandler(filters.TEXT & ~filters.COMMAND, h_email)],
            S_EXQ:              [CallbackQueryHandler(cb_exq,     pattern="^EX_")],
            S_EXID:             [MessageHandler(filters.TEXT & ~filters.COMMAND, h_exid)],
            S_CONFIRM:          [CallbackQueryHandler(cb_confirm, pattern="^C_")],
            S_ATTENTE_PAIEMENT: [MessageHandler(filters.PHOTO | filters.Document.ALL, h_capture_paiement)],
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
    app.add_handler(CommandHandler("bloquer", cmd_bloquer))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_other))

    print("✅ LeMentorFx Bot V3 démarré — Signaux + Robots + Paiement")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
