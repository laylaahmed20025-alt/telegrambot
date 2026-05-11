"""
SnatchTik Bot v3.0 — Ultra Pro
Direct video delivery · HTML formatting · Linktree branding
"""

import os, logging, asyncio, httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN     = os.environ["BOT_TOKEN"]
TIKTOK_KEY    = os.environ.get("TIKTOK_API_KEY", "")
RAPIDAPI_KEY  = os.environ.get("RAPIDAPI_KEY", "")
FASTSAVER_KEY = os.environ.get("FASTSAVER_API_KEY", "")
LINKTREE      = "https://linktr.ee/snatchtik"

# ── Stats ─────────────────────────────────────────────────────────────────────
stats = {"total": 0, "tiktok": 0, "facebook": 0, "instagram": 0, "users": set()}

# ── HTML helpers ──────────────────────────────────────────────────────────────
def b(t): return f"<b>{t}</b>"
def i(t): return f"<i>{t}</i>"
def code(t): return f"<code>{t}</code>"
def link(label, url): return f'<a href="{url}">{label}</a>'

DIVIDER = "──────────────────────"
FOOTER  = f'\n{DIVIDER}\n{link("⬡  SnatchTik — All Links", LINKTREE)}'

# ── Platform detection ────────────────────────────────────────────────────────
def detect(url: str) -> str:
    u = url.lower()
    if "tiktok.com" in u: return "tiktok"
    if "facebook.com" in u or "fb.watch" in u or "fb.com" in u: return "facebook"
    if "instagram.com" in u or "instagr.am" in u: return "instagram"
    return "other"

def is_url(t: str) -> bool:
    return t.strip().startswith(("http://", "https://"))

def trim(t: str, n=160) -> str:
    if not t: return ""
    return t[:n] + ("…" if len(t) > n else "")

# ── API calls ─────────────────────────────────────────────────────────────────
async def api_tiktok(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get("https://api.tikwmapi.com/",
                            params={"url": url, "hd": 1},
                            headers={"x-tikwmapi-key": TIKTOK_KEY})
            if r.status_code == 200:
                d = r.json()
                if d.get("code") == 0:
                    return d.get("data", {})
    except Exception as e:
        logger.error(f"[tiktok] {e}")
    return {}

async def api_facebook(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(
                "https://free-facebook-downloader.p.rapidapi.com/external-api/facebook-video-downloader",
                params={"url": url}, json={"key1": "value", "key2": "value"},
                headers={"x-rapidapi-key": RAPIDAPI_KEY,
                         "x-rapidapi-host": "free-facebook-downloader.p.rapidapi.com",
                         "Content-Type": "application/json"})
            if r.status_code == 200:
                d = r.json()
                if d.get("success") and "links" in d:
                    return {"hd": d["links"].get("Download High Quality"),
                            "sd": d["links"].get("Download Low Quality")}
    except Exception as e:
        logger.error(f"[facebook] {e}")
    return {}

async def api_instagram(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get("https://api.fastsaver.io/v1/fetch",
                            params={"url": url},
                            headers={"X-Api-Key": FASTSAVER_KEY})
            if r.status_code == 200:
                d = r.json()
                if d.get("ok"):
                    res = {"title": d.get("title") or d.get("caption") or "Instagram",
                           "type": d.get("type"),
                           "video": d.get("download_url") if d.get("type") == "video" else None,
                           "thumb": d.get("thumbnail_url"),
                           "images": []}
                    if d.get("type") == "album":
                        res["images"] = [x.get("download_url") for x in d.get("items", []) if x.get("type") == "image"]
                    elif d.get("type") == "image":
                        res["images"] = [d.get("download_url")]
                    return res
    except Exception as e:
        logger.error(f"[instagram] {e}")
    return {}

# ── Keyboards ─────────────────────────────────────────────────────────────────
def home_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("TikTok", callback_data="g:tiktok"),
         InlineKeyboardButton("Facebook", callback_data="g:facebook"),
         InlineKeyboardButton("Instagram", callback_data="g:instagram")],
        [InlineKeyboardButton("الإحصائيات", callback_data="stats"),
         InlineKeyboardButton("المساعدة", callback_data="help")],
        [InlineKeyboardButton("روابط SnatchTik", url=LINKTREE)],
    ])

def back_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("القائمة الرئيسية", callback_data="home")]])

