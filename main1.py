from fastapi import FastAPI, Path, HTTPException, Query # pyright: ignore[reportMissingImports]
from pydantic import BaseModel, Field, computed_field # pyright: ignore[reportMissingImports]
from typing import Annotated, Optional, Dict, Any
import os
import json

app = FastAPI()

class Patient(BaseModel):
    id: Annotated[str, Field(..., description="ID of the patient", example="p001")]
    name: Annotated[str, Field(..., description="Name of the patient")]
    city: Annotated[str, Field(..., description="Where the patient lives")]
    age: Annotated[int, Field(..., gt=0, lt=100, description="Age of the patient")]
    height: Annotated[float, Field(..., gt=0, description="Height of the patient")]
    weight: Annotated[float, Field(..., gt=0, description="Weight of the patient")]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 24.9:
            return "Normal weight"
        elif 25 <= self.bmi < 29.9:
            return "Overweight"
        else:
            return "Obesity"

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    age: Optional[int] = Field(default=None, gt=0)
    height: Optional[float] = Field(default=None, gt=0)
    weight: Optional[float] = Field(default=None, gt=0)

def load_data():
    file_path = os.path.join(os.path.dirname(__file__), "data.json")
    with open(file_path, "r") as f:
        return json.load(f)

def save_data(data):
    file_path = os.path.join(os.path.dirname(__file__), "data.json")
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

@app.get('/')
def hello():
    return {"message": "This is the patient management system"}

@app.get('/about')
def about():
    return {
        "name": "Patient Management System",
        "version": "1.0.0",
        "description": "A simple API for managing patient records"
    }

@app.get('/view')
def view():
    data = load_data()
    return {"patients": data}

@app.get('/patient/{patient_id}')
def view_patient(
    patient_id: str = Path(..., title="Patient ID", description="The ID of the patient to view")
):
    data = load_data()
    if patient_id in data:
        return {"patient": data[patient_id]}
    raise HTTPException(status_code=404, detail="Patient not found")

@app.get('/sort')
def sort_patients(
    sort_by: str = Query(..., title="Sort By", description="Sort patients by name or age"),
    order: str = Query("asc", title="Order", description="Sort order, either 'asc' or 'desc'")
):
    data = load_data()
    if sort_by not in ["name", "age"]:
        raise HTTPException(status_code=400, detail="Invalid sort parameter")

    sorted_patients = sorted(data.items(), key=lambda x: x[1].get(sort_by))
    if order == "desc":
        sorted_patients.reverse()

    return {"sorted_patients": dict(sorted_patients)}

@app.post('/create')
def create_patient(patient: Patient):
    data = load_data()
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient with this ID already exists")
    data[patient.id] = patient.model_dump(exclude=["id"])
    save_data(data)
    return {"message": "Patient created successfully", "patient": patient}

@app.put('/update/{patient_id}')
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = load_data()
    
   # Incorrect condition (was `if patient.id is not data`)
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")

    existing_patient_info = data[patient_id]
    update_data = patient_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        existing_patient_info[key] = value  #  update if provided

    # Construct updated Patient object to validate
    updated_patient = Patient(id=patient_id, **existing_patient_info)

    # Save updated patient
    data[patient_id] = updated_patient.model_dump(exclude=["id"])
    save_data(data)
    return {"message": "Patient updated successfully", "patient": updated_patient}
@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):
    data = load_data()
    if patient_id in data:
        del data[patient_id]
        save_data(data)
        return {"message": "Patient deleted successfully"}
    raise HTTPException(status_code=404, detail="Patient not found")
