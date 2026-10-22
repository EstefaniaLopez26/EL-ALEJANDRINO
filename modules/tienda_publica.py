import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64
import os

from database.db_manager import encriptar_password, registrar_auditoria, obtener_libros_activos
from modules.seguridad_auth import vista_login_recuperacion
from modules.ventas_facturacion import CODIGOS_PROMO

# Imagen corporativa de respaldo elegante para cuando el ISBN no tenga carátula disponible
FALLBACK_COVER = "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400"

@st.cache_data
def obtener_banner_base64():
    if os.path.exists("assets/banner.png"):
        with open("assets/banner.png", "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

def mostrar_imagen_banner_con_recomendados(df_todos):
    indices_top = [0, 8, 16, 30, 32, 38, 45, 59, 73, 83]
    destacados = df_todos.iloc[[i for i in indices_top if i < len(df_todos)]]
    if destacados.empty:
        destacados = df_todos.head(8)

    libros_carrusel = pd.concat([destacados, destacados])
    items_html = ""
    for _, r in libros_carrusel.iterrows():
        items_html += (
            f'<div class="item-recomendado-banner">'
            f'<img src="{r["portada"]}" alt="{r["titulo"]}">'
            f'<div class="item-recomendado-info">'
            f'<div>'
            f'<div style="font-size:0.64rem; color:#E6C687; font-weight:700; text-transform:uppercase;">★ {r["categoria"]}</div>'
            f'<div style="font-family:\'Playfair Display\',serif; font-weight:700; font-size:0.92rem; color:#FFF; line-height:1.2; margin:2px 0; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;">{r["titulo"]}</div>'
            f'<div style="font-size:0.75rem; color:#CBD5E1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{r["autor"]}</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size:0.98rem; font-weight:800; color:#E6C687;">$ {r["precioVenta"]:,.0f} COP</div>'
            f'<div class="botones-dentro-banner">'
            f'<a href="?accion=comprar&isbn={r["isbn"]}" target="_self" class="link-accion-banner link-comprar">🛒 Comprar</a>'
            f'<a href="?accion=alquilar&isbn={r["isbn"]}" target="_self" class="link-accion-banner link-alquilar">📚 Alquilar</a>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )

    banner_b64 = obtener_banner_base64()
    bg_css = f"background-image: url('data:image/png;base64,{banner_b64}');" if banner_b64 else "background: linear-gradient(120deg, #14213D, #1B2A4A);"

    html_completo = (
        f'<div class="contenedor-imagen-banner">'
        f'<div class="imagen-banner-fondo" style="{bg_css}"></div>'
        f'<div class="capa-libros-dentro-banner">'
        f'<div class="etiqueta-superior-banner">'
        f'<span style="background:#E6C687; color:#14213D; padding:3px 12px; border-radius:20px; font-size:0.74rem; font-weight:800;">🌟 RECOMENDADOS DEL MOMENTO</span>'
        f'<span style="font-size:0.78rem; color:#F8FAFC; background:rgba(20,33,61,0.75); padding:3px 12px; border-radius:20px;">Pasa el cursor aquí para pausar y seleccionar tu libro</span>'
        f'</div>'
        f'<div class="carrusel-pista">{items_html}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html_completo, unsafe_allow_html=True)

def mostrar_landing_sobre_nosotros():
    html_landing = (
        '<div class="landing-footer-azul">'
        '<div style="text-align:center; max-width:800px; margin:0 auto;">'
        '<span style="color:#E6C687; font-size:0.78rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase;">CONOCE NUESTRA ESENCIA</span>'
        '<h2 style="color:#FFFFFF; margin:6px 0 10px 0; font-size:1.85rem;">Sobre Librería & Biblioteca El Alejandrino</h2>'
        '<p style="color:#CBD5E1; font-size:0.95rem; line-height:1.6;">'
        'Somos un espacio cultural y literario dedicado a conectar a los lectores con las grandes obras del pensamiento universal, '
        'la literatura latinoamericana y el conocimiento técnico, integrando venta en línea y servicio de préstamo bibliotecario.'
        '</p>'
        '</div>'
        '<div class="landing-grid">'
        '<div class="landing-card">'
        '<h4>🏛️ Nuestra Misión</h4>'
        '<p>Promover la lectura, la educación y la cultura en toda Colombia mediante una plataforma moderna, accesible y segura que integra un catálogo curado de obras originales con servicios ágiles de adquisición y préstamo bibliotecario.</p>'
        '</div>'
        '<div class="landing-card">'
        '<h4>🌟 Nuestra Visión</h4>'
        '<p>Consolidarnos hacia el 2030 como el ecosistema literario y bibliotecario digital referente a nivel nacional, reconocido por nuestra excelencia en el servicio al lector, innovación tecnológica y compromiso con el desarrollo cultural.</p>'
        '</div>'
        '<div class="landing-card">'
        '<h4>🤝 Nuestros Valores</h4>'
        '<p>• Catálogo con más de 100 títulos originales.<br>• Préstamos bibliotecarios flexibles.<br>• Facturación electrónica legal y pagos seguros.<br>• Atención personalizada a lectores e instituciones.</p>'
        '</div>'
        '</div>'
        '<div style="border-top:1px solid rgba(255,255,255,0.12); padding-top:16px; display:flex; justify-content:space-between; align-items:center; font-size:0.82rem; color:#94A3B8;">'
        '<div>📍 Sede Principal: Duitama & Bogotá, Colombia • 📞 Atención al Lector: (608) 760-0000 • ✉️ contacto@alejandrino.com</div>'
        '<div>© 2026 Librería El Alejandrino • Todos los derechos reservados</div>'
        '</div>'
        '</div>'
    )
    st.markdown(html_landing, unsafe_allow_html=True)

def vista_catalogo_tienda(conn, df_todos):
    f_col1, f_col2, f_col3, f_col4 = st.columns([2.3, 1.5, 1.2, 1])
    busqueda = f_col1.text_input("🔍 Buscar por título, autor, editorial o ISBN...", placeholder="Ej: Gabriel García Márquez, Clean Code, Dune...")
    categorias_disp = ["Todas las Categorías"] + sorted(df_todos['categoria'].unique().tolist())
    cat_sel = f_col2.selectbox("📂 Categoría Literaria", categorias_disp)
    orden_sel = f_col3.selectbox("↕️ Ordenar por", ["Destacados", "Menor Precio", "Mayor Precio", "Título (A-Z)", "Más Recientes"])
    libros_por_pag = f_col4.selectbox("Mostrar", [12, 24, 48, 100], index=1)

    df_filtrado = df_todos.copy()
    if busqueda:
        df_filtrado = df_filtrado[
            df_filtrado['isbn'].str.contains(busqueda, case=False) |
            df_filtrado['titulo'].str.contains(busqueda, case=False) |
            df_filtrado['autor'].str.contains(busqueda, case=False) |
            df_filtrado['editorial'].str.contains(busqueda, case=False)
        ]
    if cat_sel != "Todas las Categorías":
        df_filtrado = df_filtrado[df_filtrado['categoria'] == cat_sel]

    if orden_sel == "Menor Precio":
        df_filtrado = df_filtrado.sort_values(by="precioVenta", ascending=True)
    elif orden_sel == "Mayor Precio":
        df_filtrado = df_filtrado.sort_values(by="precioVenta", ascending=False)
    elif orden_sel == "Título (A-Z)":
        df_filtrado = df_filtrado.sort_values(by="titulo", ascending=True)
    elif orden_sel == "Más Recientes":
        df_filtrado = df_filtrado.sort_values(by="anioPublicacion", ascending=False)

    st.caption(f"Mostrando **{min(len(df_filtrado), libros_por_pag)}** de **{len(df_filtrado)}** títulos disponibles en la librería.")

    if not df_filtrado.empty:
        cols = st.columns(4)
        for idx, (_, row) in enumerate(df_filtrado.head(libros_por_pag).iterrows()):
            with cols[idx % 4]:
                card_html = (
                    f'<div class="tarjeta-libro">'
                    f'<div>'
                    f'<span class="badge-categoria">{row["categoria"]}</span>'
                    f'<img src="{row["portada"]}" alt="{row["titulo"]}" style="width: 100%; height: 180px; object-fit: contain; background-color: #F7F4EE; border-radius: 8px; padding: 6px; margin-bottom: 6px;">'
                    f'<div class="titulo-clamp">{row["titulo"]}</div>'
                    f'<p style="color:#555; font-size:0.82rem; margin:2px 0;">{row["autor"]} ({row["anioPublicacion"]})</p>'
                    f'<p style="color:#888; font-size:0.73rem; margin:0;">{row["editorial"]}</p>'
                    f'</div>'
                    f'<div>'
                    f'<p class="precio-libro">$ {row["precioVenta"]:,.0f} COP</p>'
                    f'<p style="font-size:0.76rem; color:#2E7D32; font-weight:600; margin:4px 0 8px 0;">● {row["stockDisponible"]} disponibles</p>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)
                btn_col1, btn_col2 = st.columns(2)
                if btn_col1.button("🛒 Comprar", key=f"pub_buy_{row['id']}"):
                    st.session_state['carrito'].append(row.to_dict())
                    st.session_state['vista_actual'] = "ventana_carrito"
                    st.rerun()
                if btn_col2.button("📚 Alquilar", key=f"pub_rent_{row['id']}"):
                    st.session_state['libro_alquiler_sel'] = row.to_dict()
                    st.session_state['vista_actual'] = "ventana_prestamo"
                    st.rerun()
    else:
        st.info("No se encontraron libros con los filtros seleccionados.")

def vista_tienda_publica(conn):
    df_todos = obtener_libros_activos(conn)
    mostrar_imagen_banner_con_recomendados(df_todos)

    tab_catalogo, tab_login, tab_registro = st.tabs([
        "📖 Explorar Catálogo", 
        "🔐 Iniciar Sesión",
        "📝 Crear Cuenta de Lector"
    ])
    with tab_catalogo:
        vista_catalogo_tienda(conn, df_todos)
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            n_col1, n_col2 = st.columns([1.8, 1.2], vertical_alignment="center")
            with n_col1:
                st.markdown("### 💌 Suscríbete a Noticias y Cupones Literarios")
                st.write("Ingresa tu correo para recibir novedades y activar automáticamente un **cupón del 15% de descuento (`BIENVENIDO15`)**.")
            with n_col2:
                with st.form("form_newsletter_cupon", clear_on_submit=True):
                    correo_news = st.text_input("Correo Electrónico", placeholder="tu.correo@ejemplo.com")
                    if st.form_submit_button("🎁 Recibir Cupón de 15% DCTO"):
                        if correo_news and "@" in correo_news:
                            c = conn.cursor()
                            c.execute("INSERT OR IGNORE INTO suscriptores_newsletter (correo, cupon_generado, fechaHora) VALUES (?, 'BIENVENIDO15', ?)",
                                      (correo_news.strip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            conn.commit()
                            st.session_state['cupon_activo'] = 15.0
                            st.session_state['codigo_cupon_texto'] = "BIENVENIDO15"
                            st.success("🎉 ¡Cupón **BIENVENIDO15** activado!")
                        else:
                            st.warning("Ingresa un correo electrónico válido.")

    with tab_login:
        vista_login_recuperacion(conn)

    with tab_registro:
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("### 📝 Crear Cuenta de Cliente / Lector")
            with st.form("form_reg_publico", clear_on_submit=True):
                cedula = st.text_input("Cédula / NIT")
                nombres = st.text_input("Nombres")
                apellidos = st.text_input("Apellidos")
                telefono = st.text_input("Teléfono Móvil")
                correo = st.text_input("Correo Electrónico")
                password = st.text_input("Contraseña", type="password")
                direccion = st.text_input("Dirección y Ciudad de Entrega")
                if st.form_submit_button("Registrarme Ahora"):
                    if cedula and nombres and correo and password:
                        try:
                            c = conn.cursor()
                            c.execute("""
                                INSERT INTO clientes (cedula, nombres, apellidos, telefono, correo, password, direccion, activo)
                                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                            """, (cedula.strip(), nombres, apellidos, telefono, correo.strip(), encriptar_password(password), direccion))
                            conn.commit()
                            registrar_auditoria(conn, f"{nombres} {apellidos}", "Cliente", "Clientes", "AUTORREGISTRO", f"Lector registrado ({cedula})")
                            st.success("¡Cuenta creada exitosamente! Ya puedes iniciar sesión.")
                        except Exception:
                            st.error("El documento o el correo electrónico ya se encuentran registrados.")
                    else:
                        st.warning("Completa todos los campos obligatorios.")
                        
    mostrar_landing_sobre_nosotros()

def ventana_carrito_pasarela(conn):
    c_volver, c_tit = st.columns([1.3, 4.7], vertical_alignment="center")
    if c_volver.button("⬅️ Volver a la Tienda", use_container_width=True):
        st.session_state['vista_actual'] = "tienda"
        st.rerun()
    c_tit.markdown("## 🛍️ Carrito de Compras y Pasarela de Pago Segura")
    st.markdown("---")

    if not st.session_state['carrito']:
        st.info("Tu carrito de compras está vacío en este momento. Regresa a la tienda para elegir tus obras favoritas.")
        return

    col_resumen, col_pasarela = st.columns([1.25, 1])
    with col_resumen:
        st.markdown("### 📚 Obras Seleccionadas")
        df_c = pd.DataFrame(st.session_state['carrito'])
        st.dataframe(df_c[['isbn', 'titulo', 'autor', 'editorial', 'precioVenta']], use_container_width=True, hide_index=True)
        
        cp1, cp2, cp3 = st.columns([2, 1, 1])
        cupon_in = cp1.text_input("🎟️ Cupón de Descuento", value=st.session_state['codigo_cupon_texto'], placeholder="Ej: BIENVENIDO15")
        if cp2.button("Aplicar Cupón"):
            cod_u = cupon_in.strip().upper()
            descuentos = {**CODIGOS_PROMO, "BIENVENIDO15": 15.0}
            if cod_u in descuentos:
                st.session_state['cupon_activo'] = descuentos[cod_u]
                st.session_state['codigo_cupon_texto'] = cod_u
                st.success(f"Cupón {cod_u} aplicado.")
            else:
                st.error("Cupón no válido.")
        if cp3.button("🗑️ Vaciar Carrito"):
            st.session_state['carrito'] = []
            st.session_state['cupon_activo'] = 0.0
            st.rerun()

        sub_b = round(float(df_c['precioVenta'].sum()), 2)
        desc_v = round(sub_b * (st.session_state['cupon_activo'] / 100.0), 2)
        base_g = round(sub_b - desc_v, 2)
        iva_v = round(base_g * 0.19, 2)
        tot_v = round(base_g + iva_v, 2)

        with st.container(border=True):
            st.markdown(f"""
            #### 🧾 Detalle de Facturación
            - **Subtotal Bruto:** `$ {sub_b:,.2f} COP`
            - **Descuento ({st.session_state['cupon_activo']}%):** `- $ {desc_v:,.2f} COP`
            - **Base Gravable:** `$ {base_g:,.2f} COP`
            - **IVA Legal (19%):** `$ {iva_v:,.2f} COP`
            - ### **Total a Pagar: $ {tot_v:,.2f} COP**
            """)

    with col_pasarela:
        with st.container(border=True):
            st.markdown("### 💳 Pasarela de Pago en Línea")
            with st.form("form_pasarela_ventana"):
                u_act = st.session_state.get('user_data') or {}
                nom_p = st.text_input("Nombre Completo del Comprador", value=u_act.get('nombre', ''))
                ced_p = st.text_input("Cédula / NIT", value=u_act.get('cedula', ''))
                cor_p = st.text_input("Correo Electrónico para Factura", value=u_act.get('correo', ''))
                dir_p = st.text_input("Dirección de Entrega y Ciudad", placeholder="Calle 16 # 14-22, Duitama")
                met_p = st.selectbox("Selecciona tu Medio de Pago", [
                    "💳 Tarjeta de Crédito / Débito (Visa, Mastercard, Amex)",
                    "🏦 PSE - Débito desde Cuenta Bancaria",
                    "📱 Billetera Digital (Nequi / Daviplata)",
                    "💵 Pago Contra Entrega"
                ])
                ref_p = st.text_input("Número de Tarjeta / Celular (Simulado)", placeholder="**** **** **** 4242")
                
                if st.form_submit_button("🔒 Confirmar Pago y Emitir Factura"):
                    if not nom_p or not ced_p or not dir_p:
                        st.error("Por favor completa tu nombre, documento y dirección de envío.")
                    else:
                        c = conn.cursor()
                        f_h = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        medio_bd = "Tarjeta" if "Tarjeta" in met_p else ("Transferencia" if "PSE" in met_p or "Nequi" in met_p else "Efectivo")
                        c.execute("INSERT INTO ventas (cliente_id, empleado_id, fechaHora, subtotal, descuento, iva, total, estado) VALUES (1, 1, ?, ?, ?, ?, ?, 'Pagada')",
                                  (f_h, base_g, desc_v, iva_v, tot_v))
                        v_id = c.lastrowid
                        for item in st.session_state['carrito']:
                            c.execute("INSERT INTO detalle_ventas (venta_id, isbn, titulo, cantidad, precioUnitario, subtotalLinea) VALUES (?, ?, ?, 1, ?, ?)",
                                      (v_id, item['isbn'], item['titulo'], item['precioVenta'], item['precioVenta']))
                            c.execute("UPDATE libros SET stockDisponible = MAX(0, stockDisponible - 1) WHERE isbn = ?", (item['isbn'],))
                        num_f = f"FACT-{v_id:05d}"
                        c.execute("""
                            INSERT INTO facturas (numeroFactura, venta_id, cliente_cedula, cliente_nombre, fechaEmision, subtotal, descuento, iva19, totalPagar, medioPago, montoRecibido, estado)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pagada')
                        """, (num_f, v_id, ced_p, nom_p, f_h, base_g, desc_v, iva_v, tot_v, medio_bd, tot_v))
                        conn.commit()
                        registrar_auditoria(conn, nom_p, "Cliente", "Pasarela Online", "COMPRA_APROBADA", f"Factura {num_f} por ${tot_v:,.2f}")
                        st.session_state['carrito'] = []
                        st.session_state['cupon_activo'] = 0.0
                        st.balloons()
                        st.success(f"🎉 ¡Transacción aprobada! Se generó tu Factura Legal **{num_f}** por **$ {tot_v:,.2f} COP**.")

def ventana_solicitud_prestamo(conn):
    lib_p = st.session_state['libro_alquiler_sel']
    c_volver, c_tit = st.columns([1.3, 4.7], vertical_alignment="center")
    if c_volver.button("⬅️ Volver a la Tienda", use_container_width=True):
        st.session_state['vista_actual'] = "tienda"
        st.session_state['libro_alquiler_sel'] = None
        st.rerun()
    c_tit.markdown(f"## 📚 Solicitud de Préstamo Bibliotecario")
    st.markdown("---")

    col_img, col_form = st.columns([1, 2])
    with col_img:
        st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:12px; border:1px solid #E6E2D8; text-align:center;">
                <img src="{lib_p['portada']}" onerror="this.src='{FALLBACK_COVER}'" style="height:240px; object-fit:contain; margin-bottom:10px;">
                <h4>{lib_p['titulo']}</h4>
                <p style="color:#666;">{lib_p['autor']} • {lib_p['editorial']}</p>
            </div>
        """, unsafe_allow_html=True)
    with col_form:
        with st.form("form_alquiler_ventana"):
            u_act = st.session_state.get('user_data') or {}
            ced_l = st.text_input("Cédula de Ciudadanía del Lector", value=u_act.get('cedula', ''))
            nom_l = st.text_input("Nombre Completo", value=u_act.get('nombre', ''))
            dias_l = st.selectbox("Tiempo de Préstamo Solicitado", [7, 14, 21], format_func=lambda d: f"{d} días calendario")
            if st.form_submit_button("✅ Confirmar Préstamo Bibliotecario"):
                if not ced_l or not nom_l:
                    st.warning("Por favor ingresa tu documento y nombre completo.")
                else:
                    hoy_s = datetime.now().strftime("%Y-%m-%d")
                    f_lim = (datetime.now() + timedelta(days=int(dias_l))).strftime("%Y-%m-%d")
                    id_pr = f"PR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO prestamos (idPrestamo, cliente_id, cedula_cliente, nombre_cliente, isbn, titulo_libro, empleado_id, fechaSalida, fechaLimite, estado, multa)
                        VALUES (?, 1, ?, ?, ?, ?, 3, ?, ?, 'Activo', 0.0)
                    """, (id_pr, ced_l.strip(), nom_l.strip(), lib_p['isbn'], lib_p['titulo'], hoy_s, f_lim))
                    c.execute("UPDATE libros SET stockDisponible = MAX(0, stockDisponible - 1) WHERE isbn = ?", (lib_p['isbn'],))
                    conn.commit()
                    registrar_auditoria(conn, nom_l, "Cliente", "Préstamos", "RESERVA_WEB", f"Préstamo {id_pr} ({lib_p['titulo']})")
                    st.success(f"🎉 ¡Préstamo **{id_pr}** registrado exitosamente! Límite de devolución: **{f_lim}**.")