"""
GENERADOR DE VIDEO SIMPLE Y FUNCIONAL
Genera video_ondas_70mm.mp4 con patrones visibles
"""

import numpy as np
import cv2

print("🎬 Iniciando generación de video...")
print("="*60)

# ========== CONFIGURACIÓN ==========
filename = "video_ondas_70mm.mp4"
width, height = 640, 480
fps = 30
duration = 10

# Física
g = 9.81
h = 0.05  # 5 cm
f = 10.0   # 10 Hz
c = np.sqrt(g * h)
wavelength_mm = (c / f) * 1000  # ≈ 70 mm
wavelength_px = wavelength_mm    # 1px = 1mm

k = 2 * np.pi / wavelength_px
omega = 2 * np.pi * f

print(f"λ teórica: {wavelength_mm:.2f} mm = {wavelength_px:.1f} px")
print(f"Frecuencia: {f} Hz")
print(f"Profundidad: {h*100} cm")
print("="*60)

# ========== CREAR VIDEO ==========
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

if not out.isOpened():
    print("\n❌ ERROR: No se pudo crear el video")
    print("\n🔧 Soluciones:")
    print("1. Instalar opencv: pip install opencv-python")
    print("2. En Windows: pip install opencv-python-headless")
    print("3. Verificar permisos de escritura")
    exit(1)

print(f"\n✅ Video writer creado correctamente")
print(f"Generando {duration*fps} frames...")

# Malla espacial
x = np.arange(width, dtype=np.float32)
y = np.arange(height, dtype=np.float32)
X, Y = np.meshgrid(x, y)

# Dos fuentes para interferencia
sep = 6 * wavelength_px  # Separación: 6 longitudes de onda
src1 = np.array([width/2 - sep/2, height/2])
src2 = np.array([width/2 + sep/2, height/2])

R1 = np.sqrt((X - src1[0])**2 + (Y - src1[1])**2)
R2 = np.sqrt((X - src2[0])**2 + (Y - src2[1])**2)

print(f"Fuente 1: ({src1[0]:.0f}, {src1[1]:.0f})")
print(f"Fuente 2: ({src2[0]:.0f}, {src2[1]:.0f})")
print(f"Separación: {sep:.0f} px = {sep/wavelength_px:.1f}λ")

# Generar frames
for i in range(duration * fps):
    t = i / fps
    
    # ========== ONDAS CON ALTA AMPLITUD ==========
    A = 100.0  # Amplitud MUY ALTA para visibilidad
    
    # Ondas cilíndricas con atenuación geométrica
    wave1 = (A / np.sqrt(R1 + 50)) * np.sin(k * R1 - omega * t)
    wave2 = (A / np.sqrt(R2 + 50)) * np.sin(k * R2 - omega * t)
    
    # Superposición (interferencia)
    eta = wave1 + wave2
    
    # ========== MAPEAR A INTENSIDAD ==========
    # Método directo (más visible que Laplaciano)
    intensity = 128 + eta * 0.8
    
    # Clip y convertir
    frame = np.clip(intensity, 0, 255).astype(np.uint8)
    
    # ========== MEJORAR CONTRASTE ==========
    # Ecualización adaptativa
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    frame = clahe.apply(frame)
    
    # Convertir a BGR
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    
    # ========== AÑADIR INFORMACIÓN ==========
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    # Fondo negro para texto
    overlay = frame_bgr.copy()
    cv2.rectangle(overlay, (0, 0), (400, 80), (0, 0, 0), -1)
    frame_bgr = cv2.addWeighted(frame_bgr, 0.7, overlay, 0.3, 0)
    
    # Texto
    cv2.putText(frame_bgr, f"t = {t:.2f}s | f = {f}Hz", 
               (10, 25), font, 0.6, (0, 255, 0), 2)
    cv2.putText(frame_bgr, f"lambda = {wavelength_mm:.1f}mm (teorica)", 
               (10, 50), font, 0.5, (0, 255, 0), 1)
    cv2.putText(frame_bgr, f"h = {h*100}cm | Aguas someras", 
               (10, 70), font, 0.4, (150, 150, 255), 1)
    
    # Barra de escala
    cv2.line(frame_bgr, (width-70, height-25), (width-20, height-25), (255,255,255), 4)
    cv2.line(frame_bgr, (width-70, height-30), (width-70, height-20), (255,255,255), 2)
    cv2.line(frame_bgr, (width-20, height-30), (width-20, height-20), (255,255,255), 2)
    cv2.putText(frame_bgr, "50mm", (width-65, height-40), font, 0.4, (255,255,255), 1)
    
    # Marcar fuentes (puntos rojos)
    cv2.circle(frame_bgr, (int(src1[0]), int(src1[1])), 6, (0, 0, 255), -1)
    cv2.circle(frame_bgr, (int(src2[0]), int(src2[1])), 6, (0, 0, 255), -1)
    
    # Escribir frame
    out.write(frame_bgr)
    
    # Progreso
    if (i + 1) % 30 == 0:
        progress = 100 * (i + 1) / (duration * fps)
        print(f"  Progreso: {progress:.0f}% ({i+1}/{duration*fps} frames)")

out.release()

print(f"\n{'='*60}")
print("✅ ¡VIDEO GENERADO EXITOSAMENTE!")
print(f"{'='*60}")
print(f"\n📁 Archivo: {filename}")
print(f"📏 Resolución: {width}x{height}")
print(f"🎞️  FPS: {fps}")
print(f"⏱️  Duración: {duration} segundos")
print(f"\n📊 PARÁMETROS DEL VIDEO:")
print(f"   • λ teórica: {wavelength_mm:.2f} mm")
print(f"   • Frecuencia: {f} Hz")
print(f"   • Profundidad: {h*100} cm")
print(f"   • Calibración: 1.0 px/mm")
print(f"\n📋 CONFIGURACIÓN PARA STREAMLIT:")
print(f"   1. Cargar: {filename}")
print(f"   2. Calibración: 1.0 px/mm")
print(f"   3. Frecuencia: {f} Hz")
print(f"   4. Profundidad: {h*100} cm")
print(f"   5. λ esperada: ~{wavelength_mm:.0f} mm")
print(f"   6. Error esperado: < 5%")
print(f"\n🎬 Reproduce el video para verificar que se ven las ondas")
print("="*60)
