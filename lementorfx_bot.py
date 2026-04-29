import logging, json, os, re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)

TOKEN       = "7575039426:AAHnnxr8L7OVdy5TuSsA45rt1l1ID5ubFYc"
ADMIN_ID    = 7412212489
EXNESS_LINK = "https://one.exnessonelink.com/a/do7n4lz3on"
DB_FILE     = "membres_vip.json"

# ═══════════════════════════════════════════════════════
# CANAUX VIP DISPONIBLES
# ═══════════════════════════════════════════════════════

CANAUX = {
    "1": {"nom": "LeMentor Signal",             "emoji": "📡", "lien": "https://t.me/+HJ9qJhRZ7mg0MmFk"},
    "2": {"nom": "Forex Master Mind",           "emoji": "🧠", "lien": "https://t.me/+O-qp8FFqU3M2YzU0"},
    "3": {"nom": "Forex Manipulation",          "emoji": "🎯", "lien": "https://t.me/+nmaRfODrkkJhNTJk"},
    "4": {"nom": "Supply & Demand Intraday",    "emoji": "📊", "lien": "https://t.me/+PNPC0O0teFhiMGY0"},
    "5": {"nom": "Sadeeq FX",                   "emoji": "💎", "lien": "https://t.me/+RM5QY9P10mM1ODRk"},
    "6": {"nom": "ShadTrading Premium",         "emoji": "🔥", "lien": "https://t.me/+Tn3gEe_HOediN2M0"},
}

S_LANG, S_NOM, S_PAYS, S_EMAIL, S_EXQ, S_EXID, S_CHOIX, S_CONFIRM = range(8)

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
# BASE DE DONNÉES
# ═══════════════════════════════════════════════════════

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE,"r",encoding="utf-8") as f: return json.load(f)
    return {"valides":{},"attente":{},"rejetes":{},"exness_ids":[],"emails":[],"bloques":[]}

def save_db(db):
    with open(DB_FILE,"w",encoding="utf-8") as f: json.dump(db,f,ensure_ascii=False,indent=2)

def eid_used(e):     return e in load_db().get("exness_ids",[])
def mail_used(e):    return e.lower() in [x.lower() for x in load_db().get("emails",[])]
def is_blocked(u):   return u in load_db().get("bloques",[])
def is_validated(u): return str(u) in load_db().get("valides",{})

def save_pending(uid, d):
    db = load_db()
    db["attente"][str(uid)] = {**d, "date": datetime.now().isoformat()}
    save_db(db)

def approve(uid):
    db = load_db()
    k = str(uid)
    if k not in db["attente"]: return None
    d = db["attente"].pop(k)
    d["statut"] = "validé"
    db["valides"][k] = d
    if d.get("exness_id"): db["exness_ids"].append(d["exness_id"])
    if d.get("email"):     db["emails"].append(d["email"].lower())
    save_db(db)
    return d

def reject(uid):
    db = load_db()
    k = str(uid)
    if k not in db["attente"]: return None
    d = db["attente"].pop(k)
    d["statut"] = "rejeté"
    db["rejetes"][k] = d
    save_db(db)
    return d

# ═══════════════════════════════════════════════════════
# TEXTES
# ═══════════════════════════════════════════════════════

