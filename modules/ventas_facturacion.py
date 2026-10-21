import streamlit as st
import pandas as pd
from datetime import datetime
import os
from fpdf import FPDF
from database.db_manager import registrar_auditoria

CODIGOS_PROMO = {
    "FERIA10": 10.0,
    "LECTOR15": 15.0,
    "BIENVENIDO15": 15.0,
    "ALEJANDRINO20": 20.0
}

class PDF(FPDF):
    def header(self):
        # Logotipo corporativo
        if os.path.exists("assets/logo.png"):
            self.image("assets/logo.png", 10, 10, 35)
        self.set_font("helvetica", "B", 16)
        self.set_text(20, 33, 61) # Azul marino institucional
        self.cell(0, 10, "LIBRERÍA & BIBLIOTECA EL ALEJANDRINO", 0, 1, "R")
        self.set_font("helvetica", "", 9)
        self.set_text(100, 100, 100)
        self.cell(0, 4, "NIT: 900.123.456-7 • Régimen Simplificado", 0, 1, "R")
        self.cell(0, 4, "Sede Principal: Duitama & Bogotá, Colombia", 0, 1, "R")
        self.cell(0, 4, "Contacto: contacto@alejandrino.com | Tel: (608) 760-0000", 0, 1, "R")
        self.ln(8)
        self.set_draw_color(230, 198, 135) # Línea dorada
        self.set_line_width(0.8)
        self.line(10, 35, 200, 35)
        self.ln(5)

    def footer(self):
        self.set_y(-25)
        self.set_font("helvetica", "I", 8)
        self.set_text(120, 120, 120)
        self.cell(0, 4, "Esta factura de venta se asimila en todos sus efectos legal a una Letra de Cambio (Art. 774 del Código de Comercio).", 0, 1, "C")
        self.cell(0, 4, f"Página {self.page_no()} | Generado por el Sistema de Gestión El Alejandrino", 0, 0, "C")

def generar_pdf_factura(factura_info, detalle_items):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Datos de la Factura y del Cliente
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text(20, 33, 61)
    pdf.cell(120, 6, f"FACTURA LEGAL DE VENTA: {factura_info['numero']}", 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, f"Fecha: {factura_info['fecha']}", 0, 1, "R")
    
    pdf.ln(3)
    pdf.set_fill_bytes = False
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(240, 242, 245)
    pdf.cell(0, 6, " DATOS DEL CLIENTE / ADQUIRENTE", 0, 1, "L", True)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 5, f" Nombre / Razón Social: {factura_info['cliente']}", 0, 1)
    pdf.cell(0, 5, f" Medio de Pago: {factura_info['medio']}  |  Estado: PAGADA", 0, 1)
    pdf.ln(5)

    # Tabla de Productos
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(20, 33, 61)
    pdf.set_text(255, 255, 255)
    pdf.cell(25, 7, "ISBN", 1, 0, "C", True)
    pdf.cell(85, 7, "Descripción de la Obra / Título", 1, 0, "C", True)
    pdf.cell(18, 7, "Cant.", 1, 0, "C", True)
    pdf.cell(31, 7, "V. Unitario", 1, 0, "C", True)
    pdf.cell(31, 7, "Subtotal", 1, 1, "C", True)

    pdf.set_font("helvetica", "", 9)
    pdf.set_text(0, 0, 0)
    for item in detalle_items:
        pdf.cell(25, 6, str(item['isbn']), 1, 0, "C")
        pdf.cell(85, 6, str(item['titulo'][:42]), 1, 0, "L")
        pdf.cell(18, 6, str(item['cantidad']), 1, 0, "C")
        pdf.cell(31, 6, f"$ {item['precioUnitario']:,.0f}", 1, 0, "R")
        pdf.cell(31, 6, f"$ {item['subtotalLinea']:,.0f}", 1, 1, "R")

    pdf.ln(5)

    # Totales y Desglose de Impuestos (IVA 19%)
    pdf.set_font("helvetica", "", 10)
    X_pos = 120
    ancho_lbl = 50
    ancho_val = 30

    def fila_total(lbl, val, bold=False):
        pdf.set_x(X_pos)
        pdf.set_font("helvetica", "B" if bold else "", 10)
        pdf.cell(ancho_lbl, 6, lbl, 1, 0, "R")
        pdf.cell(ancho_val, 6, f"$ {val:,.2f}", 1, 1, "R")

    fila_total("Subtotal Bruto:", factura_info['subtotal'] + factura_info['descuento'])
    if factura_info['descuento'] > 0:
        fila_total("Descuento Aplicado:", -factura_info['descuento'])
    fila_total("Base Gravable:", factura_info['subtotal'])
    fila_total("IVA (19% Exacto):", factura_info['iva'])
    fila_total("TOTAL A PAGAR:", factura_info['total'], bold=True)

    # Guardar en archivo temporal
    nombre_archivo = f"{factura_info['numero']}.pdf"
    pdf.output(nombre_archivo)
    return nombre_archivo

