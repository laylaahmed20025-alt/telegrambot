"""
╔══════════════════════════════════════════╗
║       SnatchTik Bot — v2.0 Pro           ║
║  TikTok · Facebook · Instagram           ║
╚══════════════════════════════════════════╝
"""

import os, logging, httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN     = os.environ["BOT_TOKEN"]
TIKTOK_KEY    = os.environ.get("TIKTOK_API_KEY", "")
RAPIDAPI_KEY  = os.environ.get("RAPIDAPI_KEY", "")
FASTSAVER_KEY = os.environ.get("FASTSAVER_API_KEY", "")
LINKTREE      = "https://linktr.ee/snatchtik"
WEBSITE       = "https://snatchtik.com"

# ── In-memory stats ───────────────────────────────────────────────────────────
stats = {"total": 0, "tiktok": 0, "facebook": 0, "instagram": 0, "users": set()}

# ── Brand strings ─────────────────────────────────────────────────────────────
BRAND_FOOTER = f"\n\n━━━━━━━━━━━━━━━━━━━━\n🌐 [SnatchTik.com]({WEBSITE})  •  🔗 [روابطنا]({LINKTREE})"

LOADING_FRAMES = [
    "⬛⬛⬛⬛⬛  0%",
    "🟩⬛⬛⬛⬛  20%",
    "🟩🟩⬛⬛⬛  40%",
    "🟩🟩🟩⬛⬛  60%",
    "🟩🟩🟩🟩⬛  80%",
    "🟩🟩🟩🟩🟩  100% ✅",
]

# ── Platform detection ────────────────────────────────────────────────────────
def detect_platform(url: str) -> str:
    u = url.lower()
    if "tiktok.com" in u or "vm.tiktok.com" in u: return "tiktok"
    if "facebook.com" in u or "fb.watch" in u or "fb.com" in u: return "facebook"
    if "instagram.com" in u or "instagr.am" in u: return "instagram"
    return "other"

def is_url(text: str) -> bool:
    return text.strip().startswith(("http://", "https://"))

def trim(text: str, n: int = 180) -> str:
    return (text[:n] + "…") if text and len(text) > n else (text or "")

# ── API callers ───────────────────────────────────────────────────────────────
async def api_tiktok(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get("https://api.tikwmapi.com/",
                            params={"url": url, "hd": 1},
                            headers={"x-tikwmapi-key": TIKTOK_KEY})
            if r.status_code == 200:
                d = r.json()
                if d.get("code") == 0 and "data" in d:
                    return d["data"]
    except Exception as e:
        logger.error(f"[tiktok api] {e}")
    return {}

async def api_facebook(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                "https://free-facebook-downloader.p.rapidapi.com/external-api/facebook-video-downloader",
                params={"url": url}, json={"key1": "value", "key2": "value"},
                headers={"x-rapidapi-key": RAPIDAPI_KEY,
                         "x-rapidapi-host": "free-facebook-downloader.p.rapidapi.com",
                         "Content-Type": "application/json"})
            if r.status_code == 200:
                d = r.json()
                if d.get("success") and "links" in d:
                    return {"hdplay": d["links"].get("Download High Quality"),
                            "play":   d["links"].get("Download Low Quality")}
    except Exception as e:
        logger.error(f"[facebook api] {e}")
    return {}

async def api_instagram(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get("https://api.fastsaver.io/v1/fetch",
                            params={"url": url}, headers={"X-Api-Key": FASTSAVER_KEY})
            if r.status_code == 200:
                d = r.json()
                if d.get("ok"):
                    result = {"title": d.get("title") or d.get("caption") or "Instagram Post",
                              "type": d.get("type"),
                              "hdplay": d.get("download_url") if d.get("type") == "video" else None,
                              "thumbnail": d.get("thumbnail_url"), "images": []}
                    if d.get("type") == "album" and "items" in d:
                        result["images"] = [i.get("download_url") for i in d["items"] if i.get("type") == "image"]
                    elif d.get("type") == "image":
                        result["images"] = [d.get("download_url")]
                    return result
    except Exception as e:
        logger.error(f"[instagram api] {e}")
    return {}

# ── Main menu keyboard ────────────────────────────────────────────────────────
def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 TikTok", callback_data="guide_tiktok"),
         InlineKeyboardButton("📘 Facebook", callback_data="guide_facebook"),
         InlineKeyboardButton("📸 Instagram", callback_data="guide_instagram")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"),
         InlineKeyboardButton("❓ المساعدة", callback_data="help")],
        [InlineKeyboardButton("🌐 الموقع الرسمي", url=WEBSITE),
         InlineKeyboardButton("🔗 روابطنا", url=LINKTREE)],
    ])

