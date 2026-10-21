import sqlite3
import hashlib
from datetime import datetime, timedelta
import pandas as pd

DB_NAME = 'alejandrino.db'

def encriptar_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def _asegurar_columna(cursor, tabla: str, columna: str, definicion: str):
    try:
        cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")
    except sqlite3.OperationalError:
        pass

def obtener_catalogo_real():
    """Catálogo de 45 libros depurados para garantizar portadas reales."""
    raw_books = [
        # LITERATURA
        ("9780307474728", "Cien años de soledad", "Gabriel García Márquez", "Vintage", "Literatura", 1967, 68000.0, 18),
        ("9780307387264", "El amor en los tiempos del cólera", "Gabriel García Márquez", "Vintage", "Literatura", 1985, 62000.0, 14),
        ("9781400034956", "Crónica de una muerte anunciada", "Gabriel García Márquez", "Vintage", "Literatura", 1981, 45000.0, 20),
        ("9780143126393", "La sombra del viento", "Carlos Ruiz Zafón", "Penguin", "Literatura", 2001, 71000.0, 20),
        ("9780802130303", "Ficciones", "Jorge Luis Borges", "Grove Press", "Literatura", 1944, 54000.0, 15),
        ("9780571260840", "La ciudad y los perros", "Mario Vargas Llosa", "Faber", "Literatura", 1963, 66000.0, 10),

        # CLÁSICOS UNIVERSALES
        ("9780451524935", "1984", "George Orwell", "Signet Classics", "Clásicos", 1949, 49000.0, 25),
        ("9780060850524", "Un mundo feliz", "Aldous Huxley", "Harper", "Clásicos", 1932, 52000.0, 16),
        ("9780141439518", "Orgullo y prejuicio", "Jane Austen", "Penguin", "Clásicos", 1813, 56000.0, 14),
        ("9780140449136", "Crimen y castigo", "Fiódor Dostoievski", "Penguin", "Clásicos", 1866, 74000.0, 9),
        ("9780553213690", "La metamorfosis", "Franz Kafka", "Bantam", "Clásicos", 1915, 38000.0, 21),
        ("9780743273565", "El gran Gatsby", "F. Scott Fitzgerald", "Scribner", "Clásicos", 1925, 47000.0, 12),
        ("9780140449266", "El conde de Montecristo", "Alejandro Dumas", "Penguin", "Clásicos", 1844, 89000.0, 7),
        ("9780141439556", "Cumbres borrascosas", "Emily Brontë", "Penguin", "Clásicos", 1847, 53000.0, 11),
        ("9780140449181", "Los miserables", "Victor Hugo", "Penguin", "Clásicos", 1862, 92000.0, 5),
        ("9780140268867", "La Odisea", "Homero", "Gredos", "Clásicos", 1800, 62000.0, 10),
        ("9780684801223", "El viejo y el mar", "Ernest Hemingway", "Planeta", "Clásicos", 1952, 43000.0, 15),
        ("9780679720201", "El extranjero", "Albert Camus", "Alianza", "Clásicos", 1942, 45000.0, 12),

        # CIENCIA FICCIÓN Y FANTASÍA
        ("9780547928227", "El Hobbit", "J.R.R. Tolkien", "Mariner", "Fantasía", 1937, 69000.0, 16),
        ("9780547928210", "El Señor de los Anillos", "J.R.R. Tolkien", "Mariner", "Fantasía", 1954, 82000.0, 11),
        ("9780441172719", "Dune", "Frank Herbert", "Ace", "Fantasía", 1965, 78000.0, 14),
        ("9780553293357", "Fundación", "Isaac Asimov", "Bantam", "Fantasía", 1951, 59000.0, 13),
        ("9781451673319", "Fahrenheit 451", "Ray Bradbury", "Simon", "Fantasía", 1953, 51000.0, 19),
        ("9780553103540", "Juego de tronos", "George R.R. Martin", "Bantam", "Fantasía", 1996, 84000.0, 9),
        ("9780590353427", "Harry Potter y la piedra", "J.K. Rowling", "Scholastic", "Fantasía", 1997, 63000.0, 24),
        ("9780439064873", "Harry Potter y la cámara", "J.K. Rowling", "Scholastic", "Fantasía", 1998, 63000.0, 18),
        ("9780439136365", "Harry Potter y el prisionero", "J.K. Rowling", "Scholastic", "Fantasía", 1999, 65000.0, 15),
        ("9780345404473", "Ovejas eléctricas", "Philip K. Dick", "Del Rey", "Fantasía", 1968, 56000.0, 7),
        ("9780553418026", "El marciano", "Andy Weir", "Crown", "Fantasía", 2011, 61000.0, 12),
        ("9780439023481", "Los juegos del hambre", "Suzanne Collins", "Scholastic", "Fantasía", 2008, 57000.0, 17),

        # MISTERIO Y THRILLER
        ("9780307474278", "El código Da Vinci", "Dan Brown", "Vintage", "Misterio", 2003, 64000.0, 14),
        ("9780307743657", "El resplandor", "Stephen King", "Anchor", "Misterio", 1977, 73000.0, 13),
        ("9781501142970", "It (Eso)", "Stephen King", "Scribner", "Misterio", 1986, 88000.0, 8),
        ("9780062073488", "Diez negritos", "Agatha Christie", "Planeta", "Misterio", 1939, 49000.0, 16),
        ("9780062073501", "Asesinato en el Orient Express", "Agatha Christie", "Planeta", "Misterio", 1934, 49000.0, 15),
        ("9780156001311", "El nombre de la rosa", "Umberto Eco", "Mariner", "Misterio", 1980, 75000.0, 9),
        ("9781594634024", "La chica del tren", "Paula Hawkins", "Riverhead", "Misterio", 2015, 58000.0, 10),
        ("9780345803481", "Perdida", "Gillian Flynn", "Crown", "Misterio", 2012, 60000.0, 8),
        ("9780312924584", "El silencio de los corderos", "Thomas Harris", "St. Martin's", "Misterio", 1988, 59000.0, 7),

        # DESARROLLO, NEGOCIOS Y TECNOLOGÍA
        ("9780735211292", "Hábitos atómicos", "James Clear", "Avery", "Desarrollo", 2018, 69000.0, 30),
        ("9780062316097", "Sapiens", "Yuval Noah Harari", "Harper", "Desarrollo", 2011, 76000.0, 25),
        ("9780807014295", "El hombre en busca de sentido", "Viktor Frankl", "Herder", "Desarrollo", 1946, 48000.0, 22),
        ("9781612680194", "Padre rico, padre pobre", "Robert T. Kiyosaki", "Aguilar", "Desarrollo", 1997, 58000.0, 24),
        ("9780132350884", "Clean Code", "Robert C. Martin", "Prentice Hall", "Tecnología", 2008, 125000.0, 14),
        ("9780135957059", "The Pragmatic Programmer", "Andrew Hunt", "Addison", "Tecnología", 2019, 132000.0, 8),
    ]

    catalogo_final = []
    for isbn, titulo, autor, editorial, categoria, anio, precio, stock in raw_books:
        portada_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
        catalogo_final.append((isbn, titulo, autor, editorial, categoria, anio, precio, stock, 5, portada_url, 1))
    
    return catalogo_final

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS empleados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, cedula TEXT UNIQUE NOT NULL, nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL, telefono TEXT, correo TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
                    rol TEXT NOT NULL, activo INTEGER DEFAULT 1)''')
    _asegurar_columna(c, "empleados", "telefono", "TEXT DEFAULT ''")

    c.execute('''CREATE TABLE IF NOT EXISTS editoriales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, nit TEXT UNIQUE NOT NULL, razonSocial TEXT NOT NULL,
                    contacto TEXT, telefono TEXT, direccion TEXT, correo TEXT, activo INTEGER DEFAULT 1)''')
    _asegurar_columna(c, "editoriales", "direccion", "TEXT DEFAULT 'Bogotá, Colombia'")

    # ¡ESTO BORRA LA TABLA DE LIBROS FEOS PARA FORZAR EL REINICIO!
    c.execute("DROP TABLE IF EXISTS libros")
    
    c.execute('''CREATE TABLE libros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, isbn TEXT UNIQUE NOT NULL, titulo TEXT NOT NULL,
                    autor TEXT NOT NULL, editorial TEXT NOT NULL, categoria TEXT NOT NULL,
                    anioPublicacion INTEGER DEFAULT 2020, precioVenta REAL DEFAULT 0.0,
                    stockDisponible INTEGER DEFAULT 0, stockMinimo INTEGER DEFAULT 5,
                    portada TEXT, activo INTEGER DEFAULT 1)''')

    c.execute('''CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, cedula TEXT UNIQUE NOT NULL, nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL, telefono TEXT, correo TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
                    direccion TEXT, activo INTEGER DEFAULT 1)''')
    _asegurar_columna(c, "clientes", "activo", "INTEGER DEFAULT 1")

    c.execute('''CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, empleado_id INTEGER,
                    fechaHora TEXT NOT NULL, subtotal REAL NOT NULL, descuento REAL DEFAULT 0.0,
                    iva REAL NOT NULL, total REAL NOT NULL, estado TEXT DEFAULT 'Pagada')''')
    _asegurar_columna(c, "ventas", "descuento", "REAL DEFAULT 0.0")

    c.execute('''CREATE TABLE IF NOT EXISTS detalle_ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER NOT NULL, isbn TEXT NOT NULL,
                    titulo TEXT NOT NULL, cantidad INTEGER NOT NULL, precioUnitario REAL NOT NULL, subtotalLinea REAL NOT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS facturas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, numeroFactura TEXT UNIQUE NOT NULL, venta_id INTEGER NOT NULL,
                    cliente_cedula TEXT, cliente_nombre TEXT, fechaEmision TEXT NOT NULL, subtotal REAL NOT NULL,
                    descuento REAL DEFAULT 0.0, iva19 REAL NOT NULL, totalPagar REAL NOT NULL,
                    medioPago TEXT DEFAULT 'Efectivo', montoRecibido REAL DEFAULT 0.0,
                    estado TEXT DEFAULT 'Pagada', motivoAnulacion TEXT, notaCredito TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS prestamos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, idPrestamo TEXT UNIQUE NOT NULL, cliente_id INTEGER NOT NULL,
                    cedula_cliente TEXT NOT NULL, nombre_cliente TEXT NOT NULL, isbn TEXT NOT NULL,
                    titulo_libro TEXT NOT NULL, empleado_id INTEGER, fechaSalida TEXT NOT NULL,
                    fechaLimite TEXT NOT NULL, fechaDevolucion TEXT, estadoEjemplar TEXT DEFAULT 'Bueno',
                    estado TEXT DEFAULT 'Activo', multa REAL DEFAULT 0.0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS entradas_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, isbn TEXT NOT NULL, titulo TEXT NOT NULL,
                    cantidad INTEGER NOT NULL, costoUnitario REAL NOT NULL, numeroFacturaProveedor TEXT NOT NULL,
                    fechaHora TEXT NOT NULL, empleado_nombre TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_nombre TEXT NOT NULL, rol TEXT NOT NULL,
                    modulo TEXT NOT NULL, accion TEXT NOT NULL, detalle TEXT NOT NULL, fechaHora TEXT NOT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS suscriptores_newsletter (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, correo TEXT UNIQUE NOT NULL,
                    cupon_generado TEXT NOT NULL, fechaHora TEXT NOT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS carrito_persistente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, isbn TEXT, titulo TEXT, autor TEXT,
                    editorial TEXT, categoria TEXT, precioVenta REAL, portada TEXT)''')

    conn.commit()

    usuarios_base = [
        ("10000001", "Estefania", "Lopez", "3100000001", "admin@alejandrino.com", encriptar_password("admin123"), "Administrador", 1),
        ("10000002", "Diana", "Estupiñan", "3100000002", "vendedor@alejandrino.com", encriptar_password("vendedor123"), "Vendedor", 1),
        ("10000003", "Carlos", "Mendoza", "3100000003", "bibliotecario@alejandrino.com", encriptar_password("biblio123"), "Bibliotecario", 1),
        ("10000004", "Pedro", "Alarcón", "3100000004", "almacenista@alejandrino.com", encriptar_password("almacen123"), "Almacenista", 1)
    ]
    for ced, nom, ape, tel, cor, pwd, rol, act in usuarios_base:
        c.execute("INSERT OR IGNORE INTO empleados (cedula, nombres, apellidos, telefono, correo, password, rol, activo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (ced, nom, ape, tel, cor, pwd, rol, act))

    editoriales_base = [
        ("900123456-1", "Editorial Planeta Colombia", "Carlos Gómez", "3101234567", "Calle 73 # 7-60, Bogotá", "contacto@planeta.com.co"),
        ("900987654-3", "Penguin Random House", "Ana María Ruiz", "3209876543", "Carrera 11 # 79-35, Bogotá", "info@penguinrandomhouse.com"),
        ("800456789-0", "Fondo de Cultura Económica", "Luis Herrera", "3154443322", "Calle 11 # 5-60, Bogotá", "ventas@fce.com.co")
    ]
    for nit, raz, con, tel, dir_e, cor_e in editoriales_base:
        c.execute("INSERT OR IGNORE INTO editoriales (nit, razonSocial, contacto, telefono, direccion, correo, activo) VALUES (?, ?, ?, ?, ?, ?, 1)",
                  (nit, raz, con, tel, dir_e, cor_e))

    for libro in obtener_catalogo_real():
        c.execute("""
            INSERT INTO libros (isbn, titulo, autor, editorial, categoria, anioPublicacion, precioVenta, stockDisponible, stockMinimo, portada, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, libro)

    pwd_cli = encriptar_password("cliente123")
    clientes_base = [("1052345678", "Javier", "Rodríguez", "3159876543", "cliente@correo.com", pwd_cli, "Calle 16 # 14-22, Duitama")]
    for ced, nom, ape, tel, cor, pwd, dir_c in clientes_base:
        c.execute("INSERT OR IGNORE INTO clientes (cedula, nombres, apellidos, telefono, correo, password, direccion, activo) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
                  (ced, nom, ape, tel, cor, pwd, dir_c))

    conn.commit()
    return conn

def registrar_auditoria(conn, usuario_nombre: str, rol: str, modulo: str, accion: str, detalle: str):
    c = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO auditoria (usuario_nombre, rol, modulo, accion, detalle, fechaHora)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (usuario_nombre, rol, modulo, accion, detalle, fecha_actual))
    conn.commit()

# Sin bloqueo de caché para que cargue los datos frescos
def obtener_libros_activos(conn):
    return pd.read_sql_query("SELECT * FROM libros WHERE activo = 1", conn)