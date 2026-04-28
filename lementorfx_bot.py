#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║          LEMENTORFX — BOT TELEGRAM OFFICIEL             ║
║          Partenaire IB Exness · Signaux XAU/USD         ║
║          @lementorfx · @salomonryn                      ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
import json
import os
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)

# ══════════════════════════════════════════════════════════
# ⚙️  CONFIGURATION
# ══════════════════════════════════════════════════════════

TOKEN        = "7575039426:AAHnnxr8L7OVdy5TuSsA45rt1l1ID5ubFYc"
ADMIN_ID     = 7412212489
CANAL_PRIVE  = "https://t.me/+HJ9qJhRZ7mg0MmFk"
CANAL_PUBLIC = "https://t.me/lementorforexgroup"
EXNESS_LINK  = "https://one.exnessonelink.com/a/do7n4lz3on"
DB_FILE      = "lmentorfx_membres.json"

# ══════════════════════════════════════════════════════════
# ÉTATS
# ══════════════════════════════════════════════════════════
(
    ATTENTE_LANGUE,
    ATTENTE_NOM,
    ATTENTE_PAYS,
    ATTENTE_EMAIL,
    ATTENTE_EXNESS_COMPTE,
    ATTENTE_EXNESS_ID,
    ATTENTE_CONFIRMATION,
) = range(7)

# ══════════════════════════════════════════════════════════
# BASE DE DONNÉES LOCALE
# ══════════════════════════════════════════════════════════

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"membres": {}, "exness_ids": [], "emails": [], "bloques": []}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def exness_id_existe(exness_id):
    return exness_id in load_db().get("exness_ids", [])

def email_existe(email):
    return email.lower() in [e.lower() for e in load_db().get("emails", [])]

def enregistrer_membre(user_id, data):
    db = load_db()
    db["membres"][str(user_id)] = {**data, "date": datetime.now().isoformat(), "statut": "validé"}
    if data.get("exness_id"):
        db["exness_ids"].append(data["exness_id"])
    if data.get("email"):
        db["emails"].append(data["email"].lower())
    save_db(db)

def est_bloque(user_id):
    return user_id in load_db().get("bloques", [])

# ══════════════════════════════════════════════════════════
# TEXTES FR / EN
# ══════════════════════════════════════════════════════════