def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]])

# ── /start ────────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    stats["users"].add(user.id)
    name = user.first_name or "صديقي"
    text = (
        f"✨ *أهلاً وسهلاً، {name}!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🚀 *SnatchTik Bot* — أقوى بوت لتحميل الفيديوهات\n\n"
        "🎯 *ما الذي يمكنني فعله؟*\n"
        "┣ 🎵 تحميل TikTok بدون علامة مائية\n"
        "┣ 🎧 استخراج الصوت MP3 من TikTok\n"
        "┣ 📘 تحميل فيديوهات Facebook (HD)\n"
        "┗ 📸 تحميل صور وفيديوهات Instagram\n\n"
        "⚡ *كيف تستخدمني؟*\n"
        "فقط أرسل الرابط مباشرةً وأنا سأتكفل بالباقي!\n\n"
        "🔥 *سريع · مجاني · بدون علامة مائية*"
        f"{BRAND_FOOTER}"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode=constants.ParseMode.MARKDOWN,
                                         reply_markup=main_menu_kb(), disable_web_page_preview=True)
    else:
        await update.callback_query.edit_message_text(text, parse_mode=constants.ParseMode.MARKDOWN,
                                                       reply_markup=main_menu_kb(), disable_web_page_preview=True)

# ── /stats ────────────────────────────────────────────────────────────────────
async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📊 *إحصائيات SnatchTik Bot*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 إجمالي التحميلات: `{stats['total']:,}`\n"
        f"🎵 TikTok: `{stats['tiktok']:,}`\n"
        f"📘 Facebook: `{stats['facebook']:,}`\n"
        f"📸 Instagram: `{stats['instagram']:,}`\n"
        f"👥 المستخدمون الفريدون: `{len(stats['users']):,}`"
        f"{BRAND_FOOTER}"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode=constants.ParseMode.MARKDOWN,
                                         reply_markup=back_kb(), disable_web_page_preview=True)
    else:
        await update.callback_query.edit_message_text(text, parse_mode=constants.ParseMode.MARKDOWN,
                                                       reply_markup=back_kb(), disable_web_page_preview=True)

# ── /help ─────────────────────────────────────────────────────────────────────
async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "❓ *دليل الاستخدام*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "*📋 الأوامر المتاحة:*\n"
        "┣ /start — الصفحة الرئيسية\n"
        "┣ /help  — هذا الدليل\n"
        "┗ /stats — الإحصائيات\n\n"
        "*🎯 خطوات التحميل:*\n"
        "1️⃣ افتح TikTok / Facebook / Instagram\n"
        "2️⃣ انسخ رابط الفيديو أو المنشور\n"
        "3️⃣ الصقه هنا وأرسله\n"
        "4️⃣ اضغط زر التحميل ✅\n\n"
        "*⚠️ ملاحظات مهمة:*\n"
        "┣ فيديوهات Facebook يجب أن تكون عامة\n"
        "┣ حسابات Instagram يجب أن تكون عامة\n"
        "┗ روابط التحميل صالحة لفترة محدودة\n\n"
        "*🆘 هل واجهت مشكلة؟*\n"
        f"زر موقعنا: [snatchtik.com]({WEBSITE})"
        f"{BRAND_FOOTER}"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode=constants.ParseMode.MARKDOWN,
                                         reply_markup=back_kb(), disable_web_page_preview=True)
    else:
        await update.callback_query.edit_message_text(text, parse_mode=constants.ParseMode.MARKDOWN,
                                                       reply_markup=back_kb(), disable_web_page_preview=True)

# ── Callback buttons ──────────────────────────────────────────────────────────
GUIDE = {
    "guide_tiktok": (
        "🎵 *دليل تحميل TikTok*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ *ما يدعمه البوت:*\n"
        "┣ فيديو HD بدون علامة مائية\n"
        "┣ استخراج الصوت MP3\n"
        "┗ روابط vm.tiktok.com المختصرة\n\n"
        "📋 *طريقة الاستخدام:*\n"
        "أرسل رابط TikTok مباشرةً الآن ⬇️"
    ),
    "guide_facebook": (
        "📘 *دليل تحميل Facebook*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ *ما يدعمه البوت:*\n"
        "┣ فيديو جودة عالية HD\n"
        "┗ فيديو جودة عادية SD\n\n"
        "⚠️ *شروط:*\n"
        "┗ يجب أن يكون الفيديو عاماً (Public)\n\n"
        "📋 *طريقة الاستخدام:*\n"
        "أرسل رابط Facebook مباشرةً الآن ⬇️"
    ),
    "guide_instagram": (
        "📸 *دليل تحميل Instagram*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ *ما يدعمه البوت:*\n"
        "┣ فيديو Reels\n"
        "┣ صورة منفردة\n"
        "┗ ألبوم صور (Carousel)\n\n"
        "⚠️ *شروط:*\n"
        "┗ يجب أن يكون الحساب عاماً (Public)\n\n"
        "📋 *طريقة الاستخدام:*\n"
        "أرسل رابط Instagram مباشرةً الآن ⬇️"
    ),
}

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "main_menu":
        await cmd_start(update, ctx)
    elif data == "stats":
        await cmd_stats(update, ctx)
    elif data == "help":
        await cmd_help(update, ctx)
    elif data in GUIDE:
        await q.edit_message_text(
            GUIDE[data] + BRAND_FOOTER,
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=back_kb(),
            disable_web_page_preview=True,
        )

