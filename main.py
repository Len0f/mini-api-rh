from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import json, os

app = FastAPI(title="Mini-API RH", version="1.0")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Mini-API RH", version="1.0")

# En dev: ouvrir largement (évite les 400 sur OPTIONS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # tu peux remettre une liste précise plus tard
    allow_credentials=False,    # False si allow_origins="*"
    allow_methods=["*"],        # accepte POST/GET/PUT/DELETE/OPTIONS...
    allow_headers=["*"],        # accepte "Content-Type", etc.
)

DATA_FILE = "employees.json"


class Employee(BaseModel):
    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=0, le=120)
    position: str = Field(..., min_length=1)
    is_full_time: bool = True

def load_data() -> List[Employee]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
        return [Employee(**e) for e in raw]

def save_data(employees: List[Employee]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([e.model_dump() for e in employees], f, ensure_ascii=False, indent=2)

@app.get("/employees", response_model=List[Employee])
def list_employees(position: Optional[str] = Query(None, description="Filtrer par poste exact")):
    emps = load_data()
    if position:
        emps = [e for e in emps if e.position.lower() == position.lower()]
    return emps

@app.post("/employees", response_model=Employee, status_code=201)
def add_employee(emp: Employee):
    emps = load_data()
    if any(e.name.lower() == emp.name.lower() for e in emps):
        raise HTTPException(409, detail="Un collaborateur avec ce nom existe déjà.")
    emps.append(emp)
    save_data(emps)
    return emp

@app.put("/employees/{name}", response_model=Employee)
def update_employee(name: str, payload: Employee):
    emps = load_data()
    for i, e in enumerate(emps):
        if e.name.lower() == name.lower():
            emps[i] = payload
            save_data(emps)
            return payload
    raise HTTPException(404, detail="Collaborateur introuvable.")

@app.delete("/employees/{name}", status_code=204)
def delete_employee(name: str):
    emps = load_data()
    for i, e in enumerate(emps):
        if e.name.lower() == name.lower():
            del emps[i]
            save_data(emps)
            return
    raise HTTPException(404, detail="Collaborateur introuvable.")

@app.get("/stats")
def stats():
    emps = load_data()
    total = len(emps)
    if total == 0:
        return {"total": 0, "full_time_pct": 0.0, "avg_age": None}
    full_time = sum(1 for e in emps if e.is_full_time)
    avg_age = round(sum(e.age for e in emps) / total, 2)
    return {
        "total": total,
        "full_time_pct": round(full_time / total * 100, 2),
        "avg_age": avg_age,
    }
