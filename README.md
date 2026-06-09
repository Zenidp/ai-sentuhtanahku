# 🏛️ Sentuh Tanahku AI — Senta

> Asisten Virtual Cerdas Layanan Pertanahan BPN berbasis RAG (Retrieval-Augmented Generation)

**Senta** (Sentuh Tanahku AI) adalah asisten AI conversational yang dirancang khusus untuk membantu masyarakat memahami layanan pertanahan di Badan Pertanahan Nasional (BPN). Senta menjawab pertanyaan seputar sertifikasi tanah, hak tanggungan, balik nama, PNBP, dan prosedur pertanahan lainnya — berdasarkan dokumen SOP dan regulasi hukum resmi BPN.

---

## 📐 Arsitektur Sistem

Proyek ini terdiri dari **dua repository** yang bekerja bersama:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SENTUH TANAHKU AI SYSTEM                     │
│                                                                 │
│  ┌──────────────────────┐        ┌─────────────────────────┐   │
│  │   ai-sentuhtanahku   │        │  ai-sentuhtanahku-ui    │   │
│  │        -api          │◄──────►│  (Next.js Frontend)     │   │
│  │  (FastAPI Backend)   │  HTTP  │  Vercel AI Gateway      │   │
│  └──────────┬───────────┘        └─────────────────────────┘   │
│             │                                                   │
│             ▼                                                   │
│  ┌──────────────────────┐                                       │
│  │   Supabase (pgvector)│                                       │
│  │   Vector Database    │                                       │
│  │   bpn_knowledge_base │                                       │
│  └──────────────────────┘                                       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            Multi-LLM Fallback Chain                      │   │
│  │  SambaNova → Cerebras → OpenRouter → NVIDIA NIM →        │   │
│  │  Groq → Mistral → Scaleway → Cloudflare → Gemini         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Alur Kerja RAG

```
User bertanya
     │
     ▼
[1] Gemini Embedding (768 dim)
     │
     ▼
[2] Vector Search di Supabase (match_bpn_knowledge)
     │
     ▼
[3] Dokumen relevan (top 3, threshold ≥ 0.5)
     │
     ▼
[4] Prompt dirangkai + riwayat chat
     │
     ▼
[5] Fallback Chain LLM (28+ model, 9 provider)
     │
     ▼
[6] Jawaban "Senta" yang friendly + sumber referensi
```

---

## 📦 Struktur Repository

```
📁 ai-sentuhtanahku-api/          ← Backend (repo ini)
├── main.py                        ← FastAPI app + fallback chain LLM
├── app_ui.py                      ← Streamlit UI (untuk testing lokal)
├── ingest_pdf.py                  ← Script import dokumen PDF ke Supabase
├── ingest_json.py                 ← Script import data JSON ke Supabase
├── ingest_txt.py                  ← Script import dokumen TXT ke Supabase
├── inject_data.py                 ← Script inject data manual ke Supabase
├── data_bpn.json                  ← Dataset SOP BPN terstruktur
├── requirements.txt               ← Dependencies Python
└── .devcontainer/devcontainer.json← Dev Container config

📁 ai-sentuhtanahku-ui/           ← Frontend (repo terpisah)
├── app/(chat)/                    ← Halaman chat utama
├── app/(auth)/                    ← Autentikasi (NextAuth v5)
├── components/                    ← UI Components (Radix UI + Tailwind)
├── lib/ai/                        ← Model config, providers, prompts
├── lib/db/                        ← Drizzle ORM + PostgreSQL migrations
└── artifacts/                     ← Artifact rendering (code, text, sheet)
```

---

## 🚀 Tech Stack

### Backend — `ai-sentuhtanahku-api`

| Komponen | Teknologi |
|---|---|
| Framework | FastAPI |
| Runtime | Python 3.11 |
| Embedding | Google Gemini (`gemini-embedding-001`, 768 dim) |
| Vector DB | Supabase + pgvector |
| LLM Providers | SambaNova, Cerebras, OpenRouter, NVIDIA NIM, Groq, Mistral, Scaleway, Cloudflare, Gemini |
| UI Testing | Streamlit |
| Deploy | Render.com |

### Frontend — `ai-sentuhtanahku-ui`

| Komponen | Teknologi |
|---|---|
| Framework | Next.js 16 (App Router) |
| Runtime | React 19 + TypeScript |
| AI SDK | Vercel AI SDK v6 (`ai`) + `@ai-sdk/gateway` |
| Auth | NextAuth v5 |
| Database | PostgreSQL + Drizzle ORM |
| Cache | Redis |
| File Storage | Vercel Blob |
| Styling | Tailwind CSS v4 + Radix UI |
| Deploy | Vercel |

---

## 🤖 Multi-LLM Fallback Chain

