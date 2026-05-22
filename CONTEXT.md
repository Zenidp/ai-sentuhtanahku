# 🌱 PROJECT CONTEXT — Sentuh Tanahku AI
> File ini dibaca Claude Code di awal setiap sesi baru.
> Update file ini setiap kali ada perubahan signifikan.

---

## 🎯 Tujuan Project
**Senta (Sentuh Tanahku AI)** — Asisten hukum pertanahan Indonesia berbasis AI.
User bisa tanya seputar layanan BPN (Badan Pertanahan Nasional), dan AI menjawab berdasarkan knowledge base hukum pertanahan Indonesia menggunakan RAG (Retrieval-Augmented Generation).

---

## 🛠️ Tech Stack

### Frontend — `ai-sentuhtanahku-ui`
- **Framework:** Next.js 16 (App Router)
- **Language:** TypeScript 5.6
- **AI SDK:** Vercel AI SDK 6
- **Database:** PostgreSQL via Drizzle ORM 0.34
- **Auth:** NextAuth.js v5 (beta)
- **Cache/Stream:** Redis (resumable streams)
- **Storage:** Vercel Blob (file upload)
- **UI:** shadcn/ui + Radix UI + Tailwind CSS 4
- **Testing:** Playwright E2E
- **Linter:** Biome (ganti ESLint+Prettier)

### Backend — `ai-sentuhtanahku-api`
- **Language:** Python 3.11
- **Framework:** FastAPI + Uvicorn
- **LLM Step 3:** 6 provider, 16 model — urutan kualitas terbaik (lihat FALLBACK_CHAIN)
- **Embedding Step 1:** Gemini embedding-001 (768 dimensi, wajib, tidak bisa diganti)
- **Vector DB:** Supabase + pgvector
- **Validation:** Pydantic v2
- **SDK tambahan:** `groq`, `cerebras-cloud-sdk`

---

## 🌐 URLs & Infrastruktur

| Service | URL |
|---------|-----|
| **Frontend (live)** | https://ai-sentuhtanahku-ui.vercel.app/ |
| **Backend API** | https://ai-sentuhtanahku-api.onrender.com |
| **Backend Health** | https://ai-sentuhtanahku-api.onrender.com/ |
| **Backend Docs (Swagger)** | https://ai-sentuhtanahku-api.onrender.com/docs |
| **Test Provider** | https://ai-sentuhtanahku-api.onrender.com/test-provider/{provider} |

**Cron Job:** cron-job.org → hit `GET /` setiap 5 menit (`*/5 * * * *`) untuk mencegah Render free tier spin down.

---

## 📁 Struktur Folder Penting

### Frontend
```
ai-sentuhtanahku-ui/
├── app/(auth)/              # Login, register, NextAuth endpoints
├── app/(chat)/              # Halaman chat utama
│   ├── api/chat/route.ts    # Jembatan ke FastAPI backend
│   └── chat/[id]/page.tsx   # Chat per session
├── lib/ai/
│   ├── models.ts            # Konfigurasi model (UI selector)
│   ├── providers.ts         # Vercel AI Gateway
│   └── prompts.ts           # System prompts
├── lib/db/
│   ├── schema.ts            # Drizzle schema (User, Chat, Message, Vote)
│   └── queries.ts           # Database query functions
└── components/              # Semua komponen React
```

### Backend
```
ai-sentuhtanahku-api/
├── main.py                  # FastAPI app + FALLBACK_CHAIN 6 provider 16 model
├── requirements.txt         # Python dependencies (incl. groq, cerebras-cloud-sdk)
├── ingest_json.py           # Inject data dari JSON ke Supabase ← cara utama
├── ingest_pdf.py            # Inject dari PDF (folder: dokumen_sumber/)
├── ingest_txt.py            # Inject dari TXT (folder: dokumen_sumber_txt/)
└── data_bpn.json            # Knowledge base BPN utama
```

---

## 🔄 Arsitektur Alur Chat (RAG)

```
User kirim pertanyaan
        ↓
[STEP 1] Embedding → Gemini embedding-001 (768 dim)
         SELALU Gemini, tidak bisa diganti karena DB sudah format ini
        ↓
[STEP 2] Vector Search → Supabase (match_bpn_knowledge)
         threshold: 0.5, top 3 dokumen
        ↓
[STEP 3] Generate Jawaban → FALLBACK_CHAIN (16 model, 6 provider)
         Urutan: kualitas terbaik dulu (model terbesar = jawaban terbaik)
         Kalau gagal/limit → otomatis coba model berikutnya
         Gemini disimpan paling akhir (quota paling kecil)
```

