import streamlit as st
import pandas as pd
import sqlite3
from database.db_manager import encriptar_password, registrar_auditoria

def vista_login_recuperacion(conn):
    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        # Usamos session_state para alternar entre Login y Recuperar contraseña de forma limpia
        modo = st.session_state.get('modo_auth', 'login')

        if modo == 'login':
            st.markdown("### 🔐 Iniciar Sesión")
            with st.form("form_login_unico"):
                correo = st.text_input("Correo Electrónico")
                password = st.text_input("Contraseña", type="password")
                
                col_btn1, col_btn2 = st.columns(2)
                ingresar = col_btn1.form_submit_button("Ingresar")
                
                if ingresar:
                    c = conn.cursor()
                    pass_hash = encriptar_password(password)
                    
                    c.execute("SELECT id, nombres, apellidos, rol FROM empleados WHERE correo = ? AND password = ? AND activo = 1", (correo.strip(), pass_hash))
                    emp = c.fetchone()
                    if emp:
                        st.session_state['usuario_autenticado'] = True
                        st.session_state['tipo_usuario'] = 'empleado'
                        st.session_state['user_data'] = {"id": emp[0], "nombre": f"{emp[1]} {emp[2]}", "rol": emp[3], "correo": correo.strip()}
                        registrar_auditoria(conn, f"{emp[1]} {emp[2]}", emp[3], "Seguridad", "LOGIN", "Ingreso exitoso al panel interno")
                        st.rerun()
                    else:
                        c.execute("SELECT id, cedula, nombres, apellidos FROM clientes WHERE correo = ? AND password = ? AND activo = 1", (correo.strip(), pass_hash))
                        cli = c.fetchone()
                        if cli:
                            st.session_state['usuario_autenticado'] = True
                            st.session_state['tipo_usuario'] = 'cliente'
                            st.session_state['user_data'] = {"id": cli[0], "cedula": cli[1], "nombre": f"{cli[2]} {cli[3]}", "rol": "Cliente", "correo": correo.strip()}
                            registrar_auditoria(conn, f"{cli[2]} {cli[3]}", "Cliente", "Seguridad", "LOGIN", "Ingreso exitoso a tienda")
                            st.rerun()
                        else:
                            st.error("Credenciales incorrectas o cuenta inactiva.")

            if st.button("¿Olvidaste tu contraseña? Restablécela aquí"):
                st.session_state['modo_auth'] = 'recuperar'
                st.rerun()

        else:
            st.markdown("### 🔑 Recuperar Contraseña")
            with st.form("form_recuperar_clave"):
                correo_rec = st.text_input("Correo Electrónico Registrado")
                nueva_clave = st.text_input("Nueva Contraseña", type="password")
                confirmar_clave = st.text_input("Confirmar Nueva Contraseña", type="password")
                
                actualizar = st.form_submit_button("Actualizar Contraseña")
                
                if actualizar:
                    if not correo_rec or not nueva_clave:
                        st.warning("Completa todos los campos.")
                    elif nueva_clave != confirmar_clave:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        c = conn.cursor()
                        nuevo_hash = encriptar_password(nueva_clave)
                        c.execute("UPDATE empleados SET password = ? WHERE correo = ?", (nuevo_hash, correo_rec.strip()))
                        if c.rowcount == 0:
                            c.execute("UPDATE clientes SET password = ? WHERE correo = ?", (nuevo_hash, correo_rec.strip()))
                        if c.rowcount > 0:
                            conn.commit()
                            registrar_auditoria(conn, correo_rec, "Sistema", "Seguridad", "RECUPERAR_CLAVE", "Contraseña restablecida")
                            st.success("¡Contraseña actualizada con éxito!")
                        else:
                            st.error("No encontramos una cuenta con ese correo.")

            if st.button("⬅️ Volver al Iniciar Sesión"):
                st.session_state['modo_auth'] = 'login'
                st.rerun()

