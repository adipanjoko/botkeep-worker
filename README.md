# botkeep-worker

Server FastAPI penerima tugas eksekusi dari n8n. Standar deployment PaaS
(Railway / Render / Heroku): `Procfile` + `requirements.txt`.

## Deploy ke PaaS

1. Push repo ini ke GitHub.
2. Di Railway/Render: **New Project → Deploy from GitHub repo**.
   - Build otomatis: `pip install -r requirements.txt`
   - Start otomatis: `web: uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`
3. **WAJIB** set environment variable di dashboard PaaS:

   | Variable | Nilai |
   |---|---|
   | `WORKER_TOKEN` | token rahasia buatanmu (mis. hasil `openssl rand -hex 24`) |

   Tanpa `WORKER_TOKEN`, semua endpoint menolak dengan HTTP 500.
   Token JANGAN ditulis di kode — hanya lewat env.

## Cara pakai dari n8n

HTTP Request node → header `X-Token: <WORKER_TOKEN>`:

**Eksekusi Python** — `POST /eksekusi-python`
```json
{
  "skrip_utuh": "for row in data_target:\n    hasil_komputasi.append(row * 2)",
  "data_pecahan": [1, 2, 3]
}
```
Respons: `{"status": "sukses", "hasil": [2, 4, 6]}`.
Skrip dieksekusi dengan `data_target` tersedia dan wajib mengisi
`hasil_komputasi`.

**Eksekusi terminal** — `POST /eksekusi-terminal`
```json
{"perintah_bash": "ls -la /tmp"}
```
Respons: `{"status": "sukses", "output": "...", "error": "..."}`.

**Status mesin** — `GET /status-pc`
Respons: `{"status": "aktif", "cpu_terpakai_persen": 12.5, "ram_sisa_mb": 3450.2, ...}`

**Health check** — `GET /health` → `{"ok": true}` (tanpa token, untuk PaaS).

## Lokal

```bash
pip install -r requirements.txt
WORKER_TOKEN=<tokenmu> uvicorn main:app --host 0.0.0.0 --port 8000
```

## Keamanan

Endpoint ini mengeksekusi kode arbitrer — selalu pakai token kuat,
jangan expose tanpa HTTPS, dan batasi siapa yang tahu URL + tokennya.