def txt(lang, key, **kw):
    T = {
        "fr": {
            "bienvenue": (
                "🤖 *Bienvenue chez LeMentorFx !*\n\n"
                "Je suis le bot officiel de *@lementorfx* — Partenaire IB Exness & mentor trading.\n\n"
                "Tu vas recevoir :\n"
                "📡 Signaux XAU/USD gratuits *(PHANTOM TRAP)*\n"
                "🎓 Éducation SMC/ICT complète\n"
                "🤝 Accompagnement personnalisé\n"
                "🤖 Robot EA gratuit *(filleuls Exness)*\n\n"
                "📋 Procédure rapide — *2 minutes*. Allons-y ! 👇"
            ),
            "nom":     "👤 *Étape 1/5 — Identité*\n\nQuel est ton *nom complet* ?",
            "pays":    "🌍 *Étape 2/5 — Pays*\n\nDans quel pays es-tu situé ?",
            "email":   (
                "📧 *Étape 3/5 — Adresse email*\n\n"
                "Entre l'adresse email utilisée pour créer ton compte Exness.\n\n"
                "⚠️ *Important :* c'est avec cette adresse que @lementorfx vérifiera "
                "que tu es bien inscrit via le lien de parrainage."
            ),
            "email_invalide": "❌ Email invalide. Entre une adresse email correcte (ex: nom@gmail.com) :",
            "email_existe":   (
                "❌ *Cet email est déjà enregistré.*\n\n"
                "Chaque email ne peut être utilisé qu'une seule fois.\n"
                "Si tu penses que c'est une erreur → @lementorfx"
            ),
            "exness_q": (
                "🏦 *Étape 4/5 — Compte Exness*\n\n"
                "Le canal est *100% gratuit*.\n"
                "Seule condition : t'inscrire sur Exness via notre lien.\n\n"
                "👇 *As-tu déjà un compte Exness ?*"
            ),
            "pas_compte": (
                f"⚠️ *Pas encore de compte Exness ?*\n\n"
                f"Ouvre ton compte gratuitement ici :\n{EXNESS_LINK}\n\n"
                "✅ Reviens taper /start une fois inscrit."
            ),
            "exness_id": (
                "🔢 *Étape 5/5 — ID Exness*\n\n"
                "Ton ID Exness est un numéro à *7–9 chiffres* dans ton espace personnel.\n\n"
                "📌 *Comment le trouver :*\n"
                "1️⃣ Va sur exness.com → connecte-toi\n"
                "2️⃣ Clique sur ton profil *(haut à droite)*\n"
                "3️⃣ L'ID apparaît sur le tableau de bord\n\n"
                "👇 Entre ton ID Exness :"
            ),
            "id_invalide":  "❌ ID invalide. Un ID Exness = *7 à 9 chiffres uniquement*.\nEssaie encore :",
            "id_existe":    "❌ *Cet ID Exness est déjà enregistré.*\nChaque ID ne peut être utilisé qu'une seule fois.\nContacte @lementorfx si c'est une erreur.",
            "recap": (
                "✅ *Récapitulatif*\n\n"
                "👤 Nom : *{nom}*\n"
                "🌍 Pays : *{pays}*\n"
                "📧 Email : *{email}*\n"
                "🏦 ID Exness : *{exid}*\n"
                "📱 Telegram : @{user}\n\n"
                "Tout est correct ?"
            ),
            "valide": (
                "🎉 *Inscription validée !*\n\n"
                "Bienvenue dans la communauté *LeMentorFx* !\n\n"
                "🔐 *Ton accès au canal privé :*\n"
                "👇👇👇\n"
                "{canal}\n"
                "👆👆👆\n\n"
                "📌 *Étapes suivantes :*\n"
                "1. Rejoins le canal via le lien ci-dessus\n"
                "2. Active les notifications 🔔\n"
                "3. Lis les règles épinglées\n"
                "4. Attends le prochain signal 📡\n\n"
                "Des questions ? → @lementorfx"
            ),
            "notif_admin": (
                "🆕 *NOUVELLE INSCRIPTION*\n\n"
                "👤 Nom : {nom}\n"
                "🌍 Pays : {pays}\n"
                "📧 Email : {email}\n"
                "🏦 ID Exness : {exid}\n"
                "📱 Telegram : @{user}\n"
                "🆔 User ID : {uid}\n"
                "📅 Date : {date}"
            ),
            "annule":  "❌ Inscription annulée. Tape /start pour recommencer.",
            "bloque":  "⛔ Accès refusé.",
        },
        "en": {
            "bienvenue": (
                "🤖 *Welcome to LeMentorFx!*\n\n"
                "I'm the official bot of *@lementorfx* — Exness IB Partner & trading mentor.\n\n"
                "You'll receive:\n"
                "📡 Free XAU/USD signals *(PHANTOM TRAP)*\n"
                "🎓 Full SMC/ICT education\n"
                "🤝 Personal coaching\n"
                "🤖 Free EA Robot *(Exness referrals)*\n\n"
                "📋 Quick process — *2 minutes*. Let's go! 👇"
            ),
            "nom":     "👤 *Step 1/5 — Identity*\n\nWhat is your *full name*?",
            "pays":    "🌍 *Step 2/5 — Country*\n\nWhich country are you in?",
            "email":   (
                "📧 *Step 3/5 — Email address*\n\n"
                "Enter the email address used to create your Exness account.\n\n"
                "⚠️ *Important:* @lementorfx will use this email to verify "
                "that you registered via the referral link."
            ),
            "email_invalide": "❌ Invalid email. Enter a valid address (e.g. name@gmail.com):",
            "email_existe":   (
                "❌ *This email is already registered.*\n\n"
                "Each email can only be used once.\n"
                "If you think this is an error → @lementorfx"
            ),
            "exness_q": (
                "🏦 *Step 4/5 — Exness Account*\n\n"
                "The channel is *100% free*.\n"
                "Only condition: register on Exness via our link.\n\n"
                "👇 *Do you already have an Exness account?*"
            ),
            "pas_compte": (
                f"⚠️ *No Exness account yet?*\n\n"
                f"Open your account for free here:\n{EXNESS_LINK}\n\n"
                "✅ Come back and type /start once registered."
            ),
            "exness_id": (
                "🔢 *Step 5/5 — Exness ID*\n\n"
                "Your Exness ID is a *7–9 digit number* in your personal area.\n\n"
                "📌 *How to find it:*\n"
                "1️⃣ Go to exness.com → log in\n"
                "2️⃣ Click your profile *(top right)*\n"
                "3️⃣ The ID appears on the dashboard\n\n"
                "👇 Enter your Exness ID:"
            ),
            "id_invalide":  "❌ Invalid ID. An Exness ID = *7 to 9 digits only*.\nTry again:",
            "id_existe":    "❌ *This Exness ID is already registered.*\nEach ID can only be used once.\nContact @lementorfx if this is an error.",
            "recap": (
                "✅ *Summary*\n\n"
                "👤 Name: *{nom}*\n"
                "🌍 Country: *{pays}*\n"
                "📧 Email: *{email}*\n"
                "🏦 Exness ID: *{exid}*\n"
                "📱 Telegram: @{user}\n\n"
                "Is everything correct?"
            ),
            "valide": (
                "🎉 *Registration approved!*\n\n"
                "Welcome to the *LeMentorFx* community!\n\n"
                "🔐 *Your private channel access:*\n"
                "👇👇👇\n"
                "{canal}\n"
                "👆👆👆\n\n"
                "📌 *Next steps:*\n"
                "1. Join the channel via the link above\n"
                "2. Enable notifications 🔔\n"
                "3. Read the pinned rules\n"
                "4. Wait for the next signal 📡\n\n"
                "Questions? → @lementorfx"
            ),
            "notif_admin": (
                "🆕 *NEW REGISTRATION*\n\n"
                "👤 Name: {nom}\n"
                "🌍 Country: {pays}\n"
                "📧 Email: {email}\n"
                "🏦 Exness ID: {exid}\n"
                "📱 Telegram: @{user}\n"
                "🆔 User ID: {uid}\n"
                "📅 Date: {date}"
            ),
            "annule":  "❌ Registration cancelled. Type /start to restart.",
            "bloque":  "⛔ Access denied.",
        }
    }
    s = T.get(lang, T["fr"]).get(key, "")
    return s.format(**kw) if kw else s

