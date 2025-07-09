from fastapi import FastAPI, Request, Form, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import shutil
import time
from scripts import check_missing_anime_mal, sorted_plan_to_watch_mal, anime_franchise_tree

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_upload_file(upload_file: UploadFile, destination: str):
    with open(destination, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/run_script", response_class=HTMLResponse)
async def run_script(
    request: Request,
    script: str = Form(...),
    malusername: str = Form(""),
    output_types: list[str] = Form(...),
    xmlfile: UploadFile = File(None)
):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    input_path = os.path.join(UPLOAD_DIR, "animelist.xml")

    if xmlfile:
        save_upload_file(xmlfile, input_path)
    elif malusername:
        # Future enhancement: Fetch XML from MAL user
        return templates.TemplateResponse("home.html", {"request": request, "error": "Username fetching not implemented yet."})
    else:
        return templates.TemplateResponse("home.html", {"request": request, "error": "Please upload a file or enter a username."})

    html_path = os.path.join(OUTPUT_DIR, f"output_{timestamp}.html")
    txt_path = os.path.join(OUTPUT_DIR, f"output_{timestamp}.txt")

    # Run selected script
    if script == "Check Missing Anime":
        check_missing_anime_mal.run(xml_path=input_path, html_output=html_path)
    elif script == "Sort Plan To Watch":
        sorted_plan_to_watch_mal.run(xml_path=input_path, html_output=html_path, txt_output=txt_path)
    elif script == "Anime Franchise Tree":
        anime_franchise_tree.run(xml_path=input_path, html_output=html_path)
    else:
        return templates.TemplateResponse("home.html", {"request": request, "error": "Unknown script selected."})

    return templates.TemplateResponse("results.html", {
        "request": request,
        "html_result": f"/{html_path}",
        "txt_result": f"/{txt_path}" if os.path.exists(txt_path) else None,
        "generated_at": timestamp
    })
