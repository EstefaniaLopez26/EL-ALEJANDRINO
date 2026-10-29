from fpdf import FPDF
import os
import tempfile

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
        self.set_y(-45) 
        self.set_font("helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        # Eliminado el texto de "Página 1" para un diseño más limpio
        self.cell(0, 4, "Documento generado por el Sistema El Alejandrino", 0, 0, "C")

def generar_factura_pdf(datos_venta, detalles_venta, ruta_salida=None):
    pdf = FacturaPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=50) 

    if os.path.exists("assets/qr_instagram.png"):
        pdf.image("assets/qr_instagram.png", x=165, y=230, w=35)
    
    # Detalles Factura/Cliente
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(20, 33, 61)
    pdf.cell(95, 8, "DETALLES DE LA FACTURA", 0, 0, "L")
    pdf.cell(95, 8, "DATOS DEL CLIENTE", 0, 1, "L")
    
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(30, 6, "No. Factura:", 0, 0, "L")
    pdf.cell(65, 6, str(datos_venta.get('numero_factura', 'N/A')), 0, 0, "L")
    pdf.cell(30, 6, "Cliente:", 0, 0, "L")
    pdf.cell(65, 6, str(datos_venta.get('cliente_nombre', 'Cliente de Mostrador')), 0, 1, "L")
    
    pdf.cell(30, 6, "Fecha:", 0, 0, "L")
    pdf.cell(65, 6, str(datos_venta.get('fecha', 'N/A')), 0, 0, "L")
    pdf.cell(30, 6, "Identificación:", 0, 0, "L")
    pdf.cell(65, 6, str(datos_venta.get('cliente_cedula', '222222222')), 0, 1, "L")
    
    pdf.ln(5)

    # Tabla de Productos
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(20, 33, 61)
    pdf.set_text_color(255, 255, 255)
    
    # Ajuste de anchos para que el total cuadre perfecto
    w_isbn = 25
    w_desc = 85
    w_cant = 18
    w_unit = 31
    w_sub = 31
    
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
        isbn = item.get('isbn', 'N/A')
        titulo = item.get('titulo', 'Sin Título')[:42]
        cantidad = item.get('cantidad', 1)
        precio = item.get('precioUnitario', item.get('precioVenta', 0))
        subtotal = item.get('subtotalLinea', cantidad * precio)
        
        pdf.cell(w_isbn, 8, str(isbn), 1, 0, "C", fill=fill)
        pdf.cell(w_desc, 8, str(titulo), 1, 0, "L", fill=fill)
        pdf.cell(w_cant, 8, str(cantidad), 1, 0, "C", fill=fill)
        pdf.cell(w_unit, 8, f"$ {precio:,.0f}", 1, 0, "R", fill=fill)
        pdf.cell(w_sub, 8, f"$ {subtotal:,.0f}", 1, 1, "R", fill=fill)
        fill = not fill

    pdf.set_font("helvetica", "", 9)
    
    X_pos = 10 + w_isbn + w_desc + w_cant 
    ancho_lbl = w_unit
    ancho_val = w_sub
    
    def fila_total(lbl, val, bold=False, fill_bg=False):
        pdf.set_x(X_pos)
        pdf.set_font("helvetica", "B" if bold else "", 10 if bold else 9)
        if bold:
            pdf.set_fill_color(20, 33, 61)
            pdf.set_text_color(255, 255, 255)
        else:
            pdf.set_fill_color(220, 220, 220)
        pdf.cell(ancho_lbl, 8, lbl, 1, 0, "R", fill=bold or fill_bg)
        pdf.cell(ancho_val, 8, f"$ {val:,.2f}", 1, 1, "R", fill=bold or fill_bg)
        pdf.set_text_color(0, 0, 0)

        pdf.ln(8) 

    subt = datos_venta.get('subtotal', 0)
    desc = datos_venta.get('descuento', 0)
    tot = datos_venta.get('total', 0)

    subtotal_real = tot + desc 
    
    fila_total("Subtotal", subtotal_real, fill_bg=True)
    if desc > 0:
        fila_total("Descuento", -desc, fill_bg=True)
        
    fila_total("TOTAL A PAGAR", tot, bold=True)

    if ruta_salida is None:
        if not os.path.exists("facturas_pdf"):
            os.makedirs("facturas_pdf")
        ruta_salida = os.path.join("facturas_pdf", f"Factura_{datos_venta.get('numero_factura', '000')}.pdf")
        
    pdf.output(ruta_salida)
    return ruta_salida