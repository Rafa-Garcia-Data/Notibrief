import json
import os
import re
import threading
import traceback
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="Notibrief")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

DATA_FILE = Path(__file__).parent / "captured_posts.json"


def load_posts():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text("utf-8"))
        except Exception:
            return []
    return []


def save_posts(posts):
    DATA_FILE.write_text(json.dumps(posts, ensure_ascii=False, indent=2), "utf-8")


def is_linkedin_url(url):
    return bool(url and "linkedin.com" in url)


def clean(text):
    text = re.sub(r"[\u2600-\u27BF\U0001F600-\U0001FAFF]", "", text)
    return re.sub(r"\s+", " ", text).strip()


@app.get("/api/status")
def status():
    return {"ok": True, "posts_count": len(load_posts())}


@app.post("/api/capture")
async def capture(request: Request):
    body = await request.json()
    url = body.get("url", "").strip()
    text = clean(body.get("text", ""))
    images = body.get("images", [])

    if not is_linkedin_url(url):
        return JSONResponse({"error": "No es LinkedIn"}, status_code=400)

    posts = load_posts()
    if any(p["url"] == url for p in posts):
        return {"ok": True, "duplicate": True}

    posts.append({
        "url": url,
        "text": text,
        "images": images,
        "captured_at": datetime.now().isoformat(),
    })
    save_posts(posts)
    return {"ok": True, "total": len(posts), "has_text": bool(text), "has_images": bool(images)}


@app.get("/api/posts")
def get_posts():
    return {"posts": load_posts()}


@app.delete("/api/posts/{index}")
def delete_post(index: int):
    posts = load_posts()
    if 0 <= index < len(posts):
        posts.pop(index)
        save_posts(posts)
        return {"ok": True}
    return JSONResponse({"error": "Invalid"}, status_code=400)


@app.post("/api/clear")
def clear_posts():
    save_posts([])
    return {"ok": True}


@app.post("/api/posts/{index}/summarize")
def summarize_post(index: int):
    posts = load_posts()
    if not (0 <= index < len(posts)):
        return JSONResponse({"error": "Invalid"}, status_code=400)
    post = posts[index]
    text = post.get("text", "")
    if not text or len(text) < 50:
        return {"ok": False, "error": "Sin texto para resumir"}
    try:
        from resumidor import Resumidor
        r = Resumidor()
        s = r.resumir(text, max_length=400, min_length=100)
        posts[index]["summary"] = s
        save_posts(posts)
        return {"ok": True, "summary": s}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/summarize-all")
def summarize_all():
    posts = load_posts()
    with_text = [i for i, p in enumerate(posts) if len(p.get("text", "")) > 50]
    if not with_text:
        return JSONResponse({"error": "No hay posts con texto para resumir"}, status_code=400)
    try:
        from resumidor import Resumidor
        r = Resumidor()
        for i in with_text:
            if not posts[i].get("summary"):
                posts[i]["summary"] = r.resumir(posts[i]["text"], max_length=400, min_length=100)
        save_posts(posts)
        return {"ok": True, "count": len(with_text)}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/shutdown")
def shutdown():
    threading.Thread(target=lambda: os._exit(0), daemon=True).start()
    return {"ok": True, "message": "Apagando servidor..."}


@app.get("/", response_class=HTMLResponse)
def web_ui():
    return WEB_UI


