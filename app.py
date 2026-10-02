import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import os

# 1. Configuración de página
st.set_page_config(page_title="Librería El Alejandrino", page_icon="📚", layout="wide")

# 2. Cargar Estilos de forma modular desde la carpeta assets
def cargar_css(ruta_css):
    try:
        with open(ruta_css, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("No se encontró el archivo de estilos en assets/style.css")

cargar_css("assets/style.css")

# 3. Base de Datos Inteligente con Datos Iniciales y Portadas
def init_db():
    conn = sqlite3.connect('alejandrino.db', check_same_thread=False)
    c = conn.cursor()
    
    # Empleados / Roles
    c.execute('''CREATE TABLE IF NOT EXISTS empleados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cedula TEXT UNIQUE NOT NULL,
                    nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    correo TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    activo INTEGER DEFAULT 1)''')
    
    # Proveedores / Editoriales
    c.execute('''CREATE TABLE IF NOT EXISTS editoriales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nit TEXT UNIQUE NOT NULL,
                    razonSocial TEXT NOT NULL,
                    contacto TEXT,
                    telefono TEXT,
                    correo TEXT,
                    activo INTEGER DEFAULT 1)''')
    
    # Libros con columna de portada
    c.execute('''CREATE TABLE IF NOT EXISTS libros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    isbn TEXT UNIQUE NOT NULL,
                    titulo TEXT NOT NULL,
                    autor TEXT NOT NULL,
                    editorial TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    precioVenta REAL DEFAULT 0.0,
                    stockDisponible INTEGER DEFAULT 0,
                    portada TEXT,
                    activo INTEGER DEFAULT 1)''')
    
    # Clientes / Lectores
    c.execute('''CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cedula TEXT UNIQUE NOT NULL,
                    nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    telefono TEXT,
                    correo TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    direccion TEXT)''')
    
    # Ventas y Facturación
    c.execute('''CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    empleado_id INTEGER,
                    fechaHora TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    iva REAL NOT NULL,
                    total REAL NOT NULL,
                    estado TEXT DEFAULT 'Pagada')''')
    
    conn.commit()
    
    # Crear Administrador por defecto
    c.execute("SELECT COUNT(*) FROM empleados WHERE correo = 'admin@alejandrino.com'")
    if c.fetchone()[0] == 0:
        pass_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("""
            INSERT INTO empleados (cedula, nombres, apellidos, correo, password, rol, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("10000000", "Administrador", "Principal", "admin@alejandrino.com", pass_hash, "Administrador", 1))
        conn.commit()

    # Nutrir base de datos con Proveedores de prueba si está vacía
    c.execute("SELECT COUNT(*) FROM editoriales")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO editoriales (nit, razonSocial, contacto, telefono, correo) VALUES (?, ?, ?, ?, ?)", [
            ("900123456-1", "Editorial Planeta Colombia", "Carlos Gomez", "3101234567", "contacto@planeta.com"),
            ("900987654-3", "Penguin Random House", "Ana Maria Ruiz", "3209876543", "info@penguinrandomhouse.com")
        ])
        conn.commit()

    # Nutrir base de datos con Libros de prueba y portadas reales si está vacía
    c.execute("SELECT COUNT(*) FROM libros")
    if c.fetchone()[0] == 0:
        c.executemany("""
            INSERT INTO libros (isbn, titulo, autor, editorial, categoria, precioVenta, stockDisponible, portada)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ("9789584275", "Cien años de soledad", "Gabriel García Márquez", "Editorial Planeta Colombia", "Ficción", 65000.0, 12, "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400"),
            ("9789588940", "La María", "Jorge Isaacs", "Penguin Random House", "Clásicos", 45000.0, 8, "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400"),
            ("9780307474", "El amor en los tiempos del cólera", "Gabriel García Márquez", "Editorial Planeta Colombia", "Ficción", 59000.0, 15, "https://images.unsplash.com/photo-1495640388908-05fa85288e61?w=400")
        ])
        conn.commit()
        
    return conn

conn = init_db()

