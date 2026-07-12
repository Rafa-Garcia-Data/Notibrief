# Notibrief

Captura publicaciones de LinkedIn y genera resumenes extractivos con un clic. Sin scraping, sin baneos.

## Como funciona

1. Instala la extension de Chrome en `extension/` en la carpetaraíz de la app. SOLO UNA VEZ este paso. 
2. Haz click derecho en un post de LinkedIn ( justo donde haces click en "más" para desplegar la publicación) → **Enviar a Notibrief**
3. Abre `http://localhost:8787` para ver los posts y generar resumenes
4. Pulsa **RESUMIR TODO** o resumir individualmente
5. Pulsa **Cerrar Aplicacion** para apagar el servidor

## Instalacion con Docker (recomendado)

### Requisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y ejecutandose

### Pasos
1. Doble clic en `start.bat`
2. Se construye la imagen, arranca el servidor y se abre el navegador automaticamente
3. Para apagar: boton **Cerrar Aplicacion** en la web o doble clic en `stop.bat` en la carpeta raíz de la app.

## Instalacion sin Docker

### Requisitos
- Python 3.10+
- Google Chrome con la extension cargada

### Pasos
```bash
pip install -r requirements.txt
python server.py
```

## Extension de Chrome

1. Abre `chrome://extensions` en Chrome
2. Activa **Modo desarrollador**
3. Clic en **Cargar extension sin empaquetar**
4. Selecciona la carpeta `extension/`
5. Asegurate de que el servidor este corriendo en `localhost:8787`

## Arquitectura

```
LinkedIn (navegador)
    │  click derecho → "Enviar a Notibrief"
    ▼
content.js (captura texto + imagenes del DOM)
    │
    ▼
background.js (envia al servidor)
    │
    ▼
server.py:8787 (almacena, limpia, resume)
    │
    ▼
Web UI (muestra posts con imagenes inline + resumenes)
```

- **Sin scraping**: la extension lee el DOM del navegador autenticado
- **Sin dependencias pesadas**: resumen extractivo puro (TF-IDF), sin modelos de ML
- **Cero baneos**: el servidor nunca toca LinkedIn

## Estructura del proyecto

```
Notibrief/
├── server.py              # Servidor FastAPI + web UI
├── resumidor.py           # Resumen extractivo (TF-IDF)
├── captured_posts.json    # Posts capturados
├── Dockerfile             # Imagen Docker
├── docker-compose.yml     # Servicio Docker
├── start.bat              # Lanzador one-click
├── stop.bat               # Detener servidor
├── requirements.txt       # Dependencias Python
└── extension/             # Extension Chrome
    ├── manifest.json
    ├── content.js
    ├── background.js
    └── icons/
```

## API

| Endpoint | Metodo | Descripcion |
|---|---|---|
| `/api/status` | GET | Estado del servidor |
| `/api/posts` | GET | Lista de posts capturados |
| `/api/capture` | POST | Capturar un post nuevo |
| `/api/posts/{index}/summarize` | POST | Resumir un post |
| `/api/summarize-all` | POST | Resumir todos los posts |
| `/api/posts/{index}` | DELETE | Eliminar un post |
| `/api/clear` | POST | Limpiar todos los posts |
| `/api/shutdown` | POST | Apagar el servidor |

## Tecnologias

- **Backend**: Python, FastAPI, Uvicorn
- **Frontend**: HTML/CSS/JS embebido
- **Resumen**: Extractivo TF-IDF (sin modelos de ML)
- **Extension**: Chrome Extension Manifest V3
- **Container**: Docker
