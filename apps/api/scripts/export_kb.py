"""
Export knowledge base produksi (Supabase) ke data/kb_snapshot.json — TANPA embedding.

Tujuan: seluruh isi tabel bpn_knowledge_base ikut ter-versioning di git,
jadi ada backup dan setiap koreksi konten bisa dilacak riwayatnya.

Pakai:
    cd apps/api
    python scripts/export_kb.py

Butuh SUPABASE_URL dan SUPABASE_KEY di environment atau di file .env.
Jalankan ulang setiap selesai mengedit isi KB, lalu commit hasilnya.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "kb_snapshot.json"
PAGE_SIZE = 500


def load_dotenv() -> None:
    """Muat .env sederhana (KEY=VALUE) dari folder apps/api tanpa dependensi."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def fetch_page(base_url: str, key: str, offset: int) -> list:
    params = urllib.parse.urlencode({
        "select": "id,metadata,content_to_embed,content",
        "order": "id.asc",
        "limit": PAGE_SIZE,
        "offset": offset,
    })
    req = urllib.request.Request(
        f"{base_url}/rest/v1/bpn_knowledge_base?{params}",
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    load_dotenv()
    base_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = os.getenv("SUPABASE_KEY", "").strip()
    if not base_url or not key:
        sys.exit("❌ SUPABASE_URL / SUPABASE_KEY belum diset (di .env atau environment).")

    rows, offset = [], 0
    while True:
        page = fetch_page(base_url, key, offset)
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    OUTPUT.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"✅ {len(rows)} dokumen diekspor ke {OUTPUT.relative_to(Path.cwd()) if OUTPUT.is_relative_to(Path.cwd()) else OUTPUT}")


if __name__ == "__main__":
    main()
