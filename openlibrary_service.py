import requests
from flask import current_app
 
BASE_URL = "https://openlibrary.org"
 
class OpenLibraryError(Exception):
    pass
 
def solicitar(ruta, parametros=None):
    contacto = current_app.config["OPENLIBRARY_CONTACT"]
    headers = {"User-Agent": f"BibliotecaTaller/1.0 ({contacto})"}
    try:
        respuesta = requests.get(
            BASE_URL + ruta, params=parametros,
            headers=headers, timeout=12
        )
        respuesta.raise_for_status()
        return respuesta.json()
    except (requests.RequestException, ValueError) as exc:
        raise OpenLibraryError("No fue posible consultar Open Library") from exc
 
def normalizar(libro):
    autores = libro.get("author_name") or []
    isbns = libro.get("isbn") or []
    return {
        "clave": libro.get("key"),
        "titulo": libro.get("title"),
        "autor": autores[0] if autores else "Desconocido",
        "anio": libro.get("first_publish_year"),
        "isbn": isbns[0] if isbns else None
    }
 
def buscar(campo, valor):
    datos = solicitar("/search.json", {campo: valor, "limit": 10})
    return [normalizar(item) for item in datos.get("docs", [])]
 
def consultar_isbn(isbn):
    return solicitar(f"/isbn/{isbn}.json")