def url_kb(rows: list):
    """rows = list of (label, url)"""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, url=u)] for label, u in rows] +
        [[InlineKeyboardButton("روابط SnatchTik", url=LINKTREE)]]
    )

# ── Screens ───────────────────────────────────────────────────────────────────
HOME_TEXT = (
    f"{b('SnatchTik')}\n"
    f"{DIVIDER}\n"
    f"حمّل فيديوهاتك بدون علامة مائية\n\n"
    f"{b('المنصات المدعومة')}\n"
    f"  TikTok · Facebook · Instagram\n\n"
    f"{b('كيف تستخدم البوت؟')}\n"
    f"  أرسل الرابط مباشرةً\n"
    f"  البوت سيرسل الفيديو تلقائياً\n"
    f"{FOOTER}"
)

HELP_TEXT = (
    f"{b('دليل الاستخدام')}\n"
    f"{DIVIDER}\n\n"
    f"{b('الخطوات')}\n"
    f"  ١ — انسخ رابط الفيديو\n"
    f"  ٢ — الصقه هنا وأرسله\n"
    f"  ٣ — الفيديو يصلك مباشرةً\n\n"
    f"{b('الأوامر')}\n"
    f"  /start   القائمة الرئيسية\n"
    f"  /help    هذا الدليل\n"
    f"  /stats   الإحصائيات\n\n"
    f"{b('ملاحظات')}\n"
    f"  Facebook — يجب أن يكون الفيديو عاماً\n"
    f"  Instagram — يجب أن يكون الحساب عاماً\n"
    f"  الفيديوهات الكبيرة تُرسَل كرابط تحميل"
    f"{FOOTER}"
)

GUIDES = {
    "tiktok":    (f"{b('TikTok')}\n{DIVIDER}\n\nيدعم البوت:\n  فيديو HD بدون علامة مائية\n  استخراج الصوت MP3\n  الروابط المختصرة vm.tiktok.com\n\nأرسل الرابط الآن" + FOOTER),
    "facebook":  (f"{b('Facebook')}\n{DIVIDER}\n\nيدعم البوت:\n  جودة عالية HD\n  جودة عادية SD\n\nشرط: الفيديو يجب أن يكون عاماً\n\nأرسل الرابط الآن" + FOOTER),
    "instagram": (f"{b('Instagram')}\n{DIVIDER}\n\nيدعم البوت:\n  Reels وفيديوهات\n  صورة منفردة\n  ألبوم صور\n\nشرط: الحساب يجب أن يكون عاماً\n\nأرسل الرابط الآن" + FOOTER),
}

def stats_text():
    return (
        f"{b('إحصائيات SnatchTik Bot')}\n"
        f"{DIVIDER}\n\n"
        f"إجمالي التحميلات   {code(f\"{stats['total']:,}\")}\n"
        f"TikTok             {code(f\"{stats['tiktok']:,}\")}\n"
        f"Facebook           {code(f\"{stats['facebook']:,}\")}\n"
        f"Instagram          {code(f\"{stats['instagram']:,}\")}\n"
        f"المستخدمون         {code(f\"{len(stats['users']):,}\")}"
        f"{FOOTER}"
    )

# ── Loading animation ─────────────────────────────────────────────────────────
BARS = ["▱▱▱▱▱", "▰▱▱▱▱", "▰▰▱▱▱", "▰▰▰▱▱", "▰▰▰▰▱", "▰▰▰▰▰"]

async def animate(msg, label: str):
    for bar in BARS[:-1]:
        try:
            await msg.edit_text(
                f"{b(label)}\n{DIVIDER}\n\n{bar}",
                parse_mode=ParseMode.HTML)
            await asyncio.sleep(0.55)
        except Exception:
            break

# ── Command handlers ──────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    stats["users"].add(update.effective_user.id)
    send = update.message.reply_text if update.message else update.callback_query.edit_message_text
    await send(HOME_TEXT, parse_mode=ParseMode.HTML,
               reply_markup=home_kb(), disable_web_page_preview=True)

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    send = update.message.reply_text if update.message else update.callback_query.edit_message_text
    await send(HELP_TEXT, parse_mode=ParseMode.HTML,
               reply_markup=back_kb(), disable_web_page_preview=True)

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    send = update.message.reply_text if update.message else update.callback_query.edit_message_text
    await send(stats_text(), parse_mode=ParseMode.HTML,
               reply_markup=back_kb(), disable_web_page_preview=True)

