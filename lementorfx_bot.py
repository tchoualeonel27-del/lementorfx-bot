import logging, json, os, re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)

TOKEN       = os.environ.get("BOT_TOKEN", "7575039426:AAEoTVawvW6uLOZf3b9C5xMcxjfy8GXbBmk")
ADMIN_ID    = 7412212489
CANAL_VIP   = "https://t.me/+HJ9qJhRZ7mg0MmFk"
CANAL_PUB   = "https://t.me/lementorforexgroup"
EXNESS_LINK = "https://one.exnessonelink.com/a/do7n4lz3on"
SUPPORT_1   = "https://t.me/salomonryn"
SUPPORT_2   = "https://t.me/lementorfx"
DB_FILE     = "membres.json"

(S_LANG, S_MENU,
 S_NOM, S_PRENOM, S_PAYS, S_VILLE,
 S_TEL, S_EMAIL, S_NIVEAU, S_OBJECTIF,
 S_EXQ, S_EXID, S_CONFIRM,
 S_PAIEMENT) = range(14)

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════
# BASE DE DONNÉES
# ══════════════════════════════════════════════════════

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {
        "valides_ib": {}, "valides_pay": {},
        "attente_ib": {}, "attente_pay": {},
        "rejetes": {}, "bloques": [],
        "exness_ids": [], "emails": []
    }

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def is_blocked(u):  return u in load_db().get("bloques", [])
def eid_used(e):    return e in load_db().get("exness_ids", [])
def mail_used(e):   return e.lower() in [x.lower() for x in load_db().get("emails", [])]
def is_validated(u):
    db = load_db(); k = str(u)
    return k in db.get("valides_ib", {}) or k in db.get("valides_pay", {})

def save_pending_ib(uid, d):
    db = load_db()
    db["attente_ib"][str(uid)] = {**d, "date": datetime.now().isoformat(), "type": "IB_Exness"}
    save_db(db)

def save_pending_pay(uid, d):
    db = load_db()
    db["attente_pay"][str(uid)] = {**d, "date": datetime.now().isoformat(), "type": "Paiement_100USD"}
    save_db(db)

def approve_ib(uid):
    db = load_db(); k = str(uid)
    if k not in db["attente_ib"]: return None
    d = db["attente_ib"].pop(k); d["statut"] = "valide_IB"
    db["valides_ib"][k] = d
    if d.get("exness_id"): db["exness_ids"].append(d["exness_id"])
    if d.get("email"):     db["emails"].append(d["email"].lower())
    save_db(db); return d

def approve_pay(uid):
    db = load_db(); k = str(uid)
    if k not in db["attente_pay"]: return None
    d = db["attente_pay"].pop(k); d["statut"] = "valide_Paiement"
    db["valides_pay"][k] = d
    if d.get("email"): db["emails"].append(d["email"].lower())
    save_db(db); return d

def reject_ib(uid):
    db = load_db(); k = str(uid)
    if k not in db["attente_ib"]: return None
    d = db["attente_ib"].pop(k); d["statut"] = "rejete"
    db["rejetes"][k + "_ib"] = d; save_db(db); return d

def reject_pay(uid):
    db = load_db(); k = str(uid)
    if k not in db["attente_pay"]: return None
    d = db["attente_pay"].pop(k); d["statut"] = "rejete_pay"
    db["rejetes"][k + "_pay"] = d; save_db(db); return d

def ban_member(uid):
    db = load_db()
    if uid not in db["bloques"]:
        db["bloques"].append(uid)
    save_db(db)

# ══════════════════════════════════════════════════════
# TEXTES FR / EN
# ══════════════════════════════════════════════════════

