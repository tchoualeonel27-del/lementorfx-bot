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
DB_FILE      = "membres.json"

S_LANG, S_NOM, S_PAYS, S_EMAIL, S_EXQ, S_EXID, S_CONFIRM = range(7)

# ── BASE DE DONNÉES ──────────────────────────────────────

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE,"r",encoding="utf-8") as f: return json.load(f)
    return {"membres":{},"en_attente":{},"exness_ids":[],"emails":[],"bloques":[]}

def save_db(db):
    with open(DB_FILE,"w",encoding="utf-8") as f: json.dump(db,f,ensure_ascii=False,indent=2)

def eid_exist(e):  return e in load_db().get("exness_ids",[])
def mail_exist(e): return e.lower() in [x.lower() for x in load_db().get("emails",[])]
def bloque(uid):   return uid in load_db().get("bloques",[])

def mettre_en_attente(uid, d):
    """Sauvegarde le membre en attente de validation manuelle"""
    db = load_db()
    db["en_attente"][str(uid)] = {**d, "date": datetime.now().isoformat(), "statut": "en_attente"}
    save_db(db)

def valider_membre(uid):
    """Valide un membre après vérification Exness"""
    db = load_db()
    uid = str(uid)
    if uid not in db["en_attente"]:
        return None
    d = db["en_attente"].pop(uid)
    d["statut"] = "validé"
    db["membres"][uid] = d
    if d.get("exness_id"): db["exness_ids"].append(d["exness_id"])
    if d.get("email"):     db["emails"].append(d["email"].lower())
    save_db(db)
    return d

def rejeter_membre(uid):
    """Rejette un membre"""
    db = load_db()
    uid = str(uid)
    d = db["en_attente"].pop(uid, None)
    if d:
        d["statut"] = "rejeté"
        db["membres"][uid] = d
        save_db(db)
    return d

# ── TEXTES ───────────────────────────────────────────────

FR = {
"lang":   "🌍 *Choisis ta langue / Choose your language:*",
"bienve": "🤖 *Bienvenue chez LeMentorFx !*\n\nBot officiel de *@lementorfx* — Partenaire IB Exness.\n\n✅ Signaux XAU/USD gratuits\n✅ Éducation SMC/ICT\n✅ Robot EA gratuit *(filleuls Exness)*\n\n2 minutes pour t'inscrire 👇",
"nom":    "👤 *Étape 1/5*\n\nTon *nom complet* ?",
"pays":   "🌍 *Étape 2/5*\n\nTon pays ?",
"email":  "📧 *Étape 3/5*\n\nAdresse email utilisée sur Exness ?\n\n⚠️ Servira à vérifier ton parrainage.",
"ebad":   "❌ Email invalide. Réessaie :",
"edup":   "❌ Email déjà enregistré. Contacte @lementorfx.",
"exq":    "🏦 *Étape 4/5*\n\nAs-tu un compte Exness ?",
"noex":   f"⚠️ Ouvre ton compte Exness gratuitement :\n{EXNESS_LINK}\n\nReviens taper /start une fois inscrit ✅",
"exid":   "🔢 *Étape 5/5*\n\nTon *ID Exness* (7 à 9 chiffres) ?\n\n📌 exness.com → Profil → tableau de bord",
"idbad":  "❌ ID invalide (7-9 chiffres). Réessaie :",
"iddup":  "❌ ID déjà enregistré. Contacte @lementorfx.",
"recap":  "✅ *Vérification*\n\n👤 {nom}\n🌍 {pays}\n📧 {email}\n🏦 ID: {exid}\n📱 @{user}\n\nTout est correct ?",

# ⚠️ NOUVEAU : message d'attente au lieu du lien direct
"attente": (
    "⏳ *Demande envoyée !*\n\n"
    "Tes informations ont été transmises à *@lementorfx* pour vérification.\n\n"
    "📋 *Ce qui se passe maintenant :*\n"
    "1. @lementorfx vérifie ton ID Exness sur son espace partenaire\n"
    "2. Si tu es bien inscrit via le lien de parrainage ✅\n"
    "3. Tu reçois le lien du canal privé directement ici\n\n"
    "⏱ Délai : *quelques heures maximum*\n\n"
    "❓ Des questions ? → @lementorfx"
),

# Message envoyé si rejeté
"rejete": (
    "❌ *Inscription non validée*\n\n"
    "Ton ID Exness *{exid}* n'a pas pu être vérifié comme filleul de @lementorfx.\n\n"
    "💡 *Que faire ?*\n"
    "→ Si tu n'as pas de compte Exness, crée-en un ici :\n"
    f"{EXNESS_LINK}\n\n"
    "→ Si tu en as déjà un, contacte @lementorfx pour régulariser.\n\n"
    "Une fois fait, retape /start."
),

# Message envoyé si validé (avec lien)
"valide": (
    "🎉 *Accès accordé !*\n\n"
    "Ton parrainage Exness a été vérifié ✅\n\n"
    "🔐 *Ton lien d'accès au canal privé :*\n"
    "👇👇👇\n{canal}\n👆👆👆\n\n"
    "Active les notifications 🔔\n"
    "Lis les règles épinglées 📌\n\n"
    "Questions → @lementorfx"
),

"cancel": "❌ Annulé. /start pour recommencer.",
}