T = {
"fr": {
"accueil": (
    "👋 *Bonjour et bienvenue !*\n\n"
    "Je suis l'assistant officiel de *LeMentorFx* 🤖\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🏆 *Accès VIP — Ce que tu vas recevoir :*\n\n"
    "📡 Signaux XAU/USD *(PHANTOM TRAP)*\n"
    "🧠 Analyses Forex avancées\n"
    "🎯 Stratégies de manipulation\n"
    "📊 Supply & Demand Intraday\n"
    "💎 Contenus premium exclusifs\n"
    "🔥 Groupes de traders professionnels\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "✅ *Condition unique :* être filleul Exness de @lementorfx\n\n"
    "⏱ Inscription en *2 minutes*\n\n"
    "👇 *Appuie sur Commencer pour démarrer*"
),
"nom":   "━━━━━━━━━━━━━━━━━━━━━\n👤 *ÉTAPE 1 / 5 — Identité*\n━━━━━━━━━━━━━━━━━━━━━\n\nQuel est ton *nom complet* ?\n\n_Ex : Jean-Pierre Mvogo_",
"pays":  "━━━━━━━━━━━━━━━━━━━━━\n🌍 *ÉTAPE 2 / 5 — Pays*\n━━━━━━━━━━━━━━━━━━━━━\n\nDans quel pays es-tu situé ?\n\n_Ex : Cameroun, Sénégal, France..._",
"email": (
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "📧 *ÉTAPE 3 / 5 — Email Exness*\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Entre l'adresse email de ton compte Exness.\n\n"
    "⚠️ Cet email sera vérifié sur le tableau de bord "
    "partenaire de @lementorfx pour confirmer le parrainage.\n\n"
    "_Ex : tonnom@gmail.com_"
),
"ebad":  "❌ *Email invalide.* Entre une adresse correcte :\n_Ex : tonnom@gmail.com_",
"edup":  "❌ *Email déjà enregistré.*\nContacte @lementorfx si c'est une erreur.",
"exq":   (
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🏦 *ÉTAPE 4 / 5 — Compte Exness*\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "As-tu un compte Exness ?\n\n"
    "💡 L'accès VIP est *100% gratuit*.\n"
    "Seule condition : être inscrit via le lien de @lementorfx."
),
"noex":  (
    "⚠️ *Pas encore de compte Exness ?*\n\n"
    "C'est *gratuit* et ça prend 3 minutes !\n\n"
    f"🔗 *Lien officiel de parrainage :*\n{EXNESS_LINK}\n\n"
    "✅ Une fois inscrit, reviens ici et tape /start\n"
    "Je t'accompagnerai pour finaliser ton accès VIP."
),
"exid":  (
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🔢 *ÉTAPE 5 / 5 — ID Exness*\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Entre ton *ID de compte Exness*\n_(numéro de 7 à 9 chiffres)_\n\n"
    "📌 *Comment trouver ton ID :*\n"
    "1️⃣ Va sur *exness.com* → connecte-toi\n"
    "2️⃣ Clique sur ton *Profil* _(haut à droite)_\n"
    "3️⃣ L'ID s'affiche sur le tableau de bord\n\n"
    "👇 Entre ton ID maintenant :"
),
"idbad": "❌ *ID invalide.* L'ID Exness = 7 à 9 chiffres uniquement.\nEssaie encore :",
"iddup": "❌ *Cet ID est déjà utilisé.*\nContacte @lementorfx si c'est une erreur.",
"choix": (
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🏆 *CHOIX DES GROUPES VIP*\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Sélectionne les groupes auxquels tu veux accéder.\n"
    "Tu peux en choisir *un ou plusieurs*, ou *tous* !\n\n"
    "✅ = sélectionné | ☐ = non sélectionné\n\n"
    "👇 Sélectionne puis appuie sur *Confirmer* :"
),
"recap": (
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "📋 *RÉCAPITULATIF*\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "👤 Nom : *{nom}*\n"
    "🌍 Pays : *{pays}*\n"
    "📧 Email : *{email}*\n"
    "🏦 ID Exness : *{exid}*\n"
    "📱 Telegram : @{user}\n\n"
    "🏆 *Groupes demandés :*\n{groupes}\n\n"
    "Tout est correct ?"
),
"attente": (
    "⏳ *Demande envoyée avec succès !*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Tes informations ont été transmises à *@lementorfx*.\n\n"
    "📋 *Prochaines étapes :*\n\n"
    "1️⃣ @lementorfx vérifie ton ID Exness\n"
    "   sur son espace partenaire\n\n"
    "2️⃣ Si tu es bien son filleul ✅\n"
    "   → Tu reçois les liens VIP ici\n\n"
    "3️⃣ Si non ❌\n"
    "   → Tu reçois un message explicatif\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "⏱ *Délai : quelques heures maximum*\n\n"
    "Questions → @lementorfx 💬"
),
"valide": (
    "🎉 *ACCÈS VIP ACCORDÉ !*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Ton parrainage Exness a été *vérifié et validé* ✅\n\n"
    "Bienvenue dans la communauté *LeMentorFx* ! 🔥\n\n"
    "🏆 *Tes accès VIP :*\n\n"
    "{liens}\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "📌 *Pour chaque groupe :*\n"
    "• Clique le lien → Rejoins\n"
    "• Active les notifications 🔔\n"
    "• Lis les règles épinglées\n\n"
    "Bon trading ! 🚀\n"
    "Des questions → @lementorfx"
),
"rejete": (
    "❌ *Accès VIP non accordé*\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "L'ID Exness *{exid}* n'a pas pu être vérifié\n"
    "comme filleul de @lementorfx.\n\n"
    "💡 *Solutions :*\n\n"
    "▸ Pas encore de compte Exness ?\n"
    f"  → Crée-en un : {EXNESS_LINK}\n\n"
    "▸ Compte existant mais pas via notre lien ?\n"
    "  → Contacte @lementorfx pour régulariser\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Une fois réglé, tape /start pour recommencer."
),
"cancel": "❌ Inscription annulée.\nTape /start quand tu veux recommencer.",
"deja":   "✅ Tu es déjà inscrit et validé !\nDes questions → @lementorfx",
},

"en": {
"accueil": (
    "👋 *Hello and welcome!*\n\n"
    "I'm the official assistant of *LeMentorFx* 🤖\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "🏆 *VIP Access — What you'll receive:*\n\n"
    "📡 XAU/USD Signals *(PHANTOM TRAP)*\n"
    "🧠 Advanced Forex analysis\n"
    "🎯 Manipulation strategies\n"
    "📊 Supply & Demand Intraday\n"
    "💎 Exclusive premium content\n"
    "🔥 Professional traders groups\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "✅ *One condition:* be an Exness referral of @lementorfx\n\n"
    "⏱ Registration in *2 minutes*\n\n"
    "👇 *Press Start to begin*"
),
"nom":   "━━━━━━━━━━━━━━━━━━━━━\n👤 *STEP 1 / 5 — Identity*\n━━━━━━━━━━━━━━━━━━━━━\n\nWhat is your *full name*?\n\n_Ex: John Smith_",
"pays":  "━━━━━━━━━━━━━━━━━━━━━\n🌍 *STEP 2 / 5 — Country*\n━━━━━━━━━━━━━━━━━━━━━\n\nWhich country are you in?\n\n_Ex: Nigeria, UK, USA..._",
"email": "━━━━━━━━━━━━━━━━━━━━━\n📧 *STEP 3 / 5 — Exness Email*\n━━━━━━━━━━━━━━━━━━━━━\n\nEnter the email used for your Exness account.\n\n⚠️ This will be verified against @lementorfx's partner dashboard.\n\n_Ex: yourname@gmail.com_",
"ebad":  "❌ *Invalid email.* Enter a valid address:\n_Ex: yourname@gmail.com_",
"edup":  "❌ *Email already registered.*\nContact @lementorfx if this is an error.",
"exq":   "━━━━━━━━━━━━━━━━━━━━━\n🏦 *STEP 4 / 5 — Exness Account*\n━━━━━━━━━━━━━━━━━━━━━\n\nDo you have an Exness account?\n\n💡 VIP access is *100% free*.\nOnly condition: registered via @lementorfx's link.",
"noex":  f"⚠️ *No Exness account yet?*\n\nIt's *free* and takes 3 minutes!\n\n🔗 *Official referral link:*\n{EXNESS_LINK}\n\n✅ Once registered, come back and type /start",
"exid":  "━━━━━━━━━━━━━━━━━━━━━\n🔢 *STEP 5 / 5 — Exness ID*\n━━━━━━━━━━━━━━━━━━━━━\n\nEnter your *Exness account ID*\n_(7 to 9 digit number)_\n\n📌 *How to find it:*\n1️⃣ Go to *exness.com* → log in\n2️⃣ Click *Profile* _(top right)_\n3️⃣ ID appears on the dashboard\n\n👇 Enter your ID now:",
"idbad": "❌ *Invalid ID.* Exness ID = 7 to 9 digits only.\nTry again:",
"iddup": "❌ *This ID is already used.*\nContact @lementorfx if this is an error.",
"choix": "━━━━━━━━━━━━━━━━━━━━━\n🏆 *VIP GROUP SELECTION*\n━━━━━━━━━━━━━━━━━━━━━\n\nSelect the groups you want access to.\nYou can choose *one, several, or all*!\n\n✅ = selected | ☐ = not selected\n\n👇 Select then press *Confirm:*",
"recap": "━━━━━━━━━━━━━━━━━━━━━\n📋 *SUMMARY*\n━━━━━━━━━━━━━━━━━━━━━\n\n👤 Name: *{nom}*\n🌍 Country: *{pays}*\n📧 Email: *{email}*\n🏦 Exness ID: *{exid}*\n📱 Telegram: @{user}\n\n🏆 *Groups requested:*\n{groupes}\n\nIs everything correct?",
"attente": "⏳ *Request submitted!*\n\n━━━━━━━━━━━━━━━━━━━━━\nYour info has been sent to *@lementorfx*.\n\n📋 *Next steps:*\n\n1️⃣ @lementorfx verifies your Exness ID\n   in his partner dashboard\n\n2️⃣ If you are his referral ✅\n   → You receive VIP links here\n\n3️⃣ If not ❌\n   → You receive an explanatory message\n\n━━━━━━━━━━━━━━━━━━━━━\n⏱ *Delay: a few hours maximum*\n\nQuestions → @lementorfx 💬",
"valide": "🎉 *VIP ACCESS GRANTED!*\n\n━━━━━━━━━━━━━━━━━━━━━\nYour Exness referral has been *verified and approved* ✅\n\nWelcome to *LeMentorFx* community! 🔥\n\n🏆 *Your VIP access links:*\n\n{liens}\n━━━━━━━━━━━━━━━━━━━━━\n\n📌 *For each group:*\n• Click the link → Join\n• Enable notifications 🔔\n• Read pinned rules\n\nHappy trading! 🚀\nQuestions → @lementorfx",
"rejete": f"❌ *VIP Access Not Approved*\n\n━━━━━━━━━━━━━━━━━━━━━\nExness ID *{{exid}}* could not be verified as a referral of @lementorfx.\n\n💡 *Solutions:*\n\n▸ No Exness account?\n  → Create one: {EXNESS_LINK}\n\n▸ Account exists but not via our link?\n  → Contact @lementorfx\n\n━━━━━━━━━━━━━━━━━━━━━\nOnce resolved, type /start again.",
"cancel": "❌ Registration cancelled.\nType /start whenever you want to restart.",
"deja":   "✅ You are already registered and validated!\nQuestions → @lementorfx",
}}