Sistem otomatis mencoba model dari kualitas tertinggi, bergeser ke berikutnya jika gagal. Total **28+ model dari 9 provider**:

| Priority | Provider | Model | Size |
|---|---|---|---|
| 1 | SambaNova | DeepSeek-V3.1 | 671B |
| 2 | Cerebras | qwen-3-235b-a22b | 235B |
| 3 | OpenRouter | hermes-3-llama-3.1-405b:free | 405B |
| 4 | OpenRouter | owl-alpha | 1M ctx |
| 5 | NVIDIA NIM | nemotron-3-super-120b | 120B |
| 6 | OpenRouter | gpt-oss-120b:free | 120B |
| 7 | Scaleway | qwen3-235b | 235B |
| 8 | SambaNova | Meta-Llama-3.3-70B | 70B |
| 9 | Groq | llama-3.3-70b-versatile | 70B |
| 10 | Mistral | mistral-large-2411 | ~70B |
| ... | Cloudflare, Gemini | *(fallback akhir)* | 8B+ |

> Sistem ini memastikan **zero downtime** meskipun beberapa provider sedang down atau melebihi kuota.

---

## 🛠️ Setup & Instalasi

### Backend (`ai-sentuhtanahku-api`)

**1. Clone dan install dependencies**
```bash
git clone https://github.com/username/ai-sentuhtanahku-api.git
cd ai-sentuhtanahku-api
pip install -r requirements.txt
```

**2. Buat file `.env`**
```env
# Wajib
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
GEMINI_API_KEY=your-gemini-api-key        # Wajib untuk embedding

# Opsional (semakin banyak, semakin kuat fallback-nya)
GROQ_API_KEY=your-groq-api-key
CEREBRAS_API_KEY=your-cerebras-api-key
MISTRAL_API_KEY=your-mistral-api-key
SAMBANOVA_API_KEY=your-sambanova-api-key
NVIDIA_NIM_API_KEY=your-nvidia-api-key
OPENROUTER_API_KEY=your-openrouter-api-key
SCALEWAY_API_KEY=your-scaleway-api-key
CLOUDFLARE_ACCOUNT_ID=your-cf-account-id
CLOUDFLARE_API_TOKEN=your-cf-api-token
```

**3. Setup Supabase**

Buat tabel `bpn_knowledge_base` di Supabase dengan pgvector:
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE bpn_knowledge_base (
  id BIGSERIAL PRIMARY KEY,
  content TEXT,
  content_to_embed TEXT,
  metadata JSONB,
  embedding VECTOR(768)
);