EN = {
"lang":   "🌍 *Choisis ta langue / Choose your language:*",
"bienve": "🤖 *Welcome to LeMentorFx!*\n\nOfficial bot of *@lementorfx* — Exness IB Partner.\n\n✅ Free XAU/USD signals\n✅ SMC/ICT education\n✅ Free EA Robot *(Exness referrals)*\n\n2 minutes to register 👇",
"nom":    "👤 *Step 1/5*\n\nYour *full name*?",
"pays":   "🌍 *Step 2/5*\n\nYour country?",
"email":  "📧 *Step 3/5*\n\nEmail used on Exness?\n\n⚠️ Used to verify your referral.",
"ebad":   "❌ Invalid email. Try again:",
"edup":   "❌ Email already registered. Contact @lementorfx.",
"exq":    "🏦 *Step 4/5*\n\nDo you have an Exness account?",
"noex":   f"⚠️ Open your Exness account for free:\n{EXNESS_LINK}\n\nCome back and type /start once registered ✅",
"exid":   "🔢 *Step 5/5*\n\nYour *Exness ID* (7 to 9 digits)?\n\n📌 exness.com → Profile → dashboard",
"idbad":  "❌ Invalid ID (7-9 digits). Try again:",
"iddup":  "❌ ID already registered. Contact @lementorfx.",
"recap":  "✅ *Review*\n\n👤 {nom}\n🌍 {pays}\n📧 {email}\n🏦 ID: {exid}\n📱 @{user}\n\nIs everything correct?",

"attente": (
    "⏳ *Request submitted!*\n\n"
    "Your information has been sent to *@lementorfx* for verification.\n\n"
    "📋 *What happens next:*\n"
    "1. @lementorfx verifies your Exness ID in his partner dashboard\n"
    "2. If you registered via the referral link ✅\n"
    "3. You receive the private channel link directly here\n\n"
    "⏱ Delay: *a few hours maximum*\n\n"
    "❓ Questions? → @lementorfx"
),

"rejete": (
    "❌ *Registration not approved*\n\n"
    "Your Exness ID *{exid}* could not be verified as a referral of @lementorfx.\n\n"
    "💡 *What to do?*\n"
    "→ If you don't have an Exness account, create one here:\n"
    f"{EXNESS_LINK}\n\n"
    "→ If you already have one, contact @lementorfx.\n\n"
    "Then type /start again."
),

"valide": (
    "🎉 *Access granted!*\n\n"
    "Your Exness referral has been verified ✅\n\n"
    "🔐 *Your private channel access link:*\n"
    "👇👇👇\n{canal}\n👆👆👆\n\n"
    "Enable notifications 🔔\n"
    "Read the pinned rules 📌\n\n"
    "Questions → @lementorfx"
),

"cancel": "❌ Cancelled. /start to restart.",
}

def g(lang, key, **kw):
    d = FR if lang=="fr" else EN
    s = d.get(key,"")
    return s.format(**kw) if kw else s

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)

# ── CONVERSATION ─────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if bloque(update.effective_user.id):
        await update.message.reply_text("⛔"); return ConversationHandler.END
    ctx.user_data.clear()
    ctx.user_data["u"] = update.effective_user.username or str(update.effective_user.id)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🇫🇷 Français", callback_data="L_fr"),
        InlineKeyboardButton("🇬🇧 English",  callback_data="L_en"),
    ]])
    await update.message.reply_text(FR["lang"], parse_mode="Markdown", reply_markup=kb)
    return S_LANG

async def cb_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = "fr" if q.data=="L_fr" else "en"
    ctx.user_data["l"] = lang
    await q.edit_message_text(g(lang,"bienve"), parse_mode="Markdown")
    await q.message.reply_text(g(lang,"nom"), parse_mode="Markdown")
    return S_NOM