# ── Callback handler ──────────────────────────────────────────────────────────
async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data
    if d == "home":   await cmd_start(update, ctx)
    elif d == "help": await cmd_help(update, ctx)
    elif d == "stats":await cmd_stats(update, ctx)
    elif d.startswith("g:"):
        plat = d[2:]
        await q.edit_message_text(GUIDES[plat], parse_mode=ParseMode.HTML,
                                   reply_markup=back_kb(), disable_web_page_preview=True)

# ── Media sending helpers ─────────────────────────────────────────────────────
async def send_video_smart(update, caption, video_url, thumb_url=None, fallback_label="تحميل الفيديو"):
    """Try to send video natively; fall back to button if too large / error."""
    try:
        await update.message.reply_video(
            video=video_url,
            caption=caption,
            parse_mode=ParseMode.HTML,
            supports_streaming=True,
            read_timeout=60, write_timeout=60, connect_timeout=15,
        )
        return True
    except TelegramError as e:
        logger.warning(f"[send_video] native failed ({e}), falling back to button")
    # Fallback: send as button
    await update.message.reply_text(
        caption,
        parse_mode=ParseMode.HTML,
        reply_markup=url_kb([(fallback_label, video_url)]),
        disable_web_page_preview=True,
    )
    return False

async def send_audio_smart(update, caption, audio_url):
    try:
        await update.message.reply_audio(
            audio=audio_url, caption=caption, parse_mode=ParseMode.HTML,
            read_timeout=60, write_timeout=60,
        )
    except TelegramError:
        await update.message.reply_text(
            caption, parse_mode=ParseMode.HTML,
            reply_markup=url_kb([("تحميل MP3", audio_url)]),
            disable_web_page_preview=True,
        )

async def send_photo_smart(update, caption, photo_url, kb=None):
    try:
        await update.message.reply_photo(
            photo=photo_url, caption=caption,
            parse_mode=ParseMode.HTML, reply_markup=kb,
        )
    except TelegramError:
        await update.message.reply_text(
            caption, parse_mode=ParseMode.HTML, reply_markup=kb,
            disable_web_page_preview=True,
        )

# ── Platform processors ───────────────────────────────────────────────────────
async def process_tiktok(update, url, loading_msg):
    data = await api_tiktok(url)
    if not data:
        raise ValueError("تعذّر جلب بيانات الفيديو. تأكد من الرابط وحاول مجدداً.")

    video_hd = data.get("hdplay") or data.get("play") or data.get("wmplay")
    video_sd = data.get("play") or data.get("wmplay")
    audio    = data.get("music") or (data.get("music_info") or {}).get("play")
    cover    = data.get("cover")
    title    = trim(data.get("title", "TikTok Video"))
    author   = (data.get("author") or {}).get("nickname", "")
    likes    = data.get("digg_count", 0)
    comments = data.get("comment_count", 0)
    duration = data.get("duration", 0)

    if not video_hd:
        raise ValueError("لا يوجد رابط فيديو متاح.")

    caption = (
        f"{b(title)}\n"
        f"{DIVIDER}\n"
        f"{'@' + author if author else ''}"
        f"{'  ·  ' if author else ''}{duration}s\n"
        f"♡ {likes:,}   ✦ {comments:,}"
        f"{FOOTER}"
    )

    await loading_msg.delete()
    stats["total"] += 1; stats["tiktok"] += 1

    # Send video natively
    await send_video_smart(update, caption, video_hd, cover, "تحميل الفيديو HD")

    # Send audio separately if available
    if audio:
        audio_cap = f"{b('الصوت — ' + title)}\n{b('TikTok MP3')}{FOOTER}"
        await send_audio_smart(update, audio_cap, audio)