def vista_ventas_caja(conn, user):
    st.header("💰 Punto de Venta (POS) y Facturación")
    
    if 'orden_venta' not in st.session_state:
        st.session_state['orden_venta'] = []
    if 'descuento_pct' not in st.session_state:
        st.session_state['descuento_pct'] = 0.0

    df_cli = pd.read_sql_query("SELECT id, cedula, nombres, apellidos FROM clientes WHERE activo=1", conn)
    df_lib = pd.read_sql_query("SELECT isbn, titulo, precioVenta, stockDisponible FROM libros WHERE activo=1 AND stockDisponible > 0", conn)

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.subheader("1. Seleccionar Obras")
        with st.form("form_item_venta"):
            lib_opts = [f"{r['isbn']} - {r['titulo']} ($ {r['precioVenta']:,.0f} | Disp: {r['stockDisponible']})" for _, r in df_lib.iterrows()]
            item_sel = st.selectbox("Buscar Obra por ISBN o Título", lib_opts if lib_opts else ["Sin stock"])
            cant_v = st.number_input("Cantidad", min_value=1, value=1)
            if st.form_submit_button("➕ Agregar a la Orden"):
                if lib_opts:
                    isbn_v = item_sel.split(" - ")[0]
                    row_l = df_lib[df_lib['isbn'] == isbn_v].iloc[0]
                    if cant_v > row_l['stockDisponible']:
                        st.error(f"🚫 Solo hay {row_l['stockDisponible']} unidades disponibles.")
                    else:
                        sub_linea = round(float(row_l['precioVenta']) * cant_v, 2)
                        st.session_state['orden_venta'].append({
                            "isbn": isbn_v,
                            "titulo": row_l['titulo'],
                            "cantidad": int(cant_v),
                            "precioUnitario": float(row_l['precioVenta']),
                            "subtotalLinea": sub_linea
                        })
                        st.rerun()

        st.subheader("2. Convenios y Cupones Promocionales")
        col_p1, col_p2 = st.columns([2, 1])
        cod_input = col_p1.text_input("Código de Descuento (BIENVENIDO15, FERIA10, LECTOR15, ALEJANDRINO20)")
        if col_p2.button("Validar Cupón"):
            cod_clean = cod_input.strip().upper()
            if cod_clean in CODIGOS_PROMO:
                st.session_state['descuento_pct'] = CODIGOS_PROMO[cod_clean]
                st.success(f"Descuento del {st.session_state['descuento_pct']}% aplicado.")
            else:
                st.error("Cupón inválido o expirado.")

    with c2:
        st.subheader("3. Liquidación y Factura")
        if not st.session_state['orden_venta']:
            st.info("Agrega libros en el panel izquierdo para iniciar la facturación.")
        else:
            df_orden = pd.DataFrame(st.session_state['orden_venta'])
            st.dataframe(df_orden[['isbn', 'titulo', 'cantidad', 'precioUnitario', 'subtotalLinea']], use_container_width=True, hide_index=True)
            
            subtotal_bruto = round(float(df_orden['subtotalLinea'].sum()), 2)
            valor_descuento = round(subtotal_bruto * (st.session_state['descuento_pct'] / 100.0), 2)
            subtotal_neto = round(subtotal_bruto - valor_descuento, 2)
            iva_19 = round(subtotal_neto * 0.19, 2)
            total_pagar = round(subtotal_neto + iva_19, 2)

            st.markdown(f"""
            - **Subtotal Bruto:** $ {subtotal_bruto:,.2f} COP
            - **Descuento ({st.session_state['descuento_pct']}%):** - $ {valor_descuento:,.2f} COP
            - **Base Gravable:** $ {subtotal_neto:,.2f} COP
            - **IVA (19%):** $ {iva_19:,.2f} COP
            - ### **Total a Pagar: $ {total_pagar:,.2f} COP**
            """)

            with st.form("form_cobrar_factura"):
                cli_opts = [f"{r['cedula']} - {r['nombres']} {r['apellidos']}" for _, r in df_cli.iterrows()]
                cli_venta = st.selectbox("Cliente", cli_opts)
                medio_pago = st.selectbox("Medio de Pago", ["Efectivo", "Tarjeta", "Transferencia / PSE"])
                monto_recibido = st.number_input("Valor Recibido ($ COP)", min_value=0.0, value=float(total_pagar), step=1000.0)
                
                if st.form_submit_button("✅ Emitir Factura Legal"):
                    if monto_recibido < total_pagar:
                        st.error("🚫 El monto recibido es inferior al total a cobrar.")
                    else:
                        ced_cli = cli_venta.split(" - ")[0]
                        nom_cli = cli_venta.split(" - ")[1]
                        id_cli = int(df_cli[df_cli['cedula'] == ced_cli].iloc[0]['id'])
                        fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO ventas (cliente_id, empleado_id, fechaHora, subtotal, descuento, iva, total, estado)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pagada')
                        """, (id_cli, user['id'], fecha_emision, subtotal_neto, valor_descuento, iva_19, total_pagar))
                        venta_id = c.lastrowid
                        
                        for item in st.session_state['orden_venta']:
                            c.execute("""
                                INSERT INTO detalle_ventas (venta_id, isbn, titulo, cantidad, precioUnitario, subtotalLinea)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (venta_id, item['isbn'], item['titulo'], item['cantidad'], item['precioUnitario'], item['subtotalLinea']))
                            c.execute("UPDATE libros SET stockDisponible = stockDisponible - ? WHERE isbn = ?", (item['cantidad'], item['isbn']))
                        
                        num_factura = f"FACT-{venta_id:05d}"
                        c.execute("""
                            INSERT INTO facturas (numeroFactura, venta_id, cliente_cedula, cliente_nombre, fechaEmision, subtotal, descuento, iva19, totalPagar, medioPago, montoRecibido, estado)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pagada')
                        """, (num_factura, venta_id, ced_cli, nom_cli, fecha_emision, subtotal_neto, valor_descuento, iva_19, total_pagar, medio_pago, monto_recibido))
                        conn.commit()
                        
                        cambio = round(monto_recibido - total_pagar, 2)
                        registrar_auditoria(conn, user['nombre'], user['rol'], "Facturación", "EMITIR_FACTURA", f"Emitió {num_factura} por ${total_pagar:,.2f}")
                        
                        # Generar el PDF corporativo
                        factura_info = {
                            "numero": num_factura, "fecha": fecha_emision, "cliente": f"{nom_cli} ({ced_cli})",
                            "subtotal": subtotal_neto, "descuento": valor_descuento, "iva": iva_19,
                            "total": total_pagar, "medio": medio_pago
                        }
                        pdf_path = generar_pdf_factura(factura_info, st.session_state['orden_venta'])

                        st.session_state['ultima_factura'] = {
                            "info": factura_info, "cambio": cambio, "pdf_path": pdf_path
                        }
                        st.session_state['orden_venta'] = []
                        st.session_state['descuento_pct'] = 0.0
                        st.rerun()

            if st.button("🗑️ Limpiar Orden"):
                st.session_state['orden_venta'] = []
                st.session_state['descuento_pct'] = 0.0
                st.rerun()

        if 'ultima_factura' in st.session_state:
            f = st.session_state['ultima_factura']
            st.success(f"🎉 Factura **{f['info']['numero']}** generada con éxito. Cambio a devolver: **$ {f['cambio']:,.2f} COP**")
            
            with open(f['pdf_path'], "rb") as pdf_file:
                st.download_button(
                    label="📥 Descargar Factura Profesional en PDF",
                    data=pdf_file,
                    file_name=f"{f['info']['numero']}.pdf",
                    mime="application/pdf"
                )

