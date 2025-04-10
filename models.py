from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Mision(Base):
    """
    Representa una misión dentro del juego.
    """
    __tablename__ = 'misiones'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False)
    descripcion = Column(Text, nullable=True)
    experiencia = Column(Integer, default=0)
    estado = Column(Enum('pendiente', 'completada', name='estados'), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.now)

    # Relación con MisionPersonaje
    personajes = relationship("MisionPersonaje", back_populates="mision")

class Personaje(Base):
    """
    Representa un personaje dentro del juego.
    """
    __tablename__ = 'personajes'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(30), nullable=False)
    experiencia = Column(Integer, default=0)
    misiones = relationship("MisionPersonaje", back_populates="personaje")

class MisionPersonaje(Base):
    """
    Tabla intermedia para la relación muchos a muchos entre Personaje y Mision.
    También permite manejar el orden FIFO de las misiones.
    """
    __tablename__ = 'misiones_personaje'
    
    personaje_id = Column(Integer, ForeignKey('personajes.id'), primary_key=True)
    mision_id = Column(Integer, ForeignKey('misiones.id'), primary_key=True)
    orden = Column(Integer)  # Para mantener el orden FIFO de las misiones

    # Relaciones inversas
    personaje = relationship("Personaje", back_populates="misiones")
    mision = relationship("Mision", back_populates="personajes")