T = {
"fr": {

"accueil": (
    "Bienvenue chez LeMentorFx !\n\n"
    "Je suis l'assistant officiel de @lementorfx\n"
    "Partenaire IB Exness · Signaux XAU/USD PHANTOM TRAP\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Ce que tu obtiens en rejoignant :\n\n"
    "📡 Signaux XAU/USD en temps réel (PHANTOM TRAP)\n"
    "🎓 Formation de base en trading incluse\n"
    "🧠 Stratégies SMC / ICT expliquées\n"
    "🤝 Accompagnement personnalisé\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "2 options pour rejoindre :\n\n"
    "Option 1 — GRATUIT\n"
    "Ouvre un compte Exness via notre lien de parrainage\n\n"
    "Option 2 — 100 USD à vie\n"
    "Accès direct, sans condition de broker\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Quelle option te convient ?"
),

"apercu_pub": (
    "Avant de commencer, jette un oeil\n"
    "à nos résultats en temps réel :\n\n"
    f"📊 Canal public gratuit :\n{CANAL_PUB}\n\n"
    "Tu y trouveras 1 signal gratuit par jour\n"
    "et nos résultats récents.\n\n"
    "Quand tu es prêt, reviens choisir ton option !"
),

"choix_ib": (
    "Option 1 — ACCÈS GRATUIT via Exness\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Ouvre ton compte Exness via le lien officiel\n"
    "de @lementorfx. Complète le formulaire.\n"
    "@lementorfx vérifie ton parrainage\n"
    "et t'envoie l'accès immédiatement.\n\n"
    "100% gratuit · Aucun frais caché\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Appuie sur Commencer l'inscription"
),

"choix_pay": (
    "Option 2 — ACCÈS 100 USD à vie\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Accès immédiat au groupe privé de signaux.\n"
    "Aucune condition de broker. Paiement unique.\n\n"
    "Paiement unique · Accès à vie · Toutes paires\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Appuie sur Voir les détails de paiement"
),

"nom":     "ÉTAPE 1/9 — Nom\n\nQuel est ton nom de famille ?",
"prenom":  "ÉTAPE 2/9 — Prénom\n\nQuel est ton prénom ?",
"pays":    "ÉTAPE 3/9 — Pays\n\nDans quel pays es-tu ?\nEx : Cameroun, France, Sénégal...",
"ville":   "ÉTAPE 4/9 — Ville\n\nDans quelle ville ?\nEx : Yaoundé, Paris, Dakar...",
"tel":     "ÉTAPE 5/9 — WhatsApp / Téléphone\n\nTon numéro ?\nEx : +237 6XX XXX XXX",
"email":   "ÉTAPE 6/9 — Email\n\nTon adresse email ?\nEx : nom@gmail.com",
"niveau":  "ÉTAPE 7/9 — Niveau en trading",
"objectif":"ÉTAPE 8/9 — Objectif\n\nQuel est ton objectif principal avec le trading ?\nEx : revenus complémentaires, liberté financière...",
"exq":     "ÉTAPE 9/9 — Compte Exness\n\nAs-tu un compte Exness ?",
"exid":    (
    "Ton ID Exness (7 à 9 chiffres)\n\n"
    "Comment le trouver :\n"
    "1. Va sur exness.com et connecte-toi\n"
    "2. Clique sur ton Profil (haut à droite)\n"
    "3. L'ID s'affiche sur le tableau de bord\n\n"
    "Entre ton ID Exness :"
),
"noex": (
    "Pas encore de compte Exness ?\n\n"
    "C'est gratuit et ça prend 3 minutes.\n"
    f"Lien officiel de parrainage :\n{EXNESS_LINK}\n\n"
    "Une fois inscrit, reviens taper /start\n"
    "pour finaliser ton inscription."
),
"ebad":        "Email invalide. Entre une adresse correcte :\nEx : nom@gmail.com",
"edup":        "Cet email est déjà enregistré.\nSi c'est une erreur, contacte le support.",
"idbad":       "ID invalide. L'ID Exness contient 7 à 9 chiffres uniquement. Réessaie :",
"iddup":       "Cet ID Exness est déjà utilisé.\nContacte le support si c'est une erreur.",
"trop_court":  "Réponse trop courte. Réessaie :",

"recap_ib": (
    "RÉCAPITULATIF DE TON INSCRIPTION\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Nom : {nom} {prenom}\n"
    "Pays / Ville : {pays}, {ville}\n"
    "Téléphone : {tel}\n"
    "Email : {email}\n"
    "Niveau : {niveau}\n"
    "Objectif : {objectif}\n"
    "ID Exness : {exid}\n"
    "Telegram : @{user}\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Tout est correct ?"
),

"attente_ib": (
    "Demande envoyée avec succès !\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "@lementorfx vérifie ton ID Exness\n"
    "sur son tableau de bord partenaire.\n\n"
    "Si validé — tu reçois le lien d'accès ici\n"
    "Si non — tu reçois un message explicatif\n\n"
    "Délai : quelques heures maximum\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "En attendant, rejoins notre canal public\n"
    "pour découvrir nos résultats :\n\n"
    f"{CANAL_PUB}\n\n"
    "1 signal gratuit par jour t'y attend !"
),

"paiement_info": (
    "PAIEMENT — ACCÈS VIP 100 USD\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Binance Pay\n"
    "ID : 556807688\n\n"
    "Binance USDT TRC20\n"
    "TEWKJtPsn4RsrEt2kiLNCDMUVKLGQ6RLJb\n\n"
    "Binance BEP20\n"
    "0xc28a3818c31fc79bddb080d41d40771b9f25f962\n\n"
    "PayPal\n"
    "capor51@gmail.com\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Montant exact : 100 USD\n\n"
    "Avant de payer, donne-moi :\n"
    "Ton prénom ?"
),

"pay_prenom": "Ton prénom ?",
"pay_email":  "Ton adresse email ?",

"attente_pay": (
    "Capture reçue ! Merci {nom}\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Ta preuve de paiement est en cours\n"
    "de vérification par @lementorfx.\n\n"
    "Si confirmé — tu reçois ton accès ici\n"
    "Si non — tu reçois un message explicatif\n\n"
    "Délai : quelques heures maximum\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "En attendant, rejoins notre canal public :\n\n"
    f"{CANAL_PUB}\n\n"
    "1 signal gratuit par jour t'y attend !"
),

"valide": (
    "ACCÈS ACCORDÉ ! Bienvenue !\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Ton accès au groupe privé LeMentorFx\n"
    "est maintenant activé !\n\n"
    "Ton lien d'accès :\n\n"
    "{canal}\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Une fois dans le groupe :\n\n"
    "Lis bien le message épinglé avant de commencer.\n"
    "Il contient tout ce qu'il faut savoir\n"
    "pour bien démarrer et profiter pleinement\n"
    "des signaux et de la formation.\n\n"
    "Bon trading et bienvenue dans la famille !\n"
    "@lementorfx"
),

"rejete_ib": (
    "Accès non accordé\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Ton ID Exness {exid} n'a pas été trouvé\n"
    "dans les filleuls de @lementorfx.\n\n"
    "Solutions :\n\n"
    f"Ouvre un nouveau compte Exness :\n{EXNESS_LINK}\n\n"
    "Ou opte pour l'accès à 100 USD\n"
    "en tapant /start et choisissant l'Option 2.\n\n"
    "Support :\n"
    f"{SUPPORT_1}\n{SUPPORT_2}"
),

"rejete_pay": (
    "Paiement non confirmé\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Le paiement n'a pas pu être vérifié.\n\n"
    "Vérifie :\n"
    "Le montant envoyé est bien 100 USD\n"
    "La capture montre bien la confirmation\n"
    "Les coordonnées de paiement\n\n"
    "Tape /start pour réessayer\n"
    "ou contacte le support :\n"
    f"{SUPPORT_1}\n{SUPPORT_2}"
),

"support": (
    "Support LeMentorFx\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Pour toute question ou problème,\n"
    "contacte directement @lementorfx :\n\n"
    f"{SUPPORT_1}\n{SUPPORT_2}"
),

"deja_valide": (
    "Tu es déjà membre validé !\n\n"
    "Si tu rencontres un problème,\n"
    "contacte le support :\n"
    f"{SUPPORT_1}\n{SUPPORT_2}"
),

"bloque": "Accès refusé. / Access denied.",
"cancel": "Inscription annulée. Tape /start pour recommencer.",
},

# ══════════════════════════════════════════════════════
# ENGLISH
# ══════════════════════════════════════════════════════
"en": {

"accueil": (
    "Welcome to LeMentorFx!\n\n"
    "I'm the official assistant of @lementorfx\n"
    "Exness IB Partner · XAU/USD Signals PHANTOM TRAP\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "What you get by joining:\n\n"
    "📡 Real-time XAU/USD signals (PHANTOM TRAP)\n"
    "🎓 Basic trading education included\n"
    "🧠 SMC / ICT strategies explained\n"
    "🤝 Personal coaching\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "2 options to join:\n\n"
    "Option 1 — FREE\n"
    "Open an Exness account via our referral link\n\n"
    "Option 2 — 100 USD lifetime\n"
    "Direct access, no broker condition\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Which option suits you?"
),

"apercu_pub": (
    "Before you begin, take a look\n"
    "at our real-time results:\n\n"
    f"📊 Free public channel:\n{CANAL_PUB}\n\n"
    "You'll find 1 free signal per day\n"
    "and our recent results.\n\n"
    "When you're ready, come back and choose your option!"
),

"choix_ib": (
    "Option 1 — FREE ACCESS via Exness\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Open your Exness account via @lementorfx's\n"
    "official link. Fill out the registration form.\n"
    "@lementorfx verifies your referral\n"
    "and sends you access immediately.\n\n"
    "100% free · No hidden fees\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Press Start Registration to continue"
),

"choix_pay": (
    "Option 2 — 100 USD LIFETIME ACCESS\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Immediate access to the private signals group.\n"
    "No broker condition. One-time payment.\n\n"
    "One-time payment · Lifetime access\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Press View Payment Details to continue"
),

"nom":     "STEP 1/9 — Last Name\n\nWhat is your last name?",
"prenom":  "STEP 2/9 — First Name\n\nWhat is your first name?",
"pays":    "STEP 3/9 — Country\n\nWhich country are you in?\nEx: Nigeria, UK, USA...",
"ville":   "STEP 4/9 — City\n\nWhich city?\nEx: Lagos, London, New York...",
"tel":     "STEP 5/9 — WhatsApp / Phone\n\nYour number?\nEx: +234 XXX XXX XXXX",
"email":   "STEP 6/9 — Email\n\nYour email address?\nEx: name@gmail.com",
"niveau":  "STEP 7/9 — Trading Level",
"objectif":"STEP 8/9 — Goal\n\nWhat is your main trading goal?\nEx: extra income, financial freedom...",
"exq":     "STEP 9/9 — Exness Account\n\nDo you have an Exness account?",
"exid":    (
    "Your Exness ID (7 to 9 digits)\n\n"
    "How to find it:\n"
    "1. Go to exness.com and log in\n"
    "2. Click your Profile (top right)\n"
    "3. ID appears on the dashboard\n\n"
    "Enter your Exness ID:"
),
"noex": (
    "No Exness account yet?\n\n"
    "It's free and takes 3 minutes.\n"
    f"Official referral link:\n{EXNESS_LINK}\n\n"
    "Once registered, come back and type /start\n"
    "to complete your registration."
),
"ebad":       "Invalid email. Enter a valid address:\nEx: name@gmail.com",
"edup":       "This email is already registered.\nContact support if this is an error.",
"idbad":      "Invalid ID. Exness ID contains 7 to 9 digits only. Try again:",
"iddup":      "This Exness ID is already used.\nContact support if this is an error.",
"trop_court": "Answer too short. Try again:",

"recap_ib": (
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

"attente_ib": (
    "Request submitted successfully!\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "@lementorfx is verifying your Exness ID\n"
    "on his partner dashboard.\n\n"
    "If validated — you receive access here\n"
    "If not — you receive an explanatory message\n\n"
    "Delay: a few hours maximum\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "In the meantime, join our public channel\n"
    "to discover our results:\n\n"
    f"{CANAL_PUB}\n\n"
    "1 free signal per day is waiting for you!"
),

"paiement_info": (
    "PAYMENT — VIP ACCESS 100 USD\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Binance Pay\n"
    "ID: 556807688\n\n"
    "Binance USDT TRC20\n"
    "TEWKJtPsn4RsrEt2kiLNCDMUVKLGQ6RLJb\n\n"
    "Binance BEP20\n"
    "0xc28a3818c31fc79bddb080d41d40771b9f25f962\n\n"
    "PayPal\n"
    "capor51@gmail.com\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Exact amount: 100 USD\n\n"
    "Before paying, please tell me:\n"
    "Your first name?"
),

"pay_prenom": "Your first name?",
"pay_email":  "Your email address?",

"attente_pay": (
    "Screenshot received! Thank you {nom}\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Your payment proof is being verified\n"
    "by @lementorfx.\n\n"
    "If confirmed — you receive access here\n"
    "If not — you receive an explanatory message\n\n"
    "Delay: a few hours maximum\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "In the meantime, join our public channel:\n\n"
    f"{CANAL_PUB}\n\n"
    "1 free signal per day is waiting for you!"
),

"valide": (
    "ACCESS GRANTED! Welcome!\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Your access to the private\n"
    "LeMentorFx group is now active!\n\n"
    "Your access link:\n\n"
    "{canal}\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Once in the group:\n\n"
    "Please read the pinned message carefully\n"
    "before you start. It contains everything\n"
    "you need to know to get the most\n"
    "out of the signals and training.\n\n"
    "Happy trading and welcome to the family!\n"
    "@lementorfx"
),

"rejete_ib": (
    "Access not approved\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Exness ID {exid} was not found\n"
    "in @lementorfx's referrals.\n\n"
    "Solutions:\n\n"
    f"Open a new Exness account:\n{EXNESS_LINK}\n\n"
    "Or choose the 100 USD access option\n"
    "by typing /start and selecting Option 2.\n\n"
    "Support:\n"
    f"{SUPPORT_1}\n{SUPPORT_2}"
),

"rejete_pay": (
    "Payment not confirmed\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Your payment could not be verified.\n\n"
    "Check:\n"
    "Amount sent is exactly 100 USD\n"
    "Screenshot clearly shows the confirmation\n"
    "Payment details are correct\n\n"
    "Type /start to try again\n"
    "or contact support:\n"
    f"{SUPPORT_1}\n{SUPPORT_2}"
),

"support": (
    "LeMentorFx Support\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "For any question or issue,\n"
    "contact @lementorfx directly:\n\n"
    f"{SUPPORT_1}\n{SUPPORT_2}"
),

"deja_valide": (
    "You are already a validated member!\n\n"
    "If you have a problem,\n"
    "contact support:\n"
    f"{SUPPORT_1}\n{SUPPORT_2}"
),

"bloque": "Accès refusé. / Access denied.",
"cancel": "Registration cancelled. Type /start to restart.",
}}

def g(lang, key, **kw):
    s = T.get(lang, T["fr"]).get(key, "")
    return s.format(**kw) if kw else s

# ══════════════════════════════════════════════════════
# CLAVIERS
# ══════════════════════════════════════════════════════

def kb_lang():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Francais", callback_data="L_fr"),
        InlineKeyboardButton("English",  callback_data="L_en"),
    ]])

