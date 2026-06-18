from sqlalchemy import Column, String, Integer, LargeBinary, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampedTenant


class ProgramaMateria(Base, TimestampedTenant):
    """Programa oficial de una materia por carrera y cohorte (HU-23).

    El archivo (PDF) se almacena en la base como contenido binario para
    mantener la trazabilidad multi-tenant sin depender de almacenamiento
    externo. El reemplazo es soft-delete + alta nueva (auditoría append-only).
    """
    __tablename__ = "programas_materia"

    materia_id = Column(UUID(as_uuid=True), ForeignKey("materias.id", ondelete="CASCADE"), nullable=False)
    carrera_id = Column(UUID(as_uuid=True), ForeignKey("carreras.id", ondelete="CASCADE"), nullable=False)
    cohorte_id = Column(UUID(as_uuid=True), ForeignKey("cohortes.id", ondelete="CASCADE"), nullable=False)

    titulo = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False, default="application/pdf")
    file_size = Column(Integer, nullable=False, default=0)
    contenido = Column(LargeBinary, nullable=False)

    materia = relationship("Materia")
    carrera = relationship("Carrera")
    cohorte = relationship("Cohorte")

    __table_args__ = (
        Index("idx_programa_tenant_materia", "tenant_id", "materia_id"),
    )

    def __repr__(self):
        return f"<ProgramaMateria(id={self.id!r}, titulo={self.titulo!r})>"
