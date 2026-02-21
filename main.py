from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import pandas as pd
from io import BytesIO
import chardet
import requests
from ai_engine import generate_analysis

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Background Processing Function
# ==========================================
def process_analysis(analysis_id: int, df, question: str):

    db: Session = SessionLocal()

    try:
        analysis = db.query(models.Analysis).filter(
            models.Analysis.id == analysis_id
        ).first()

        if not analysis:
            return

        print("Starting AI processing...")
        print("Rows received:", len(df))

        ai_output = generate_analysis(df, question)

        if not ai_output:
            raise Exception("AI returned empty output")

        analysis.ai_output = ai_output
        analysis.industry = ai_output.get("industry", "General Business")
        analysis.status = "completed"

        print("AI processing completed.")

    except Exception as e:
        print("AI ERROR:", str(e))

        # Save error message in DB for debugging
        analysis.ai_output = {"error": str(e)}
        analysis.status = "failed"

    finally:
        db.commit()
        db.close()


# ==========================================
# Upload Endpoint
# ==========================================
@app.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(None),
    question: str = Form(...),
    google_sheet_url: str = Form(None)
):
    try:
        df = None

        # -------- Google Sheets --------
        if google_sheet_url and "docs.google.com" in google_sheet_url:
            export_url = google_sheet_url.split("/edit")[0] + "/export?format=csv"
            response = requests.get(export_url)

            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid Google Sheets URL")

            df = pd.read_csv(BytesIO(response.content))

        # -------- File Upload --------
        elif file:
            content = await file.read()
            filename = file.filename.lower()

            if filename.endswith(".csv"):
                encoding = chardet.detect(content)["encoding"]
                df = pd.read_csv(BytesIO(content), encoding=encoding)

            elif filename.endswith(".xlsx"):
                df = pd.read_excel(BytesIO(content), engine="openpyxl")

            elif filename.endswith(".xls"):
                df = pd.read_excel(BytesIO(content), engine="xlrd")

            else:
                raise HTTPException(status_code=400, detail="Unsupported file format")

        else:
            raise HTTPException(status_code=400, detail="No file provided")

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Uploaded dataset is empty")

        # -------- Store Analysis Record --------
        db: Session = SessionLocal()

        new_analysis = models.Analysis(
            filename=file.filename if file else "Google Sheet",
            question=question,
            status="processing"
        )

        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)

        # -------- PASS FULL DATAFRAME --------
        background_tasks.add_task(
            process_analysis,
            new_analysis.id,
            df,
            question
        )

        db.close()

        return {
            "analysis_id": new_analysis.id,
            "status": "processing"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Get Analysis Endpoint
# ==========================================
@app.get("/analysis/{analysis_id}")
def get_analysis(analysis_id: int):

    db: Session = SessionLocal()

    analysis = db.query(models.Analysis).filter(
        models.Analysis.id == analysis_id
    ).first()

    db.close()

    if not analysis:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "id": analysis.id,
        "status": analysis.status,
        "analysis": analysis.ai_output
    }