def kb_menu(lang):
    a = "Voir nos resultats (gratuit)" if lang=="fr" else "See our results (free)"
    b = "Option 1 — Gratuit via Exness" if lang=="fr" else "Option 1 — Free via Exness"
    c = "Option 2 — 100 USD a vie" if lang=="fr" else "Option 2 — 100 USD lifetime"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👀 {a}", callback_data="M_apercu")],
        [InlineKeyboardButton(f"FREE {b}", callback_data="M_ib")],
        [InlineKeyboardButton(f"💳 {c}", callback_data="M_pay")],
    ])

def kb_back(lang):
    s = "Retour au menu" if lang=="fr" else "Back to menu"
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"← {s}", callback_data="M_back")]])

def kb_start_ib(lang):
    a = "Commencer l'inscription" if lang=="fr" else "Start Registration"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🚀 {a}", callback_data="GO_IB")],
        [InlineKeyboardButton("← Retour / Back", callback_data="M_back")],
    ])

def kb_start_pay(lang):
    a = "Voir les details de paiement" if lang=="fr" else "View Payment Details"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💳 {a}", callback_data="GO_PAY")],
        [InlineKeyboardButton("← Retour / Back", callback_data="M_back")],
    ])

def kb_exq(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Oui / Yes",              callback_data="EX_oui")],
        [InlineKeyboardButton("En cours / In progress", callback_data="EX_oui")],
        [InlineKeyboardButton("Pas encore / Not yet",   callback_data="EX_non")],
    ])