async def h_nom(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    l = ctx.user_data.get("l","fr")
    v = update.message.text.strip()
    if len(v)<2: await update.message.reply_text("❌ Trop court."); return S_NOM
    ctx.user_data["nom"] = v
    await update.message.reply_text(g(l,"pays"), parse_mode="Markdown")
    return S_PAYS

async def h_pays(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    l = ctx.user_data.get("l","fr")
    ctx.user_data["pays"] = update.message.text.strip()
    await update.message.reply_text(g(l,"email"), parse_mode="Markdown")
    return S_EMAIL

async def h_email(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    l = ctx.user_data.get("l","fr")
    v = update.message.text.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$",v):
        await update.message.reply_text(g(l,"ebad"), parse_mode="Markdown"); return S_EMAIL
    if mail_exist(v):
        await update.message.reply_text(g(l,"edup"), parse_mode="Markdown"); return ConversationHandler.END
    ctx.user_data["email"] = v
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Oui / Yes",              callback_data="EX_oui")],
        [InlineKeyboardButton("❌ Pas encore / Not yet",   callback_data="EX_non")],
        [InlineKeyboardButton("🔄 En cours / In progress", callback_data="EX_oui")],
    ])
    await update.message.reply_text(g(l,"exq"), parse_mode="Markdown", reply_markup=kb)
    return S_EXQ

async def cb_exq(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    l = ctx.user_data.get("l","fr")
    if q.data=="EX_non":
        await q.edit_message_text(g(l,"noex"), parse_mode="Markdown"); return ConversationHandler.END
    await q.edit_message_text(g(l,"exid"), parse_mode="Markdown")
    return S_EXID

async def h_exid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    l = ctx.user_data.get("l","fr")
    v = update.message.text.strip().replace(" ","")
    if not re.match(r"^\d{7,9}$",v):
        await update.message.reply_text(g(l,"idbad"), parse_mode="Markdown"); return S_EXID
    if eid_exist(v):
        await update.message.reply_text(g(l,"iddup"), parse_mode="Markdown"); return ConversationHandler.END
    ctx.user_data["exid"] = v
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Confirmer / Confirm", callback_data="C_ok"),
        InlineKeyboardButton("✏️ Corriger / Edit",     callback_data="C_edit"),
    ]])
    await update.message.reply_text(
        g(l,"recap", nom=ctx.user_data.get("nom","—"), pays=ctx.user_data.get("pays","—"),
          email=ctx.user_data.get("email","—"), exid=v, user=ctx.user_data.get("u","—")),
        parse_mode="Markdown", reply_markup=kb)
    return S_CONFIRM

async def cb_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    l = ctx.user_data.get("l","fr")
    if q.data=="C_edit":
        await q.edit_message_text(g(l,"exid"), parse_mode="Markdown"); return S_EXID

    uid  = update.effective_user.id
    nom  = ctx.user_data.get("nom","—")
    pays = ctx.user_data.get("pays","—")
    email= ctx.user_data.get("email","—")
    exid = ctx.user_data.get("exid","—")
    user = ctx.user_data.get("u","—")

    # Sauvegarde EN ATTENTE (pas validé encore)
    mettre_en_attente(uid, {
        "nom":nom,"pays":pays,"email":email,
        "exness_id":exid,"username":user,"lang":l,"user_id":uid
    })

    # Message au client : attendre la vérification
    await q.edit_message_text(g(l,"attente"), parse_mode="Markdown")

    # ── NOTIFICATION ADMIN avec boutons VALIDER / REJETER ──
    kb_admin = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ VALIDER",  callback_data=f"ADM_ok_{uid}"),
        InlineKeyboardButton("❌ REJETER",  callback_data=f"ADM_no_{uid}"),
    ]])
    try:
        await ctx.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"🆕 *NOUVELLE DEMANDE*\n\n"
                f"👤 {nom}\n🌍 {pays}\n📧 {email}\n"
                f"🏦 ID Exness: `{exid}`\n📱 @{user}\n🆔 {uid}\n"
                f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                f"📌 *Vérifie sur ton espace Exness que cet ID / email est bien ton filleul.*\n"
                f"Puis clique ✅ VALIDER ou ❌ REJETER ci-dessous."
            ),
            parse_mode="Markdown",
            reply_markup=kb_admin
        )
    except Exception as e:
        logging.warning(f"notif admin: {e}")

    return ConversationHandler.END

# ── ADMIN : VALIDER OU REJETER ────────────────────────────