# ── Animated loading ──────────────────────────────────────────────────────────
import asyncio

async def animate_loading(msg, platform_line: str):
    for frame in LOADING_FRAMES[:-1]:
        try:
            await msg.edit_text(
                f"⚙️ *جاري المعالجة...*\n{platform_line}\n\n{frame}",
                parse_mode=constants.ParseMode.MARKDOWN,
            )
            await asyncio.sleep(0.6)
        except Exception:
            break

# ── Result cards ──────────────────────────────────────────────────────────────
def tiktok_card(data: dict) -> tuple[str, InlineKeyboardMarkup]:
    title    = trim(data.get("title", "TikTok Video"))
    author   = (data.get("author") or {}).get("nickname", "—")
    likes    = data.get("digg_count", 0)
    comments = data.get("comment_count", 0)
    shares   = data.get("share_count", 0)
    video_hd = data.get("hdplay") or data.get("play") or data.get("wmplay")
    video_sd = data.get("play") or data.get("wmplay")
    audio    = data.get("music") or (data.get("music_info") or {}).get("play")
    duration = data.get("duration", 0)

    text = (
        f"🎵 *{title}*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 `{author}`\n"
        f"⏱ المدة: `{duration}s`\n\n"
        f"❤️ `{likes:,}`  💬 `{comments:,}`  🔁 `{shares:,}`"
        f"{BRAND_FOOTER}"
    )
    btns = []
    if video_hd:
        btns.append([InlineKeyboardButton("📥 تحميل HD (بدون علامة)", url=video_hd)])
    if video_sd and video_sd != video_hd:
        btns.append([InlineKeyboardButton("📥 تحميل SD", url=video_sd)])
    if audio:
        btns.append([InlineKeyboardButton("🎵 تحميل MP3 فقط", url=audio)])
    btns.append([InlineKeyboardButton("🌐 الموقع", url=WEBSITE),
                 InlineKeyboardButton("🔗 روابطنا", url=LINKTREE)])
    return text, InlineKeyboardMarkup(btns)

def facebook_card(data: dict) -> tuple[str, InlineKeyboardMarkup]:
    text = (
        "📘 *Facebook Video*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ تم جلب الفيديو بنجاح!\n"
        "اختر جودة التحميل:"
        f"{BRAND_FOOTER}"
    )
    btns = []
    if data.get("hdplay"):
        btns.append([InlineKeyboardButton("📥 تحميل HD جودة عالية", url=data["hdplay"])])
    if data.get("play"):
        btns.append([InlineKeyboardButton("📥 تحميل SD جودة عادية", url=data["play"])])
    btns.append([InlineKeyboardButton("🌐 الموقع", url=WEBSITE),
                 InlineKeyboardButton("🔗 روابطنا", url=LINKTREE)])
    return text, InlineKeyboardMarkup(btns)

def instagram_card(data: dict) -> tuple[str, list, InlineKeyboardMarkup]:
    title  = trim(data.get("title", "Instagram Post"))
    mtype  = data.get("type", "")
    vurl   = data.get("hdplay")
    images = data.get("images", [])
    icons  = {"video": "🎬", "image": "🖼", "album": "🖼"}
    icon   = icons.get(mtype, "📸")
    text = (
        f"📸 *{title}*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{icon} النوع: `{mtype}`\n"
        f"{'🖼 عدد الصور: `' + str(len(images)) + '`' if mtype == 'album' else ''}"
        f"{BRAND_FOOTER}"
    )
    btns = []
    if vurl:
        btns.append([InlineKeyboardButton("📥 تحميل الفيديو", url=vurl)])
    elif images:
        if mtype == "album":
            for i, img in enumerate(images[:8]):
                btns.append([InlineKeyboardButton(f"🖼 تحميل الصورة {i+1}", url=img)])
        else:
            btns.append([InlineKeyboardButton("📥 تحميل الصورة", url=images[0])])
    btns.append([InlineKeyboardButton("🌐 الموقع", url=WEBSITE),
                 InlineKeyboardButton("🔗 روابطنا", url=LINKTREE)])
    thumb = data.get("thumbnail") if mtype == "video" else (images[0] if images else None)
    return text, thumb, InlineKeyboardMarkup(btns)