def kb_niveau(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Debutant / Beginner",         callback_data="NIV_deb")],
        [InlineKeyboardButton("Intermediaire / Intermediate",callback_data="NIV_int")],
        [InlineKeyboardButton("Avance / Advanced",           callback_data="NIV_ava")],
        [InlineKeyboardButton("Expert",                      callback_data="NIV_exp")],
    ])

def kb_confirm(lang):
    c = "Confirmer / Confirm"
    e = "Corriger / Edit"
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"✅ {c}", callback_data="C_ok"),
        InlineKeyboardButton(f"✏️ {e}", callback_data="C_edit"),
    ]])

def kb_support(lang):
    s = "Contacter le support" if lang=="fr" else "Contact support"
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"💬 {s}", callback_data="SUPPORT")]])

def kb_restart(lang):
    s = "Demarrer / Start"
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"🚀 {s}", callback_data="RESTART")]])

# ══════════════════════════════════════════════════════
# FICHE ADMIN
# ══════════════════════════════════════════════════════

def fiche_admin_ib(d, uid):
    return (
        f"NOUVELLE DEMANDE IB EXNESS\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Nom : {d.get('nom','')} {d.get('prenom','')}\n"
        f"Pays / Ville : {d.get('pays','')}, {d.get('ville','')}\n"
        f"Téléphone : {d.get('tel','')}\n"
        f"Email : {d.get('email','')}\n"
        f"Niveau : {d.get('niveau','')}\n"
        f"Objectif : {d.get('objectif','')}\n"
        f"ID Exness : {d.get('exness_id','')}\n"
        f"Telegram : @{d.get('username','')}\n"
        f"User ID : {uid}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Date : {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n\n"
        f"Verifie sur ton espace Exness Partner.\nPuis clique :"
    )

