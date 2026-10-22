import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database.db_manager import registrar_auditoria

VALOR_MULTA_DIA = 2500.0

def vista_prestamos(conn, user):
    st.header("📚 Servicio de Biblioteca y Préstamos")
    t_hist, t_pres, t_dev = st.tabs(["📋 Historial y Estado de Préstamos", "📤 Nuevo Préstamo", "📥 Recepción y Devoluciones"])
    
    with t_hist:
        filtro_ced = st.text_input("🔍 Buscar por Cédula, Nombre del Lector o Código de Préstamo")
        df_h = pd.read_sql_query("SELECT idPrestamo, cedula_cliente, nombre_cliente, isbn, titulo_libro, fechaSalida, fechaLimite, fechaDevolucion, estadoEjemplar, estado, multa FROM prestamos ORDER BY id DESC", conn)
        if filtro_ced:
            df_h = df_h[df_h['cedula_cliente'].str.contains(filtro_ced, case=False) | df_h['nombre_cliente'].str.contains(filtro_ced, case=False) | df_h['idPrestamo'].str.contains(filtro_ced, case=False)]
        st.dataframe(df_h, use_container_width=True, hide_index=True)

    with t_pres:
        df_cli = pd.read_sql_query("SELECT id, cedula, nombres, apellidos FROM clientes WHERE activo=1", conn)
        df_lib = pd.read_sql_query("SELECT isbn, titulo, stockDisponible FROM libros WHERE activo=1 AND stockDisponible > 0", conn)
        
        with st.form("form_nuevo_prestamo"):
            c1, c2 = st.columns(2)
            cli_opciones = [f"{r['cedula']} - {r['nombres']} {r['apellidos']}" for _, r in df_cli.iterrows()]
            cli_sel = c1.selectbox("Seleccionar Lector", cli_opciones if cli_opciones else ["Sin clientes"])
            lib_opciones = [f"{r['isbn']} - {r['titulo']} (Disponibles: {r['stockDisponible']})" for _, r in df_lib.iterrows()]
            lib_sel = c2.selectbox("Obra Solicitada", lib_opciones if lib_opciones else ["Sin stock disponible"])
            dias_prestamo = c1.number_input("Días Autorizados de Préstamo", min_value=1, max_value=30, value=8)
            
            if st.form_submit_button("Autorizar Préstamo"):
                if cli_opciones and lib_opciones:
                    ced_c = cli_sel.split(" - ")[0]
                    nom_c = cli_sel.split(" - ")[1]
                    id_c = int(df_cli[df_cli['cedula'] == ced_c].iloc[0]['id'])
                    isbn_l = lib_sel.split(" - ")[0]
                    tit_l = lib_sel.split(" - ")[1].split(" (Disponibles:")[0]
                    
                    hoy_str = datetime.now().strftime("%Y-%m-%d")
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM prestamos WHERE cedula_cliente=? AND (estado='Activo' AND fechaLimite < ?)", (ced_c, hoy_str))
                    vencidos = c.fetchone()[0]
                    if vencidos > 0:
                        st.error("🚫 El lector presenta un préstamo vencido pendiente por devolver.")
                    else:
                        id_prestamo = f"PR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        f_limite = (datetime.now() + timedelta(days=int(dias_prestamo))).strftime("%Y-%m-%d")
                        
                        c.execute("""
                            INSERT INTO prestamos (idPrestamo, cliente_id, cedula_cliente, nombre_cliente, isbn, titulo_libro, empleado_id, fechaSalida, fechaLimite, estado, multa)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Activo', 0.0)
                        """, (id_prestamo, id_c, ced_c, nom_c, isbn_l, tit_l, user['id'], hoy_str, f_limite))
                        c.execute("UPDATE libros SET stockDisponible = stockDisponible - 1 WHERE isbn = ?", (isbn_l,))
                        conn.commit()
                        registrar_auditoria(conn, user['nombre'], user['rol'], "Préstamos", "PRESTAR", f"Préstamo {id_prestamo} a {ced_c}")
                        st.success(f"✅ Préstamo `{id_prestamo}` registrado. Fecha límite de entrega: **{f_limite}**.")
                        st.rerun()

    with t_dev:
        df_act = pd.read_sql_query("SELECT * FROM prestamos WHERE estado='Activo'", conn)
        if df_act.empty:
            st.info("No hay préstamos activos pendientes de devolución.")
        else:
            opciones_p = [f"{r['idPrestamo']} | {r['nombre_cliente']} ({r['cedula_cliente']}) - {r['titulo_libro']} (Vence: {r['fechaLimite']})" for _, r in df_act.iterrows()]
            pres_sel = st.selectbox("Seleccionar Préstamo Activo", opciones_p)
            id_p_sel = pres_sel.split(" | ")[0]
            row_p = df_act[df_act['idPrestamo'] == id_p_sel].iloc[0]
            
            with st.form("form_devolucion"):
                c1, c2 = st.columns(2)
                estado_ejemplar = c1.selectbox("Estado Físico del Libro Devuelto", ["Bueno", "Regular", "Dañado"])
                fecha_rec = c2.date_input("Fecha de Recepción", value=datetime.now())
                
                if st.form_submit_button("Registrar Retorno de Obra"):
                    f_lim_dt = datetime.strptime(row_p['fechaLimite'], "%Y-%m-%d").date()
                    dias_mora = (fecha_rec - f_lim_dt).days
                    multa_calc = max(0.0, dias_mora * VALOR_MULTA_DIA)
                    
                    c = conn.cursor()
                    c.execute("""
                        UPDATE prestamos SET fechaDevolucion=?, estadoEjemplar=?, estado='Devuelto', multa=?
                        WHERE idPrestamo=?
                    """, (fecha_rec.strftime("%Y-%m-%d"), estado_ejemplar, multa_calc, id_p_sel))
                    c.execute("UPDATE libros SET stockDisponible = stockDisponible + 1 WHERE isbn = ?", (row_p['isbn'],))
                    conn.commit()
                    registrar_auditoria(conn, user['nombre'], user['rol'], "Préstamos", "DEVOLUCION", f"Retorno {id_p_sel} - Multa: ${multa_calc:,.0f}")
                    
                    if multa_calc > 0:
                        st.warning(f"⚠️ Entrega con retraso ({dias_mora} días). Se liquidó recargo por mora de **${multa_calc:,.2f} COP**.")
                    else:
                        st.success("✅ Ejemplar recibido a tiempo y reintegrado al inventario disponible.")
                    st.rerun()