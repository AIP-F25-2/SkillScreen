from fastapi import FastAPI

app = FastAPI(title="Coding Service")

@app.get("/problems")
def get_problems():
    return {"problems": ["FizzBuzz", "Reverse String", "Palindrome Checker"]}

@app.post("/submit")
def submit_solution(solution: dict):
    return {"status": "submitted", "solution": solution}
