import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import VideoJob, Account

from bson import ObjectId

app = FastAPI(title="AI Shorts Automation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateJobRequest(BaseModel):
    title: Optional[str] = None
    subreddit: Optional[str] = None
    reddit_post_url: Optional[str] = None
    keyword: Optional[str] = None
    voice: Optional[str] = None
    aspect_ratio: Optional[str] = None
    include_captions: Optional[bool] = True
    include_broll: Optional[bool] = True
    autopost_youtube: Optional[bool] = False
    autopost_tiktok: Optional[bool] = False
    autopost_instagram: Optional[bool] = False


class ConnectAccountRequest(BaseModel):
    platform: str
    account_name: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "AI Shorts Automation Backend Running"}


@app.get("/schema")
async def schema():
    return {
        "collections": ["account", "videojob"],
        "models": {
            "account": Account.model_json_schema(),
            "videojob": VideoJob.model_json_schema(),
        },
    }


@app.get("/jobs")
async def list_jobs():
    try:
        docs = get_documents("videojob", limit=100)
        out = []
        for d in docs:
            d = dict(d)
            if "_id" in d:
                d["id"] = str(d["_id"])  # expose as id
                del d["_id"]
            out.append(d)
        return {"items": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobs")
async def create_job(payload: CreateJobRequest):
    try:
        job = VideoJob(
            title=payload.title,
            subreddit=payload.subreddit,
            reddit_post_url=payload.reddit_post_url,
            keyword=payload.keyword,
            voice=payload.voice or "female-soft",
            aspect_ratio=payload.aspect_ratio or "9:16",
            include_captions=True if payload.include_captions is None else payload.include_captions,
            include_broll=True if payload.include_broll is None else payload.include_broll,
            autopost_youtube=bool(payload.autopost_youtube),
            autopost_tiktok=bool(payload.autopost_tiktok),
            autopost_instagram=bool(payload.autopost_instagram),
            status="queued",
        )
        inserted_id = create_document("videojob", job)
        return {"id": inserted_id, "status": job.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobs/{job_id}/process")
async def process_job(job_id: str):
    """
    Demo processor that marks a job as completed and returns a mock video URL.
    In a real system, this would:
    - fetch Reddit content
    - generate script & TTS
    - render video with captions/b-roll
    - upload to platforms if enabled
    """
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")
        oid = ObjectId(job_id)
        job = db["videojob"].find_one({"_id": oid})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Start processing
        db["videojob"].update_one({"_id": oid}, {"$set": {"status": "processing"}})

        # Simulate processing result
        platforms_posted = []
        if job.get("autopost_youtube"):
            platforms_posted.append("youtube")
        if job.get("autopost_tiktok"):
            platforms_posted.append("tiktok")
        if job.get("autopost_instagram"):
            platforms_posted.append("instagram")

        result_url = "https://samplelib.com/lib/preview/mp4/sample-5s.mp4"  # placeholder demo video

        db["videojob"].update_one(
            {"_id": oid},
            {"$set": {
                "status": "completed",
                "result_video_url": result_url,
                "platforms_posted": platforms_posted,
            }}
        )

        updated = db["videojob"].find_one({"_id": oid})
        updated_out = dict(updated)
        updated_out["id"] = str(updated_out.pop("_id"))
        return updated_out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/accounts")
async def list_accounts():
    try:
        docs = get_documents("account", limit=50)
        out = []
        for d in docs:
            d = dict(d)
            if "_id" in d:
                d["id"] = str(d["_id"])  # expose as id
                del d["_id"]
            out.append(d)
        return {"items": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/accounts/connect")
async def connect_account(payload: ConnectAccountRequest):
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")
        platform = (payload.platform or "").lower()
        if platform not in ("youtube", "tiktok", "instagram"):
            raise HTTPException(status_code=400, detail="Invalid platform")

        # Upsert a connected account stub (demo)
        db["account"].update_one(
            {"platform": platform},
            {"$set": {"platform": platform, "account_name": payload.account_name or platform.title(), "connected": True}},
            upsert=True,
        )
        doc = db["account"].find_one({"platform": platform})
        out = dict(doc)
        out["id"] = str(out.pop("_id"))
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
