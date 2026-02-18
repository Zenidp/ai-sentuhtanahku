from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
import os
import requests

app = FastAPI(title="API AI Sentuh Tanahku (RAG Mode)")

# --- KONFIGURASI KEAMANAN (PENTING!) ---
# Mengambil kunci dari Environment Variables di Render/Laptop
# Jangan tulis API Key langsung di sini agar aman saat push ke GitHub.
# SUPABASE_URL = os.environ.get("https://hzmlxnsnuycvqkpetxhe.supabase.co")
# SUPABASE_KEY = os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh6bWx4bnNudXljdnFrcGV0eGhlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzNDM1ODQsImV4cCI6MjA4NjkxOTU4NH0.0ahv8dGihy3EtCeR-NTPUuh4faW8lnJyq-laH7KGxW0")
# GEMINI_API_KEY = os.environ.get("AIzaSyA9k21yPFqTkX2YMU8IeIH2ew2RJ5S9G2o")
SUPABASE_URL = "https://hzmlxnsnuycvqkpetxhe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh6bWx4bnNudXljdnFrcGV0eGhlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzNDM1ODQsImV4cCI6MjA4NjkxOTU4NH0.0ahv8dGihy3EtCeR-NTPUuh4faW8lnJyq-laH7KGxW0"
#GEMINI_API_KEY = "AIzaSyA9k21yPFqTkX2YMU8IeIH2ew2RJ5S9G2o"
GEMINI_API_KEY = "AIzaSyDv2QoB8quhebCJikjLwpmIL6w21mzh5-Q"

class ChatRequest(BaseModel):
    pesan: str
    session_id: str = "default"  # Default value jika user lupa mengirim

@app.get("/")
def read_root():
    return {"status": "Sistem RAG Sentuh Tanahku (Gemini 2.5) Aktif!"}

@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    # Validasi variabel environment sebelum lanjut
    if not GEMINI_API_KEY or not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Konfigurasi server belum lengkap (API Key hilang).")

    try:
        # Inisialisasi Client Gemini Baru
        client = genai.Client(api_key=GEMINI_API_KEY)

        # 1. Ubah pertanyaan warga menjadi angka (Embedding)
        # Menggunakan model embedding yang sama dengan saat inject data
        emb_response = client.models.embed_content(
            model='gemini-embedding-001',
            contents=request.pesan
        )
        # Akses values vektor (sesuaikan dengan struktur SDK terbaru)
        query_vector = emb_response.embeddings[0].values

        # 2. Cari dokumen yang relevan di Supabase via RPC match_bpn_documents
        rpc_url = f"{SUPABASE_URL}/rest/v1/rpc/match_bpn_documents"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Payload untuk mencari kemiripan
        payload = {
            "query_embedding": query_vector,
            "match_threshold": 0.5, # Ambil yang kemiripannya di atas 50%
            "match_count": 3        # Ambil 3 dokumen terbaik
        }
        
        db_response = requests.post(rpc_url, headers=headers, json=payload)
        
        if db_response.status_code != 200:
            raise Exception(f"Error Supabase: {db_response.text}")
            
        documents = db_response.json()

        # 3. Gabungkan hasil pencarian menjadi konteks untuk Gemini
        # Jika tidak ada dokumen yang cocok, beri konteks kosong
        if not documents:
            konteks_dokumen = "Tidak ditemukan dokumen SOP spesifik yang relevan."
            sumber_list = []
        else:
            konteks_dokumen = "\n\n".join([doc['konten'] for doc in documents])
            sumber_list = list(set([doc['sumber'] for doc in documents]))

        # 4. Minta Gemini menjawab berdasarkan data tersebut
        # Menggunakan model TERBARU: gemini-2.5-flash
        # Update Prompt di main.py agar lebih cerdas & ramah
        prompt_sistem = f"""
        PERAN ANDA:
        Anda adalah "SENTA", Asisten Virtual Senior di Kementerian ATR/BPN yang ramah, profesional, dan sangat teliti.
        Tugas Anda adalah menjelaskan prosedur pertanahan yang rumit menjadi bahasa yang mudah dipahami oleh warga awam.

        ATURAN MENJAWAB:
        1. **Empati:** Awali jawaban dengan sapaan sopan atau empati (contoh: "Baik, saya bantu jelaskan...", "Mohon maaf atas kendalanya...").
        2. **Struktur:** Gunakan poin-poin (bullet points) jika menjelaskan syarat dokumen agar mudah dibaca.
        3. **Akurasi Mutlak:** HANYA gunakan informasi dari "REFERENSI DATA BPN" di bawah ini. Jangan mengarang pasal atau biaya.
        4. **Jujur:** Jika informasi tidak ada di referensi, katakan: "Mohon maaf, informasi spesifik tersebut belum tersedia di database saya. Silakan kunjungi Kantor Pertanahan terdekat."
        5. **Call to Action:** Akhiri dengan kalimat penutup yang membantu (contoh: "Semoga membantu! Ada lagi yang ingin ditanyakan?").

        REFERENSI DATA BPN (SOP & PERATURAN):
        {konteks_dokumen}

        PERTANYAAN WARGA: {request.pesan}
        """

        # Generate jawaban menggunakan Gemini 2.5 Flash
        ai_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_sistem
        )

        return {
            "status": "success",
            "model_used": "gemini-2.5-flash",
            "jawaban": ai_response.text,
            "sumber": sumber_list
        }

    except Exception as e:
        print(f"Error: {str(e)}") # Print ke log server untuk debugging
        raise HTTPException(status_code=500, detail=str(e))