def g(lang, key, **kw):
    s = T.get(lang, T["fr"]).get(key, "")
    return s.format(**kw) if kw else s

# ═══════════════════════════════════════════════════════
# HELPERS — CLAVIER SÉLECTION GROUPES
# ═══════════════════════════════════════════════════════

def build_choix_kb(selected: set) -> InlineKeyboardMarkup:
    rows = []
    for k, c in CANAUX.items():
        check = "✅" if k in selected else "☐"
        rows.append([InlineKeyboardButton(
            f"{check} {c['emoji']} {c['nom']}",
            callback_data=f"CH_{k}"
        )])
    rows.append([
        InlineKeyboardButton("🔷 Tous / All",     callback_data="CH_ALL"),
        InlineKeyboardButton("🔲 Aucun / None",   callback_data="CH_NONE"),
    ])
    rows.append([InlineKeyboardButton("✅ Confirmer / Confirm →", callback_data="CH_OK")])
    return InlineKeyboardMarkup(rows)

def format_groupes_texte(selected: set, lang: str) -> str:
    if not selected:
        return "  _(aucun sélectionné)_" if lang=="fr" else "  _(none selected)_"
    lines = []
    for k in sorted(selected):
        c = CANAUX[k]
        lines.append(f"  {c['emoji']} {c['nom']}")
    return "\n".join(lines)