# ── URL handler ───────────────────────────────────────────────────────────────
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    user = update.effective_user
    stats["users"].add(user.id)

    if not is_url(text):
        await update.message.reply_text(
            "🤔 *لم أفهم رسالتك!*\n\n"
            "أرسل رابطاً مباشراً من:\n"
            "🎵 TikTok  •  📘 Facebook  •  📸 Instagram\n\n"
            "أو اضغط /start للقائمة الرئيسية",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=main_menu_kb(),
        )
        return

    platform = detect_platform(text)
    if platform == "other":
        await update.message.reply_text(
            "⚠️ *رابط غير مدعوم*\n\n"
            "نحن ندعم فقط:\n"
            "🎵 TikTok  •  📘 Facebook  •  📸 Instagram",
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=back_kb(),
        )
        return

    icons = {"tiktok": "🎵", "facebook": "📘", "instagram": "📸"}
    loading = await update.message.reply_text(
        f"⚙️ *جاري المعالجة...*\n{icons[platform]} {platform.capitalize()}\n\n⬛⬛⬛⬛⬛  0%",
        parse_mode=constants.ParseMode.MARKDOWN,
    )
    await animate_loading(loading, f"{icons[platform]} {platform.capitalize()}")

    try:
        if platform == "tiktok":
            data = await api_tiktok(text)
            if not data:
                raise ValueError("no_data")
            video_url = data.get("hdplay") or data.get("play") or data.get("wmplay")
            if not video_url:
                raise ValueError("no_url")
            cover = data.get("cover")
            card_text, kb = tiktok_card(data)
            await loading.delete()
            stats["total"] += 1; stats["tiktok"] += 1
            if cover:
                try:
                    await update.message.reply_photo(photo=cover, caption=card_text,
                        parse_mode=constants.ParseMode.MARKDOWN, reply_markup=kb)
                    return
                except Exception:
                    pass
            await update.message.reply_text(card_text, parse_mode=constants.ParseMode.MARKDOWN,
                                             reply_markup=kb, disable_web_page_preview=True)

        elif platform == "facebook":
            data = await api_facebook(text)
            if not data or (not data.get("hdplay") and not data.get("play")):
                raise ValueError("no_data")
            card_text, kb = facebook_card(data)
            await loading.delete()
            stats["total"] += 1; stats["facebook"] += 1
            await update.message.reply_text(card_text, parse_mode=constants.ParseMode.MARKDOWN,
                                             reply_markup=kb, disable_web_page_preview=True)

        elif platform == "instagram":
            data = await api_instagram(text)
            if not data:
                raise ValueError("no_data")
            card_text, thumb, kb = instagram_card(data)
            await loading.delete()
            stats["total"] += 1; stats["instagram"] += 1
            if thumb:
                try:
                    await update.message.reply_photo(photo=thumb, caption=card_text,
                        parse_mode=constants.ParseMode.MARKDOWN, reply_markup=kb)
                    return
                except Exception:
                    pass
            await update.message.reply_text(card_text, parse_mode=constants.ParseMode.MARKDOWN,
                                             reply_markup=kb, disable_web_page_preview=True)

    except ValueError as ve:
        err_map = {
            "no_data": "❌ *تعذّر جلب البيانات*\n\nتأكد من:\n┣ صحة الرابط\n┣ أن المحتوى عام\n┗ حاول مرة أخرى",
            "no_url":  "❌ *لا يوجد رابط تحميل*\n\nالفيديو غير متاح أو محمي.",
        }
        msg = err_map.get(str(ve), "❌ خطأ غير متوقع.")
        try:
            await loading.edit_text(msg + BRAND_FOOTER, parse_mode=constants.ParseMode.MARKDOWN,
                                     reply_markup=back_kb(), disable_web_page_preview=True)
        except Exception:
            pass
    except Exception as e:
        logger.error(f"[handle_message] {e}", exc_info=True)
        try:
            await loading.edit_text(
                "❌ *حدث خطأ أثناء المعالجة*\n\nيرجى المحاولة مرة أخرى." + BRAND_FOOTER,
                parse_mode=constants.ParseMode.MARKDOWN, reply_markup=back_kb(), disable_web_page_preview=True)
        except Exception:
            pass

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🤖 SnatchTik Pro Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