def fiche_admin_pay(d, uid):
    return (
        f"PAIEMENT 100 USD\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Nom : {d.get('nom','')}\n"
        f"Email : {d.get('email','')}\n"
        f"Telegram : @{d.get('username','')}\n"
        f"User ID : {uid}\n"
        f"Date : {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n\n"
        f"Capture de paiement ci-dessous.\nPuis clique :"
    )

# ══════════════════════════════════════════════════════
# CONVERSATION
# ══════════════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_blocked(uid):
        await update.message.reply_text(g("fr","bloque")); return ConversationHandler.END
    if is_validated(uid):
        lang = ctx.user_data.get("l","fr")
        await update.message.reply_text(g(lang,"deja_valide"), reply_markup=kb_support(lang))
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

    if q.data == "M_apercu":
        await q.edit_message_text(g(lang,"apercu_pub"),
                                  reply_markup=kb_back(lang),
                                  disable_web_page_preview=True)
        return S_MENU
    elif q.data == "M_back":
        await q.edit_message_text(g(lang,"accueil"), reply_markup=kb_menu(lang))
        return S_MENU
    elif q.data == "M_ib":
        ctx.user_data["offre"] = "ib"
        await q.edit_message_text(g(lang,"choix_ib"), reply_markup=kb_start_ib(lang))
        return S_MENU
    elif q.data == "M_pay":
        ctx.user_data["offre"] = "pay"
        await q.edit_message_text(g(lang,"choix_pay"), reply_markup=kb_start_pay(lang))
        return S_MENU
    elif q.data == "GO_IB":
        ctx.user_data["offre"] = "ib"
        await q.edit_message_text(g(lang,"nom"))
        return S_NOM
    elif q.data == "GO_PAY":
        ctx.user_data["offre"] = "pay"
        await q.edit_message_text(g(lang,"paiement_info"), disable_web_page_preview=True)
        return S_PAIEMENT
    elif q.data == "SUPPORT":
        await q.edit_message_text(g(lang,"support"), disable_web_page_preview=True)
        return ConversationHandler.END
    return S_MENU

