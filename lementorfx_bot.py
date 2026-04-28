#!/usr/bin/env python3
import logging, json, os, re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)

TOKEN        = "7575039426:AAHnnxr8L7OVdy5TuSsA45rt1l1ID5ubFYc"
ADMIN_ID     = 7412212489
CANAL_PRIVE  = "https://t.me/+HJ9qJhRZ7mg0MmFk"
CANAL_PUBLIC = "https://t.me/lementorforexgroup"
EXNESS_LINK  = "https://one.exnessonelink.com/a/do7n4lz3on"
DB_FILE      = "lmentorfx_membres.json"

(ATTENTE_LANGUE, ATTENTE_NOM, ATTENTE_PAYS,
 ATTENTE_EMAIL, ATTENTE_EXNESS_COMPTE,
 ATTENTE_EXNESS_ID, ATTENTE_CONFIRMATION) = range(7)

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"membres": {}, "exness_ids": [], "emails": [], "bloques": []}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def exness_id_existe(eid):   return eid in load_db().get("exness_ids", [])
def email_existe(em):         return em.lower() in [e.lower() for e in load_db().get("emails", [])]
def est_bloque(uid):          return uid in load_db().get("bloques", [])

def enregistrer_membre(user_id, data):
    db = load_db()
    db["membres"][str(user_id)] = {**data, "date": datetime.now().isoformat()}
    if data.get("exness_id"): db["exness_ids"].append(data["exness_id"])
    if data.get("email"):     db["emails"].append(data["email"].lower())
    save_db(db)

MSG = {
"fr": {
"start":  "🌍 *Choisis ta langue / Choose your language:*",
"bienve": ("🤖 *Bienvenue chez LeMentorFx !*\n\n"
           "Bot officiel de *@lementorfx* — Partenaire IB Exness & mentor trading.\n\n"
           "✅ Signaux XAU/USD gratuits *(PHANTOM TRAP)*\n"
           "✅ Éducation SMC/ICT\n"
           "✅ Accompagnement personnalisé\n"
           "✅ Robot EA gratuit *(filleuls Exness)*\n\n"
           "Procédure rapide — *2 minutes*. 👇"),
"nom":    "👤 *Étape 1/5*\n\nQuel est ton *nom complet* ?",
"pays":   "🌍 *Étape 2/5*\n\nDans quel pays es-tu ?",
"email":  ("📧 *Étape 3/5 — Email Exness*\n\n"
           "Entre l'adresse email que tu as utilisée pour créer ton compte Exness.\n\n"
           "⚠️ Cette adresse servira à vérifier que tu es bien inscrit via le lien de parrainage."),
"email_bad": "❌ Email invalide. Entre une adresse correcte *(ex: nom@gmail.com)* :",
"email_dup": "❌ *Cet email est déjà enregistré.*\nContacte @lementorfx si c'est une erreur.",
"exq":    ("🏦 *Étape 4/5 — Compte Exness*\n\n"
           "Le canal est *100% gratuit*.\n"
           "Seule condition : compte Exness via notre lien.\n\n"
           "👇 As-tu déjà un compte Exness ?"),
"no_ex":  f"⚠️ *Pas encore de compte Exness ?*\n\nOuvre-le gratuitement ici :\n{EXNESS_LINK}\n\n✅ Reviens taper /start une fois inscrit.",
"exid":   ("🔢 *Étape 5/5 — ID Exness*\n\n"
           "Ton ID Exness = numéro *7 à 9 chiffres* dans ton espace personnel.\n\n"
           "📌 Comment trouver :\n"
           "1️⃣ exness.com → connecte-toi\n"
           "2️⃣ Clique ton profil *(haut à droite)*\n"
           "3️⃣ L'ID apparaît sur le tableau de bord\n\n"
           "👇 Entre ton ID Exness :"),
"id_bad":  "❌ ID invalide. L'ID Exness = *7 à 9 chiffres uniquement*. Réessaie :",
"id_dup":  "❌ *Cet ID Exness est déjà utilisé.*\nContacte @lementorfx si c'est une erreur.",
"recap":  ("✅ *Récapitulatif*\n\n"
           "👤 Nom : *{nom}*\n🌍 Pays : *{pays}*\n📧 Email : *{email}*\n"
           "🏦 ID Exness : *{exid}*\n📱 Telegram : @{user}\n\nTout est correct ?"),
"valide": ("🎉 *Inscription validée !*\n\n"
           "Bienvenue dans *LeMentorFx* !\n\n"
           "🔐 *Ton accès au canal privé :*\n"
           "👇👇👇\n{canal}\n👆👆👆\n\n"
           "📌 Étapes :\n1. Rejoins le canal via le lien\n"
           "2. Active les notifications 🔔\n3. Lis les règles épinglées\n"
           "4. Attends le prochain signal 📡\n\nQuestions → @lementorfx"),
"notif":  ("🆕 *NOUVELLE INSCRIPTION*\n\n"
           "👤 {nom}\n🌍 {pays}\n📧 {email}\n🏦 ID: {exid}\n"
           "📱 @{user}\n🆔 {uid}\n📅 {date}"),
"annule": "❌ Annulé. Tape /start pour recommencer.",
},
"en": {
"start":  "🌍 *Choisis ta langue / Choose your language:*",
"bienve": ("🤖 *Welcome to LeMentorFx!*\n\n"
           "Official bot of *@lementorfx* — Exness IB Partner & trading mentor.\n\n"
           "✅ Free XAU/USD signals *(PHANTOM TRAP)*\n"
           "✅ SMC/ICT education\n✅ Personal coaching\n"
           "✅ Free EA Robot *(Exness referrals)*\n\nQuick process — *2 minutes*. 👇"),
"nom":    "👤 *Step 1/5*\n\nWhat is your *full name*?",
"pays":   "🌍 *Step 2/5*\n\nWhich country are you in?",
"email":  ("📧 *Step 3/5 — Exness Email*\n\n"
           "Enter the email address you used to create your Exness account.\n\n"
           "⚠️ This will be used to verify you registered via the referral link."),
"email_bad": "❌ Invalid email. Enter a valid address *(e.g. name@gmail.com)* :",
"email_dup": "❌ *This email is already registered.*\nContact @lementorfx if this is an error.",
"exq":    ("🏦 *Step 4/5 — Exness Account*\n\n"
           "The channel is *100% free*.\n"
           "Only condition: Exness account via our link.\n\n"
           "👇 Do you already have an Exness account?"),
"no_ex":  f"⚠️ *No Exness account yet?*\n\nOpen yours for free here:\n{EXNESS_LINK}\n\n✅ Come back and type /start once registered.",
"exid":   ("🔢 *Step 5/5 — Exness ID*\n\n"
           "Your Exness ID = *7 to 9 digit number* in your personal area.\n\n"
           "📌 How to find it:\n1️⃣ exness.com → log in\n"
           "2️⃣ Click your profile *(top right)*\n"
           "3️⃣ ID appears on dashboard\n\n👇 Enter your Exness ID:"),
"id_bad":  "❌ Invalid ID. Exness ID = *7 to 9 digits only*. Try again:",
"id_dup":  "❌ *This Exness ID is already used.*\nContact @lementorfx if this is an error.",
"recap":  ("✅ *Summary*\n\n"
           "👤 Name: *{nom}*\n🌍 Country: *{pays}*\n📧 Email: *{email}*\n"
           "🏦 Exness ID: *{exid}*\n📱 Telegram: @{user}\n\nIs everything correct?"),
"valide": ("🎉 *Registration approved!*\n\n"
           "Welcome to *LeMentorFx*!\n\n"
           "🔐 *Your private channel access:*\n"
           "👇👇👇\n{canal}\n👆👆👆\n\n"
           "📌 Steps:\n1. Join the channel via the link\n"
           "2. Enable notifications 🔔\n3. Read pinned rules\n"
           "4. Wait for the next signal 📡\n\nQuestions → @lementorfx"),
"notif":  ("🆕 *NEW REGISTRATION*\n\n"
           "👤 {nom}\n🌍 {pays}\n📧 {email}\n🏦 ID: {exid}\n"
           "📱 @{user}\n🆔 {uid}\n📅 {date}"),
"annule": "❌ Cancelled. Type /start to restart.",
}}