def format_liens_valide(selected: set) -> str:
    lines = []
    for k in sorted(selected):
        c = CANAUX[k]
        lines.append(f"{c['emoji']} *{c['nom']}*\n🔗 {c['lien']}")
    return "\n\n".join(lines)

# ═══════════════════════════════════════════════════════
# CONVERSATION
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
    ctx.user_data["sel"] = set()
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
    lang = "fr" if q.data=="L_fr" else "en"
    ctx.user_data["l"] = lang
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🚀 Commencer / Start →", callback_data="GO")
    ]])
    await q.edit_message_text(g(lang,"accueil"), parse_mode="Markdown", reply_markup=kb)
    return S_NOM

async def cb_go(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = ctx.user_data.get("l","fr")
    await q.edit_message_text(g(lang,"nom"), parse_mode="Markdown")
    return S_NOM

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
    ctx.user_data["sel"] = set()
    await update.message.reply_text(
        g(lang,"choix"), parse_mode="Markdown",
        reply_markup=build_choix_kb(set()))
    return S_CHOIX

async def cb_choix(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = ctx.user_data.get("l","fr")
    sel  = ctx.user_data.get("sel", set())
    code = q.data  # CH_1 .. CH_6 | CH_ALL | CH_NONE | CH_OK

    if code == "CH_ALL":
        sel = set(CANAUX.keys())
    elif code == "CH_NONE":
        sel = set()
    elif code == "CH_OK":
        if not sel:
            await q.answer("⚠️ Sélectionne au moins un groupe !", show_alert=True); return S_CHOIX
        ctx.user_data["sel"] = sel
        # Passer au récapitulatif
        nom   = ctx.user_data.get("nom","—")
        pays  = ctx.user_data.get("pays","—")
        email = ctx.user_data.get("email","—")
        exid  = ctx.user_data.get("exid","—")
        user  = ctx.user_data.get("u","—")
        groupes_txt = format_groupes_texte(sel, lang)
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Confirmer / Confirm", callback_data="C_ok"),
            InlineKeyboardButton("✏️ Modifier / Edit",     callback_data="C_edit"),
        ]])
        await q.edit_message_text(
            g(lang,"recap", nom=nom, pays=pays, email=email, exid=exid, user=user, groupes=groupes_txt),
            parse_mode="Markdown", reply_markup=kb)
        return S_CONFIRM
    else:
        k = code.replace("CH_","")
        if k in sel: sel.discard(k)
        else:        sel.add(k)

    ctx.user_data["sel"] = sel
    try:
        await q.edit_message_reply_markup(reply_markup=build_choix_kb(sel))
    except: pass
    return S_CHOIX