async def process_facebook(update, url, loading_msg):
    data = await api_facebook(url)
    if not data or (not data.get("hd") and not data.get("sd")):
        raise ValueError("تعذّر جلب الفيديو. تأكد من أن الفيديو عام (Public).")

    hd = data.get("hd")
    sd = data.get("sd")
    caption = f"{b('Facebook Video')}\n{DIVIDER}\n اختر جودة التحميل:{FOOTER}"

    await loading_msg.delete()
    stats["total"] += 1; stats["facebook"] += 1

    # Try HD native first
    sent = False
    if hd:
        sent = await send_video_smart(update, caption + "\n\n" + i("جودة عالية HD"), hd, fallback_label="تحميل HD")

    # If native HD worked, also offer SD as button; otherwise offer both as buttons
    if not sent:
        links = []
        if hd: links.append(("تحميل HD", hd))
        if sd: links.append(("تحميل SD", sd))
        links.append(("روابط SnatchTik", LINKTREE))
        await update.message.reply_text(
            caption, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(l, url=u)] for l, u in links]),
            disable_web_page_preview=True,
        )
    elif sd:
        await update.message.reply_text(
            i("أو حمّل بجودة عادية:"), parse_mode=ParseMode.HTML,
            reply_markup=url_kb([("تحميل SD", sd)]),
        )


async def process_instagram(update, url, loading_msg):
    data = await api_instagram(url)
    if not data:
        raise ValueError("تعذّر جلب البيانات. تأكد من أن الحساب عام (Public).")

    title  = trim(data.get("title", "Instagram"))
    mtype  = data.get("type")
    video  = data.get("video")
    images = data.get("images", [])
    thumb  = data.get("thumb")
    caption_base = f"{b(title)}\n{DIVIDER}{FOOTER}"

    await loading_msg.delete()
    stats["total"] += 1; stats["instagram"] += 1

    if mtype == "video" and video:
        await send_video_smart(update, caption_base, video, thumb, "تحميل الفيديو")

    elif mtype == "image" and images:
        await send_photo_smart(update, caption_base, images[0])

    elif mtype == "album" and images:
        # Send photos as a media group (up to 10)
        from telegram import InputMediaPhoto
        group = [InputMediaPhoto(media=u, caption=(caption_base if i == 0 else ""), parse_mode=ParseMode.HTML)
                 for i, u in enumerate(images[:10])]
        try:
            await update.message.reply_media_group(media=group)
        except TelegramError:
            # fallback: buttons
            links = [(f"صورة {i+1}", u) for i, u in enumerate(images[:8])]
            await update.message.reply_text(
                caption_base, parse_mode=ParseMode.HTML,
                reply_markup=url_kb(links), disable_web_page_preview=True,
            )
    else:
        raise ValueError("لا يوجد محتوى قابل للتحميل.")

# ── Main message handler ──────────────────────────────────────────────────────
async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    stats["users"].add(update.effective_user.id)

    if not is_url(text):
        await update.message.reply_text(
            f"{b('أرسل رابطاً صحيحاً')}\n{DIVIDER}\n\n"
            "نحن ندعم:\n  TikTok · Facebook · Instagram",
            parse_mode=ParseMode.HTML, reply_markup=home_kb(),
        )
        return

    platform = detect(text)
    if platform == "other":
        await update.message.reply_text(
            f"{b('رابط غير مدعوم')}\n{DIVIDER}\n\n"
            "المنصات المدعومة:\n  TikTok · Facebook · Instagram",
            parse_mode=ParseMode.HTML, reply_markup=back_kb(),
        )
        return

    labels = {"tiktok": "TikTok", "facebook": "Facebook", "instagram": "Instagram"}
    loading = await update.message.reply_text(
        f"{b(labels[platform])}\n{DIVIDER}\n\n▱▱▱▱▱",
        parse_mode=ParseMode.HTML,
    )
    await animate(loading, labels[platform])

    try:
        if platform == "tiktok":
            await process_tiktok(update, text, loading)
        elif platform == "facebook":
            await process_facebook(update, text, loading)
        elif platform == "instagram":
            await process_instagram(update, text, loading)

    except ValueError as e:
        await loading.edit_text(
            f"{b('تعذّر التحميل')}\n{DIVIDER}\n\n{e}{FOOTER}",
            parse_mode=ParseMode.HTML, reply_markup=back_kb(), disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(f"[on_message] {e}", exc_info=True)
        try:
            await loading.edit_text(
                f"{b('حدث خطأ غير متوقع')}\n{DIVIDER}\n\nيرجى المحاولة لاحقاً.{FOOTER}",
                parse_mode=ParseMode.HTML, reply_markup=back_kb(), disable_web_page_preview=True,
            )
        except Exception:
            pass

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    logger.info("SnatchTik Bot v3.0 Pro — Running")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
