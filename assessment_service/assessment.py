from fastapi import FastAPI

app = FastAPI(title="Assessment Service")

questions = ["What is Python?", "Explain microservices.", "What is JWT?"]

@app.get("/questions")
def get_questions():
    return {"questions": questions}

@app.post("/submit")
def submit_assessment(answer: dict):
    return {"status": "submitted", "answer": answer}