# Control de Sesión Global
if 'usuario_autenticado' not in st.session_state:
    st.session_state['usuario_autenticado'] = False
    st.session_state['user_data'] = None
    st.session_state['tipo_usuario'] = None
    st.session_state['carrito'] = []

# Cabecera Profesional con el nuevo Logo PNG horizontal y Título Institucional
col_logo, col_titulo = st.columns([2, 5])

with col_logo:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=380)

with col_titulo:
    st.markdown("""
        <div style="background-color: #1B2A4A; padding: 25px 20px; border-radius: 8px; color: white; box-shadow: 0 3px 8px rgba(0,0,0,0.15); text-align: center; margin-top: 10px;">
            <h2 style="margin:0; font-family: 'Georgia', serif; font-size: 1.7rem; color: #E6C687; letter-spacing: 1px;">Cultura, Literatura y Conocimiento</h2>
            <p style="margin:8px 0 0 0; font-style: italic; font-size: 1rem; color: #E0E0E0;">Bienvenidos a su espacio literario</p>
        </div>
    """, unsafe_allow_html=True)

# Mostrar Banner panorámico con dimensiones controladas
if os.path.exists("assets/banner.png"):
    st.markdown('<div class="banner-contenedor">', unsafe_allow_html=True)
    st.image("assets/banner.png", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Consultas auxiliares
def obtener_libros():
    return pd.read_sql_query("SELECT * FROM libros WHERE activo = 1", conn)

# ==========================================
# FLUJO DE SESIÓN Y VISTAS
# ==========================================
if not st.session_state['usuario_autenticado']:
    tab_catalogo, tab_login, tab_registro = st.tabs(["📖 Catálogo y Tienda Online", "🔐 Iniciar Sesión", "📝 Registro de Clientes"])
    
    with tab_catalogo:
        st.markdown("### 🌟 Novedades y Catálogo Disponible")
        busqueda = st.text_input("🔍 Buscar por título, autor o categoría...")
        df_libros = obtener_libros()
        
        if busqueda:
            df_libros = df_libros[
                df_libros['titulo'].str.contains(busqueda, case=False) | 
                df_libros['autor'].str.contains(busqueda, case=False) |
                df_libros['categoria'].str.contains(busqueda, case=False)
            ]
            
        if not df_libros.empty:
            cols = st.columns(3)
            for index, row in df_libros.iterrows():
                with cols[index % 3]:
                    st.markdown(f"""
                        <div class="tarjeta-libro">
                            <img src="{row['portada']}" style="width: 100%; height: 220px; object-fit: cover; border-radius: 4px; margin-bottom: 10px;">
                            <h4 style="margin: 5px 0; color: #2C2A29;">{row['titulo']}</h4>
                            <p style="color: #666; font-size: 0.9rem; margin: 2px;"><b>Autor:</b> {row['autor']}</p>
                            <p style="color: #C8102E; font-weight: bold; font-size: 1.1rem; margin: 5px 0;">$ {row['precioVenta']:,.0f}</p>
                            <p style="font-size: 0.8rem; color: #888;">Stock disponible: {row['stockDisponible']} unidades</p>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"🛒 Agregar al Carrito", key=f"btn_{row['id']}"):
                        st.session_state['carrito'].append(row.to_dict())
                        st.success(f"¡Agregado '{row['titulo']}' al carrito!")
        else:
            st.info("No se encontraron libros con los filtros ingresados.")
            
        if st.session_state['carrito']:
            st.markdown("---")
            st.subheader("🛍️ Tu Carrito de Compras")
            df_carrito = pd.DataFrame(st.session_state['carrito'])
            st.dataframe(df_carrito[['titulo', 'precioVenta']], use_container_width=True)
            if st.button("Finalizar Compra (Iniciar Sesión Requerida)"):
                st.warning("Por favor inicia sesión como cliente para procesar tu pago.")

    with tab_login:
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.markdown("### Acceso al Sistema")
            with st.form("form_login_unico"):
                correo = st.text_input("Correo Electrónico")
                password = st.text_input("Contraseña", type="password")
                btn_ingresar = st.form_submit_button("Ingresar")
                
                if btn_ingresar:
                    c = conn.cursor()
                    pass_hash = hashlib.sha256(password.encode()).hexdigest()
                    
                    c.execute("SELECT id, nombres, apellidos, rol FROM empleados WHERE correo = ? AND password = ? AND activo = 1", (correo.strip(), pass_hash))
                    empleado = c.fetchone()
                    
                    if empleado:
                        st.session_state['usuario_autenticado'] = True
                        st.session_state['tipo_usuario'] = 'empleado'
                        st.session_state['user_data'] = {"id": empleado[0], "nombre": f"{empleado[1]} {empleado[2]}", "rol": empleado[3]}
                        st.success(f"¡Bienvenido al panel interno, {empleado[1]}!")
                        st.rerun()
                    else:
                        c.execute("SELECT id, nombres, apellidos FROM clientes WHERE correo = ? AND password = ?", (correo.strip(), pass_hash))
                        cliente = c.fetchone()
                        if cliente:
                            st.session_state['usuario_autenticado'] = True
                            st.session_state['tipo_usuario'] = 'cliente'
                            st.session_state['user_data'] = {"id": cliente[0], "nombre": f"{cliente[1]} {cliente[2]}", "rol": "Cliente"}
                            st.success(f"¡Bienvenido de nuevo, {cliente[1]}!")
                            st.rerun()
                        else:
                            st.error("Correo o contraseña incorrectos.")
            st.caption("💡 Admin de prueba: `admin@alejandrino.com` / `admin123`")

    with tab_registro:
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("### Registro de Nuevo Lector / Cliente")
            with st.form("form_reg_cliente", clear_on_submit=True):
                cedula = st.text_input("Cédula")
                nombres = st.text_input("Nombres")
                apellidos = st.text_input("Apellidos")
                telefono = st.text_input("Teléfono")
                correo = st.text_input("Correo Electrónico")
                password = st.text_input("Contraseña", type="password")
                direccion = st.text_input("Dirección de Entrega")
                
                if st.form_submit_button("Registrarse"):
                    if cedula and correo and password:
                        try:
                            pass_hash = hashlib.sha256(password.encode()).hexdigest()
                            c = conn.cursor()
                            c.execute("""
                                INSERT INTO clientes (cedula, nombres, apellidos, telefono, correo, password, direccion)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (cedula, nombres, apellidos, telefono, correo, pass_hash, direccion))
                            conn.commit()
                            st.success("¡Registro exitoso! Ya puedes iniciar sesión.")
                        except sqlite3.IntegrityError:
                            st.error("La cédula o el correo ya se encuentran registrados.")
                    else:
                        st.warning("Por favor complete los campos obligatorios.")

else:
    tipo = st.session_state['tipo_usuario']
    user = st.session_state['user_data']
    
    with st.sidebar:
        st.markdown(f"### 👤 Sesión Activa")
        st.write(f"**{user['nombre']}**")
        st.caption(f"Rol: `{user['rol']}`")
        st.markdown("---")
        
        if tipo == 'empleado':
            menu = st.radio("Panel Interno", ["🏠 Inicio", "📖 Catálogo y Stock", "📦 Proveedores", "👥 Clientes", "🔄 Préstamos", "💰 Ventas (IVA 19%)"])
        else:
            menu = st.radio("Menú Cliente", ["🏠 Explorar Tienda", "🛒 Mi Carrito y Compras", "📚 Mis Préstamos"])
            
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión"):
            st.session_state['usuario_autenticado'] = False
            st.session_state['user_data'] = None
            st.session_state['tipo_usuario'] = None
            st.rerun()

    if tipo == 'empleado':
        if menu == "🏠 Inicio":
            st.header(f"Panel de Control - {user['rol']}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Libros Activos", len(obtener_libros()))
            with col2:
                st.metric("Proveedores", len(pd.read_sql_query("SELECT * FROM editoriales", conn)))
            with col3:
                st.metric("Clientes", len(pd.read_sql_query("SELECT * FROM clientes", conn)))
        elif menu == "📖 Catálogo y Stock":
            st.header("Gestión de Inventario y Libros")
            with st.form("form_nuevo_libro", clear_on_submit=True):
                c1, c2 = st.columns(2)
                isbn = c1.text_input("ISBN")
                titulo = c2.text_input("Título")
                autor = c1.text_input("Autor")
                editorial = c2.selectbox("Editorial", pd.read_sql_query("SELECT razonSocial FROM editoriales", conn)['razonSocial'].tolist())
                categoria = c1.text_input("Categoría")
                precio = c2.number_input("Precio ($)", min_value=0.0, step=1000.0)
                portada = c1.text_input("URL de la Portada (Imagen)")
                
                if st.form_submit_button("Guardar Libro"):
                    c = conn.cursor()
                    c.execute("INSERT INTO libros (isbn, titulo, autor, editorial, categoria, precioVenta, stockDisponible, portada) VALUES (?, ?, ?, ?, ?, ?, 10, ?)",
                              (isbn, titulo, autor, editorial, categoria, precio, portada))
                    conn.commit()
                    st.success("¡Libro agregado al catálogo con stock inicial de 10!")
                    st.rerun()
            st.dataframe(obtener_libros(), use_container_width=True)
        elif menu == "📦 Proveedores":
            st.header("Gestión de Proveedores")
            st.dataframe(pd.read_sql_query("SELECT * FROM editoriales", conn), use_container_width=True)
        elif menu == "👥 Clientes":
            st.header("Directorio de Clientes")
            st.dataframe(pd.read_sql_query("SELECT id, cedula, nombres, apellidos, telefono, correo, direccion FROM clientes", conn), use_container_width=True)
        elif menu == "🔄 Préstamos":
            st.header("Control de Préstamos Bibliotecarios")
            st.info("Módulo operativo de préstamos.")
        elif menu == "💰 Ventas (IVA 19%)":
            st.header("Caja y Facturación con IVA (19%)")
            st.info("Módulo de caja abierto.")
    else:
        if menu == "🏠 Explorar Tienda":
            st.header("Catálogo General")
            df_libros = obtener_libros()
            cols = st.columns(3)
            for index, row in df_libros.iterrows():
                with cols[index % 3]:
                    st.markdown(f"""
                        <div class="tarjeta-libro">
                            <img src="{row['portada']}" style="width: 100%; height: 220px; object-fit: cover; border-radius: 4px; margin-bottom: 10px;">
                            <h4 style="margin: 5px 0;">{row['titulo']}</h4>
                            <p style="color: #666; font-size: 0.9rem;">{row['autor']}</p>
                            <p style="color: #C8102E; font-weight: bold; font-size: 1.1rem;">$ {row['precioVenta']:,.0f}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button("Añadir al Carrito", key=f"cli_btn_{row['id']}"):
                        st.session_state['carrito'].append(row.to_dict())
                        st.success("¡Añadido!")
        elif menu == "🛒 Mi Carrito y Compras":
            st.header("🛒 Tu Carrito de Compras")
            if st.session_state['carrito']:
                df_c = pd.DataFrame(st.session_state['carrito'])
                st.dataframe(df_c[['titulo', 'precioVenta']], use_container_width=True)
                subtotal = df_c['precioVenta'].sum()
                iva = subtotal * 0.19
                total = subtotal + iva
                st.markdown(f"""
                    ### Resumen de Pago
                    - **Subtotal:** $ {subtotal:,.2f}
                    - **IVA (19%):** ${iva:,.2f}                     - **Total a Pagar:**$ {total:,.2f}
                """)
                if st.button("Confirmar Pedido / Pagar"):
                    st.success("¡Compra realizada con éxito!")
                    st.session_state['carrito'] = []
            else:
                st.info("Tu carrito está vacío.")
        elif menu == "📚 Mis Préstamos":
            st.header("Historial de Préstamos Activos")
            st.info("No tienes préstamos bibliotecarios activos.")