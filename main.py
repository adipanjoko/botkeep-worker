"""
botkeep-worker — server FastAPI penerima tugas dari n8n (standar PaaS).

Deploy (Railway / Render / Heroku):
  - Build otomatis dari requirements.txt, start via Procfile.
  - WAJIB set env WORKER_TOKEN di dashboard PaaS (jangan hardcode token!).

Endpoint (semua butuh header X-Token):
  POST /eksekusi-python   {"skrip_utuh": "...", "data_pecahan": [...]}
  POST /eksekusi-terminal  {"perintah_bash": "..."}
  GET  /status-pc         -> info CPU/RAM
  GET  /health            -> {"ok": true} (untuk health check PaaS)
"""

from fastapi import FastAPI, Request, HTTPException, Header
import uvicorn
import subprocess
import psutil
import os

app = FastAPI(title="botkeep-worker")

# Token HANYA dari environment variable — tidak ada default hardcoded.
# Set di PaaS: WORKER_TOKEN=<token-rahasia-anda>
TOKEN_RAHASIA = os.environ.get("WORKER_TOKEN", "")


def verifikasi_token(token: str | None):
    if not TOKEN_RAHASIA:
        raise HTTPException(
            status_code=500, detail="WORKER_TOKEN belum di-set di server"
        )
    if token != TOKEN_RAHASIA:
        raise HTTPException(status_code=401, detail="Akses Ditolak: Token Salah")


@app.get("/health")
def health():
    return {"ok": True, "service": "botkeep-worker"}


@app.post("/eksekusi-python")
async def eksekusi_python(req: Request, x_token: str | None = Header(default=None)):
    verifikasi_token(x_token)

    payload = await req.json()
    skrip = payload.get("skrip_utuh")
    data_target = payload.get("data_pecahan", [])

    if not skrip:
        raise HTTPException(status_code=422, detail="field 'skrip_utuh' wajib diisi")

    try:
        ruang_kerja = {"data_target": data_target, "hasil_komputasi": []}
        exec(skrip, globals(), ruang_kerja)
        return {"status": "sukses", "hasil": ruang_kerja.get("hasil_komputasi", [])}
    except Exception as e:
        return {"status": "gagal", "error": str(e)}


@app.post("/eksekusi-terminal")
async def eksekusi_terminal(req: Request, x_token: str | None = Header(default=None)):
    verifikasi_token(x_token)

    payload = await req.json()
    perintah = payload.get("perintah_bash")

    if not perintah:
        raise HTTPException(status_code=422, detail="field 'perintah_bash' wajib diisi")

    try:
        hasil = subprocess.run(
            perintah, shell=True, capture_output=True, text=True, timeout=600
        )
        return {"status": "sukses", "output": hasil.stdout, "error": hasil.stderr}
    except subprocess.TimeoutExpired:
        return {"status": "gagal", "error": "timeout setelah 600 detik"}
    except Exception as e:
        return {"status": "gagal", "error": str(e)}


@app.get("/status-pc")
def status_pc(x_token: str | None = Header(default=None)):
    verifikasi_token(x_token)

    ram = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1)

    return {
        "status": "aktif",
        "cpu_terpakai_persen": cpu,
        "ram_sisa_mb": round(ram.available / (1024 * 1024), 2),
        "penyimpanan_sementara": os.getcwd(),
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