async def cb_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = ctx.user_data.get("l","fr")

    if q.data == "C_edit":
        ctx.user_data["sel"] = ctx.user_data.get("sel", set())
        await q.edit_message_text(g(lang,"choix"), parse_mode="Markdown",
                                  reply_markup=build_choix_kb(ctx.user_data["sel"]))
        return S_CHOIX

    uid   = update.effective_user.id
    nom   = ctx.user_data.get("nom","—")
    pays  = ctx.user_data.get("pays","—")
    email = ctx.user_data.get("email","—")
    exid  = ctx.user_data.get("exid","—")
    user  = ctx.user_data.get("u","—")
    sel   = ctx.user_data.get("sel", set())
    groupes_selectionnes = [CANAUX[k]["nom"] for k in sorted(sel)]

    save_pending(uid, {
        "nom":nom,"pays":pays,"email":email,"exness_id":exid,
        "username":user,"lang":lang,"user_id":uid,
        "groupes": groupes_selectionnes
    })

    await q.edit_message_text(g(lang,"attente"), parse_mode="Markdown")

    # ── Notification admin avec boutons ──
    groupes_txt = "\n".join([f"  • {n}" for n in groupes_selectionnes])
    kb_admin = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ VALIDER L'ACCÈS VIP", callback_data=f"A_ok_{uid}"),
        InlineKeyboardButton("❌ REJETER",              callback_data=f"A_no_{uid}"),
    ]])
    notif = (
        f"🆕 *NOUVELLE DEMANDE VIP*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Nom : *{nom}*\n"
        f"🌍 Pays : *{pays}*\n"
        f"📧 Email : `{email}`\n"
        f"🏦 ID Exness : `{exid}`\n"
        f"📱 Telegram : @{user}\n"
        f"🆔 User ID : `{uid}`\n"
        f"📅 {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏆 *Groupes demandés :*\n{groupes_txt}\n\n"
        f"📌 Vérifie sur ton espace Exness Partner\n"
        f"que cet email/ID est bien ton filleul.\n\n"
        f"👇 Puis clique :"
    )
    try:
        await ctx.bot.send_message(chat_id=ADMIN_ID, text=notif,
                                   parse_mode="Markdown", reply_markup=kb_admin)
        log.info(f"Notif admin envoyée — {nom} ({uid})")
    except Exception as e:
        log.error(f"ERREUR notif admin: {e}")

    return ConversationHandler.END

