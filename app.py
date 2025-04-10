from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Base, Personaje, Mision, MisionPersonaje
from database import get_db, crear_base_datos
from pydantic import BaseModel
from typing import List
from datetime import datetime

app = FastAPI()

crear_base_datos()

class PersonajeCreate(BaseModel):
    nombre: str

class MisionCreate(BaseModel):
    nombre: str
    descripcion: str = None
    experiencia: int = 0

class MisionResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str
    experiencia: int
    estado: str

class PersonajeResponse(BaseModel):
    id: int
    nombre: str
    experiencia: int
    misiones: List[MisionResponse] = []

@app.post("/personajes", response_model=PersonajeResponse)
def crear_personaje(personaje: PersonajeCreate, db: Session = Depends(get_db)):
    db_personaje = Personaje(nombre=personaje.nombre)
    db.add(db_personaje)
    db.commit()
    db.refresh(db_personaje)
    return db_personaje

@app.post("/misiones", response_model=MisionResponse)
def crear_mision(mision: MisionCreate, db: Session = Depends(get_db)):
    db_mision = Mision(
        nombre=mision.nombre,
        descripcion=mision.descripcion,
        experiencia=mision.experiencia,
        estado='pendiente'
    )
    db.add(db_mision)
    db.commit()
    db.refresh(db_mision)
    return db_mision

@app.post("/personajes/{personaje_id}/misiones/{mision_id}", response_model=PersonajeResponse)
def aceptar_mision(personaje_id: int, mision_id: int, db: Session = Depends(get_db)):

    personaje = db.query(Personaje).filter(Personaje.id == personaje_id).first()
    if not personaje:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    mision = db.query(Mision).filter(Mision.id == mision_id).first()
    if not mision:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    
    existe_relacion = db.query(MisionPersonaje).filter(
        MisionPersonaje.personaje_id == personaje_id,
        MisionPersonaje.mision_id == mision_id
    ).first()
    
    if existe_relacion:
        raise HTTPException(
            status_code=400,
            detail="El personaje ya tiene asignada esta misión"
        )
    max_orden = db.query(func.max(MisionPersonaje.orden)).filter(
        MisionPersonaje.personaje_id == personaje_id
    ).scalar() or 0
    
    nueva_mision_personaje = MisionPersonaje(
        personaje_id=personaje_id,
        mision_id=mision_id,
        orden=max_orden + 1
    )
    
    db.add(nueva_mision_personaje)
    db.commit()
    
    db.refresh(personaje)
    return personaje

@app.post("/personajes/{personaje_id}/completar", response_model=PersonajeResponse)
def completar_mision(personaje_id: int, db: Session = Depends(get_db)):

    personaje = db.query(Personaje).filter(Personaje.id == personaje_id).first()
    if not personaje:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    mision_personaje = db.query(MisionPersonaje).filter(
        MisionPersonaje.personaje_id == personaje_id
    ).order_by(MisionPersonaje.orden.asc()).first()
    
    if not mision_personaje:
        raise HTTPException(status_code=404, detail="No hay misiones pendientes")
    
    mision = db.query(Mision).filter(Mision.id == mision_personaje.mision_id).first()
    
    mision.estado = 'completada'
    
    personaje.experiencia += mision.experiencia
    
    db.delete(mision_personaje)
    
    misiones_restantes = db.query(MisionPersonaje).filter(
        MisionPersonaje.personaje_id == personaje_id,
        MisionPersonaje.orden > mision_personaje.orden
    ).all()
    
    for mp in misiones_restantes:
        mp.orden -= 1
    
    db.commit()
    db.refresh(personaje)
    return personaje

@app.get("/personajes/{personaje_id}/misiones", response_model=List[MisionResponse])
def listar_misiones(personaje_id: int, db: Session = Depends(get_db)):

    personaje = db.query(Personaje).filter(Personaje.id == personaje_id).first()
    if not personaje:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    misiones = db.query(Mision).join(MisionPersonaje).filter(
        MisionPersonaje.personaje_id == personaje_id
    ).order_by(MisionPersonaje.orden.asc()).all()
    
    return misiones