def m(lang, key, **kw):
    s = MSG.get(lang, MSG["fr"]).get(key, "")
    return s.format(**kw) if kw else s

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if est_bloque(update.effective_user.id):
        await update.message.reply_text("⛔ Accès refusé."); return ConversationHandler.END
    context.user_data.clear()
    context.user_data["username"] = update.effective_user.username or str(update.effective_user.id)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
        InlineKeyboardButton("🇬🇧 English",  callback_data="lang_en"),
    ]])
    await update.message.reply_text(m("fr","start"), parse_mode="Markdown", reply_markup=kb)
    return ATTENTE_LANGUE

async def cb_langue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = "fr" if q.data == "lang_fr" else "en"
    context.user_data["lang"] = lang
    await q.edit_message_text(m(lang,"bienve"), parse_mode="Markdown")
    await q.message.reply_text(m(lang,"nom"), parse_mode="Markdown")
    return ATTENTE_NOM

async def recv_nom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang","fr")
    nom = update.message.text.strip()
    if len(nom) < 2:
        await update.message.reply_text("❌ Nom trop court."); return ATTENTE_NOM
    context.user_data["nom"] = nom
    await update.message.reply_text(m(lang,"pays"), parse_mode="Markdown")
    return ATTENTE_PAYS

async def recv_pays(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang","fr")
    context.user_data["pays"] = update.message.text.strip()
    await update.message.reply_text(m(lang,"email"), parse_mode="Markdown")
    return ATTENTE_EMAIL

async def recv_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang","fr")
    email = update.message.text.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        await update.message.reply_text(m(lang,"email_bad"), parse_mode="Markdown"); return ATTENTE_EMAIL
    if email_existe(email):
        await update.message.reply_text(m(lang,"email_dup"), parse_mode="Markdown"); return ConversationHandler.END
    context.user_data["email"] = email
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Oui / Yes",              callback_data="ex_oui")],
        [InlineKeyboardButton("❌ Pas encore / Not yet",   callback_data="ex_non")],
        [InlineKeyboardButton("🔄 En cours / In progress", callback_data="ex_encours")],
    ])
    await update.message.reply_text(m(lang,"exq"), parse_mode="Markdown", reply_markup=kb)
    return ATTENTE_EXNESS_COMPTE

