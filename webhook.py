import os
from http.server import BaseHTTPRequestHandler
import json
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Ambil Token Bot dari Environment Variable Vercel
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Inisialisasi Aplikasi Bot Telegram
app_telegram = Application.builder().token(BOT_TOKEN).build()

# Perintah /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Selamat datang di **Bot Asisten Keamanan WhatsApp**.\n\n"
        "Jika Anda lupa PIN Verifikasi Dua Langkah akun WhatsApp Anda, "
        "silakan ketik perintah `/resetpin` untuk melihat panduan pemulihan.",
        parse_mode="Markdown"
    )

# Perintah /resetpin (Memunculkan Peringatan Awal dengan Tombol Merah)
async def reset_pin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("🔴 YA, SAYA LUPA PIN WA SAYA", callback_data="pilih_solusi"),
        ],
        [
            InlineKeyboardButton("❌ Batalkan", callback_data="batal")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚠️ **PERINGATAN DUA LANGKAH WHATSAPP** ⚠️\n\n"
        "Apakah Anda sedang terkunci di luar aplikasi WhatsApp karena lupa PIN verifikasi?\n\n"
        "Silakan konfirmasi untuk melanjutkan ke opsi pemulihan.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# Handler Aksi Tombol
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    
    if query.data == "pilih_solusi":
        # Memunculkan alert sistem pop-up sebelum mengganti teks
        await query.answer(text="Membuka Panduan Pemulihan Akun...", show_alert=True)
        
        # Opsi interaktif untuk pengguna
        keyboard = [
            [
                InlineKeyboardButton("📧 Gunakan Jalur Email", callback_data="solusi_email"),
                InlineKeyboardButton("⏳ Tanpa Email (7 Hari)", callback_data="solusi_tanpa_email")
            ],
            [
                InlineKeyboardButton("🛡️ Hubungi Support Resmi WA", url="mailto:support@://whatsapp.com")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="💡 **PILIH METODE PEMULIHAN WHATSAPP** 💡\n\n"
                 "Silakan pilih metode di bawah ini yang sesuai dengan kondisi akun WhatsApp Anda saat ini:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    elif query.data == "solusi_email":
        await query.answer()
        await query.edit_message_text(
            text="📧 **Cara Reset Menggunakan Email:**\n\n"
                 "1. Buka aplikasi WhatsApp Anda yang terkunci.\n"
                 "2. Pada layar input PIN, ketuk tulisan **Lupa PIN?** lalu pilih **Kirim Email**.\n"
                 "3. Buka kotak masuk email Anda, lalu klik **Tautan Tautan Konfirmasi** yang dikirim oleh WhatsApp.\n"
                 "4. Masuk kembali ke WhatsApp dan buat PIN verifikasi baru Anda.\n\n"
                 "_*Catatan:_ Opsi ini hanya bekerja jika Anda pernah mendaftarkan email saat menyalakan 2FA pertama kali.\n\n"
                 "Ketik /resetpin untuk kembali ke menu awal.",
            parse_mode="Markdown"
        )
        
    elif query.data == "solusi_tanpa_email":
        await query.answer()
        await query.edit_message_text(
            text="⏳ **Cara Reset TANPA Akses Email:**\n\n"
                 "Jika Anda tidak mengaitkan email ke WhatsApp, Anda harus **menunggu selama 7 hari**.\n\n"
                 "1. Hitung mundur **7 hari berturut-turut** dimulai dari hari terakhir Anda berhasil login WhatsApp.\n"
                 "2. Selama masa tunggu ini, nomor Anda tetap aman tetapi Anda tidak bisa membuka pesan.\n"
                 "3. Setelah hari ke-7 terlewati, buka WhatsApp kembali, pilih **Lupa PIN?**, maka opsi **Atur Ulang Akun** akan otomatis muncul secara gratis.\n\n"
                 "Ketik /resetpin untuk kembali ke menu awal.",
            parse_mode="Markdown"
        )
        
    elif query.data == "batal":
        await query.answer(text="Dibatalkan.")
        await query.edit_message_text(text="❌ Proses dibatalkan. Gunakan perintah /resetpin jika butuh bantuan lagi.")

# Daftarkan fungsi ke sistem handler
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(CommandHandler("resetpin", reset_pin))
app_telegram.add_handler(CallbackQueryHandler(button_handler))

# Handler Serverless Vercel
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            json_data = json.loads(post_data.decode('utf-8'))
            update = Update.de_json(json_data, app_telegram.bot)
            
            loop = asyncio.get_event_loop()
            loop.run_until_complete(app_telegram.initialize())
            loop.run_until_complete(app_telegram.process_update(update))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
