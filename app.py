from flask import Flask, jsonify, request
from config import Config
from models import db, Busqueda, LibroGuardado
from openlibrary_service import buscar, consultar_isbn, OpenLibraryError
 
app = Flask(__name__)
app.config.from_object(Config)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///biblioteca.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
 
@app.errorhandler(OpenLibraryError)
def error_externo(error):
    return jsonify({"error": str(error)}), 502
 
@app.get("/salud")
def salud():
    return jsonify({"estado": "activo"}), 200
 
def registrar(criterio, termino):
    db.session.add(Busqueda(criterio=criterio, termino=termino))
    db.session.commit()
 
@app.get("/libros/buscar")
def buscar_titulo():
    titulo = (request.args.get("titulo") or "").strip()
    if len(titulo) < 2:
        return jsonify({"error": "titulo debe tener al menos 2 caracteres"}), 400
    resultados = buscar("title", titulo)
    registrar("titulo", titulo)
    return jsonify({"consulta": titulo, "total": len(resultados),
                    "resultados": resultados}), 200
 
@app.get("/libros/autor")
def buscar_autor():
    nombre = (request.args.get("nombre") or "").strip()
    if len(nombre) < 2:
        return jsonify({"error": "nombre debe tener al menos 2 caracteres"}), 400
    resultados = buscar("author", nombre)
    registrar("autor", nombre)
    return jsonify({"consulta": nombre, "total": len(resultados),
                    "resultados": resultados}), 200
 
@app.get("/libros/isbn/<isbn>")
def libro_por_isbn(isbn):
    if not (isbn.isdigit() and len(isbn) in (10, 13)):
        return jsonify({"error": "ISBN debe contener 10 o 13 dígitos"}), 400
    try:
        libro = consultar_isbn(isbn)
    except OpenLibraryError:
        return jsonify({"error": "No fue posible obtener el ISBN"}), 502
    registrar("isbn", isbn)
    return jsonify({"isbn": isbn, "titulo": libro.get("title"),
                    "fecha_publicacion": libro.get("publish_date"),
                    "editoriales": libro.get("publishers", [])}), 200
 
@app.get("/historial")
def listar_historial():
    registros = Busqueda.query.order_by(Busqueda.id.desc()).limit(50).all()
    return jsonify([{"id": r.id, "criterio": r.criterio,
                     "termino": r.termino, "fecha": r.fecha.isoformat()}
                    for r in registros]), 200

@app.get("/historial/<int:id>")
def buscar_historial_por_id(id):
    registro = db.session.get(Busqueda, id)

    if registro is None:
        return jsonify({"error": "El registro del historial no existe"}), 404

    return jsonify({
        "id": registro.id,
        "criterio": registro.criterio,
        "termino": registro.termino,
        "fecha": registro.fecha.isoformat()
    }), 200

@app.post("/biblioteca")
def crear_libro():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "Envía un objeto JSON válido"}), 400
 
    titulo = datos.get("titulo")
    autor = datos.get("autor")
    isbn = datos.get("isbn")
    anio = datos.get("anio")
 
    if not all(isinstance(v, str) and v.strip()
               for v in (titulo, autor, isbn)):
        return jsonify({"error": "titulo, autor e isbn son obligatorios"}), 400
 
    titulo, autor, isbn = titulo.strip(), autor.strip(), isbn.strip()
    if len(titulo) > 250 or len(autor) > 200:
        return jsonify({"error": "Título o autor demasiado largo"}), 400
    if not (isbn.isdigit() and len(isbn) in (10, 13)):
        return jsonify({"error": "ISBN debe tener 10 o 13 dígitos"}), 400
    if anio is not None and (type(anio) is not int or not 0 < anio <= 2100):
        return jsonify({"error": "anio debe ser un entero válido"}), 400
 
    if LibroGuardado.query.filter_by(isbn=isbn).first():
        return jsonify({"error": "El ISBN ya está guardado"}), 409
 
    libro = LibroGuardado(titulo=titulo, autor=autor, isbn=isbn, anio=anio)
    db.session.add(libro)
    db.session.commit()
    return jsonify({"mensaje": "Libro guardado", "id": libro.id}), 201


@app.get("/biblioteca")
def listar_biblioteca():
    libros = LibroGuardado.query.order_by(LibroGuardado.id.desc()).all()
    return jsonify([{
        "id": libro.id,
        "titulo": libro.titulo,
        "autor": libro.autor,
        "isbn": libro.isbn,
        "anio": libro.anio
    } for libro in libros]), 200



@app.delete("/biblioteca/<int:id>")
def eliminar_libro(id):
    libro = db.session.get(LibroGuardado, id)
    if libro is None:
        return jsonify({"error": "Libro no encontrado"}), 404
 
    db.session.delete(libro)
    db.session.commit()
    return jsonify({"mensaje": "Libro eliminado", "id": id}), 200


# ------------------------------------------
# ELIMINAR UN REGISTRO DEL HISTORIAL
# ------------------------------------------

@app.route("/historial/<int:id>", methods=["DELETE"])
def eliminar_historial(id):

    # Buscar el registro en la base de datos
    registro = db.session.get(Busqueda, id)

    # Verificar si el registro existe
    if registro is None:
        return jsonify({
            "error": "El registro del historial no existe"
        }), 404

    # Eliminar el registro encontrado
    db.session.delete(registro)

    # Confirmar los cambios en la base de datos
    db.session.commit()

    # Devolver respuesta al cliente
    return jsonify({
        "mensaje": "Registro del historial eliminado correctamente",
        "id_eliminado": id
    }), 200



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