# ── INSCRIPTION IB ────────────────────────────────────

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
        "NIV_deb": "Debutant / Beginner",
        "NIV_int": "Intermediaire / Intermediate",
        "NIV_ava": "Avance / Advanced",
        "NIV_exp": "Expert"
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
        g(lang,"recap_ib",
          nom=ctx.user_data.get("nom",""), prenom=ctx.user_data.get("prenom",""),
          pays=ctx.user_data.get("pays",""), ville=ctx.user_data.get("ville",""),
          tel=ctx.user_data.get("tel",""), email=ctx.user_data.get("email",""),
          niveau=ctx.user_data.get("niveau",""), objectif=ctx.user_data.get("objectif",""),
          exid=v, user=ctx.user_data.get("u","")),
        reply_markup=kb_confirm(lang))
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
        "lang":      lang, "user_id": uid,
    }
    save_pending_ib(uid, d)
    await q.edit_message_text(g(lang,"attente_ib"), disable_web_page_preview=True)

    kb_admin = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ VALIDER ACCES", callback_data=f"AIB_ok_{uid}"),
        InlineKeyboardButton("❌ REJETER",       callback_data=f"AIB_no_{uid}"),
    ]])
    try:
        await ctx.bot.send_message(chat_id=ADMIN_ID,
            text=fiche_admin_ib(d, uid), reply_markup=kb_admin)
    except Exception as e:
        log.error(f"Notif admin IB: {e}")
    return ConversationHandler.END

# ── PAIEMENT ─────────────────────────────────────────

async def h_pay_nom(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    v = update.message.text.strip()
    if len(v) < 2: await update.message.reply_text(g(lang,"trop_court")); return S_PAIEMENT
    ctx.user_data["pay_nom"] = v
    await update.message.reply_text(g(lang,"pay_email"))
    return S_PAIEMENT

async def h_capture(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    uid  = update.effective_user.id
    user = ctx.user_data.get("u","—")
    nom  = ctx.user_data.get("pay_nom","—")
    email= ctx.user_data.get("pay_email","—")

    d = {"nom": nom, "email": email, "username": user, "lang": lang, "user_id": uid}
    save_pending_pay(uid, d)

    await update.message.reply_text(g(lang,"attente_pay", nom=nom),
                                    disable_web_page_preview=True)

    kb_admin = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ CONFIRMER PAIEMENT", callback_data=f"APAY_ok_{uid}"),
        InlineKeyboardButton("❌ REJETER",             callback_data=f"APAY_no_{uid}"),
    ]])
    try:
        await ctx.bot.send_message(chat_id=ADMIN_ID, text=fiche_admin_pay(d, uid))
        if update.message.photo:
            await ctx.bot.send_photo(chat_id=ADMIN_ID,
                photo=update.message.photo[-1].file_id, reply_markup=kb_admin)
        elif update.message.document:
            await ctx.bot.send_document(chat_id=ADMIN_ID,
                document=update.message.document.file_id, reply_markup=kb_admin)
        else:
            await ctx.bot.send_message(chat_id=ADMIN_ID,
                text="Aucune image recue.", reply_markup=kb_admin)
    except Exception as e:
        log.error(f"Notif admin paiement: {e}")
    return ConversationHandler.END

