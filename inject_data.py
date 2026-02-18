import os
import requests
from google import genai

# 1. KONFIGURASI KUNCI (ISI BAGIAN INI!)
SUPABASE_URL = "https://hzmlxnsnuycvqkpetxhe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh6bWx4bnNudXljdnFrcGV0eGhlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzNDM1ODQsImV4cCI6MjA4NjkxOTU4NH0.0ahv8dGihy3EtCeR-NTPUuh4faW8lnJyq-laH7KGxW0"
#GEMINI_API_KEY = "AIzaSyA9k21yPFqTkX2YMU8IeIH2ew2RJ5S9G2o"
GEMINI_API_KEY = "AIzaSyDAqf4d8eebsvLmZVlf0_TwDrM3tPfAeu8"

# 2. INISIALISASI GEMINI
client = genai.Client(api_key=GEMINI_API_KEY)

# 3. DATA DOKUMEN SOP BPN
dokumen_bpn = [
  {
    "judul": "Pengecekan Sertifikat",
    "konten": "Sangat wajib. Pengecekan sertifikat (Checking) dilakukan di Kantor Pertanahan oleh PPAT sebelum pembuatan akta. Tujuannya untuk memastikan kesesuaian data fisik dan yuridis, serta memastikan sertifikat tersebut asli, tidak sedang diblokir, tidak dalam sengketa, dan tidak sedang dijaminkan ke pihak lain.",
    "sumber": "Pasal 97 Permen ATR/BPN No. 3 Tahun 1997"
  },
  {
    "judul": "Blokir Sertifikat",
    "konten": "Pihak yang berkepentingan (misal: ahli waris yang bersengketa atau korban penipuan) dapat mengajukan permohonan pencatatan blokir ke BPN. Syaratnya membawa bukti identitas, bukti hubungan hukum dengan tanah tersebut, dan alasan blokir. Blokir berlaku 30 hari dan bisa diperpanjang jika ada perintah pengadilan.",
    "sumber": "Permen ATR/BPN No. 13 Tahun 2017 tentang Tata Cara Blokir dan Sita"
  },
  {
    "judul": "Status Kepemilikan Apartemen",
    "konten": "Berbeda. SHMSRS (Sertifikat Hak Milik atas Satuan Rumah Susun) memberikan hak kepemilikan atas unit (ruang) secara individu, ditambah hak bersama atas tanah bersama, benda bersama, dan bagian bersama. Status tanah berdirinya apartemen biasanya adalah HGB, bukan SHM murni.",
    "sumber": "UU No. 20 Tahun 2011 tentang Rumah Susun"
  },
  {
    "judul": "Kepemilikan Tanah oleh Badan Hukum",
    "konten": "Tidak boleh. Badan Hukum (PT, Yayasan, Koperasi) dilarang memiliki SHM. Jika sebuah PT membeli tanah SHM, haknya wajib diturunkan menjadi Hak Guna Bangunan (HGB) atau Hak Pakai. Jika dipaksakan tetap SHM, maka hak tanah tersebut hapus demi hukum dan tanah menjadi milik negara.",
    "sumber": "Pasal 21 UU No. 5 Tahun 1960 (UUPA)"
  },
  {
    "judul": "Selisih Luas Tanah",
    "konten": "Pemilik tanah dapat mengajukan permohonan 'Pengembalian Batas' atau 'Pengukuran Ulang' ke BPN. Petugas ukur akan mengecek kembali batas-batas fisik. Jika memang terjadi perubahan alam atau kesalahan ukur lama, dapat dilakukan perbaikan data fisik pada sertifikat melalui prosedur adminitrasi di BPN.",
    "sumber": "Pasal 16 PP No. 24 Tahun 1997"
  },
  {
    "judul": "Biaya Honorarium PPAT",
    "konten": "Uang jasa (honorarium) PPAT termasuk uang saksi untuk pembuatan akta tidak boleh melebihi 1% (satu persen) dari harga transaksi yang tercantum di dalam akta. Namun, untuk masyarakat tidak mampu, PPAT wajib memberikan jasa secara cuma-cuma.",
    "sumber": "Pasal 32 Peraturan Menteri ATR/BPN No. 33 Tahun 2021"
  },
  {
    "judul": "Larangan Tanah Absente",
    "konten": "Pemilik tanah pertanian wajib bertempat tinggal di kecamatan tempat tanah itu berada (atau berbatasan langsung). Kepemilikan tanah pertanian secara 'Guntai' (Absente) dilarang untuk mencegah penguasaan tanah tanpa digarap, kecuali bagi PNS/TNI/Pensiunan dengan batasan luas tertentu.",
    "sumber": "PP No. 224 Tahun 1961 & PP No. 41 Tahun 1964"
  },
  {
    "judul": "Prosedur Over Kredit",
    "konten": "Jangan hanya menggunakan kuitansi atau Surat Kuasa jual bawah tangan. Cara yang sah adalah melalui 'Novasi' resmi di Bank (debitur diganti). Atau jika Bank menolak, lakukan Akta Pengikatan Jual Beli (PPJB) lunas + Surat Kuasa Mengambil Sertifikat + Kuasa Menjual di hadapan Notaris agar hak pembeli terlindungi.",
    "sumber": "KUHPerdata Buku III tentang Perikatan"
  },
  {
    "judul": "Perbedaan Notaris dan PPAT",
    "konten": "Notaris berwenang membuat akta otentik umum (seperti pendirian PT, Waris, Perjanjian), diangkat oleh Kemenkumham. PPAT khusus berwenang membuat akta peralihan hak atas tanah (Jual Beli, Hibah, APHT), diangkat oleh Kementerian ATR/BPN. Seseorang bisa merangkap jabatan keduanya.",
    "sumber": "UU Jabatan Notaris & PP No. 37 Tahun 1998"
  },
  {
    "judul": "Status Tanah Wakaf",
    "konten": "Tidak bisa. Harta benda yang sudah diwakafkan dilarang dijadikan jaminan, disita, dihibahkan, dijual, diwariskan, ditukar, atau dialihkan dalam bentuk pengalihan hak lainnya. Statusnya menjadi milik umat/Allah untuk kepentingan umum/ibadah.",
    "sumber": "UU No. 41 Tahun 2004 tentang Wakaf"
  },
  {
    "judul": "Penghapusan Hak Tanggungan (Roya)",
    "konten": "Setelah kredit lunas, Bank akan memberikan surat lunas dan sertifikat HT. Debitur wajib membawanya ke BPN (kini bisa online/elektronik) untuk proses Roya. Proses ini akan menghapus catatan beban utang di buku tanah sertifikat, sehingga sertifikat kembali bersih.",
    "sumber": "Pasal 22 UU No. 4 Tahun 1996"
  },
  {
    "judul": "Izin KKPR",
    "konten": "KKPR adalah dokumen yang menyatakan kesesuaian antara rencana kegiatan pemanfaatan ruang dengan Rencana Tata Ruang (RTR). Sebelum mengurus perizinan berusaha atau mendirikan bangunan (PBG) di atas tanah, pemilik wajib memastikan tanah tersebut sesuai zonanya melalui KKPR.",
    "sumber": "PP No. 21 Tahun 2021 tentang Penyelenggaraan Penataan Ruang"
  },
  {
    "judul": "Salinan Akta PPAT",
    "konten": "Bisa. Pihak yang berkepentingan (penjual/pembeli) dapat meminta Salinan Akta (Grosse Akta) kepada PPAT yang membuat akta tersebut. PPAT wajib menyimpan Minuta Akta (dokumen asli) sebagai arsip negara yang tidak boleh dikeluarkan.",
    "sumber": "PP No. 37 Tahun 1998 tentang Peraturan Jabatan PPAT"
  },
  {
    "judul": "Tanah Sempadan Sungai",
    "konten": "Tanah yang masuk dalam garis sempadan sungai (zona pelindung sungai) adalah tanah negara yang dilarang dimiliki dengan Hak Milik (SHM) dan dilarang mendirikan bangunan permanen di atasnya. Sertifikat tidak akan diterbitkan jika hasil ukur BPN menunjukkan lokasi berada di zona terlarang.",
    "sumber": "Permen PUPR No. 28/PRT/M/2015"
  },
  {
    "judul": "Sanksi Tanah Terlantar",
    "konten": "Pemerintah dapat menetapkan tanah tersebut sebagai Tanah Terlantar. Setelah melalui peringatan (1, 2, dan 3), hak atas tanah dapat dihapuskan, diputuskan hubungan hukumnya, dan tanah kembali dikuasai Negara atau diberikan kepada pihak lain yang membutuhkan (Bank Tanah).",
    "sumber": "PP No. 20 Tahun 2021 tentang Penertiban Kawasan dan Tanah Terlantar"
  },
  {
    "judul": "Pemecahan Sertifikat",
    "konten": "Pemilik mengajukan permohonan pemecahan ke BPN dengan melampirkan Site Plan yang disetujui dinas tata kota. BPN akan melakukan pengukuran dan menerbitkan Surat Ukur baru untuk tiap kavling. Sertifikat induk akan ditarik/dimatikan dan diganti dengan sertifikat-sertifikat pecahan.",
    "sumber": "Pasal 48 PP No. 24 Tahun 1997"
  },
  {
    "judul": "Hak Jalan (Servitut)",
    "konten": "Tidak boleh, terutama jika jalan tersebut adalah satu-satunya akses (tanah terkurung). Pemilik tanah yang terkurung berhak menuntut jalan keluar ke jalan umum dari tetangganya dengan ganti rugi yang layak. Tanah memiliki fungsi sosial yang tidak boleh merugikan kepentingan umum.",
    "sumber": "Pasal 6 UUPA & Pasal 667 KUHPerdata"
  },
  {
    "judul": "Definisi Warkah",
    "konten": "Warkah adalah kumpulan dokumen riwayat yang menjadi dasar penerbitan sertifikat tanah. Isinya meliputi surat permohonan, bukti alas hak (girik/AJB lama), identitas pemohon, dan data pengukuran. Warkah disimpan di arsip BPN dan bersifat rahasia, hanya bisa dibuka atas perintah pengadilan atau penyidikan.",
    "sumber": "Permen ATR/BPN No. 3 Tahun 1997"
  },
  {
    "judul": "Persetujuan Pasangan",
    "konten": "Wajib, jika tanah tersebut diperoleh selama perkawinan (Harta Gono-Gini), meskipun sertifikatnya hanya atas nama suami atau istri saja. Tanpa persetujuan pasangan, jual beli cacat hukum dan bisa dibatalkan. Kecuali ada Perjanjian Pisah Harta yang dibuat di Notaris.",
    "sumber": "Pasal 36 UU No. 1 Tahun 1974 tentang Perkawinan"
  },
  {
    "judul": "Tanah Tanpa Ahli Waris",
    "konten": "Jika seseorang meninggal dunia tanpa meninggalkan ahli waris (baik sedarah maupun pasangan) dan tidak meninggalkan wasiat, maka harta bendanya (termasuk tanah) akan jatuh menjadi milik Negara.",
    "sumber": "Pasal 832 KUHPerdata (Burgerlijk Wetboek)"
  }
]

def generate_embedding(teks: str) -> list[float]:
    """Mengubah teks menjadi vektor menggunakan Gemini"""
    print(f"Mengubah ke angka: '{teks[:30]}...'")
    response = client.models.embed_content(
        model='gemini-embedding-001', # <--- GANTI JADI INI
        contents=teks,
    )
    return response.embeddings[0].values

def inject_ke_supabase():
    print("Memulai injeksi data ke Supabase (Metode API API Rest)...\n")
    
    # Header khusus untuk otentikasi REST API Supabase
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # URL Endpoint untuk tabel 'bpn_documents'
    endpoint_url = f"{SUPABASE_URL}/rest/v1/bpn_documents"

    for doc in dokumen_bpn:
        vektor = generate_embedding(doc["konten"])
        
        payload = {
            "judul": doc["judul"],
            "konten": doc["konten"],
            "sumber": doc["sumber"],
            "embedding": vektor
        }
        
        # Kirim HTTP POST ke Supabase
        response = requests.post(endpoint_url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            print(f"✅ Berhasil menyuntikkan: {doc['judul']}")
        else:
            print(f"❌ Gagal: {response.text}")

    print("\n🎉 Proses Selesai!")

if __name__ == "__main__":
    inject_ke_supabase()