# ══════════════════════════════════════════════════════════
# HANDLERS
# ══════════════════════════════════════════════════════════

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if est_bloque(user.id):
        await update.message.reply_text("⛔ Accès refusé. / Access denied.")
        return ConversationHandler.END
    context.user_data.clear()
    context.user_data["username"] = user.username or str(user.id)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
        InlineKeyboardButton("🇬🇧 English",  callback_data="lang_en"),
    ]])
    await update.message.reply_text(
        "🌍 *Choisis ta langue / Choose your language:*",
        parse_mode="Markdown", reply_markup=kb
    )
    return ATTENTE_LANGUE


async def cb_langue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = "fr" if q.data == "lang_fr" else "en"
    context.user_data["lang"] = lang
    await q.edit_message_text(txt(lang, "bienvenue"), parse_mode="Markdown")
    await q.message.reply_text(txt(lang, "nom"), parse_mode="Markdown")
    return ATTENTE_NOM


async def recv_nom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nom = update.message.text.strip()
    lang = context.user_data.get("lang", "fr")
    if len(nom) < 2:
        await update.message.reply_text("❌ Nom trop court / Name too short.")
        return ATTENTE_NOM
    context.user_data["nom"] = nom
    await update.message.reply_text(txt(lang, "pays"), parse_mode="Markdown")
    return ATTENTE_PAYS


async def recv_pays(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["pays"] = update.message.text.strip()
    lang = context.user_data.get("lang", "fr")
    await update.message.reply_text(txt(lang, "email"), parse_mode="Markdown")
    return ATTENTE_EMAIL


async def recv_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "fr")
    email = update.message.text.strip().lower()
    # Validation email
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        await update.message.reply_text(txt(lang, "email_invalide"), parse_mode="Markdown")
        return ATTENTE_EMAIL
    # Anti-doublon email
    if email_existe(email):
        await update.message.reply_text(txt(lang, "email_existe"), parse_mode="Markdown")
        return ConversationHandler.END
    context.user_data["email"] = email
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Oui / Yes",             callback_data="ex_oui")],
        [InlineKeyboardButton("❌ Pas encore / Not yet",  callback_data="ex_non")],
        [InlineKeyboardButton("🔄 En cours / In progress",callback_data="ex_encours")],
    ])
    await update.message.reply_text(txt(lang, "exness_q"), parse_mode="Markdown", reply_markup=kb)
    return ATTENTE_EXNESS_COMPTE


async def cb_exness_compte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "fr")
    if q.data == "ex_non":
        await q.edit_message_text(txt(lang, "pas_compte"), parse_mode="Markdown")
        return ConversationHandler.END
    await q.edit_message_text(txt(lang, "exness_id"), parse_mode="Markdown")
    return ATTENTE_EXNESS_ID


async def recv_exness_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "fr")
    raw = update.message.text.strip().replace(" ", "")
    if not re.match(r"^\d{7,9}$", raw):
        await update.message.reply_text(txt(lang, "id_invalide"), parse_mode="Markdown")
        return ATTENTE_EXNESS_ID
    if exness_id_existe(raw):
        await update.message.reply_text(txt(lang, "id_existe"), parse_mode="Markdown")
        return ConversationHandler.END
    context.user_data["exness_id"] = raw
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Confirmer / Confirm", callback_data="ok"),
        InlineKeyboardButton("✏️ Corriger / Edit",     callback_data="edit"),
    ]])
    await update.message.reply_text(
        txt(lang, "recap",
            nom=context.user_data.get("nom","—"),
            pays=context.user_data.get("pays","—"),
            email=context.user_data.get("email","—"),
            exid=raw,
            user=context.user_data.get("username","—")
        ),
        parse_mode="Markdown", reply_markup=kb
    )
    return ATTENTE_CONFIRMATION


