"""Genera una presentació 16:9 d'ús del connector (font editable)."""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Presentacio_us_Connector_microbit_ThingSpeak.pptx"
IMG = ROOT / "assets" / "app_icon.png"
SCREEN = ROOT / "docs" / "captura_real.png"

NAVY = RGBColor(15, 37, 57)
BLUE = RGBColor(20, 111, 166)
CYAN = RGBColor(22, 195, 223)
PALE = RGBColor(235, 246, 250)
WHITE = RGBColor(255, 255, 255)
INK = RGBColor(23, 46, 64)
MUTED = RGBColor(91, 117, 133)
GOLD = RGBColor(244, 179, 64)

p = Presentation()
p.slide_width = Inches(13.333)
p.slide_height = Inches(7.5)


def color_bg(slide, color):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color


def textbox(slide, text, x, y, w, h, size=23, color=INK, bold=False, align=None):
    sh = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = sh.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.07)
    tf.margin_right = Inches(0.07)
    tf.margin_top = Inches(0.03)
    tf.margin_bottom = Inches(0.03)
    for i, line in enumerate(text.split("\n")):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.text = line
        para.font.name = "Aptos"
        para.font.size = Pt(size)
        para.font.bold = bold
        para.font.color.rgb = color
        para.space_after = Pt(13)
        if align is not None:
            para.alignment = align
    return sh


def rounded(slide, x, y, w, h, color=PALE):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def base(title, subtitle, n):
    s = p.slides.add_slide(p.slide_layouts[6])
    color_bg(s, WHITE)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, p.slide_width, Inches(0.17))
    bar.fill.solid()
    bar.fill.fore_color.rgb = BLUE
    bar.line.fill.background()
    textbox(s, title, 0.75, 0.42, 12, 0.68, 31, NAVY, True)
    textbox(s, subtitle, 0.78, 1.15, 11.8, 0.52, 16, MUTED)
    textbox(s, "Connector micro:bit → ThingSpeak  ·  Projecte educatiu obert", 0.79, 7.10, 9.9, 0.26, 10, MUTED)
    textbox(s, str(n).zfill(2), 12.05, 7.08, 0.54, 0.28, 11, BLUE, True, PP_ALIGN.RIGHT)
    return s


# 01 Cover
s = p.slides.add_slide(p.slide_layouts[6])
color_bg(s, NAVY)
rounded(s, 0.70, 0.73, 11.9, 5.98, RGBColor(22, 66, 94))
textbox(s, "DEL SENSOR\nAL NÚVOL", 1.19, 1.07, 8.2, 2.3, 48, WHITE, True)
textbox(s, "Connector micro:bit → ThingSpeak", 1.20, 4.00, 8.85, 0.61, 27, CYAN, True)
textbox(s, "Presentació d'ús · Windows · USB/Sèrie · IoT educatiu", 1.20, 4.89, 9.3, 0.61, 20, WHITE)
s.shapes.add_picture(str(IMG), Inches(9.85), Inches(1.95), height=Inches(3.35))
textbox(s, "Codi reconstruït a partir de la versió 5.1.4", 1.22, 6.37, 10.2, 0.31, 13, WHITE)

# 02 Architecture
s = base("Com funciona el connector?", "La micro:bit no necessita Wi-Fi: el PC envia les dades a Internet.", 2)
items = [("SENSOR", "Temperatura\nLlum\nHumitat"), ("micro:bit", "Lectura de dades\nper ràdio o sèrie"), ("WINDOWS", "USB + connector\n115200 bauds"), ("THINGSPEAK", "HTTPS + camps\nGràfics al núvol")]
xs = [0.64, 3.86, 7.08, 10.30]
for i, ((a, b), x) in enumerate(zip(items, xs)):
    rounded(s, x, 2.30, 2.35, 2.52, PALE)
    textbox(s, a, x + 0.14, 2.69, 2.07, 0.44, 23, BLUE, True, PP_ALIGN.CENTER)
    textbox(s, b, x + 0.12, 3.32, 2.10, 1.22, 17, INK, False, PP_ALIGN.CENTER)
    if i < 3:
        textbox(s, "→", x + 2.40, 3.10, 0.69, 0.58, 38, CYAN, True, PP_ALIGN.CENTER)
textbox(s, "La xarxa s'utilitza des de l'ordinador, no des de la placa.", 1.10, 5.65, 11, 0.63, 21, INK, True, PP_ALIGN.CENTER)