def vista_gestion_empleados(conn, user):
    st.header("👔 Gestión de Equipo y Permisos")
    t_crear, t_editar, t_consultar = st.tabs(["➕ Registrar Colaborador", "✏️ Actualizar / Estado", "🔍 Directorio de Personal"])
    
    with t_crear:
        with st.form("form_nuevo_emp", clear_on_submit=True):
            c1, c2 = st.columns(2)
            cedula = c1.text_input("Cédula")
            nombres = c2.text_input("Nombres")
            apellidos = c1.text_input("Apellidos")
            telefono = c2.text_input("Teléfono")
            correo = c1.text_input("Correo Institucional")
            rol = c2.selectbox("Cargo / Rol en el Sistema", ["Administrador", "Vendedor", "Bibliotecario", "Almacenista"])
            password = c1.text_input("Contraseña Asignada", type="password")
            
            if st.form_submit_button("Guardar Colaborador"):
                if cedula and nombres and correo and password:
                    try:
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO empleados (cedula, nombres, apellidos, telefono, correo, password, rol, activo)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                        """, (cedula, nombres, apellidos, telefono, correo.strip(), encriptar_password(password), rol))
                        conn.commit()
                        registrar_auditoria(conn, user['nombre'], user['rol'], "Empleados", "CREAR", f"Registró empleado {cedula} ({rol})")
                        st.success("Colaborador registrado exitosamente.")
                    except sqlite3.IntegrityError:
                        st.error("La cédula o el correo ya pertenecen a otro colaborador.")
                else:
                    st.warning("Completa todos los campos obligatorios.")

    with t_editar:
        df_emp = pd.read_sql_query("SELECT id, cedula, nombres, apellidos, telefono, correo, rol, activo FROM empleados", conn)
        emp_sel = st.selectbox("Seleccionar Colaborador por Cédula", df_emp['cedula'].tolist())
        if emp_sel:
            datos = df_emp[df_emp['cedula'] == emp_sel].iloc[0]
            with st.form("form_edit_emp"):
                c1, c2 = st.columns(2)
                n_nom = c1.text_input("Nombres", value=datos['nombres'])
                n_ape = c2.text_input("Apellidos", value=datos['apellidos'])
                n_tel = c1.text_input("Teléfono", value=str(datos['telefono'] or ''))
                n_rol = c2.selectbox("Cargo / Rol", ["Administrador", "Vendedor", "Bibliotecario", "Almacenista"], index=["Administrador", "Vendedor", "Bibliotecario", "Almacenista"].index(datos['rol']))
                estado_actual = "Activo" if datos['activo'] == 1 else "Inactivo"
                n_est = c1.selectbox("Estado de la Cuenta", ["Activo", "Inactivo"], index=0 if estado_actual == "Activo" else 1)
                
                if st.form_submit_button("Guardar Cambios"):
                    act_val = 1 if n_est == "Activo" else 0
                    c = conn.cursor()
                    c.execute("UPDATE empleados SET nombres=?, apellidos=?, telefono=?, rol=?, activo=? WHERE cedula=?",
                              (n_nom, n_ape, n_tel, n_rol, act_val, emp_sel))
                    conn.commit()
                    registrar_auditoria(conn, user['nombre'], user['rol'], "Empleados", "ACTUALIZAR", f"Modificó colaborador {emp_sel}")
                    st.success("Información actualizada correctamente.")
                    st.rerun()

    with t_consultar:
        filtro = st.text_input("Buscar por Cédula o Nombre")
        df_mostrar = pd.read_sql_query("SELECT id, cedula, nombres, apellidos, telefono, correo, rol, CASE WHEN activo=1 THEN 'Activo' ELSE 'Inactivo' END as estado FROM empleados", conn)
        if filtro:
            df_mostrar = df_mostrar[df_mostrar['cedula'].str.contains(filtro, case=False) | df_mostrar['nombres'].str.contains(filtro, case=False)]
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

def vista_auditoria(conn):
    st.header("🛡️ Bitácora de Seguridad y Operaciones")
    filtro_mod = st.selectbox("Filtrar por Área Operativa", ["Todos", "Seguridad", "Catálogo", "Proveedores", "Stock", "Clientes", "Pasarela Online", "Facturación", "Préstamos", "Empleados"])
    df_aud = pd.read_sql_query("SELECT * FROM auditoria ORDER BY id DESC", conn)
    if filtro_mod != "Todos":
        df_aud = df_aud[df_aud['modulo'] == filtro_mod]
    st.dataframe(df_aud, use_container_width=True, hide_index=True)