# ═══════════════════════════════════════════════════════
# ADMIN — VALIDER / REJETER
# ═══════════════════════════════════════════════════════

async def cb_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("⛔ Non autorisé.", show_alert=True); return
    await q.answer()

    parts  = q.data.split("_")   # A_ok_UID ou A_no_UID
    action = parts[1]
    uid    = int(parts[2])

    if action == "ok":
        d = approve(uid)
        if not d:
            await q.edit_message_text("⚠️ Introuvable. Déjà traité ?"); return
        lang = d.get("lang","fr")
        sel  = set()
        # Retrouver les clés des groupes depuis les noms
        noms_sel = d.get("groupes",[])
        for k, c in CANAUX.items():
            if c["nom"] in noms_sel: sel.add(k)
        if not sel: sel = set(CANAUX.keys())  # fallback : tous
        liens_txt = format_liens_valide(sel)
        try:
            await ctx.bot.send_message(
                chat_id=uid,
                text=g(lang,"valide", liens=liens_txt),
                parse_mode="Markdown"
            )
            await q.edit_message_text(
                f"✅ *VIP validé et liens envoyés !*\n\n"
                f"👤 {d.get('nom')} (@{d.get('username')})\n"
                f"🏦 ID: {d.get('exness_id')}\n"
                f"🏆 Groupes: {', '.join(d.get('groupes',[]))}",
                parse_mode="Markdown")
        except Exception as e:
            await q.edit_message_text(f"⚠️ Validé mais erreur envoi : {e}")

    elif action == "no":
        d = reject(uid)
        if not d:
            await q.edit_message_text("⚠️ Introuvable. Déjà traité ?"); return
        lang = d.get("lang","fr")
        try:
            await ctx.bot.send_message(
                chat_id=uid,
                text=g(lang,"rejete", exid=d.get("exness_id","?")),
                parse_mode="Markdown")
            await q.edit_message_text(
                f"❌ *Rejeté*\n\n"
                f"👤 {d.get('nom')} (@{d.get('username')})\n"
                f"🏦 ID: {d.get('exness_id')}\n"
                f"Le client a été informé.",
                parse_mode="Markdown")
        except Exception as e:
            await q.edit_message_text(f"⚠️ Rejeté mais erreur envoi : {e}")

