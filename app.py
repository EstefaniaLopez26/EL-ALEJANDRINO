import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. Configuración de página
st.set_page_config(page_title="El Alejandrino | Gestión Financiera", page_icon="📚", layout="wide")

# 2. Función para cargar estilos CSS externos
def cargar_css(ruta_css):
    try:
        with open(ruta_css, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

cargar_css("assets/style.css")

# 3. Motor de Base de Datos SQLite (Ampliado con tabla de ingresos)
def init_db():
    conn = sqlite3.connect('alejandrino.db', check_same_thread=False)
    c = conn.cursor()
    # Tabla de libros
    c.execute('''CREATE TABLE IF NOT EXISTS libros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    autor TEXT NOT NULL,
                    isbn TEXT UNIQUE,
                    precio REAL DEFAULT 0.0,
                    stock INTEGER DEFAULT 0)''')
    # Tabla de préstamos
    c.execute('''CREATE TABLE IF NOT EXISTS prestamos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    libro_id INTEGER,
                    cliente TEXT NOT NULL,
                    fecha_prestamo TEXT NOT NULL,
                    estado TEXT DEFAULT 'Activo',
                    FOREIGN KEY (libro_id) REFERENCES libros (id))''')
    # Nueva tabla de ingresos / transacciones financieras
    c.execute('''CREATE TABLE IF NOT EXISTS ingresos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concepto TEXT NOT NULL,
                    monto REAL NOT NULL,
                    fecha TEXT NOT NULL)''')
    conn.commit()
    return conn

conn = init_db()

# Funciones de lógica de datos
def obtener_libros():
    return pd.read_sql_query("SELECT id, titulo, autor, isbn, precio, stock FROM libros", conn)

def obtener_prestamos_activos():
    query = """
    SELECT p.id, l.titulo, p.cliente, p.fecha_prestamo 
    FROM prestamos p 
    JOIN libros l ON p.libro_id = l.id 
    WHERE p.estado = 'Activo'
    """
    return pd.read_sql_query(query, conn)

def obtener_ingresos():
    return pd.read_sql_query("SELECT id, concepto, monto, fecha FROM ingresos", conn)

# 4. Navegación Lateral (Sidebar)
with st.sidebar:
    st.markdown("### 🏛️ El Alejandrino")
    st.caption("Panel de Gestión Bibliotecaria")
    st.markdown("---")
    menu = st.radio("Menú Principal", ["🏠 Inicio", "📖 Catálogo e Inventario", "🔄 Préstamos", "💰 Finanzas e Ingresos"])
    st.markdown("---")
    st.markdown("<p style='color: #8C7A6B; font-size: 0.85rem;'>Versión 2.2 - Módulo Financiero</p>", unsafe_allow_html=True)

# 5. Vistas de la Aplicación
if menu == "🏠 Inicio":
    st.markdown("<h1 class='titulo-principal'>Librería El Alejandrino</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitulo'>Plataforma inteligente para la administración de inventarios, préstamos e ingresos</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    df_ingresos = obtener_ingresos()
    total_ingresos = df_ingresos['monto'].sum() if not df_ingresos.empty else 0.0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div class='tarjeta-info'>
                <h3 style='color: #5C4033; margin-top: 0;'>💰 Ingresos Totales</h3>
                <h2 style='color: #2C2A29; margin: 5px 0;'>$ {total_ingresos:,.2f}</h2>
                <p style='color: #665C54;'>Flujo de caja registrado en el sistema.</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class='tarjeta-info'>
                <h3 style='color: #5C4033; margin-top: 0;'>🔄 Flujo de Préstamos</h3>
                <p style='color: #665C54;'>Gestión dinámica de salidas y control de devoluciones automatizadas.</p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div class='tarjeta-info'>
                <h3 style='color: #5C4033; margin-top: 0;'>⚡ Núcleo Portátil</h3>
                <p style='color: #665C54;'>Base de datos local en SQLite sin bloqueos de servidor externos.</p>
            </div>
        """, unsafe_allow_html=True)

elif menu == "📖 Catálogo e Inventario":
    st.header("📖 Administración de Catálogo y Precios")
    st.markdown("---")
    
    with st.expander("➕ Registrar Nuevo Libro en el Sistema", expanded=False):
        with st.form("form_nuevo_libro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            titulo = col1.text_input("Título del libro")
            autor = col2.text_input("Autor")
            isbn = col1.text_input("ISBN (Código único)")
            precio = col1.number_input("Precio unitario ($)", min_value=0.0, value=0.0, step=1000.0)
            stock = col2.number_input("Cantidad inicial en stock", min_value=1, value=1)
            
            if st.form_submit_button("Guardar en el Sistema"):
                if titulo and autor and isbn:
                    try:
                        c = conn.cursor()
                        c.execute("INSERT INTO libros (titulo, autor, isbn, precio, stock) VALUES (?, ?, ?, ?, ?)", 
                                  (titulo, autor, isbn, precio, stock))
                        conn.commit()
                        st.success("¡Libro registrado con éxito!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Error: Este código ISBN ya se encuentra registrado.")
                else:
                    st.warning("Por favor completa los campos obligatorios.")
                    
    st.markdown("### 📊 Inventario Actual")
    df_libros = obtener_libros()
    if not df_libros.empty:
        st.dataframe(df_libros, use_container_width=True, hide_index=True)
    else:
        st.info("El inventario está vacío actualmente.")

elif menu == "🔄 Préstamos":
    st.header("🔄 Control de Préstamos y Devoluciones")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📤 Registrar Nuevo Préstamo", "📥 Recepción y Devoluciones"])
    
    with tab1:
        df_libros = obtener_libros()
        if not df_libros.empty:
            libros_disponibles = df_libros[df_libros['stock'] > 0]
            if not libros_disponibles.empty:
                with st.form("form_prestamo", clear_on_submit=True):
                    opciones_libros = dict(zip(libros_disponibles['titulo'], libros_disponibles['id']))
                    libro_elegido = st.selectbox("Seleccionar Libro Disponible", list(opciones_libros.keys()))
                    cliente = st.text_input("Nombre del Estudiante / Cliente")
                    
                    if st.form_submit_button("Confirmar Salida"):
                        if cliente:
                            id_libro = opciones_libros[libro_elegido]
                            fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
                            
                            c = conn.cursor()
                            c.execute("INSERT INTO prestamos (libro_id, cliente, fecha_prestamo) VALUES (?, ?, ?)", 
                                      (id_libro, cliente, fecha_hoy))
                            c.execute("UPDATE libros SET stock = stock - 1 WHERE id = ?", (id_libro,))
                            conn.commit()
                            
                            st.success(f"Préstamo registrado exitosamente para {cliente}.")
                            st.rerun()
                        else:
                            st.warning("Por favor ingresa el nombre del cliente.")
            else:
                st.warning("No hay libros con stock disponible para préstamo.")
        else:
            st.info("No hay libros registrados en el catálogo.")

    with tab2:
        df_activos = obtener_prestamos_activos()
        if not df_activos.empty:
            st.dataframe(df_activos, use_container_width=True, hide_index=True)
            with st.form("form_dev"):
                id_a_devolver = st.selectbox("Seleccione el ID del préstamo a retornar", df_activos['id'])
                if st.form_submit_button("Registrar Devolución y Stock"):
                    c = conn.cursor()
                    c.execute("UPDATE prestamos SET estado = 'Devuelto' WHERE id = ?", (id_a_devolver,))
                    c.execute("""
                        UPDATE libros SET stock = stock + 1 
                        WHERE id = (SELECT libro_id FROM prestamos WHERE id = ?)
                    """, (id_a_devolver,))
                    conn.commit()
                    st.success("¡Devolución registrada correctamente!")
                    st.rerun()
        else:
            st.success("No hay préstamos pendientes de devolución.")

elif menu == "💰 Finanzas e Ingresos":
    st.header("💰 Gestión de Ingresos y Aspectos Financieros")
    st.markdown("---")
    
    col_reg, col_list = st.columns([1, 2])
    
    with col_reg:
        st.subheader("Registrar Ingreso")
        with st.form("form_ingreso", clear_on_submit=True):
            concepto = st.text_input("Concepto (Ej. Venta de libro, Multa)")
            monto = st.number_input("Monto ($)", min_value=0.0, step=500.0)
            
            if st.form_submit_button("Guardar Ingreso"):
                if concepto and monto > 0:
                    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                    c = conn.cursor()
                    c.execute("INSERT INTO ingresos (concepto, monto, fecha) VALUES (?, ?, ?)", 
                              (concepto, monto, fecha_hoy))
                    conn.commit()
                    st.success("¡Ingreso registrado con éxito!")
                    st.rerun()
                else:
                    st.warning("Ingresa un concepto válido y un monto mayor a cero.")
                    
    with col_list:
        st.subheader("Historial de Entradas Financieras")
        df_ingresos = obtener_ingresos()
        if not df_ingresos.empty:
            st.dataframe(df_ingresos, use_container_width=True, hide_index=True)
            total = df_ingresos['monto'].sum()
            st.metric(label="Total Acumulado", value=f"$ {total:,.2f}")
        else:
            st.info("Aún no hay registros financieros en el sistema.")