<<<<<<< HEAD
# Placeholder for app.py
=======
# main.py
from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil, os, subprocess, time

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

SCRIPT_MAP = {
    "check_missing": "scripts/check_missing_anime_mal.py",
    "sort_plan": "scripts/sorted_plan_to_watch_mal.py",
    "franchise_tree": "scripts/anime_franchise_tree.py"
}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/run_tool", response_class=HTMLResponse)
async def run_tool(request: Request, 
                   file: UploadFile, 
                   tool: str = Form(...),
                   output_type: str = Form("html")):

    # Save file as animelist.xml
    file_path = "animelist.xml"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Select script
    script_path = SCRIPT_MAP.get(tool)
    if not script_path or not os.path.exists(script_path):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Script not found or not available."
        })

    # Remove old outputs
    for ext in ["html", "txt"]:
        output_file = f"output.{ext}"
        if os.path.exists(output_file):
            os.remove(output_file)

    # Run script
    try:
        result = subprocess.run(["python", script_path], capture_output=True, text=True, timeout=600)
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Script execution failed: {str(e)}"
        })

    # Return result
    html_path = "output.html"
    txt_path = "output.txt"
    output_files = []
    if output_type in ["html", "both"] and os.path.exists(html_path):
        output_files.append(("HTML", html_path))
    if output_type in ["txt", "both"] and os.path.exists(txt_path):
        output_files.append(("Text", txt_path))

    return templates.TemplateResponse("upload_success.html", {
        "request": request,
        "files": output_files,
        "tool_name": tool.replace("_", " ").title()
    })
>>>>>>> 1b98142e54bb9f37437e4795742a63c97a5ef4fc
