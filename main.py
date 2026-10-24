import io, os, time, uuid, webbrowser
from pathlib import Path
from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from config import settings
from excel_service import parse_excel_file, search_images_for_store, get_progress, export_salla_template
from openserp_manager import get_status as openserp_status

app = FastAPI(title='Salla Excel Desktop Engine')
app.mount('/static', StaticFiles(directory=settings.STATIC_DIR), name='static')
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name='index.html')

@app.post('/api/parse')
async def api_parse(file: UploadFile = File(...)):
    content = await file.read()
    return parse_excel_file(content, file.filename)

@app.post('/api/search-images')
async def api_search(data: dict):
    return await search_images_for_store(data.get('products') or [], use_ai=data.get('use_ai', True), job_id=data.get('job_id') or str(uuid.uuid4()))

@app.get('/api/progress/{job_id}')
async def api_prog(job_id: str):
    return get_progress(job_id)

@app.post('/api/export-salla-template')
async def api_exp(data: dict):
    content = export_salla_template(data.get('results') or [], data.get('template_type', 'new'))
    ts = int(time.time())
    type = data.get('template_type', 'new')
    prefix = "salla_update_products" if type == "update" else "salla_new_products"
    return StreamingResponse(io.BytesIO(content), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': f'attachment; filename="{prefix}_{ts}.xlsx"'})

if __name__ == '__main__':
    import uvicorn
    webbrowser.open('http://127.0.0.1:8585')
    uvicorn.run(app, host='127.0.0.1', port=8585)