WEB_UI = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Notibrief</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f3f2ef;color:#333}
.hdr{background:linear-gradient(135deg,#0a66c2,#004182);color:#fff;padding:28px 32px}
.hdr h1{font-size:26px;font-weight:700}.hdr p{opacity:.8;margin-top:4px;font-size:13px}
.w{max-width:880px;margin:24px auto;padding:0 16px}
.st{display:flex;gap:12px;margin-bottom:20px}
.sc{background:#fff;border-radius:12px;padding:18px;flex:1;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.08)}
.sn{font-size:36px;font-weight:700;color:#0a66c2}.sl{font-size:12px;color:#666;margin-top:2px}
.ho{background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
.ho h3{margin-bottom:10px;font-size:15px}.ho ol{padding-left:20px;font-size:13px;line-height:1.8;color:#555}
.ac{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}
.btn{padding:10px 22px;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;transition:all .2s}
.bp{background:#0a66c2;color:#fff}.bp:hover{background:#004182}
.bg{background:#27ae60;color:#fff}.bg:hover{background:#1e8449}
.bd{background:#fff;color:#e74c3c;border:1px solid #e74c3c}.bd:hover{background:#fdf0ef}
.bs{background:#2c3e50;color:#fff}.bs:hover{background:#1a252f}
.btn:disabled{opacity:.5;cursor:not-allowed}
.lst{display:flex;flex-direction:column;gap:12px}
.cd{background:#fff;border-radius:12px;padding:16px 20px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.cd .au{font-weight:600;font-size:14px}.cd .dt{font-size:11px;color:#999}
.cd .tx{font-size:13px;color:#555;line-height:1.5;margin:8px 0;max-height:120px;overflow:hidden}
.cd .ln{color:#0a66c2;text-decoration:none;font-size:12px;font-weight:500}.cd .ln:hover{text-decoration:underline}
.cd .sm{background:#e8f4fd;border-left:3px solid #0a66c2;padding:10px 14px;border-radius:0 8px 8px 0;margin-top:10px;font-size:13px;line-height:1.5}
.cd .no{font-size:12px;color:#999;font-style:italic;margin-top:6px}
.cd .a2{display:flex;gap:8px;margin-top:10px}.cd .a2 .btn{padding:5px 14px;font-size:12px}
.img-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px;margin:10px 0}
.img-grid img{width:100%;border-radius:8px;cursor:pointer;transition:transform .2s}
.img-grid img:hover{transform:scale(1.03)}
.gs{background:#fff;border-radius:12px;padding:20px 24px;box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:20px}
.gs h3{margin-bottom:8px;font-size:16px}.gs p{font-size:14px;line-height:1.6;color:#555}
.em{text-align:center;padding:60px 20px;color:#999}.em h2{font-size:18px;margin-bottom:6px}.em p{font-size:13px}
.ld{display:inline-block;width:16px;height:16px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:sp .6s linear infinite}
@keyframes sp{to{transform:rotate(360deg)}}
.toast{position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:8px;font-size:14px;font-weight:600;color:#fff;box-shadow:0 4px 12px rgba(0,0,0,.3);z-index:9999;transition:opacity .3s}
.modal-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.85);z-index:10000;display:flex;align-items:center;justify-content:center;cursor:pointer}
.modal-overlay img{max-width:90vw;max-height:90vh;border-radius:8px}
</style>
</head>
<body>
<div class="hdr"><h1>Notibrief</h1><p>Click derecho en LinkedIn &rarr; Enviar a Notibrief</p></div>
<div class="w">
  <div class="st">
    <div class="sc"><div class="sn" id="pc">0</div><div class="sl">Capturados</div></div>
    <div class="sc"><div class="sn" id="sc">0</div><div class="sl">Con texto</div></div>
    <div class="sc"><div class="sn" id="sr">0</div><div class="sl">Resumenes</div></div>
  </div>
  <div class="ho">
    <h3>Como funciona</h3>
    <ol>
      <li>Click derecho en LinkedIn &rarr; <b>Enviar a Notibrief</b></li>
      <li>El servidor captura el texto e imagenes del post</li>
      <li>Pulsa <b>RESUMIR TODO</b> para generar resumenes</li>
    </ol>
  </div>
  <div class="ac">
    <button class="btn bp" onclick="load()">Actualizar</button>
    <button class="btn bg" id="br" onclick="sumAll()">RESUMIR TODO</button>
    <button class="btn bd" onclick="clr()">Limpiar</button>
    <button class="btn bs" onclick="shutdown()">Cerrar Aplicacion</button>
  </div>
  <div class="lst" id="pl">
    <div class="em"><h2>Sin posts</h2><p>Captura publicaciones con click derecho en LinkedIn.</p></div>
  </div>
</div>
<script>
let P=[];
async function api(m,p,b){const o={method:m,headers:{'Content-Type':'application/json'}};if(b)o.body=JSON.stringify(b);return(await fetch(p,o)).json()}
function toast(m,e){const d=document.createElement('div');d.className='toast';d.style.cssText='background:'+(e?'#e74c3c':'#27ae60');d.textContent=m;document.body.appendChild(d);setTimeout(()=>{d.style.opacity='0';setTimeout(()=>d.remove(),300)},2500)}
function esc(s){const d=document.createElement('div');d.textContent=s||'';return d.innerHTML}
function showImg(src){const o=document.createElement('div');o.className='modal-overlay';o.onclick=()=>o.remove();const i=document.createElement('img');i.src=src;o.appendChild(i);document.body.appendChild(o)}
function render(){
  const el=document.getElementById('pl');
  document.getElementById('pc').textContent=P.length;
  document.getElementById('sc').textContent=P.filter(p=>p.text).length;
  document.getElementById('sr').textContent=P.filter(p=>p.summary).length;
  if(!P.length){el.innerHTML='<div class="em"><h2>Sin posts</h2><p>Captura publicaciones con click derecho en LinkedIn.</p></div>';return}
  el.innerHTML=P.map((p,i)=>{
    const imgs=(p.images||[]).map(im=>'<img src="'+esc(im.src)+'" alt="'+esc(im.alt)+'" onclick="showImg(\''+esc(im.src)+'\')" loading="lazy">').join('');
    return `<div class="cd">
    <div class="dt">${new Date(p.captured_at).toLocaleString('es')}</div>
    <a class="ln" href="${esc(p.url)}" target="_blank">${esc(p.url)}</a>
    ${p.text?'<div class="tx">'+esc(p.text.substring(0,500))+(p.text.length>500?'...':'')+'</div>':'<div class="no">Sin contenido</div>'}
    ${imgs?'<div class="img-grid">'+imgs+'</div>':''}
    ${p.summary?'<div class="sm"><b>Resumen:</b> '+esc(p.summary)+'</div>':''}
    <div class="a2">
      ${p.text?'<button class="btn bp" onclick="res1('+i+')" '+(p.summary?'disabled':'')+('">'+(p.summary?'OK':'Resumir'))+'</button>':''}
      <button class="btn bd" onclick="del('+i+')">X</button>
    </div>
  </div>`}).join('');
}
async function load(){const d=await api('GET','/api/posts');P=d.posts||[];render()}
async function sumAll(){
  const b=document.getElementById('br');b.disabled=true;b.innerHTML='<span class="ld"></span> Resumiendo...';
  try{const d=await api('POST','/api/summarize-all');
    if(d.ok){toast('Resumidos '+d.count+' posts');load()}else toast(d.error||'Error',true)
  }catch{toast('Error',true)}
  b.disabled=false;b.textContent='RESUMIR TODO';
}
async function res1(i){toast('Resumiendo...');const d=await api('POST','/api/posts/'+i+'/summarize');if(d.ok){P[i].summary=d.summary;render();toast('OK')}else toast(d.error||'Error',true)}
async function del(i){await api('DELETE','/api/posts/'+i);load()}
async function clr(){if(!confirm('Limpiar todo?'))return;await api('POST','/api/clear');load()}
async function shutdown(){if(!confirm('Cerrar Notibrief?'))return;toast('Apagando...');await api('POST','/api/shutdown');setTimeout(()=>{document.body.innerHTML='<div style="display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;color:#666"><h2>Notibrief detenido</h2></div>'},1000)}
load();setInterval(load,10000);
</script>
</body>
</html>"""


if __name__ == "__main__":
    print("=" * 50)
    print("  NOTIBRIEF - http://localhost:8787")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8787, log_level="info")
