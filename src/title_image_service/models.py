from pydantic import BaseModel


class ImageRequest(BaseModel):
    titel:       str = ""
    text:        str = ""
    vordergrund: str = "white"
    hintergrund: str = "black"
    breite:      int = 1024
    font:        str = "Rubik Glitch"
    titelzeilen: int = 1
    dateiname:   str = ""  # Leer → linkedin_title_<YYYY-MM-DD-HH-mm>.png