async def cb_exness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = context.user_data.get("lang","fr")
    if q.data == "ex_non":
        await q.edit_message_text(m(lang,"no_ex"), parse_mode="Markdown"); return ConversationHandler.END
    await q.edit_message_text(m(lang,"exid"), parse_mode="Markdown")
    return ATTENTE_EXNESS_ID

async def recv_exid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang","fr")
    raw = update.message.text.strip().replace(" ","")
    if not re.match(r"^\d{7,9}$", raw):
        await update.message.reply_text(m(lang,"id_bad"), parse_mode="Markdown"); return ATTENTE_EXNESS_ID
    if exness_id_existe(raw):
        await update.message.reply_text(m(lang,"id_dup"), parse_mode="Markdown"); return ConversationHandler.END
    context.user_data["exness_id"] = raw
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Confirmer / Confirm", callback_data="ok"),
        InlineKeyboardButton("✏️ Corriger / Edit",     callback_data="edit"),
    ]])
    await update.message.reply_text(
        m(lang,"recap", nom=context.user_data.get("nom","—"), pays=context.user_data.get("pays","—"),
          email=context.user_data.get("email","—"), exid=raw, user=context.user_data.get("username","—")),
        parse_mode="Markdown", reply_markup=kb)
    return ATTENTE_CONFIRMATION

async def cb_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = context.user_data.get("lang","fr")
    if q.data == "edit":
        await q.edit_message_text(m(lang,"exid"), parse_mode="Markdown"); return ATTENTE_EXNESS_ID
    user = update.effective_user
    data = {k: context.user_data.get(k) for k in ["nom","pays","email","exness_id","username","lang"]}
    data["user_id"] = user.id
    enregistrer_membre(user.id, data)
    await q.edit_message_text(m(lang,"valide", canal=CANAL_PRIVE), parse_mode="Markdown")
    try:
        await context.bot.send_message(chat_id=ADMIN_ID,
            text=m("fr","notif", nom=data["nom"], pays=data["pays"], email=data["email"],
                   exid=data["exness_id"], user=data["username"], uid=user.id,
                   date=datetime.now().strftime("%d/%m/%Y %H:%M")),
            parse_mode="Markdown")
    except Exception as e:
        logging.warning(f"Notif admin: {e}")
    return ConversationHandler.END

async def annuler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang","fr")
    await update.message.reply_text(m(lang,"annule"))
    return ConversationHandler.END

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    await update.message.reply_text(
        f"📊 *Stats*\n\n👥 Membres : *{len(db['membres'])}*\n🏦 IDs Exness : *{len(db['exness_ids'])}*\n📧 Emails : *{len(db['emails'])}*",
        parse_mode="Markdown")

async def cmd_liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    membres = list(db["membres"].values())[-20:]
    if not membres: await update.message.reply_text("Aucun membre."); return
    lines = [f"• *{x.get('nom','?')}* | {x.get('pays','?')} | {x.get('email','?')} | {x.get('exness_id','?')}" for x in membres]
    await update.message.reply_text("📋 *20 derniers :*\n\n" + "\n".join(lines), parse_mode="Markdown")

async def cmd_bloquer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: await update.message.reply_text("Usage: /bloquer [id]"); return
    try:
        uid = int(context.args[0]); db = load_db()
        if uid not in db["bloques"]: db["bloques"].append(uid); save_db(db)
        await update.message.reply_text(f"✅ {uid} bloqué.")
    except: await update.message.reply_text("ID invalide.")

async def msg_inconnu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tape /start pour t'inscrire.\nType /start to register.")

def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ATTENTE_LANGUE:        [CallbackQueryHandler(cb_langue,  pattern="^lang_")],
            ATTENTE_NOM:           [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_nom)],
            ATTENTE_PAYS:          [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_pays)],
            ATTENTE_EMAIL:         [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_email)],
            ATTENTE_EXNESS_COMPTE: [CallbackQueryHandler(cb_exness,  pattern="^ex_")],
            ATTENTE_EXNESS_ID:     [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_exid)],
            ATTENTE_CONFIRMATION:  [CallbackQueryHandler(cb_confirm, pattern="^(ok|edit)$")],
        },
        fallbacks=[CommandHandler("annuler", annuler)],
        allow_reentry=True,
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("stats",   cmd_stats))
    app.add_handler(CommandHandler("liste",   cmd_liste))
    app.add_handler(CommandHandler("bloquer", cmd_bloquer))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_inconnu))
    print("✅ LeMentorFx Bot démarré — @lementorfx")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