**FALLBACK_CHAIN saat ini (urutan kualitas) — 22 model, 9 provider:**
```
1.  sambanova  / DeepSeek-V3.1                              (671B)
2.  cerebras   / qwen-3-235b-a22b-instruct-2507             (235B Preview)
3.  nvidia     / llama-3.1-nemotron-ultra-253b-v1           (253B)
4.  openrouter / llama-3.1-nemotron-ultra-253b-v1:free      (253B free)
5.  sambanova  / gpt-oss-120b                               (120B)
6.  cerebras   / gpt-oss-120b                               (120B)
7.  sambanova  / Meta-Llama-3.3-70B-Instruct                (70B)
8.  groq       / llama-3.3-70b-versatile                    (70B)
9.  mistral    / mistral-large-2411                         (~70B)
10. cloudflare / llama-3.3-70b-instruct-fp8-fast            (70B quant)
11. nvidia     / meta/llama-3.3-70b-instruct                (70B)
12. openrouter / meta-llama/llama-3.3-70b-instruct:free     (70B free)
13. scaleway   / llama-3.3-70b-instruct                     (70B free)
14. openrouter / deepseek/deepseek-r1-distill-llama-70b:free(70B reasoning free)
15. mistral    / mistral-medium-2505                        (Medium)
16. cerebras   / zai-glm-4.7                                (Preview)
17. groq       / llama-3.1-8b-instant                       (8B)
18. mistral    / mistral-small-2506                         (Small)
19. cerebras   / llama3.1-8b                                (8B)
20. cloudflare / llama-3.1-8b-instruct                      (8B)
21. gemini     / gemini-2.5-flash                           (quota kecil)
22. gemini     / gemini-2.5-flash-lite                      (quota kecil)
```

**Menambah LLM baru:** Tambah fungsi `try_xxx(prompt, model)` dan sisipkan di `FALLBACK_CHAIN` di `main.py`.

---

## 🔑 Environment Variables

### Frontend (`ai-sentuhtanahku-ui` — Vercel)
```env
AUTH_SECRET=****            # Secret untuk NextAuth session
AI_GATEWAY_API_KEY=****     # Vercel AI Gateway key
BLOB_READ_WRITE_TOKEN=****  # Vercel Blob storage
POSTGRES_URL=****           # PostgreSQL connection string
REDIS_URL=****              # Redis connection string
```

### Backend (`ai-sentuhtanahku-api` — Render)
```env
SUPABASE_URL=****           # Wajib
SUPABASE_KEY=****           # Wajib
GEMINI_API_KEY=****         # Wajib (embedding Step 1 + fallback terakhir)
GROQ_API_KEY=****           # Opsional
CEREBRAS_API_KEY=****       # Opsional
MISTRAL_API_KEY=****        # Opsional
SAMBANOVA_API_KEY=****      # Opsional
CLOUDFLARE_ACCOUNT_ID=****  # Opsional
CLOUDFLARE_API_TOKEN=****   # Opsional
NVIDIA_NIM_API_KEY=****     # Opsional — daftar di build.nvidia.com (1000 credits gratis)
OPENROUTER_API_KEY=****     # Opsional — daftar di openrouter.ai (200 req/hari gratis permanen)
SCALEWAY_API_KEY=****       # Opsional — isi dengan SCW_SECRET_KEY (1 juta token gratis)
```

---

## ✅ Progress & Status

### Sudah Selesai (Sesi 21 Mei 2026)
- [x] Analisis lengkap tech stack UI dan API
- [x] Identifikasi semua gap & masalah project
- [x] Implementasi `FALLBACK_CHAIN` awal (Groq → Gemini)
- [x] Tambah Groq SDK ke `requirements.txt`

