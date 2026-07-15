# 🏛️ Sentuh Tanahku AI — Senta

> Asisten Virtual Cerdas Layanan Pertanahan BPN berbasis RAG (Retrieval-Augmented Generation)

**Senta** (Sentuh Tanahku AI) adalah asisten AI conversational yang membantu masyarakat memahami layanan pertanahan di Badan Pertanahan Nasional (BPN): sertifikasi tanah, hak tanggungan, balik nama, PNBP, dan prosedur pertanahan lainnya — berdasarkan dokumen SOP dan regulasi hukum resmi BPN.

Repository ini adalah **monorepo** yang berisi seluruh sistem:

| App | Teknologi | Deploy | Dokumentasi |
|---|---|---|---|
| [`apps/api`](apps/api/) | FastAPI + Supabase (pgvector) + 9 provider LLM | Render | [README](apps/api/README.md) |
| [`apps/web`](apps/web/) | Next.js (App Router) + Vercel AI SDK + Drizzle | Vercel | [README](apps/web/README.md) |

---

## 📐 Arsitektur Sistem

```
┌────────────────────────────────────────────────────────────────┐
│                    SENTUH TANAHKU AI SYSTEM                    │
│                                                                │
│  ┌──────────────────────┐         ┌────────────────────────┐  │
│  │      apps/web        │  HTTP   │       apps/api         │  │
│  │  Next.js Frontend    │◄───────►│   FastAPI Backend      │  │
│  │  (Vercel)            │         │   (Render)             │  │
│  └──────────────────────┘         └───────────┬────────────┘  │
│                                               │                │
│                                               ▼                │
│                                   ┌────────────────────────┐  │
│                                   │  Supabase (pgvector)   │  │
│                                   │  bpn_knowledge_base    │  │
│                                   └────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Multi-LLM Fallback Chain (28+ model)        │ │
│  │  SambaNova → Cerebras → OpenRouter → NVIDIA NIM → Groq   │ │
│  │  → Mistral → Scaleway → Cloudflare → Gemini              │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

### Alur Kerja RAG

1. User bertanya lewat UI (`apps/web`)
2. Backend membuat embedding pertanyaan via **Gemini** (`gemini-embedding-001`, 768 dim)
3. Vector search di Supabase (`match_bpn_knowledge`, top 3, threshold ≥ 0.5)
4. Prompt dirangkai bersama riwayat percakapan
5. **Fallback chain** mencoba model terbaik dulu (28+ model, 9 provider) — zero downtime meski sebagian provider down/kena kuota
6. Jawaban "Senta" yang ramah + daftar sumber referensi hukum

---

## 📦 Struktur Repository

```
.
├── apps/
│   ├── api/               # Backend FastAPI (RAG + fallback chain LLM)
│   │   ├── main.py
│   │   ├── data/          # Knowledge base sumber (data_bpn.json)
│   │   └── scripts/       # Ingest data, utilitas Render, demo Streamlit
│   └── web/               # Frontend Next.js (chat UI, auth, riwayat)
│       ├── app/           # App Router: (chat) & (auth)
│       ├── components/    # Radix UI + Tailwind
│       └── lib/           # AI providers, Drizzle ORM, migrations
├── docs/
│   └── DEPLOYMENT.md      # Panduan deploy Render + Vercel (monorepo)
├── .github/workflows/     # CI (lint & typecheck kedua app)
├── CONTEXT.md             # Konteks proyek untuk sesi AI-assisted development
├── LICENSE                # Apache 2.0
└── README.md
```

---

## 🚀 Menjalankan Secara Lokal

### Backend (API)

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # isi kredensial (Supabase + minimal GEMINI_API_KEYS)
uvicorn main:app --reload # http://localhost:8000 (docs: /docs)
```

### Frontend (Web)

```bash
cd apps/web
pnpm install
cp .env.example .env.local  # isi kredensial (Postgres, Auth, dll.)
pnpm db:migrate
pnpm dev                    # http://localhost:3000
```

Detail lengkap (setup Supabase + SQL pgvector, ingest data, daftar endpoint, format knowledge base) ada di [apps/api/README.md](apps/api/README.md) dan [apps/web/README.md](apps/web/README.md).

---

## 🌐 API Utama

Base URL produksi: `https://ai-sentuhtanahku-api.onrender.com` · Swagger: [/docs](https://ai-sentuhtanahku-api.onrender.com/docs)

```bash
curl -X POST https://ai-sentuhtanahku-api.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"pesan": "Apa syarat balik nama sertifikat?", "session_id": "demo", "riwayat": []}'
```

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

## 🎭 Karakter "Senta"

- **Panggilan:** memanggil user dengan "Kak"
- **Gaya bicara:** friendly, santai, elegan seperti "bestie", dengan emoji yang pas ✨
- **Anti-halusinasi:** jika jawaban tidak ada di knowledge base, Senta menolak dengan sopan ("jurus ngeles elegan") alih-alih mengarang
- **Sumber:** menyebutkan dasar hukum di akhir jawaban jika tersedia

---

## 🛠️ Development

- **CI:** setiap push/PR menjalankan syntax check + Ruff (API) dan typecheck + lint (Web) — lihat [.github/workflows/ci.yml](.github/workflows/ci.yml)
- **Deployment:** lihat [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) untuk konfigurasi monorepo di Render & Vercel
- **Konvensi:** `.editorconfig` di root; frontend memakai Ultracite (Biome), lockfile tunggal `pnpm-lock.yaml`

---

## 📄 Lisensi

[Apache License 2.0](LICENSE). Frontend diturunkan dari [vercel/ai-chatbot](https://github.com/vercel/ai-chatbot) (Apache 2.0). Data dan dokumen SOP bersumber dari regulasi resmi BPN — proyek ini dibuat untuk keperluan layanan publik pertanahan Indonesia.
