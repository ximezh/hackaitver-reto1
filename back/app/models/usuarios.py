"""Usuarios con su rol, canal y vínculo a sucursal o proveedor (BE-02)."""

import re

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.catalogos import Proveedor, Sucursal
from app.models.comun import CANAL_DE_ROL, PREFIJO_DE_ROL, ConFechas, Estado, Rol, en_lista

_CANAL_SEGUN_ROL = " OR ".join(
    f"(rol = '{rol.value}' AND canal = '{canal.value}')" for rol, canal in CANAL_DE_ROL.items()
)
# Expresiones regulares en lugar de LIKE: `%` choca con el estilo de parámetros del driver.
_PREFIJOS = "|".join(re.escape(p) for p in PREFIJO_DE_ROL.values())
_PREFIJO_SEGUN_ROL = " OR ".join(
    [
        *(
            f"(rol = '{rol.value}' AND usuario ~ '^{re.escape(prefijo)}')"
            for rol, prefijo in PREFIJO_DE_ROL.items()
        ),
        # Los roles web no pueden usar los prefijos de Android.
        f"(rol NOT IN ({', '.join(repr(r.value) for r in PREFIJO_DE_ROL)}) "
        f"AND usuario !~ '^({_PREFIJOS})')",
    ]
)


class Usuario(ConFechas, Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint("usuario ~ '^[a-z0-9][a-z0-9._-]{2,39}$'", name="usuario_formato"),
        en_lista("rol", Rol, "rol"),
        CheckConstraint(_CANAL_SEGUN_ROL, name="canal_de_rol"),
        CheckConstraint(_PREFIJO_SEGUN_ROL, name="prefijo_de_rol"),
        CheckConstraint(
            "(rol = 'sucursal') = (sucursal_id IS NOT NULL)", name="sucursal_solo_de_rol_sucursal"
        ),
        CheckConstraint(
            "(rol = 'proveedor') = (proveedor_id IS NOT NULL)",
            name="proveedor_solo_de_rol_proveedor",
        ),
        en_lista("estado", Estado, "estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario: Mapped[str] = mapped_column(String(40), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    rol: Mapped[str] = mapped_column(String(12))
    canal: Mapped[str] = mapped_column(String(8))
    # Hash Argon2 (A-09). Nunca se guarda ni se devuelve la contraseña en claro.
    contrasena_hash: Mapped[str] = mapped_column(String(255))
    # `True` hasta que el usuario cambia la contraseña que le generó Oficina (R-17).
    contrasena_temporal: Mapped[bool] = mapped_column(default=True)
    estado: Mapped[str] = mapped_column(String(10), default=Estado.ACTIVO)
    sucursal_id: Mapped[int | None] = mapped_column(ForeignKey("sucursales.id"), index=True)
    proveedor_id: Mapped[int | None] = mapped_column(ForeignKey("proveedores.id"), index=True)

    sucursal: Mapped[Sucursal | None] = relationship()
    proveedor: Mapped[Proveedor | None] = relationship()