-- Fungsi RPC untuk vector search
CREATE OR REPLACE FUNCTION match_bpn_knowledge(
  query_embedding VECTOR(768),
  match_threshold FLOAT,
  match_count INT
)
RETURNS TABLE (
  id BIGINT,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
  SELECT
    id,
    content,
    metadata,
    1 - (embedding <=> query_embedding) AS similarity
  FROM bpn_knowledge_base
  WHERE 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
```

**4. Ingest data pengetahuan**
```bash
# Import dari file JSON (direkomendasikan)
python ingest_json.py

# Import dari file PDF
python ingest_pdf.py
# (taruh file PDF di folder /dokumen_sumber/)

# Import dari file TXT
python ingest_txt.py
```

**5. Jalankan server**
```bash
# Development
uvicorn main:app --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

### Frontend (`ai-sentuhtanahku-ui`)

**1. Clone dan install dependencies**
```bash
git clone https://github.com/username/ai-sentuhtanahku-ui.git
cd ai-sentuhtanahku-ui
pnpm install
```

**2. Buat file `.env.local`**
```env
AUTH_SECRET=your-random-secret-32chars
AI_GATEWAY_API_KEY=your-vercel-ai-gateway-key
BLOB_READ_WRITE_TOKEN=your-vercel-blob-token
POSTGRES_URL=your-postgres-connection-string
REDIS_URL=your-redis-connection-string
```

**3. Migrasi database**
```bash
pnpm db:migrate
```

**4. Jalankan development server**
```bash
pnpm dev
```

Akses di `http://localhost:3000`

---

## 🌐 API Endpoints

Base URL: `https://ai-sentuhtanahku-api.onrender.com`

### `GET /`
Health check — cek apakah sistem aktif.

```json
{ "status": "Sistem RAG Sentuh Tanahku (Genius + Memory Mode) Aktif!" }
```

---

### `POST /api/chat`
Endpoint utama untuk percakapan dengan Senta.

**Request Body:**
```json
{
  "pesan": "Apa syarat balik nama sertifikat?",
  "session_id": "uuid-opsional",
  "riwayat": [
    { "role": "user", "content": "Halo Senta" },
    { "role": "assistant", "content": "Halo Kak! Ada yang bisa Senta bantu? ✨" }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "provider": "groq",
  "model_used": "llama-3.3-70b-versatile",
  "jawaban": "Halo Kak! Untuk balik nama sertifikat, syaratnya adalah... 📋",
  "sumber": ["Balik Nama (PP No. 128 Tahun 2015)"]
}
```

---

### `GET /test-provider/{provider}`
Test semua model dari satu provider.

```bash
curl https://ai-sentuhtanahku-api.onrender.com/test-provider/groq
```

Provider yang tersedia: `sambanova`, `cerebras`, `groq`, `mistral`, `cloudflare`, `gemini`, `nvidia`, `openrouter`, `scaleway`

---

### `GET /test-provider/{provider}/{model}`
Test satu model spesifik.

```bash
curl "https://ai-sentuhtanahku-api.onrender.com/test-provider/openrouter/meta-llama/llama-3.3-70b-instruct:free"
```

---

## 📚 Format Data Knowledge Base

File `data_bpn.json` berisi dokumen SOP BPN dengan format:

```json
[
  {
    "metadata": {
      "kategori_layanan": "Hak Tanggungan",
      "jenis_dokumen": "Informasi Umum",
      "referensi_hukum": "UU No. 4 Tahun 1996 tentang Hak Tanggungan",
      "tags": ["hak tanggungan", "kpr", "agunan bank"]
    },
    "content_to_embed": "Penjelasan singkat untuk proses embedding...",
    "content": "KONTEN LENGKAP YANG DITAMPILKAN KE USER\n\nIsi dokumen..."
  }
]
```

Topik yang sudah tersedia di knowledge base:
- Hak Tanggungan (KPR, APHT, SKMHT)
- Balik Nama Sertifikat
- Pemecahan/Penggabungan Sertifikat
- PNBP (Penerimaan Negara Bukan Pajak)
- Pengecekan Sertifikat
- PTSL (Pendaftaran Tanah Sistematis Lengkap)
- Roya (Penghapusan Hak Tanggungan)
- Dan banyak layanan BPN lainnya

---

## 🎭 Karakter "Senta"

Senta dirancang dengan kepribadian yang unik:

- **Panggilan**: memanggil user dengan "Kak"
- **Gaya bicara**: friendly, asik, santai, elegan seperti "bestie"
- **Emoji**: digunakan secara natural dan relevan ✨
- **Bahasa**: luwes dan tidak kaku
- **Jika tidak tahu**: menggunakan "jurus ngeles elegan" — tidak mengarang, tapi tetap ramah

---

## 🚢 Deployment

### Backend — Render.com

1. Connect repository ke Render
2. Set **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Tambahkan semua environment variables di Render Dashboard
4. Deploy

Live URL: `https://ai-sentuhtanahku-api.onrender.com`

### Frontend — Vercel

1. Connect repository ke Vercel
2. Tambahkan environment variables di Vercel Dashboard
3. Deploy otomatis saat push ke `main`

Live URL: `https://ai-sentuhtanahku-ui.vercel.app`

---

## 💻 Dev Container

Backend mendukung **GitHub Codespaces** via Dev Container. Saat dibuka di Codespaces:
- Auto-install semua Python dependencies
- Auto-launch Streamlit UI di port 8501
- Preview langsung di browser

---

## 📋 Scripts yang Tersedia

### Backend
```bash
uvicorn main:app --reload          # Jalankan API server
streamlit run app_ui.py            # Jalankan UI testing Streamlit
python ingest_json.py              # Import data JSON ke Supabase
python ingest_pdf.py               # Import PDF ke Supabase
python ingest_txt.py               # Import TXT ke Supabase
python inject_data.py              # Inject data manual
python ingest_pdf_mulai_dari.py    # Import PDF mulai dari halaman tertentu
```

### Frontend
```bash
pnpm dev              # Development server dengan Turbopack
pnpm build            # Build untuk production
pnpm start            # Jalankan production build
pnpm db:migrate       # Jalankan migrasi database
pnpm db:studio        # Buka Drizzle Studio (DB GUI)
pnpm test             # Jalankan Playwright tests
pnpm lint             # Linting dengan Ultracite
pnpm format           # Format kode
```

---

## 🔗 Links

| Resource | URL |
|---|---|
| API Live | https://ai-sentuhtanahku-api.onrender.com |
| UI Live | https://ai-sentuhtanahku-ui.vercel.app |
| API Docs (Swagger) | https://ai-sentuhtanahku-api.onrender.com/docs |
| Supabase Dashboard | https://supabase.com/dashboard |

---

## 📄 Lisensi

Project ini dibuat untuk keperluan layanan publik pertanahan Indonesia. Data dan dokumen SOP bersumber dari regulasi resmi BPN.