# Gestion du flux paiement (nom → email → capture)
_pay_step = {}  # uid → step

async def h_paiement_texte(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    uid  = update.effective_user.id
    v    = update.message.text.strip()

    if "pay_nom" not in ctx.user_data:
        if len(v) < 2:
            await update.message.reply_text(g(lang,"trop_court")); return S_PAIEMENT
        ctx.user_data["pay_nom"] = v
        await update.message.reply_text(g(lang,"pay_email"))
        return S_PAIEMENT
    elif "pay_email" not in ctx.user_data:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v.lower()):
            await update.message.reply_text(g(lang,"ebad")); return S_PAIEMENT
        ctx.user_data["pay_email"] = v.lower()
        s = "Parfait ! Effectue maintenant le paiement et envoie ici ta capture d'ecran de confirmation." if lang=="fr" else "Perfect! Now make the payment and send your payment screenshot here."
        await update.message.reply_text(s)
        return S_PAIEMENT
    else:
        s = "Envoie une image (capture d'ecran), pas du texte." if lang=="fr" else "Please send an image (screenshot), not text."
        await update.message.reply_text(s)
        return S_PAIEMENT

# ══════════════════════════════════════════════════════
# ADMIN — VALIDER / REJETER
# ══════════════════════════════════════════════════════