# 03 Materials
s = base("Què necessitem?", "Tot el necessari per començar en una sessió de classe.", 3)
elements = [
    ("01", "Micro:bit", "Una placa USB;\nopcionalment una\nsegona per ràdio"),
    ("02", "Cable USB", "Ha de transmetre\ndades, no només\ncarregar"),
    ("03", "PC Windows", "Windows 10/11,\nconnector i Internet"),
    ("04", "ThingSpeak", "Canal amb camps\ni Write API Key"),
]
for n, (num, title, detail) in enumerate(elements):
    x = 0.76 + n * 3.12
    rounded(s, x, 2.2, 2.72, 3.40, PALE)
    textbox(s, num, x + 0.22, 2.49, 0.9, 0.53, 26, CYAN, True)
    textbox(s, title, x + 0.22, 3.10, 2.30, 0.45, 23, NAVY, True)
    textbox(s, detail, x + 0.22, 3.81, 2.24, 1.40, 18, INK)

# 04 Format
s = base("El llenguatge de les dades", "Cada línia de la micro:bit representa els camps del canal.", 4)
rounded(s, 0.91, 2.05, 11.55, 1.00, NAVY)
textbox(s, "23,157,623", 1.15, 2.30, 10.7, 0.47, 32, CYAN, True, PP_ALIGN.CENTER)
textbox(s, "field1 = 23       field2 = 157       field3 = 623", 1.11, 3.37, 10.8, 0.48, 25, BLUE, True, PP_ALIGN.CENTER)
rounded(s, 0.91, 4.35, 11.55, 1.20, PALE)
textbox(s, "HORT,23,157,623", 1.15, 4.62, 10.7, 0.53, 28, INK, True, PP_ALIGN.CENTER)
textbox(s, "Es pot afegir una etiqueta textual inicial. Màxim: 8 valors.", 1.16, 5.89, 10.8, 0.49, 18, MUTED, False, PP_ALIGN.CENTER)

# 05 Setup
s = base("Primer ús en quatre passos", "ThingSpeak i el connector Windows.", 5)
steps = [
    "1 · Crea el canal ThingSpeak i activa els camps",
    "2 · Copia la Write API Key (no la Read API Key)",
    "3 · Connecta la micro:bit per USB i obre l'aplicació",
    "4 · Enganxa la clau i comprova que arriben els valors",
]
for i, step in enumerate(steps):
    y = 2.00 + i * 1.05
    rounded(s, 0.95, y, 11.50, 0.80, PALE)
    textbox(s, step, 1.24, y + 0.18, 10.9, 0.40, 22, INK, i == 3)
textbox(s, "No comparteixis ni fotografiïs la clau d'escriptura.", 1.08, 6.48, 11.1, 0.4, 17, BLUE, True)

# 06 GUI
s = base("Així és el connector", "Captura real de la finestra v5.1.4, sense placa connectada.", 6)
s.shapes.add_picture(str(SCREEN), Inches(1.02), Inches(1.83), width=Inches(11.25))
textbox(s, "Botons: Reinicia pont · Canvia API Key · Debug · Quant a · Surt", 1.08, 6.58, 11.1, 0.35, 17, BLUE, True, PP_ALIGN.CENTER)

# 07 Troubleshooting
s = base("I si alguna cosa no funciona?", "El botó Debug és el primer punt de diagnosi.", 7)
problems = [
    ("Sense micro:bit", "Revisa cable, placa i port USB."),
    ("Port ocupat", "Tanca MakeCode, Mu i terminals sèrie."),
    ("No hi ha dades", "Revisa CSV i grup de ràdio 23."),
    ("ThingSpeak rebutja", "Comprova la Write API Key i l'interval."),
]
for i, (title, desc) in enumerate(problems):
    x = 0.87 + (i % 2) * 6.16
    y = 2.12 + (i // 2) * 1.92
    rounded(s, x, y, 5.55, 1.47, PALE)
    textbox(s, title, x + 0.22, y + 0.16, 5.08, 0.42, 23, BLUE, True)
    textbox(s, desc, x + 0.22, y + 0.72, 5.08, 0.56, 18, INK)

# 08 Closing
s = base("Què podem investigar?", "Repte compartit: transformem dades en coneixement.", 8)
rounded(s, 0.88, 2.02, 11.62, 3.79, NAVY)
textbox(s, "ESTACIÓ METEOROLÒGICA", 1.32, 2.41, 10.76, 0.58, 31, WHITE, True, PP_ALIGN.CENTER)
textbox(s, "HORT ESCOLAR  ·  CONFORT A L'AULA  ·  COMPARACIÓ ENTRE CENTRES", 1.12, 3.48, 11.05, 1.00, 21, CYAN, True, PP_ALIGN.CENTER)
textbox(s, "Quines dades ens ajuden a millorar el nostre entorn?", 1.38, 4.84, 10.59, 0.50, 19, WHITE, False, PP_ALIGN.CENTER)
textbox(s, "Font obert: EUPL 1.2 · Reconstrucció de l'EXE original v5.1.4", 0.88, 6.37, 11.6, 0.35, 15, MUTED, False, PP_ALIGN.CENTER)

p.save(OUT)
print("GENERATED", OUT, "SLIDES", len(p.slides), "BYTES", OUT.stat().st_size)
