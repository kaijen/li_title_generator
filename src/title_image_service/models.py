import re

from pydantic import BaseModel, field_validator


class ImageRequest(BaseModel):
    titel:       str = ""
    text:        str = ""
    vordergrund: str = "white"
    hintergrund: str = "black"
    breite:      int = 1024
    font:        str = "Rubik Glitch"
    titelzeilen: int = 1
    dateiname:   str = ""  # Leer → linkedin_title_<YYYY-MM-DD-HH-mm>.png

    @field_validator("dateiname")
    @classmethod
    def validate_dateiname(cls, v: str) -> str:
        v = v.strip()
        if v and not re.fullmatch(r"[A-Za-z0-9._\-]{1,128}", v):
            raise ValueError(
                "dateiname darf nur alphanumerische Zeichen, Punkte, "
                "Bindestriche und Unterstriche enthalten (max. 128 Zeichen)."
            )
        return v