### Sudah Selesai (Sesi 22 Mei 2026)
- [x] Expand FALLBACK_CHAIN ke 6 provider: Cerebras, Groq, Mistral, SambaNova, Gemini, Cloudflare
- [x] Tambah `cerebras-cloud-sdk` ke `requirements.txt`
- [x] Fix model name Cerebras: `gpt-oss-120b` (Production, 120B)
- [x] Refactor semua `try_xxx()` → terima parameter `(prompt, model)` — tidak hardcode model
- [x] FALLBACK_CHAIN diubah ke 4 tuple: `(provider, model, fn, has_key)`
- [x] 16 model dari 6 provider terdaftar, urutan kualitas terbaik dulu (bukan quota terbesar)
- [x] `generate_jawaban()` return `(jawaban, provider, model)`
- [x] Response `/api/chat` kini include field `provider` + `model_used` terpisah
- [x] Tambah endpoint `/test-provider/{provider}` — test tiap provider dari terminal
- [x] Fix Cloudflare model: upgrade ke `@cf/meta/llama-3.3-70b-instruct-fp8-fast`
- [x] Semua 6 provider verified jalan via `curl /test-provider/{provider}`
- [x] Kapasitas kalkulasi: ~32.400 req/hari → ~3.000–6.000 user/hari
- [x] Expand FALLBACK_CHAIN ke 9 provider: tambah NVIDIA NIM, OpenRouter, Scaleway
- [x] 22 model dari 9 provider — tambah Nemotron 253B, DeepSeek R1 reasoning
- [x] Tambah `try_nvidia()`, `try_openrouter()`, `try_scaleway()` di `main.py`
- [x] Env vars baru: `NVIDIA_NIM_API_KEY`, `OPENROUTER_API_KEY`, `SCALEWAY_API_KEY`

### Belum Selesai / Next
- [ ] Fix hardcoded API keys di `ingest_pdf.py`, `ingest_txt.py` → pindah ke `.env`
- [ ] Aktifkan artifact tools (createDocument, updateDocument) di frontend
- [ ] Integrasi penuh file upload — user bisa upload dokumen pertanahan
- [ ] Title generation otomatis (dicomment di `app/(chat)/api/chat/route.ts`)
- [ ] Tambah autentikasi di FastAPI endpoint (minimal API key header)
- [ ] Setup CORS di FastAPI
- [ ] Bersihkan file "copy" yang tidak terpakai di backend
- [ ] Self-host Ollama (opsional, kalau traffic sudah > 5.000 user/hari)

---

## ⚠️ Masalah & Solusi yang Sudah Ditemukan

| Masalah | Solusi |
|---------|--------|
| Render free tier spin down setelah 15 menit idle | Cron job hit `GET /` setiap 5 menit |
| API keys hardcoded di ingest scripts | Belum difix — `ingest_pdf.py`, `ingest_txt.py` masih hardcode |
| Endpoint `/api/chat` publik tanpa auth | Belum difix |
| LLM single point of failure | Fix: FALLBACK_CHAIN 16 model 6 provider |
| Cerebras 404 model not found | Model ID harus `gpt-oss-120b` bukan `llama-3.3-70b` |
| Mistral/Gemini tidak dikenal di test-provider | Label harus format `provider/model` agar split `/` benar |

---

## 📌 Keputusan Penting

### Arsitektur LLM
- **Step 1 (Embedding):** Selalu Gemini — tidak bisa diganti tanpa re-ingest semua data Supabase
- **Step 3 (Generate):** FALLBACK_CHAIN 16 model, urutan kualitas terbaik dulu
- **Self-host Ollama:** Hanya Step 3, Step 1 tetap Gemini. Worth it kalau traffic > 5.000 user/hari
- **Tidak ada env var `MODEL_PROVIDER`** — sistem otomatis, tidak perlu konfigurasi manual

### Cara Test Provider
```bash
curl https://ai-sentuhtanahku-api.onrender.com/test-provider/sambanova
curl https://ai-sentuhtanahku-api.onrender.com/test-provider/cerebras
curl https://ai-sentuhtanahku-api.onrender.com/test-provider/groq
curl https://ai-sentuhtanahku-api.onrender.com/test-provider/mistral
curl https://ai-sentuhtanahku-api.onrender.com/test-provider/cloudflare
curl https://ai-sentuhtanahku-api.onrender.com/test-provider/gemini
```

### Cara Inject Knowledge ke Supabase
- **Format JSON** (rekomendasi): edit `data_bpn.json` → `python ingest_json.py`
- **Format PDF**: taruh file di `dokumen_sumber/` → `python ingest_pdf.py`
- **Format TXT**: taruh file di `dokumen_sumber_txt/` → `python ingest_txt.py`

---

## 🖥️ Cara Mulai Sesi Baru di Claude Code
```
Baca CONTEXT.md, lalu ringkas apa yang sudah ada dan tanyakan apa yang ingin saya kerjakan hari ini.
```
