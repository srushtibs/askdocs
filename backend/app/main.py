from fastapi import FastAPI

app = FastAPI(title="AskDocs")

@app.get("/health")
def health():
    return {"status": "ok"}
