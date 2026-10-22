import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from database.db_manager import encriptar_password, registrar_auditoria

def vista_clientes(conn, user):
    st.header("👥 Directorio de Clientes y Lectores")
    t_con, t_reg, t_act = st.tabs(["🔍 Directorio Activo", "➕ Registrar Nuevo Cliente", "✏️ Editar Datos"])
    
    with t_con:
        busq = st.text_input("Buscar por Cédula, Nombre, Apellido o Ciudad")
        df_c = pd.read_sql_query("SELECT id, cedula, nombres, apellidos, telefono, correo, direccion FROM clientes WHERE activo=1", conn)
        if busq:
            df_c = df_c[df_c['cedula'].str.contains(busq, case=False) | df_c['nombres'].str.contains(busq, case=False) | df_c['apellidos'].str.contains(busq, case=False) | df_c['direccion'].str.contains(busq, case=False)]
        st.dataframe(df_c, use_container_width=True, hide_index=True)

    with t_reg:
        with st.form("form_nuevo_cliente", clear_on_submit=True):
            c1, c2 = st.columns(2)
            cedula = c1.text_input("Cédula / NIT")
            nombres = c2.text_input("Nombres")
            apellidos = c1.text_input("Apellidos")
            telefono = c2.text_input("Teléfono")
            correo = c1.text_input("Correo Electrónico")
            direccion = c2.text_input("Dirección y Ciudad")
            password = c1.text_input("Contraseña Inicial", type="password", value="cliente123")
            
            if st.form_submit_button("Guardar Cliente"):
                if cedula and nombres and apellidos and correo:
                    try:
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO clientes (cedula, nombres, apellidos, telefono, correo, password, direccion, activo)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                        """, (cedula.strip(), nombres, apellidos, telefono, correo.strip(), encriptar_password(password), direccion))
                        conn.commit()
                        registrar_auditoria(conn, user['nombre'], user['rol'], "Clientes", "CREAR", f"Registró cliente {cedula}")
                        st.success("Cliente registrado exitosamente.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("El documento o correo ya se encuentra registrado.")
                else:
                    st.warning("Completa los campos obligatorios.")

    with t_act:
        df_cli = pd.read_sql_query("SELECT * FROM clientes", conn)
        if not df_cli.empty:
            ced_sel = st.selectbox("Seleccionar Cliente por Documento", df_cli['cedula'].tolist())
            row_c = df_cli[df_cli['cedula'] == ced_sel].iloc[0]
            with st.form("form_act_cli"):
                c1, c2 = st.columns(2)
                n_nom = c1.text_input("Nombres", value=row_c['nombres'])
                n_ape = c2.text_input("Apellidos", value=row_c['apellidos'])
                n_tel = c1.text_input("Teléfono", value=str(row_c['telefono'] or ''))
                n_cor = c2.text_input("Correo", value=row_c['correo'])
                n_dir = c1.text_input("Dirección", value=str(row_c['direccion'] or ''))
                if st.form_submit_button("Actualizar Información"):
                    c = conn.cursor()
                    c.execute("UPDATE clientes SET nombres=?, apellidos=?, telefono=?, correo=?, direccion=? WHERE cedula=?",
                              (n_nom, n_ape, n_tel, n_cor, n_dir, ced_sel))
                    conn.commit()
                    registrar_auditoria(conn, user['nombre'], user['rol'], "Clientes", "ACTUALIZAR", f"Actualizó cliente {ced_sel}")
                    st.success("Datos actualizados correctamente.")
                    st.rerun()

def vista_catalogo_inventario(conn, user):
    st.header("📖 Gestión del Catálogo e Inventario")
    
    df_bajo = pd.read_sql_query("SELECT isbn, titulo, editorial, stockDisponible, stockMinimo FROM libros WHERE activo=1 AND stockDisponible <= stockMinimo", conn)
    if not df_bajo.empty:
        st.warning(f"⚠️ **Alerta de Reposición:** Hay {len(df_bajo)} obra(s) con inventario igual o inferior al mínimo permitido.")
        st.dataframe(df_bajo, use_container_width=True, hide_index=True)

    if user['rol'] in ["Vendedor", "Bibliotecario"]:
        busq = st.text_input("🔍 Buscar por ISBN, Título, Autor o Categoría")
        df_lib = pd.read_sql_query("SELECT isbn, titulo, autor, editorial, categoria, anioPublicacion, precioVenta, stockDisponible FROM libros WHERE activo=1", conn)
        if busq:
            df_lib = df_lib[df_lib['isbn'].str.contains(busq, case=False) | df_lib['titulo'].str.contains(busq, case=False) | df_lib['autor'].str.contains(busq, case=False) | df_lib['categoria'].str.contains(busq, case=False)]
        st.dataframe(df_lib, use_container_width=True, hide_index=True)
        return

    t_con, t_reg, t_edit = st.tabs(["📚 Inventario General (100+ Obras)", "➕ Incorporar Nuevo Libro", "✏️ Editar / Estado de Obra"])
    
    with t_con:
        busq = st.text_input("Filtrar por ISBN, Título, Autor o Categoría")
        df_lib = pd.read_sql_query("SELECT id, isbn, titulo, autor, editorial, categoria, anioPublicacion, precioVenta, stockDisponible, stockMinimo, CASE WHEN activo=1 THEN 'Activo' ELSE 'Inactivo' END as estado FROM libros", conn)
        if busq:
            df_lib = df_lib[df_lib['isbn'].str.contains(busq, case=False) | df_lib['titulo'].str.contains(busq, case=False) | df_lib['autor'].str.contains(busq, case=False) | df_lib['categoria'].str.contains(busq, case=False)]
        st.dataframe(df_lib, use_container_width=True, hide_index=True)

    with t_reg:
        ed_list = pd.read_sql_query("SELECT razonSocial FROM editoriales WHERE activo=1", conn)['razonSocial'].tolist()
        with st.form("form_reg_libro", clear_on_submit=True):
            c1, c2 = st.columns(2)
            isbn = c1.text_input("Código ISBN-13")
            titulo = c2.text_input("Título de la Obra")
            autor = c1.text_input("Autor")
            editorial = c2.selectbox("Editorial / Sello", ed_list if ed_list else ["Sin Editorial"])
            categoria = c1.selectbox("Categoría", ["Literatura Latinoamericana", "Clásicos Universales", "Ciencia Ficción y Fantasía", "Thriller y Misterio", "Psicología y Bienestar", "Negocios y Finanzas", "Tecnología y Software", "Juvenil e Historia"])
            anio = c2.number_input("Año de Publicación", min_value=1500, max_value=2026, value=2024)
            precio = c1.number_input("Precio de Venta ($ COP)", min_value=0.0, step=1000.0, value=55000.0)
            stock_min = c2.number_input("Stock Mínimo de Alerta", min_value=1, value=5)
            portada = st.text_input("URL de la Carátula (O deja vacío para usar carátula por ISBN automáticamente)")
            
            if st.form_submit_button("Registrar Obra en el Catálogo"):
                if isbn and titulo and autor:
                    url_final = portada.strip() if portada.strip() else f"https://covers.openlibrary.org/b/isbn/{isbn.strip()}-L.jpg"
                    try:
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO libros (isbn, titulo, autor, editorial, categoria, anioPublicacion, precioVenta, stockDisponible, stockMinimo, portada, activo)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 1)
                        """, (isbn.strip(), titulo, autor, editorial, categoria, anio, precio, stock_min, url_final))
                        conn.commit()
                        registrar_auditoria(conn, user['nombre'], user['rol'], "Catálogo", "CREAR", f"Registró libro ISBN {isbn}")
                        st.success("Obra incorporada al catálogo con stock inicial 0.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("El ISBN ingresado ya existe en el catálogo.")
                else:
                    st.warning("Completa el ISBN, Título y Autor.")

    with t_edit:
        df_l = pd.read_sql_query("SELECT * FROM libros", conn)
        if not df_l.empty:
            opciones_l = [f"{r['isbn']} - {r['titulo']}" for _, r in df_l.iterrows()]
            sel_l = st.selectbox("Seleccionar Obra a Modificar", opciones_l)
            isbn_sel = sel_l.split(" - ")[0]
            row_l = df_l[df_l['isbn'] == isbn_sel].iloc[0]
            with st.form("form_act_libro"):
                c1, c2 = st.columns(2)
                n_tit = c1.text_input("Título", value=row_l['titulo'])
                n_aut = c2.text_input("Autor", value=row_l['autor'])
                n_cat = c1.text_input("Categoría", value=row_l['categoria'])
                n_pre = c2.number_input("Precio de Venta ($ COP)", value=float(row_l['precioVenta']), step=1000.0)
                n_min = c1.number_input("Umbral de Stock Mínimo", value=int(row_l['stockMinimo']), min_value=1)
                n_por = c2.text_input("URL de la Carátula", value=str(row_l['portada'] or ''))
                
                est_actual = "Activo" if row_l['activo'] == 1 else "Inactivo"
                if user['rol'] == "Administrador":
                    n_est = st.selectbox("Estado en Tienda", ["Activo", "Inactivo"], index=0 if est_actual == "Activo" else 1)
                else:
                    n_est = est_actual

                if st.form_submit_button("Guardar Cambios"):
                    act_val = 1 if n_est == "Activo" else 0
                    c = conn.cursor()
                    c.execute("""
                        UPDATE libros SET titulo=?, autor=?, categoria=?, precioVenta=?, stockMinimo=?, portada=?, activo=?
                        WHERE isbn=?
                    """, (n_tit, n_aut, n_cat, n_pre, n_min, n_por, act_val, isbn_sel))
                    conn.commit()
                    registrar_auditoria(conn, user['nombre'], user['rol'], "Catálogo", "ACTUALIZAR", f"Modificó libro ISBN {isbn_sel}")
                    st.success("Datos del libro actualizados.")
                    st.rerun()

def vista_proveedores_entradas(conn, user):
    st.header("📦 Editoriales Aliadas y Recepción de Mercancía")
    t_ent, t_prov, t_edit_p = st.tabs(["📥 Recepción de Ejemplares (Kárdex)", "🏢 Directorio de Editoriales", "✏️ Actualizar Editorial"])
    
    with t_ent:
        df_libros = pd.read_sql_query("SELECT isbn, titulo, stockDisponible FROM libros WHERE activo=1", conn)
        with st.form("form_entrada_stock", clear_on_submit=True):
            c1, c2 = st.columns(2)
            factura_prov = c1.text_input("Número de Remisión / Factura de Editorial")
            opciones_libros = [f"{r['isbn']} - {r['titulo']} (Stock actual: {r['stockDisponible']})" for _, r in df_libros.iterrows()]
            libro_sel = c2.selectbox("Seleccionar Obra Recibida", opciones_libros)
            cantidad = c1.number_input("Cantidad de Ejemplares Recibidos", min_value=1, value=10)
            costo_unit = c2.number_input("Costo Unitario de Adquisición ($ COP)", min_value=0.0, step=1000.0, value=32000.0)
            
            if st.form_submit_button("Registrar Ingreso al Almacén"):
                if factura_prov and libro_sel:
                    isbn_Elegido = libro_sel.split(" - ")[0]
                    titulo_Elegido = libro_sel.split(" - ")[1].split(" (Stock")[0]
                    c = conn.cursor()
                    c.execute("UPDATE libros SET stockDisponible = stockDisponible + ? WHERE isbn = ?", (cantidad, isbn_Elegido))
                    c.execute("""
                        INSERT INTO entradas_stock (isbn, titulo, cantidad, costoUnitario, numeroFacturaProveedor, fechaHora, empleado_nombre)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (isbn_Elegido, titulo_Elegido, cantidad, costo_unit, factura_prov, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user['nombre']))
                    conn.commit()
                    registrar_auditoria(conn, user['nombre'], user['rol'], "Stock", "ENTRADA_ALMACEN", f"Ingresó +{cantidad} uds al ISBN {isbn_Elegido}")
                    st.success(f"¡Inventario actualizado! Se sumaron +{cantidad} unidades a '{titulo_Elegido}'.")
                    st.rerun()
                else:
                    st.warning("Indica el número de factura o remisión del proveedor.")
        
        st.markdown("##### 📋 Movimientos Recientes de Almacén")
        st.dataframe(pd.read_sql_query("SELECT * FROM entradas_stock ORDER BY id DESC", conn), use_container_width=True, hide_index=True)

    with t_prov:
        busq_p = st.text_input("Buscar Editorial por NIT o Razón Social")
        df_p = pd.read_sql_query("SELECT id, nit, razonSocial, contacto, telefono, direccion, correo, CASE WHEN activo=1 THEN 'Activo' ELSE 'Inactivo' END as estado FROM editoriales", conn)
        if busq_p:
            df_p = df_p[df_p['nit'].str.contains(busq_p, case=False) | df_p['razonSocial'].str.contains(busq_p, case=False)]
        st.dataframe(df_p, use_container_width=True, hide_index=True)

        with st.expander("➕ Registrar Nueva Editorial / Distribuidora"):
            with st.form("form_nuevo_prov", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nit = c1.text_input("NIT")
                razon = c2.text_input("Razón Social")
                contacto = c1.text_input("Ejecutivo de Cuenta")
                tel = c2.text_input("Teléfono de Contacto")
                dir_p = c1.text_input("Dirección Principal")
                cor_p = c2.text_input("Correo Corporativo")
                if st.form_submit_button("Guardar Editorial"):
                    if nit and razon:
                        try:
                            c = conn.cursor()
                            c.execute("INSERT INTO editoriales (nit, razonSocial, contacto, telefono, direccion, correo, activo) VALUES (?, ?, ?, ?, ?, ?, 1)",
                                      (nit.strip(), razon, contacto, tel, dir_p, cor_p))
                            conn.commit()
                            registrar_auditoria(conn, user['nombre'], user['rol'], "Proveedores", "CREAR", f"Registró editorial NIT {nit}")
                            st.success("Editorial registrada exitosamente.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("El NIT ingresado ya existe.")
                    else:
                        st.warning("Completa el NIT y la Razón Social.")

    with t_edit_p:
        df_ed = pd.read_sql_query("SELECT * FROM editoriales", conn)
        if not df_ed.empty:
            nit_sel = st.selectbox("Seleccionar Editorial por NIT", df_ed['nit'].tolist())
            r_p = df_ed[df_ed['nit'] == nit_sel].iloc[0]
            with st.form("form_act_prov"):
                c1, c2 = st.columns(2)
                n_raz = c1.text_input("Razón Social", value=r_p['razonSocial'])
                n_con = c2.text_input("Contacto", value=str(r_p['contacto'] or ''))
                n_tel = c1.text_input("Teléfono", value=str(r_p['telefono'] or ''))
                n_dir = c2.text_input("Dirección", value=str(r_p['direccion'] or ''))
                n_cor = c1.text_input("Correo", value=str(r_p['correo'] or ''))
                est_p = "Activo" if r_p['activo'] == 1 else "Inactivo"
                n_est_p = c2.selectbox("Estado", ["Activo", "Inactivo"], index=0 if est_p == "Activo" else 1)
                if st.form_submit_button("Guardar Cambios"):
                    c = conn.cursor()
                    c.execute("UPDATE editoriales SET razonSocial=?, contacto=?, telefono=?, direccion=?, correo=?, activo=? WHERE nit=?",
                              (n_raz, n_con, n_tel, n_dir, n_cor, 1 if n_est_p == "Activo" else 0, nit_sel))
                    conn.commit()
                    registrar_auditoria(conn, user['nombre'], user['rol'], "Proveedores", "ACTUALIZAR", f"Modificó editorial NIT {nit_sel}")
                    st.success("Editorial actualizada.")
                    st.rerun()