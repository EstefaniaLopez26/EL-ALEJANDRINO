from fpdf import FPDF
import os


class FacturaPDF(FPDF):
    def header(self):
        if os.path.exists("assets/logo.png"):
            self.image("assets/logo.png", 10, 8, 60)

        self.set_font("helvetica", "B", 16)
        self.set_text_color(20, 33, 61)
        self.cell(0, 8, "FACTURA COMERCIAL", 0, 1, "R")

        self.set_font("helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, "Librería El Alejandrino", 0, 1, "R")
        self.cell(0, 4, "Sede: Duitama, Boyacá", 0, 1, "R")
        self.cell(0, 4, "elalejandrino1@gmail.com", 0, 1, "R")
        self.ln(12)

        self.set_draw_color(20, 33, 61)
        self.set_line_width(0.8)
        self.line(10, 35, 200, 35)
        self.ln(5)

    def footer(self):
        self.set_y(-30)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 4, "Documento generado por el Sistema El Alejandrino - Gracias por su compra", 0, 0, "C")


def generar_factura_pdf(datos_venta, detalles_venta, ruta_salida=None):
    pdf = FacturaPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=45)

    if os.path.exists("assets/qr_instagram.png"):
        pdf.image("assets/qr_instagram.png", x=165, y=230, w=32)

    # Detalles Factura / Cliente
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(20, 33, 61)
    pdf.cell(95, 8, "DETALLES DE LA FACTURA", 0, 0, "L")
    pdf.cell(95, 8, "DATOS DEL CLIENTE", 0, 1, "L")

    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    num_factura = str(datos_venta.get('numero_factura', datos_venta.get('numero', 'N/A')))
    cliente_nombre = str(datos_venta.get('cliente_nombre', datos_venta.get('cliente', 'Cliente de Mostrador')))
    fecha = str(datos_venta.get('fecha', 'N/A'))
    identificacion = str(datos_venta.get('cliente_cedula', datos_venta.get('medio', 'N/A')))
    etiqueta_der = "Identificación:" if 'cliente_cedula' in datos_venta else "Medio de Pago:"

    pdf.cell(30, 6, "No. Factura:", 0, 0, "L")
    pdf.cell(65, 6, num_factura, 0, 0, "L")
    pdf.cell(30, 6, "Cliente:", 0, 0, "L")
    pdf.cell(65, 6, cliente_nombre, 0, 1, "L")

    pdf.cell(30, 6, "Fecha:", 0, 0, "L")
    pdf.cell(65, 6, fecha, 0, 0, "L")
    pdf.cell(30, 6, etiqueta_der, 0, 0, "L")
    pdf.cell(65, 6, identificacion, 0, 1, "L")

    pdf.ln(5)

    # Tabla de Productos
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(20, 33, 61)
    pdf.set_text_color(255, 255, 255)

    w_isbn, w_desc, w_cant, w_unit, w_sub = 25, 85, 18, 31, 31
    pdf.cell(w_isbn, 8, "ISBN", 1, 0, "C", True)
    pdf.cell(w_desc, 8, "Descripción", 1, 0, "C", True)
    pdf.cell(w_cant, 8, "Cant.", 1, 0, "C", True)
    pdf.cell(w_unit, 8, "V. Unitario", 1, 0, "C", True)
    pdf.cell(w_sub, 8, "Subtotal", 1, 1, "C", True)

    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)

    fill = False
    for item in detalles_venta:
        pdf.set_fill_color(240, 240, 240) if fill else pdf.set_fill_color(255, 255, 255)
        isbn = str(item.get('isbn', 'N/A'))
        titulo = str(item.get('titulo', 'Sin Título'))[:42]
        cantidad = int(item.get('cantidad', 1))
        precio = float(item.get('precioUnitario', item.get('precioVenta', 0)))
        subtotal = float(item.get('subtotalLinea', cantidad * precio))

        pdf.cell(w_isbn, 8, isbn, 1, 0, "C", fill=fill)
        pdf.cell(w_desc, 8, titulo, 1, 0, "L", fill=fill)
        pdf.cell(w_cant, 8, str(cantidad), 1, 0, "C", fill=fill)
        pdf.cell(w_unit, 8, f"$ {precio:,.0f}", 1, 0, "R", fill=fill)
        pdf.cell(w_sub, 8, f"$ {subtotal:,.0f}", 1, 1, "R", fill=fill)
        fill = not fill

    pdf.ln(5)

    # Bloque de Totales
    x_pos = 10 + w_isbn + w_desc + w_cant
    ancho_lbl = w_unit
    ancho_val = w_sub

    def fila_total(lbl, val, bold=False, fill_bg=False):
        pdf.set_x(x_pos)
        pdf.set_font("helvetica", "B" if bold else "", 10 if bold else 9)
        if bold:
            pdf.set_fill_color(20, 33, 61)
            pdf.set_text_color(255, 255, 255)
        else:
            pdf.set_fill_color(220, 220, 220)
            pdf.set_text_color(0, 0, 0)
        pdf.cell(ancho_lbl, 8, lbl, 1, 0, "R", fill=bold or fill_bg)
        pdf.cell(ancho_val, 8, f"$ {val:,.2f}", 1, 1, "R", fill=bold or fill_bg)
        pdf.set_text_color(0, 0, 0)

    subt_base = float(datos_venta.get('subtotal', 0))
    desc = float(datos_venta.get('descuento', 0))
    iva = float(datos_venta.get('iva', 0))
    tot = float(datos_venta.get('total', 0))
    subtotal_bruto = subt_base + desc

    fila_total("Subtotal Bruto", subtotal_bruto, fill_bg=True)
    if desc > 0:
        fila_total("Descuento", -desc, fill_bg=True)
    fila_total("IVA (19%)", iva, fill_bg=True)
    fila_total("TOTAL A PAGAR", tot, bold=True)

    if ruta_salida is None:
        os.makedirs("facturas_pdf", exist_ok=True)
        ruta_salida = os.path.join("facturas_pdf", f"{num_factura}.pdf")

    pdf.output(ruta_salida)
    return ruta_salida