async def cb_admin_decision(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await q.answer("⛔ Non autorisé."); return
    await q.answer()

    parts = q.data.split("_")  # ADM_ok_12345 ou ADM_no_12345
    action = parts[1]
    uid    = int(parts[2])

    if action == "ok":
        d = valider_membre(uid)
        if not d:
            await q.edit_message_text(f"⚠️ Membre {uid} introuvable en attente."); return

        # Envoie le lien au client
        lang = d.get("lang","fr")
        try:
            await ctx.bot.send_message(
                chat_id=uid,
                text=g(lang,"valide", canal=CANAL_PRIVE),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.warning(f"Envoi lien client: {e}")

        await q.edit_message_text(
            f"✅ *Validé et lien envoyé à {d.get('nom','?')}* (@{d.get('username','?')})\n"
            f"🏦 ID Exness: {d.get('exness_id','?')}",
            parse_mode="Markdown"
        )

    elif action == "no":
        d = rejeter_membre(uid)
        if not d:
            await q.edit_message_text(f"⚠️ Membre {uid} introuvable."); return

        lang = d.get("lang","fr")
        try:
            await ctx.bot.send_message(
                chat_id=uid,
                text=g(lang,"rejete", exid=d.get("exness_id","?")),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.warning(f"Envoi rejet client: {e}")

        await q.edit_message_text(
            f"❌ *Rejeté : {d.get('nom','?')}* (@{d.get('username','?')})\n"
            f"🏦 ID: {d.get('exness_id','?')}",
            parse_mode="Markdown"
        )

# ── COMMANDES ADMIN ───────────────────────────────────────

async def cmd_attente(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    items = list(db.get("en_attente",{}).values())
    if not items: await update.message.reply_text("✅ Aucune demande en attente."); return
    lines = [f"• *{x.get('nom','?')}* | {x.get('email','?')} | ID:{x.get('exness_id','?')} | uid:{x.get('user_id','?')}" for x in items]
    await update.message.reply_text("⏳ *Demandes en attente :*\n\n"+"\n".join(lines), parse_mode="Markdown")

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    await update.message.reply_text(
        f"📊 *Stats LeMentorFx*\n\n"
        f"👥 Membres validés : *{len(db['membres'])}*\n"
        f"⏳ En attente : *{len(db.get('en_attente',{}))}*\n"
        f"🏦 IDs Exness : *{len(db['exness_ids'])}*\n"
        f"📧 Emails : *{len(db['emails'])}*",
        parse_mode="Markdown")

async def cmd_liste(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    items = [x for x in list(db["membres"].values()) if x.get("statut")=="validé"][-15:]
    if not items: await update.message.reply_text("Aucun membre validé."); return
    lines = [f"• {x.get('nom','?')} | {x.get('pays','?')} | {x.get('email','?')} | {x.get('exness_id','?')}" for x in items]
    await update.message.reply_text("📋 *Membres validés :*\n\n"+"\n".join(lines), parse_mode="Markdown")

async def cmd_bloquer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not ctx.args: await update.message.reply_text("Usage: /bloquer [id]"); return
    try:
        uid=int(ctx.args[0]); db=load_db()
        if uid not in db["bloques"]: db["bloques"].append(uid); save_db(db)
        await update.message.reply_text(f"✅ {uid} bloqué.")
    except: await update.message.reply_text("ID invalide.")

async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    l = ctx.user_data.get("l","fr")
    await update.message.reply_text(g(l,"cancel")); return ConversationHandler.END

async def msg_other(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tape /start pour t'inscrire. / Type /start to register.")

# ── MAIN ─────────────────────────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            S_LANG:    [CallbackQueryHandler(cb_lang,    pattern="^L_")],
            S_NOM:     [MessageHandler(filters.TEXT & ~filters.COMMAND, h_nom)],
            S_PAYS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, h_pays)],
            S_EMAIL:   [MessageHandler(filters.TEXT & ~filters.COMMAND, h_email)],
            S_EXQ:     [CallbackQueryHandler(cb_exq,    pattern="^EX_")],
            S_EXID:    [MessageHandler(filters.TEXT & ~filters.COMMAND, h_exid)],
            S_CONFIRM: [CallbackQueryHandler(cb_confirm, pattern="^C_")],
        },
        fallbacks=[CommandHandler("annuler", cmd_cancel), CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    # Handler admin VALIDER/REJETER — doit être en dehors de la conversation
    app.add_handler(CallbackQueryHandler(cb_admin_decision, pattern="^ADM_"))
    app.add_handler(CommandHandler("stats",    cmd_stats))
    app.add_handler(CommandHandler("liste",    cmd_liste))
    app.add_handler(CommandHandler("attente",  cmd_attente))
    app.add_handler(CommandHandler("bloquer",  cmd_bloquer))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_other))

    print("✅ LeMentorFx Bot v2 démarré — vérification manuelle activée")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
