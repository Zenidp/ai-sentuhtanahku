from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os

# Inisialisasi Aplikasi FastAPI
app = FastAPI(
    title="API AI Sentuh Tanahku",
    description="Middleware AI untuk melayani aplikasi mobile Sentuh Tanahku",
    version="1.0.0"
)

# Konfigurasi Model AI (Gemini)
# API Key akan diambil dari Environment Variable di server demi keamanan
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

# Skema Data yang diterima dari Aplikasi Mobile
class ChatRequest(BaseModel):
    pesan: str
    session_id: str

# Endpoint untuk mengecek apakah server hidup
@app.get("/")
def read_root():
    return {"status": "Server Middleware AI Sentuh Tanahku Aktif dan Berjalan!"}

# Endpoint Utama untuk Chatbot
@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    try:
        if not GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="Gemini API Key belum diatur di server.")

        # [AREA RAG SUPABASE NANTINYA] 
        # Di sini kita akan menambahkan kode untuk mencari dokumen BPN di Supabase.
        # Untuk MVP fase awal ini, kita gunakan dokumen statis (dummy) sebagai contoh.
        dokumen_bpn = "SOP BPN: Pendaftaran tanah pertama kali memerlukan KTP, KK, Bukti Penguasaan Fisik, dan Surat Bebas Sengketa."

        # Merakit Prompt (Instruksi Sistem + Dokumen BPN + Pertanyaan Warga)
        prompt_sistem = f"""
        Anda adalah asisten virtual resmi untuk aplikasi 'Sentuh Tanahku' dari Kementerian ATR/BPN.
        Tugas Anda adalah menjawab pertanyaan warga HANYA berdasarkan informasi berikut:
        {dokumen_bpn}
        
        Jika pertanyaannya melenceng dari topik pertanahan, tolak dengan sopan.
        
        Pertanyaan Warga: {request.pesan}
        """

        # Mengirim ke Gemini API
        response = model.generate_content(prompt_sistem)

        # Mengembalikan jawaban ke Aplikasi Mobile dalam format JSON
        return {
            "status": "success",
            "jawaban": response.text,
            "sumber_dokumen": ["SOP Pendaftaran Tanah"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))