async def cb_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "fr")
    user = update.effective_user

    if q.data == "edit":
        await q.edit_message_text(txt(lang, "exness_id"), parse_mode="Markdown")
        return ATTENTE_EXNESS_ID

    # ── ENREGISTREMENT ──
    data = {
        "nom":       context.user_data.get("nom"),
        "pays":      context.user_data.get("pays"),
        "email":     context.user_data.get("email"),
        "exness_id": context.user_data.get("exness_id"),
        "username":  context.user_data.get("username"),
        "lang":      lang,
        "user_id":   user.id,
    }
    enregistrer_membre(user.id, data)

    # Message succès → lien canal privé
    await q.edit_message_text(
        txt(lang, "valide", canal=CANAL_PRIVE),
        parse_mode="Markdown"
    )

    # Notification admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=txt("fr", "notif_admin",
                nom=data["nom"], pays=data["pays"],
                email=data["email"], exid=data["exness_id"],
                user=data["username"], uid=user.id,
                date=datetime.now().strftime("%d/%m/%Y %H:%M")
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"Notif admin échouée : {e}")

    return ConversationHandler.END


async def annuler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "fr")
    await update.message.reply_text(txt(lang, "annule"))
    context.user_data.clear()
    return ConversationHandler.END

# ══════════════════════════════════════════════════════════
# COMMANDES ADMIN
# ══════════════════════════════════════════════════════════

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    await update.message.reply_text(
        f"📊 *Stats LeMentorFx Bot*\n\n"
        f"👥 Membres inscrits : *{len(db['membres'])}*\n"
        f"🏦 IDs Exness : *{len(db['exness_ids'])}*\n"
        f"📧 Emails : *{len(db['emails'])}*\n"
        f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        parse_mode="Markdown"
    )

async def cmd_liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    membres = list(db["membres"].values())[-20:]
    if not membres:
        await update.message.reply_text("Aucun membre."); return
    lines = [
        f"• *{m.get('nom','?')}* | {m.get('pays','?')} | {m.get('email','?')} | ID:{m.get('exness_id','?')}"
        for m in membres
    ]
    await update.message.reply_text(
        "📋 *20 derniers membres :*\n\n" + "\n".join(lines),
        parse_mode="Markdown"
    )

async def cmd_bloquer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("Usage: /bloquer [user_id]"); return
    try:
        uid = int(context.args[0])
        db = load_db()
        if uid not in db["bloques"]:
            db["bloques"].append(uid)
            save_db(db)
        await update.message.reply_text(f"✅ User {uid} bloqué.")
    except ValueError:
        await update.message.reply_text("ID invalide.")

async def cmd_aide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *LeMentorFx Bot*\n\n"
        "/start — Démarrer l'inscription\n"
        "/annuler — Annuler\n"
        "/stats — Statistiques *(admin)*\n"
        "/liste — Derniers membres *(admin)*\n"
        "/bloquer [id] — Bloquer un user *(admin)*\n\n"
        f"📢 Canal : {CANAL_PUBLIC}\n"
        "📱 Contact : @lementorfx",
        parse_mode="Markdown"
    )

async def msg_inconnu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Tape /start pour t'inscrire.\nType /start to register."
    )

# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ATTENTE_LANGUE:        [CallbackQueryHandler(cb_langue,        pattern="^lang_")],
            ATTENTE_NOM:           [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_nom)],
            ATTENTE_PAYS:          [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_pays)],
            ATTENTE_EMAIL:         [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_email)],
            ATTENTE_EXNESS_COMPTE: [CallbackQueryHandler(cb_exness_compte, pattern="^ex_")],
            ATTENTE_EXNESS_ID:     [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_exness_id)],
            ATTENTE_CONFIRMATION:  [CallbackQueryHandler(cb_confirmation,  pattern="^(ok|edit)$")],
        },
        fallbacks=[CommandHandler("annuler", annuler)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("stats",   cmd_stats))
    app.add_handler(CommandHandler("liste",   cmd_liste))
    app.add_handler(CommandHandler("bloquer", cmd_bloquer))
    app.add_handler(CommandHandler("aide",    cmd_aide))
    app.add_handler(CommandHandler("help",    cmd_aide))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_inconnu))

    print("✅ LeMentorFx Bot démarré — @lementorfx")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