async def cb_admin_ib(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("Acces refuse.", show_alert=True); return
    await q.answer()
    parts = q.data.split("_"); action = parts[1]; uid = int(parts[2])

    if action == "ok":
        d = approve_ib(uid)
        if not d: await q.edit_message_text("Introuvable. Deja traite ?"); return
        lang = d.get("lang","fr")
        try:
            await ctx.bot.send_message(chat_id=uid, text=g(lang,"valide", canal=CANAL_VIP),
                                       disable_web_page_preview=True)
            await q.edit_message_text(
                f"VALIDE IB\n{d.get('nom','')} {d.get('prenom','')} | @{d.get('username','')} | ID:{d.get('exness_id','')}\nAcces envoye.")
        except Exception as e: await q.edit_message_text(f"Erreur: {e}")

    elif action == "no":
        d = reject_ib(uid)
        if not d: await q.edit_message_text("Introuvable. Deja traite ?"); return
        lang = d.get("lang","fr")
        try:
            await ctx.bot.send_message(chat_id=uid,
                text=g(lang,"rejete_ib", exid=d.get("exness_id","?")),
                disable_web_page_preview=True)
            await q.edit_message_text(f"REJETE IB\n@{d.get('username','')} | ID:{d.get('exness_id','')}")
        except Exception as e: await q.edit_message_text(f"Erreur: {e}")

async def cb_admin_pay(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("Acces refuse.", show_alert=True); return
    await q.answer()
    parts = q.data.split("_"); action = parts[1]; uid = int(parts[2])

    if action == "ok":
        d = approve_pay(uid)
        if not d: await q.edit_message_text("Introuvable. Deja traite ?"); return
        lang = d.get("lang","fr")
        try:
            await ctx.bot.send_message(chat_id=uid, text=g(lang,"valide", canal=CANAL_VIP),
                                       disable_web_page_preview=True)
            try: await q.edit_message_caption(caption=f"PAIEMENT VALIDE | uid {uid}")
            except: await q.edit_message_text(f"PAIEMENT VALIDE\n@{d.get('username','')} | Acces envoye.")
        except Exception as e: await q.edit_message_text(f"Erreur: {e}")

    elif action == "no":
        d = reject_pay(uid)
        if not d: await q.edit_message_text("Introuvable. Deja traite ?"); return
        lang = d.get("lang","fr")
        try:
            await ctx.bot.send_message(chat_id=uid, text=g(lang,"rejete_pay"))
            try: await q.edit_message_caption(caption=f"PAIEMENT REJETE | uid {uid}")
            except: await q.edit_message_text(f"PAIEMENT REJETE\n@{d.get('username','')}")
        except Exception as e: await q.edit_message_text(f"Erreur: {e}")

# ══════════════════════════════════════════════════════
# COMMANDES ADMIN
# ══════════════════════════════════════════════════════

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    await update.message.reply_text(
        f"STATS LeMentorFx Bot\n\n"
        f"Membres IB valides : {len(db.get('valides_ib',{}))}\n"
        f"Membres Paiement valides : {len(db.get('valides_pay',{}))}\n"
        f"En attente IB : {len(db.get('attente_ib',{}))}\n"
        f"En attente Paiement : {len(db.get('attente_pay',{}))}\n"
        f"Rejetes : {len(db.get('rejetes',{}))}\n"
        f"Bloques : {len(db.get('bloques',[]))}\n"
        f"Total membres : {len(db.get('valides_ib',{}))+len(db.get('valides_pay',{}))}")

async def cmd_liste(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    lines = []
    for k, v in list(db.get("valides_ib",{}).items())[-10:]:
        lines.append(f"IB | {v.get('nom','')} {v.get('prenom','')} | @{v.get('username','')} | {v.get('exness_id','')}")
    for k, v in list(db.get("valides_pay",{}).items())[-10:]:
        lines.append(f"PAY | {v.get('nom','')} | @{v.get('username','')} | {v.get('email','')}")
    if not lines: await update.message.reply_text("Aucun membre encore."); return
    await update.message.reply_text("MEMBRES VALIDES (20 derniers):\n\n" + "\n".join(lines))

async def cmd_attente(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    lines = []
    for k, v in db.get("attente_ib",{}).items():
        lines.append(f"IB | {v.get('nom','')} {v.get('prenom','')} | @{v.get('username','')} | {v.get('exness_id','')} | uid:{k}")
    for k, v in db.get("attente_pay",{}).items():
        lines.append(f"PAY | {v.get('nom','')} | @{v.get('username','')} | uid:{k}")
    if not lines: await update.message.reply_text("Aucune demande en attente."); return
    await update.message.reply_text(f"{len(lines)} demande(s):\n\n" + "\n".join(lines))

async def cmd_ban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not ctx.args: await update.message.reply_text("Usage: /ban [user_id]"); return
    try:
        uid = int(ctx.args[0]); ban_member(uid)
        await update.message.reply_text(f"User {uid} banni.")
    except: await update.message.reply_text("ID invalide.")

async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    await update.message.reply_text(g(lang,"cancel"))
    return ConversationHandler.END

async def msg_other(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("l","fr")
    await update.message.reply_text(
        "Tape /start pour commencer.\nType /start to begin.",
        reply_markup=kb_restart(lang))

async def cb_restart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear()
    ctx.user_data["u"] = update.effective_user.username or str(update.effective_user.id)
    await q.edit_message_text("Choisis ta langue / Choose your language:", reply_markup=kb_lang())
    return S_LANG

async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start",   "Rejoindre LeMentorFx"),
        BotCommand("annuler", "Annuler"),
        BotCommand("stats",   "Stats (admin)"),
        BotCommand("liste",   "Liste membres (admin)"),
        BotCommand("attente", "Demandes en attente (admin)"),
        BotCommand("ban",     "Bannir un membre (admin)"),
    ])

# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", cmd_start),
            CallbackQueryHandler(cb_restart, pattern="^RESTART$"),
        ],
        states={
            S_LANG:    [CallbackQueryHandler(cb_lang,    pattern="^L_")],
            S_MENU:    [CallbackQueryHandler(cb_menu,    pattern="^(M_|GO_|SUPPORT)")],
            S_NOM:     [MessageHandler(filters.TEXT & ~filters.COMMAND, h_nom)],
            S_PRENOM:  [MessageHandler(filters.TEXT & ~filters.COMMAND, h_prenom)],
            S_PAYS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, h_pays)],
            S_VILLE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, h_ville)],
            S_TEL:     [MessageHandler(filters.TEXT & ~filters.COMMAND, h_tel)],
            S_EMAIL:   [MessageHandler(filters.TEXT & ~filters.COMMAND, h_email)],
            S_NIVEAU:  [CallbackQueryHandler(cb_niveau,  pattern="^NIV_")],
            S_OBJECTIF:[MessageHandler(filters.TEXT & ~filters.COMMAND, h_objectif)],
            S_EXQ:     [CallbackQueryHandler(cb_exq,     pattern="^EX_")],
            S_EXID:    [MessageHandler(filters.TEXT & ~filters.COMMAND, h_exid)],
            S_CONFIRM: [CallbackQueryHandler(cb_confirm, pattern="^C_")],
            S_PAIEMENT:[
                MessageHandler(filters.PHOTO | filters.Document.ALL, h_capture),
                MessageHandler(filters.TEXT & ~filters.COMMAND, h_paiement_texte),
            ],
        },
        fallbacks=[CommandHandler("annuler", cmd_cancel), CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(cb_admin_ib,  pattern="^AIB_(ok|no)_"))
    app.add_handler(CallbackQueryHandler(cb_admin_pay, pattern="^APAY_(ok|no)_"))
    app.add_handler(CommandHandler("stats",   cmd_stats))
    app.add_handler(CommandHandler("liste",   cmd_liste))
    app.add_handler(CommandHandler("attente", cmd_attente))
    app.add_handler(CommandHandler("ban",     cmd_ban))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_other))

    print("LeMentorFx Bot V5 demarre")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
