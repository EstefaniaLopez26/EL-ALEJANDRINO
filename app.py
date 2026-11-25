import streamlit as st
import os
import pandas as pd
from datetime import datetime

# IMPORTACIONES MODULARES
from database.db_manager import init_db, obtener_libros_activos
from modules.tienda_publica import (
    ventana_carrito_pasarela, ventana_solicitud_prestamo,
    vista_tienda_publica, mostrar_imagen_banner_con_recomendados,
    vista_catalogo_tienda, mostrar_landing_sobre_nosotros
)
from modules.seguridad_auth import vista_gestion_empleados, vista_auditoria
from modules.catalogos_crud import vista_clientes, vista_catalogo_inventario, vista_proveedores_entradas
from modules.biblioteca_prestamos import vista_prestamos, VALOR_MULTA_DIA
from modules.ventas_facturacion import vista_ventas_caja, vista_anulaciones_reportes
from modules.generador_pdf import generar_factura_pdf

st.set_page_config(
    page_title="Librería Alejandrino",
    page_icon="assets/logo.png",
    layout="wide"
)


def cargar_css(ruta_css):
    if os.path.exists(ruta_css):
        with open(ruta_css, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def vista_resumen_ejecutivo(conn, user):
    st.header(f"Panel Gerencial • {user['nombre']}")
    st.caption(f"Vista consolidada al {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    hoy_str = datetime.now().strftime("%Y-%m-%d")
    mes_actual = datetime.now().strftime("%Y-%m")

    df_fact = pd.read_sql_query("SELECT * FROM facturas WHERE estado='Pagada'", conn)
    df_lib = pd.read_sql_query("SELECT * FROM libros WHERE activo=1", conn)
    df_pres = pd.read_sql_query("SELECT * FROM prestamos WHERE estado='Activo'", conn)

    recaudo_mes = 0.0
    if not df_fact.empty:
        df_fact_mes = df_fact[df_fact['fechaEmision'].str.startswith(mes_actual)]
        recaudo_mes = float(df_fact_mes['totalPagar'].sum())

    total_unidades = int(df_lib['stockDisponible'].sum()) if not df_lib.empty else 0
    df_stock_bajo = df_lib[df_lib['stockDisponible'] <= df_lib['stockMinimo']] if not df_lib.empty else pd.DataFrame()
    prestamos_vencidos = df_pres[df_pres['fechaLimite'] < hoy_str] if not df_pres.empty else pd.DataFrame()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Recaudo Mes ({mes_actual})", f"$ {recaudo_mes:,.0f}")
    c2.metric("Inventario Disponible", f"{total_unidades:,} uds", f"{len(df_lib)} títulos")
    c3.metric("Préstamos Activos", len(df_pres), f"{len(prestamos_vencidos)} vencidos", delta_color="inverse")
    c4.metric("Alertas Stock Mínimo", len(df_stock_bajo), "Requieren reposición" if len(df_stock_bajo) > 0 else "Óptimo", delta_color="inverse")

    st.markdown("---")
    col_izq, col_der = st.columns([1.2, 1])

    with col_izq:
        st.subheader("🏆 Top 5 Obras Más Vendidas")
        df_top = pd.read_sql_query("""
            SELECT dv.titulo AS Obra, SUM(dv.cantidad) AS Unidades, SUM(dv.subtotalLinea) AS Ingresos
            FROM detalle_ventas dv
            JOIN ventas v ON dv.venta_id = v.id
            WHERE v.estado = 'Pagada'
            GROUP BY dv.titulo
            ORDER BY Unidades DESC
            LIMIT 5
        """, conn)
        if not df_top.empty:
            st.dataframe(df_top, use_container_width=True, hide_index=True)
        else:
            st.info("Aún no hay ventas registradas.")

        st.subheader("⏰ Préstamos Vencidos Pendientes")
        if not prestamos_vencidos.empty:
            st.dataframe(
                prestamos_vencidos[['idPrestamo', 'nombre_cliente', 'cedula_cliente', 'titulo_libro', 'fechaLimite']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("No hay préstamos vencidos a la fecha.")

    with col_der:
        st.subheader("⚠️ Alerta de Inventario Bajo")
        if not df_stock_bajo.empty:
            st.dataframe(
                df_stock_bajo[['isbn', 'titulo', 'stockDisponible', 'stockMinimo']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("Todos los títulos superan el umbral mínimo de stock.")


def vista_portal_cliente(conn, user):
    st.subheader(f"📚 Mis Préstamos y Facturas • {user['nombre']}")
    cedula_cli = user.get('cedula', '')

    tab_mis_pres, tab_mis_fact = st.tabs(["📖 Mis Préstamos Bibliotecarios", "🧾 Mis Facturas de Compra"])

    with tab_mis_pres:
        df_mis_p = pd.read_sql_query(
            """SELECT idPrestamo, isbn, titulo_libro, fechaSalida, fechaLimite, fechaDevolucion, estado, multa
               FROM prestamos WHERE cedula_cliente = ? ORDER BY id DESC""",
            conn,
            params=(cedula_cli,)
        )
        if df_mis_p.empty:
            st.info("Aún no tienes préstamos bibliotecarios registrados con tu documento.")
        else:
            hoy_dt = datetime.now().date()

            def calcular_mora_actual(row):
                if row['estado'] == 'Devuelto':
                    return float(row['multa'])
                f_lim = datetime.strptime(row['fechaLimite'], "%Y-%m-%d").date()
                dias = (hoy_dt - f_lim).days
                return max(0.0, dias * VALOR_MULTA_DIA)

            df_mis_p['Mora Estimada ($)'] = df_mis_p.apply(calcular_mora_actual, axis=1)
            st.dataframe(df_mis_p, use_container_width=True, hide_index=True)

    with tab_mis_fact:
        df_mis_f = pd.read_sql_query(
            """SELECT numeroFactura, venta_id, fechaEmision, subtotal, descuento, iva19, totalPagar, medioPago, estado
               FROM facturas WHERE cliente_cedula = ? ORDER BY id DESC""",
            conn,
            params=(cedula_cli,)
        )
        if df_mis_f.empty:
            st.info("Aún no registras compras en nuestra tienda.")
        else:
            st.dataframe(
                df_mis_f[['numeroFactura', 'fechaEmision', 'subtotal', 'descuento', 'iva19', 'totalPagar', 'medioPago', 'estado']],
                use_container_width=True,
                hide_index=True
            )

            fact_sel = st.selectbox("Seleccionar factura para descargar PDF", df_mis_f['numeroFactura'].tolist())
            if fact_sel:
                row_f = df_mis_f[df_mis_f['numeroFactura'] == fact_sel].iloc[0]
                ruta_pdf = os.path.join("facturas_pdf", f"{fact_sel}.pdf")

                if not os.path.exists(ruta_pdf):
                    df_det = pd.read_sql_query(
                        "SELECT isbn, titulo, cantidad, precioUnitario, subtotalLinea FROM detalle_ventas WHERE venta_id = ?",
                        conn,
                        params=(int(row_f['venta_id']),)
                    )
                    datos_v = {
                        'numero_factura': row_f['numeroFactura'],
                        'cliente_nombre': user['nombre'],
                        'cliente_cedula': cedula_cli,
                        'fecha': str(row_f['fechaEmision'])[:10],
                        'subtotal': float(row_f['subtotal']),
                        'descuento': float(row_f['descuento']),
                        'iva': float(row_f['iva19']),
                        'total': float(row_f['totalPagar'])
                    }
                    ruta_pdf = generar_factura_pdf(datos_v, df_det.to_dict(orient='records'), ruta_salida=ruta_pdf)

                with open(ruta_pdf, "rb") as f_pdf:
                    st.download_button(
                        label=f"📄 Descargar {fact_sel} (PDF)",
                        data=f_pdf,
                        file_name=f"{fact_sel}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )


cargar_css("assets/style.css")
conn = init_db()

if 'usuario_autenticado' not in st.session_state:
    st.session_state['usuario_autenticado'] = False
    st.session_state['user_data'] = None
    st.session_state['tipo_usuario'] = None
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = []
if 'cupon_activo' not in st.session_state:
    st.session_state['cupon_activo'] = 0.0
if 'codigo_cupon_texto' not in st.session_state:
    st.session_state['codigo_cupon_texto'] = ""
if 'vista_actual' not in st.session_state:
    st.session_state['vista_actual'] = "tienda"
if 'libro_alquiler_sel' not in st.session_state:
    st.session_state['libro_alquiler_sel'] = None

params = st.query_params
if "accion" in params and "isbn" in params:
    accion_url = params["accion"]
    isbn_url = params["isbn"]
    df_b = pd.read_sql_query("SELECT * FROM libros WHERE isbn = ? AND activo = 1", conn, params=(isbn_url,))
    if not df_b.empty:
        libro_elegido = df_b.iloc[0].to_dict()
        if int(libro_elegido.get('stockDisponible', 0)) > 0:
            if accion_url == "comprar":
                st.session_state['carrito'].append(libro_elegido)
                st.session_state['vista_actual'] = "ventana_carrito"
            elif accion_url == "alquilar":
                st.session_state['libro_alquiler_sel'] = libro_elegido
                st.session_state['vista_actual'] = "ventana_prestamo"
    st.query_params.clear()
    st.rerun()

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
        opciones_menu = [
            "🏠 Resumen Ejecutivo", "📖 Catálogo e Inventario", "📦 Proveedores y Entradas",
            "👥 Directorio de Clientes", "📚 Préstamos Bibliotecarios", "💰 Punto de Venta y Facturación",
            "📊 Finanzas, Notas Crédito y Ranking", "👔 Equipo y Roles", "🛡️ Bitácora de Seguridad"
        ]
    elif rol == "Vendedor":
        opciones_menu = ["💰 Punto de Venta y Facturación", "👥 Directorio de Clientes", "📖 Consultar Catálogo"]
    elif rol == "Bibliotecario":
        opciones_menu = ["📚 Préstamos Bibliotecarios", "👥 Directorio de Clientes", "📖 Consultar Catálogo"]
    elif rol == "Almacenista":
        opciones_menu = ["📖 Catálogo e Inventario", "📦 Proveedores y Entradas"]
    else:
        opciones_menu = ["🏠 Explorar Tienda", "🛒 Ir a Mi Carrito y Pasarela", "📚 Mis Préstamos y Facturas"]

    with st.sidebar:
        st.markdown(
            f"""
            <div style='
                color: #14213D; 
                font-family: "Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif; 
                font-size: 18px; 
                font-weight: 600; 
                letter-spacing: 0.5px;
                padding-bottom: 10px;
            '>
                👤 Perfil activo: {rol}
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write(f"**{user['nombre']}**")
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
            vista_resumen_ejecutivo(conn, user)
        elif "Catálogo" in menu:
            vista_catalogo_inventario(conn, user)
        elif "Proveedores" in menu:
            vista_proveedores_entradas(conn, user)
        elif "Clientes" in menu:
            vista_clientes(conn, user)
        elif "Préstamos" in menu:
            vista_prestamos(conn, user)
        elif "Punto de Venta" in menu:
            vista_ventas_caja(conn, user)
        elif "Finanzas" in menu:
            vista_anulaciones_reportes(conn, user)
        elif "Equipo" in menu:
            vista_gestion_empleados(conn, user)
        elif "Bitácora" in menu:
            vista_auditoria(conn)
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
            vista_portal_cliente(conn, user)