# ═══════════════════════════════════════════════════════
# COMMANDES ADMIN
# ═══════════════════════════════════════════════════════

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    await update.message.reply_text(
        f"📊 *Stats LeMentorFx VIP Bot*\n\n"
        f"✅ Membres VIP validés : *{len(db.get('valides',{}))}*\n"
        f"⏳ En attente : *{len(db.get('attente',{}))}*\n"
        f"❌ Rejetés : *{len(db.get('rejetes',{}))}*\n"
        f"🏦 IDs Exness : *{len(db.get('exness_ids',[]))}*",
        parse_mode="Markdown")

async def cmd_attente(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    items = list(db.get("attente",{}).values())
    if not items: await update.message.reply_text("✅ Aucune demande en attente."); return
    lines = []
    for x in items:
        g_txt = ", ".join(x.get("groupes",[]))
        lines.append(
            f"• *{x.get('nom','?')}* | {x.get('pays','?')}\n"
            f"  📧 {x.get('email','?')}\n"
            f"  🏦 {x.get('exness_id','?')} | @{x.get('username','?')}\n"
            f"  🏆 {g_txt}"
        )
    await update.message.reply_text(
        f"⏳ *{len(items)} demande(s) en attente :*\n\n" + "\n\n".join(lines),
        parse_mode="Markdown")

async def cmd_liste(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    items = list(db.get("valides",{}).values())[-15:]
    if not items: await update.message.reply_text("Aucun membre VIP encore."); return
    lines = [f"• *{x.get('nom','?')}* | {x.get('pays','?')} | {x.get('exness_id','?')}" for x in items]
    await update.message.reply_text("📋 *Membres VIP :*\n\n"+"\n".join(lines), parse_mode="Markdown")

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
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🚀 S'inscrire / Register", callback_data="RESTART")
    ]])
    await update.message.reply_text(
        "👋 Tape /start ou appuie sur le bouton pour t'inscrire.\n"
        "Type /start or press the button to register.",
        reply_markup=kb)

async def cb_restart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear()
    ctx.user_data["u"] = update.effective_user.username or str(update.effective_user.id)
    ctx.user_data["sel"] = set()
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🇫🇷 Français", callback_data="L_fr"),
        InlineKeyboardButton("🇬🇧 English",  callback_data="L_en"),
    ]])
    await q.edit_message_text(
        "🌍 *Choisis ta langue / Choose your language:*",
        parse_mode="Markdown", reply_markup=kb)
    return S_LANG

async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start",   "🚀 Démarrer l'inscription VIP"),
        BotCommand("annuler", "❌ Annuler"),
    ])

# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start",  cmd_start),
            CallbackQueryHandler(cb_restart, pattern="^RESTART$"),
        ],
        states={
            S_LANG:    [CallbackQueryHandler(cb_lang,    pattern="^L_")],
            S_NOM:     [
                CallbackQueryHandler(cb_go, pattern="^GO$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, h_nom),
            ],
            S_PAYS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, h_pays)],
            S_EMAIL:   [MessageHandler(filters.TEXT & ~filters.COMMAND, h_email)],
            S_EXQ:     [CallbackQueryHandler(cb_exq,    pattern="^EX_")],
            S_EXID:    [MessageHandler(filters.TEXT & ~filters.COMMAND, h_exid)],
            S_CHOIX:   [CallbackQueryHandler(cb_choix,  pattern="^CH_")],
            S_CONFIRM: [CallbackQueryHandler(cb_confirm, pattern="^C_")],
        },
        fallbacks=[
            CommandHandler("annuler", cmd_cancel),
            CommandHandler("cancel",  cmd_cancel),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(cb_admin,   pattern="^A_(ok|no)_"))
    app.add_handler(CommandHandler("stats",   cmd_stats))
    app.add_handler(CommandHandler("liste",   cmd_liste))
    app.add_handler(CommandHandler("attente", cmd_attente))
    app.add_handler(CommandHandler("bloquer", cmd_bloquer))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_other))

    print("✅ LeMentorFx VIP Bot démarré — 6 canaux VIP configurés")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