def vista_anulaciones_reportes(conn, user):
    st.header("📊 Finanzas, Notas Crédito y Estadísticas")
    t_rep, t_rank, t_anul = st.tabs(["📈 Balance de Ventas", "🏆 Ranking de Libros Más Vendidos", "🚫 Anulaciones y Notas Crédito"])
    
    with t_rep:
        df_v = pd.read_sql_query("SELECT * FROM facturas WHERE estado='Pagada'", conn)
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Netas (Base)", f"$ {df_v['subtotal'].sum():,.2f}")
        c2.metric("IVA Recaudado (19%)", f"$ {df_v['iva19'].sum():,.2f}")
        c3.metric("Total Facturado", f"$ {df_v['totalPagar'].sum():,.2f}")
        st.dataframe(df_v, use_container_width=True, hide_index=True)

    with t_rank:
        st.subheader("Obras con Mayor Rotación")
        df_top = pd.read_sql_query("""
            SELECT isbn, titulo, SUM(cantidad) as unidades_vendidas, SUM(subtotalLinea) as ingresos_generados
            FROM detalle_ventas
            GROUP BY isbn, titulo
            ORDER BY unidades_vendidas DESC
        """, conn)
        st.dataframe(df_top, use_container_width=True, hide_index=True)

    with t_anul:
        df_fact = pd.read_sql_query("SELECT * FROM facturas WHERE estado='Pagada' ORDER BY id DESC", conn)
        if df_fact.empty:
            st.info("No hay facturas pagadas para anular.")
        else:
            f_sel = st.selectbox("Seleccionar Factura", df_fact['numeroFactura'].tolist())
            row_f = df_fact[df_fact['numeroFactura'] == f_sel].iloc[0]
            with st.form("form_anular_fact"):
                st.write(f"**Cliente:** {row_f['cliente_nombre']} | **Valor Total:** $ {row_f['totalPagar']:,.2f} COP")
                motivo = st.text_area("Motivo de la Devolución / Anulación")
                if st.form_submit_button("Anular Factura y Emitir Nota Crédito"):
                    if not motivo.strip():
                        st.error("Por favor especifica el motivo de la anulación.")
                    else:
                        nota_credito = f"NC-{row_f['numeroFactura'].split('-')[1]}"
                        c = conn.cursor()
                        c.execute("UPDATE facturas SET estado='Anulada', motivoAnulacion=?, notaCredito=? WHERE numeroFactura=?",
                                  (motivo.strip(), nota_credito, f_sel))
                        c.execute("UPDATE ventas SET estado='Anulada' WHERE id=?", (int(row_f['venta_id']),))
                        
                        df_items = pd.read_sql_query("SELECT isbn, cantidad FROM detalle_ventas WHERE venta_id=?", conn, params=(int(row_f['venta_id']),))
                        for _, item in df_items.iterrows():
                            c.execute("UPDATE libros SET stockDisponible = stockDisponible + ? WHERE isbn = ?", (int(item['cantidad']), item['isbn']))
                        
                        conn.commit()
                        registrar_auditoria(conn, user['nombre'], user['rol'], "Facturación", "ANULAR_FACTURA", f"Anuló {f_sel} -> {nota_credito}")
                        st.success(f"Factura {f_sel} anulada. Se generó la Nota Crédito **{nota_credito}** y se reintegró el stock.")
                        st.rerun()

        st.dataframe(pd.read_sql_query("SELECT numeroFactura, cliente_nombre, fechaEmision, totalPagar, estado, notaCredito, motivoAnulacion FROM facturas ORDER BY id DESC", conn), use_container_width=True, hide_index=True)