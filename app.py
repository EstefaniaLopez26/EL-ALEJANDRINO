import streamlit as st
import os
import pandas as pd

# IMPORTACIONES MODULARES
from database.db_manager import init_db, obtener_libros_activos
from modules.tienda_publica import (
    ventana_carrito_pasarela, ventana_solicitud_prestamo,
    vista_tienda_publica, mostrar_imagen_banner_con_recomendados,
    vista_catalogo_tienda, mostrar_landing_sobre_nosotros
)
from modules.seguridad_auth import vista_gestion_empleados, vista_auditoria
from modules.catalogos_crud import vista_clientes, vista_catalogo_inventario, vista_proveedores_entradas
from modules.biblioteca_prestamos import vista_prestamos
from modules.ventas_facturacion import vista_ventas_caja, vista_anulaciones_reportes

st.set_page_config(
    page_title="Librería Alejandrino",
    page_icon="assets/logo.png",
    layout="wide"
)
def cargar_css(ruta_css):
    if os.path.exists(ruta_css):
        with open(ruta_css, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

cargar_css("assets/style.css")
conn = init_db()

# CONTROL DE SESIÓN (Carrito en memoria, sin Base de Datos)
if 'usuario_autenticado' not in st.session_state:
    st.session_state['usuario_autenticado'] = False
    st.session_state['user_data'] = None
    st.session_state['tipo_usuario'] = None
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = []  # El carrito ahora vive en la memoria, cero errores.
if 'cupon_activo' not in st.session_state:
    st.session_state['cupon_activo'] = 0.0
if 'codigo_cupon_texto' not in st.session_state:
    st.session_state['codigo_cupon_texto'] = ""
if 'vista_actual' not in st.session_state:
    st.session_state['vista_actual'] = "tienda" 
if 'libro_alquiler_sel' not in st.session_state:
    st.session_state['libro_alquiler_sel'] = None

# CAPTURAR CLICS DENTRO DEL BANNER ANIMADO
params = st.query_params
if "accion" in params and "isbn" in params:
    accion_url = params["accion"]
    isbn_url = params["isbn"]
    df_b = pd.read_sql_query("SELECT * FROM libros WHERE isbn = ?", conn, params=(isbn_url,))
    if not df_b.empty:
        libro_elegido = df_b.iloc[0].to_dict()
        if accion_url == "comprar":
            st.session_state['carrito'].append(libro_elegido)
            st.session_state['vista_actual'] = "ventana_carrito"
        elif accion_url == "alquilar":
            st.session_state['libro_alquiler_sel'] = libro_elegido
            st.session_state['vista_actual'] = "ventana_prestamo"
    st.query_params.clear()
    st.rerun()

# CABECERA GLOBAL (Logo y Botón Carrito)
col_logo, col_azul, col_cart = st.columns([1.4, 4.3, 1.3], vertical_alignment="center")
with col_logo:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_container_width=True)
    else:
        st.markdown("### 📚 El Alejandrino")
with col_azul:
    st.markdown('<div class="franja-azul-limpia"></div>', unsafe_allow_html=True)
with col_cart:
    cant_c = len(st.session_state['carrito'])
    suma_c = sum(item['precioVenta'] for item in st.session_state['carrito'])
    if st.button(f"🛒 Carrito ({cant_c}) • $ {suma_c:,.0f}", use_container_width=True):
        st.session_state['vista_actual'] = "ventana_carrito"
        st.rerun()

# ENRUTADOR PRINCIPAL
if st.session_state['vista_actual'] == "ventana_carrito":
    ventana_carrito_pasarela(conn)
elif st.session_state['vista_actual'] == "ventana_prestamo":
    ventana_solicitud_prestamo(conn)
elif not st.session_state['usuario_autenticado']:
    vista_tienda_publica(conn)
else:
    tipo = st.session_state['tipo_usuario']
    user = st.session_state['user_data']
    rol = user['rol']
    
    if rol == "Administrador":
        opciones_menu = ["🏠 Resumen Ejecutivo", "📖 Catálogo e Inventario", "📦 Proveedores y Entradas", "👥 Directorio de Clientes", "📚 Préstamos Bibliotecarios", "💰 Punto de Venta y Facturación", "📊 Finanzas, Notas Crédito y Ranking", "👔 Equipo y Roles", "🛡️ Bitácora de Seguridad"]
    elif rol == "Vendedor":
        opciones_menu = ["💰 Punto de Venta y Facturación", "👥 Directorio de Clientes", "📖 Consultar Catálogo"]
    elif rol == "Bibliotecario":
        opciones_menu = ["📚 Préstamos Bibliotecarios", "👥 Directorio de Clientes", "📖 Consultar Catálogo"]
    elif rol == "Almacenista":
        opciones_menu = ["📖 Catálogo e Inventario", "📦 Proveedores y Entradas"]
    else:
        opciones_menu = ["🏠 Explorar Tienda", "🛒 Ir a Mi Carrito y Pasarela", "📚 Mis Préstamos y Facturas"]

    with st.sidebar:
        st.markdown("### 👤 Sesión Activa")
        st.write(f"**{user['nombre']}**")
        st.caption(f"Perfil: `{rol}`")
        st.markdown("---")
        menu = st.radio("Navegación", opciones_menu)
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión"):
            st.session_state['usuario_autenticado'] = False
            st.session_state['user_data'] = None
            st.session_state['tipo_usuario'] = None
            st.session_state['vista_actual'] = "tienda"
            st.session_state['carrito'] = []
            st.rerun()

    # Ruteo por Rol
    if tipo == 'empleado':
        if menu == "🏠 Resumen Ejecutivo":
            st.header(f"Panel Gerencial • {user['nombre']}")
        elif "Catálogo" in menu: vista_catalogo_inventario(conn, user)
        elif "Proveedores" in menu: vista_proveedores_entradas(conn, user)
        elif "Clientes" in menu: vista_clientes(conn, user)
        elif "Préstamos" in menu: vista_prestamos(conn, user)
        elif "Punto de Venta" in menu: vista_ventas_caja(conn, user)
        elif "Finanzas" in menu: vista_anulaciones_reportes(conn, user)
        elif "Equipo" in menu: vista_gestion_empleados(conn, user)
        elif "Bitácora" in menu: vista_auditoria(conn)
    else:
        if menu == "🏠 Explorar Tienda":
            df_libros = obtener_libros_activos(conn)
            mostrar_imagen_banner_con_recomendados(df_libros)
            vista_catalogo_tienda(conn, df_libros)
            mostrar_landing_sobre_nosotros()
        elif menu == "🛒 Ir a Mi Carrito y Pasarela":
            st.session_state['vista_actual'] = "ventana_carrito"
            st.rerun()
        elif "Mis Préstamos" in menu:
            st.subheader("📚 Mis Préstamos y Facturas")