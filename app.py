import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib

# 1. Configuración de página
st.set_page_config(page_title="El Alejandrino | Sistema de Gestión y Venta de Libros", page_icon="📚", layout="wide")

# 2. Cargar estilos de forma modular desde la carpeta assets
def cargar_css(ruta_css):
    try:
        with open(ruta_css, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("No se encontró el archivo de estilos en assets/style.css, ejecutando con estilos por defecto.")

cargar_css("assets/style.css")

# 3. Motor de Base de Datos SQLite
def init_db():
    conn = sqlite3.connect('alejandrino.db', check_same_thread=False)
    c = conn.cursor()
    
    # Tabla de Empleados / Usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS empleados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cedula TEXT UNIQUE NOT NULL,
                    nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    correo TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    activo INTEGER DEFAULT 1)''')
    
    # Tabla de Proveedores / Editoriales
    c.execute('''CREATE TABLE IF NOT EXISTS editoriales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nit TEXT UNIQUE NOT NULL,
                    razonSocial TEXT NOT NULL,
                    contacto TEXT,
                    telefono TEXT,
                    correo TEXT,
                    activo INTEGER DEFAULT 1)''')
    
    # Tabla de Libros
    c.execute('''CREATE TABLE IF NOT EXISTS libros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    isbn TEXT UNIQUE NOT NULL,
                    titulo TEXT NOT NULL,
                    autor TEXT NOT NULL,
                    editorial TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    precioVenta REAL DEFAULT 0.0,
                    stockDisponible INTEGER DEFAULT 0,
                    activo INTEGER DEFAULT 1)''')
    
    # Tabla de Clientes / Lectores
    c.execute('''CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cedula TEXT UNIQUE NOT NULL,
                    nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    telefono TEXT,
                    correo TEXT,
                    direccion TEXT)''')
    
    # Tabla de Préstamos
    c.execute('''CREATE TABLE IF NOT EXISTS prestamos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    libro_id INTEGER,
                    cliente_id INTEGER,
                    fechaSalida TEXT NOT NULL,
                    fechaLimite TEXT NOT NULL,
                    fechaDevolucion TEXT,
                    estado TEXT DEFAULT 'Activo',
                    multa REAL DEFAULT 0.0,
                    FOREIGN KEY (libro_id) REFERENCES libros (id),
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id))''')
    
    # Tabla de Ventas y Facturación
    c.execute('''CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    empleado_id INTEGER,
                    fechaHora TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    iva REAL NOT NULL,
                    total REAL NOT NULL,
                    estado TEXT DEFAULT 'Pagada',
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id),
                    FOREIGN KEY (empleado_id) REFERENCES empleados (id))''')
    
    conn.commit()
    
    # Crear Administrador por defecto si no existe
    c.execute("SELECT COUNT(*) FROM empleados WHERE correo = 'admin@alejandrino.com'")
    if c.fetchone()[0] == 0:
        pass_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("""
            INSERT INTO empleados (cedula, nombres, apellidos, correo, password, rol, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("10000000", "Administrador", "Principal", "admin@alejandrino.com", pass_hash, "Administrador", 1))
        conn.commit()
        
    return conn

conn = init_db()

# Funciones de consulta y autenticación
def verificar_credenciales(correo, password):
    c = conn.cursor()
    correo_limpio = correo.strip().lower()
    pass_hash = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT id, nombres, apellidos, rol FROM empleados WHERE LOWER(correo) = ? AND password = ? AND activo = 1", (correo_limpio, pass_hash))
    return c.fetchone()

def obtener_libros():
    return pd.read_sql_query("SELECT id, isbn, titulo, autor, editorial, categoria, precioVenta, stockDisponible FROM libros WHERE activo = 1", conn)

def obtener_editoriales():
    return pd.read_sql_query("SELECT id, nit, razonSocial, contacto, telefono, correo FROM editoriales WHERE activo = 1", conn)

def obtener_clientes():
    return pd.read_sql_query("SELECT id, cedula, nombres, apellidos, telefono, correo, direccion FROM clientes", conn)

def obtener_prestamos_activos():
    query = """
    SELECT p.id, l.titulo, (c.nombres || ' ' || c.apellidos) as cliente, p.fechaSalida, p.fechaLimite, p.estado, p.multa
    FROM prestamos p
    JOIN libros l ON p.libro_id = l.id
    JOIN clientes c ON p.cliente_id = c.id
    WHERE p.estado = 'Activo'
    """
    return pd.read_sql_query(query, conn)

def obtener_empleados():
    return pd.read_sql_query("SELECT id, cedula, nombres, apellidos, correo, rol, activo FROM empleados", conn)

# 4. Control de Sesión
if 'usuario_autenticado' not in st.session_state:
    st.session_state['usuario_autenticado'] = False
    st.session_state['user_data'] = None

# 5. Barra Superior Estilo Tienda Online
st.markdown("""
    <div style="background-color: #2C2A29; padding: 12px 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
        <h2 style="color: #F0BB62; margin: 0; font-family: 'Georgia', serif;">📚 El Alejandrino</h2>
        <p style="color: #E3D9C6; margin: 0; font-style: italic;">Sistema Oficial de Gestión y Venta de Libros</p>
    </div>
""", unsafe_allow_html=True)

# 6. Estructura Principal
if not st.session_state['usuario_autenticado']:
    modo_vista = st.radio("Seleccione vista:", ["🌐 Catálogo Público (Tienda Online)", "🔐 Portal de Acceso (Empleados / Roles)"], horizontal=True)
    st.markdown("---")
    
    if modo_vista == "🌐 Catálogo Público (Tienda Online)":
        st.markdown("<h3 style='color: #4A3B32;'>Catálogo Disponible al Público</h3>", unsafe_allow_html=True)
        busqueda = st.text_input("🔍 Buscar por título, autor o categoría de libro...")
        df_libros = obtener_libros()
        
        if not df_libros.empty:
            if busqueda:
                df_libros = df_libros[
                    df_libros['titulo'].str.contains(busqueda, case=False) | 
                    df_libros['autor'].str.contains(busqueda, case=False) |
                    df_libros['categoria'].str.contains(busqueda, case=False)
                ]
            st.dataframe(df_libros, use_container_width=True, hide_index=True)
        else:
            st.info("No hay libros registrados actualmente en el sistema.")

    else:
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.markdown("### Iniciar Sesión en el Sistema")
            with st.form("form_login_limpio"):
                correo_input = st.text_input("Correo Electrónico", value="")
                password_input = st.text_input("Contraseña", type="password", value="")
                btn_login = st.form_submit_button("Ingresar al Sistema")
                
                if btn_login:
                    if correo_input and password_input:
                        usuario = verificar_credenciales(correo_input, password_input)
                        if usuario:
                            st.session_state['usuario_autenticado'] = True
                            st.session_state['user_data'] = {
                                "id": usuario[0],
                                "nombre": f"{usuario[1]} {usuario[2]}",
                                "rol": usuario[3]
                            }
                            st.success(f"¡Bienvenido, {usuario[1]}!")
                            st.rerun()
                        else:
                            st.error("Credenciales inválidas o cuenta inactiva.")
                    else:
                        st.warning("Por favor ingrese correo y contraseña.")
                        
            st.info("ℹ️ **Credenciales de prueba Administrador:**\n- Correo: `admin@alejandrino.com`\n- Contraseña: `admin123`")

else:
    user_rol = st.session_state['user_data']['rol']
    user_nombre = st.session_state['user_data']['nombre']
    
    with st.sidebar:
        st.markdown(f"### 🏛️ Panel de Control")
        st.write(f"👤 **{user_nombre}**")
        st.caption(f"Rol Activo: `{user_rol}`")
        st.markdown("---")
        
        opciones_menu = ["🏠 Inicio"]
        
        if user_rol in ["Administrador", "Almacenista"]:
            opciones_menu.extend(["📖 Catálogo de Libros", "📦 Proveedores y Stock"])
        if user_rol in ["Administrador", "Bibliotecario"]:
            opciones_menu.extend(["👥 Clientes y Lectores", "🔄 Préstamos y Devoluciones"])
        if user_rol in ["Administrador", "Vendedor"]:
            opciones_menu.append("💰 Ventas y Facturación")
        if user_rol == "Administrador":
            opciones_menu.append("⚙️️ Gestión de Empleados")
            
        menu = st.radio("Navegación Específica", opciones_menu)
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión"):
            st.session_state['usuario_autenticado'] = False
            st.session_state['user_data'] = None
            st.rerun()

    if menu == "🏠 Inicio":
        st.markdown(f"<h1 class='titulo-principal'>Panel de Operaciones</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='subtitulo'>Bienvenido al núcleo de control para el rol de <b>{user_rol}</b>.</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Libros en Catálogo", len(obtener_libros()))
        with col2:
            st.metric("Proveedores Activos", len(obtener_editoriales()))
        with col3:
            st.metric("Clientes Registrados", len(obtener_clientes()))

    elif menu == "📖 Catálogo de Libros":
        st.header("📖 Administración de Catálogo e Inventario")
        st.markdown("---")
        
        with st.form("form_libro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            isbn = col1.text_input("ISBN (Único)")
            titulo = col2.text_input("Título del Libro")
            autor = col1.text_input("Autor")
            
            editoriales_df = obtener_editoriales()
            lista_edit = editoriales_df['razonSocial'].tolist() if not editoriales_df.empty else ["Sin proveedores"]
            editorial = col2.selectbox("Editorial / Proveedor", lista_edit)
            
            categoria = col1.text_input("Categoría / Género")
            precio = col2.number_input("Precio de Venta ($)", min_value=0.0, step=1000.0)
            
            if st.form_submit_button("Guardar Libro en Catálogo"):
                if isbn and titulo and editorial != "Sin proveedores":
                    try:
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO libros (isbn, titulo, autor, editorial, categoria, precioVenta, stockDisponible)
                            VALUES (?, ?, ?, ?, ?, ?, 0)
                        """, (isbn, titulo, autor, editorial, categoria, precio))
                        conn.commit()
                        st.success("¡Libro registrado correctamente!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Error: El ISBN ya se encuentra registrado.")
                else:
                    st.warning("Debe registrar proveedores antes de ingresar libros y completar los campos.")
                    
        st.markdown("### Inventario General")
        st.dataframe(obtener_libros(), use_container_width=True, hide_index=True)

    elif menu == "📦 Proveedores y Stock":
        st.header("📦 Gestión de Proveedores y Entradas de Stock")
        st.markdown("---")
        
        tab_prov, tab_stock = st.tabs(["Registrar Proveedor (Editorial)", "Entrada de Ejemplares (Stock)"])
        
        with tab_prov:
            with st.form("form_proveedor", clear_on_submit=True):
                col1, col2 = st.columns(2)
                nit = col1.text_input("NIT de la Editorial")
                razonSocial = col2.text_input("Razón Social")
                contacto = col1.text_input("Persona de Contacto")
                telefono = col2.text_input("Teléfono")
                correo = col1.text_input("Correo Electrónico")
                
                if st.form_submit_button("Guardar Proveedor"):
                    if nit and razonSocial:
                        try:
                            c = conn.cursor()
                            c.execute("""
                                INSERT INTO editoriales (nit, razonSocial, contacto, telefono, correo)
                                VALUES (?, ?, ?, ?, ?)
                            """, (nit, razonSocial, contacto, telefono, correo))
                            conn.commit()
                            st.success("¡Proveedor registrado exitosamente!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Error: El NIT ya está registrado.")
                    else:
                        st.warning("Complete los campos obligatorios (NIT y Razón Social).")
            
            st.markdown("### Proveedores Registrados")
            st.dataframe(obtener_editoriales(), use_container_width=True, hide_index=True)
            
        with tab_stock:
            st.subheader("Entrada de Stock por Factura")
            libros_df = obtener_libros()
            if not libros_df.empty:
                with st.form("form_stock", clear_on_submit=True):
                    factura = st.text_input("Número de Factura del Proveedor")
                    libro_sel = st.selectbox("Seleccionar Libro", libros_df['titulo'].tolist())
                    cantidad = st.number_input("Cantidad de Ejemplares Recibidos", min_value=1, value=1)
                    
                    if st.form_submit_button("Actualizar Stock en Almacén"):
                        id_libro = libros_df[libros_df['titulo'] == libro_sel]['id'].values[0]
                        c = conn.cursor()
                        c.execute("UPDATE libros SET stockDisponible = stockDisponible + ? WHERE id = ?", (cantidad, id_libro))
                        conn.commit()
                        st.success(f"¡Stock actualizado! Se sumaron {cantidad} ejemplares.")
                        st.rerun()
            else:
                st.info("No hay libros en el catálogo para ingresar stock.")

    elif menu == "👥 Clientes y Lectores":
        st.header("👥 Gestión de Clientes y Lectores")
        st.markdown("---")
        
        with st.form("form_cliente", clear_on_submit=True):
            col1, col2 = st.columns(2)
            cedula = col1.text_input("Cédula / NIT del Cliente")
            nombres = col2.text_input("Nombres")
            apellidos = col1.text_input("Apellidos")
            telefono = col2.text_input("Teléfono")
            correo = col1.text_input("Correo Electrónico")
            direccion = col2.text_input("Dirección")
            
            if st.form_submit_button("Registrar Cliente"):
                if cedula and nombres:
                    try:
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO clientes (cedula, nombres, apellidos, telefono, correo, direccion)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (cedula, nombres, apellidos, telefono, correo, direccion))
                        conn.commit()
                        st.success("¡Cliente registrado exitosamente!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Error: La cédula ya se encuentra registrada.")
                else:
                    st.warning("Ingrese al menos la cédula y los nombres.")
                    
        st.markdown("### Clientes Registrados")
        st.dataframe(obtener_clientes(), use_container_width=True, hide_index=True)

    elif menu == "🔄 Préstamos y Devoluciones":
        st.header("🔄 Control de Préstamos y Devoluciones")
        st.markdown("---")
        
        tab_prest, tab_dev = st.tabs(["Registrar Préstamo", "Historial y Devoluciones"])
        
        with tab_prest:
            clientes_df = obtener_clientes()
            libros_df = obtener_libros()
            
            if not clientes_df.empty and not libros_df.empty:
                with st.form("form_nuevo_prestamo", clear_on_submit=True):
                    cliente_sel = st.selectbox("Seleccionar Cliente / Lector", (clientes_df['cedula'] + " - " + clientes_df['nombres'] + " " + clientes_df['apellidos']).tolist())
                    libro_sel = st.selectbox("Seleccionar Libro a Prestar", libros_df['titulo'].tolist())
                    dias_limite = st.number_input("Días de Préstamo", min_value=1, value=7)
                    
                    if st.form_submit_button("Confirmar Préstamo"):
                        cedula_cli = cliente_sel.split(" - ")[0]
                        id_cliente = clientes_df[clientes_df['cedula'] == cedula_cli]['id'].values[0]
                        id_libro = libros_df[libros_df['titulo'] == libro_sel]['id'].values[0]
                        
                        stock_actual = libros_df[libros_df['id'] == id_libro]['stockDisponible'].values[0]
                        if stock_actual > 0:
                            fecha_salida = datetime.now().strftime("%Y-%m-%d")
                            fecha_limite = (datetime.now() + timedelta(days=int(dias_limite))).strftime("%Y-%m-%d")
                            
                            c = conn.cursor()
                            c.execute("""
                                INSERT INTO prestamos (libro_id, cliente_id, fechaSalida, fechaLimite, estado)
                                VALUES (?, ?, ?, ?, 'Activo')
                            """, (id_libro, id_cliente, fecha_salida, fecha_limite))
                            c.execute("UPDATE libros SET stockDisponible = stockDisponible - 1 WHERE id = ?", (id_libro,))
                            conn.commit()
                            
                            st.success("¡Préstamo registrado exitosamente!")
                            st.rerun()
                        else:
                            st.error("Error: El libro seleccionado no cuenta con stock disponible.")
            else:
                st.warning("Debe tener clientes y libros registrados para procesar préstamos.")
                
        with tab_dev:
            st.subheader("Préstamos Activos y Devoluciones")
            df_prest = obtener_prestamos_activos()
            if not df_prest.empty:
                st.dataframe(df_prest, use_container_width=True, hide_index=True)
                with st.form("form_devolucion"):
                    id_prestamo = st.selectbox("Seleccione ID de Préstamo a Devolver", df_prest['id'].tolist())
                    if st.form_submit_button("Registrar Devolución"):
                        c = conn.cursor()
                        c.execute("SELECT libro_id FROM prestamos WHERE id = ?", (id_prestamo,))
                        id_lib = c.fetchone()[0]
                        
                        c.execute("UPDATE prestamos SET estado = 'Devuelto', fechaDevolucion = ? WHERE id = ?", (datetime.now().strftime("%Y-%m-%d"), id_prestamo))
                        c.execute("UPDATE libros SET stockDisponible = stockDisponible + 1 WHERE id = ?", (id_lib,))
                        conn.commit()
                        st.success("¡Devolución procesada y stock restaurado!")
                        st.rerun()
            else:
                st.info("No hay préstamos activos pendientes.")

    elif menu == "💰 Ventas y Facturación":
        st.header("💰 Módulo de Ventas y Facturación Legal (IVA 19%)")
        st.markdown("---")
        
        clientes_df = obtener_clientes()
        libros_df = obtener_libros()
        
        if not clientes_df.empty and not libros_df.empty:
            with st.form("form_venta"):
                st.subheader("Generar Orden de Venta y Factura")
                cliente_venta = st.selectbox("Cliente", (clientes_df['cedula'] + " - " + clientes_df['nombres']).tolist())
                libro_venta = st.selectbox("Libro", libros_df['titulo'].tolist())
                cantidad_venta = st.number_input("Cantidad", min_value=1, value=1)
                
                if st.form_submit_button("Calcular Total y Emitir Factura (IVA 19%)"):
                    id_lib = libros_df[libros_df['titulo'] == libro_venta]['id'].values[0]
                    precio_unitario = libros_df[libros_df['id'] == id_lib]['precioVenta'].values[0]
                    stock_disp = libros_df[libros_df['id'] == id_lib]['stockDisponible'].values[0]
                    
                    if stock_disp >= cantidad_venta:
                        subtotal = precio_unitario * cantidad_venta
                        iva19 = subtotal * 0.19
                        total_pagar = subtotal + iva19
                        
                        id_cli = clientes_df[clientes_df['cedula'] == cliente_venta.split(" - ")[0]]['id'].values[0]
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO ventas (cliente_id, empleado_id, fechaHora, subtotal, iva, total, estado)
                            VALUES (?, ?, ?, ?, ?, ?, 'Pagada')
                        """, (id_cli, st.session_state['user_data']['id'], datetime.now().strftime("%Y-%m-%d %H:%M"), subtotal, iva19, total_pagar))
                        c.execute("UPDATE libros SET stockDisponible = stockDisponible - ? WHERE id = ?", (cantidad_venta, id_lib))
                        conn.commit()
                        
                        st.success("¡Factura emitida con éxito!")
                        st.markdown(f"""
                            ### 🧾 FACTURA DE VENTA - EL ALEJANDRINO
                            - **Subtotal:** $ {subtotal:,.2f}
                            - **IVA (19%):** ${iva19:,.2f}                             - **Total a Pagar:**$ {total_pagar:,.2f}
                        """)
                    else:
                        st.error("Stock insuficiente para procesar la venta.")
        else:
            st.info("Se requieren clientes y libros en stock para realizar ventas.")

    elif menu == "⚙️ Gestión de Empleados":
        st.header("⚙️ Administración de Personal y Credenciales")
        st.markdown("---")
        
        with st.form("form_empleado_reg", clear_on_submit=True):
            col1, col2 = st.columns(2)
            cedula = col1.text_input("Cédula")
            nombres = col2.text_input("Nombres")
            apellidos = col1.text_input("Apellidos")
            correo = col2.text_input("Correo Electrónico")
            password = col1.text_input("Contraseña Temporal", type="password")
            rol = col2.selectbox("Rol Asignado", ["Administrador", "Vendedor", "Bibliotecario", "Almacenista"])
            
            if st.form_submit_button("Registrar Empleado"):
                if cedula and correo and password:
                    try:
                        pass_hash = hashlib.sha256(password.encode()).hexdigest()
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO empleados (cedula, nombres, apellidos, correo, password, rol, activo)
                            VALUES (?, ?, ?, ?, ?, ?, 1)
                        """, (cedula, nombres, apellidos, correo, pass_hash, rol))
                        conn.commit()
                        st.success(f"¡Empleado registrado con éxito bajo el rol de {rol}!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Error: La cédula o el correo ya están registrados.")
                else:
                    st.warning("Complete los campos obligatorios.")
                    
        st.markdown("### Empleados del Sistema")
        st.dataframe(obtener_empleados(), use_container_width=True, hide_index=True)