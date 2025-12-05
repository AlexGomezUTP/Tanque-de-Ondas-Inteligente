"""
GENERADOR DE VIDEO CON CONTRASTE ALTO - VERSIÓN FUNCIONAL
Este código SÍ genera patrones visibles de interferencia
"""

import cv2
import numpy as np

def generate_visible_wave_video(
    filename="video_ondas_visible.mp4",
    duration_sec=10,
    frequency_hz=10.0,
    tank_depth_cm=5.0
):
    """
    Genera video con ALTO CONTRASTE visible.
    Parámetros ajustados para que las ondas sean claramente visibles.
    """
    
    # Configuración video
    width, height = 640, 480
    fps = 30
    
    # Crear video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    if not out.isOpened():
        print("❌ Error: No se pudo crear el archivo de video")
        print("Verifica que tengas ffmpeg o codec mp4v instalado")
        return None
    
    # ========== FÍSICA ==========
    g = 9.81
    h = tank_depth_cm / 100.0
    c = np.sqrt(g * h)
    wavelength_m = c / frequency_hz
    wavelength_mm = wavelength_m * 1000
    wavelength_px = wavelength_mm  # 1px = 1mm
    
    k_px = 2 * np.pi / wavelength_px
    omega = 2 * np.pi * frequency_hz
    
    # ========== AMPLITUD ALTA PARA VISIBILIDAD ==========
    # La clave: amplitud muy grande para shadowgraphy
    A_px = 80.0  # ¡Mucho mayor que antes!
    
    print(f"📊 Configuración del video:")
    print(f"   λ = {wavelength_mm:.2f} mm = {wavelength_px:.1f} px")
    print(f"   Frecuencia: {frequency_hz} Hz")
    print(f"   Profundidad: {tank_depth_cm} cm")
    print(f"   Amplitud: {A_px} píxeles (alta para visibilidad)")
    
    # Malla espacial
    x = np.arange(width, dtype=np.float32)
    y = np.arange(height, dtype=np.float32)
    X, Y = np.meshgrid(x, y)
    
    # Dos fuentes puntuales
    separation_px = 5 * wavelength_px
    src1 = np.array([width/2 - separation_px/2, height/2])
    src2 = np.array([width/2 + separation_px/2, height/2])
    
    R1 = np.sqrt((X - src1[0])**2 + (Y - src1[1])**2)
    R2 = np.sqrt((X - src2[0])**2 + (Y - src2[1])**2)
    
    print(f"   Separación de fuentes: {separation_px:.0f} px ({separation_px/wavelength_px:.1f}λ)")
    print(f"\n🎬 Generando {duration_sec}s de video...")
    
    for frame_idx in range(duration_sec * fps):
        t = frame_idx / fps
        
        # ========== GENERAR CAMPO DE ONDAS ==========
        # Atenuación geométrica: 1/√r
        wave1 = (A_px / np.sqrt(R1 + 50)) * np.sin(k_px * R1 - omega * t)
        wave2 = (A_px / np.sqrt(R2 + 50)) * np.sin(k_px * R2 - omega * t)
        
        # Superposición (interferencia)
        eta = wave1 + wave2
        
        # ========== TÉCNICA SHADOWGRAPHY ==========
        # Opción 1: Segundo derivado (Laplaciano) - Más físico
        # Simula cómo se ve la luz refractada por las ondas
        
        # Calcular segundo derivado (curvatura)
        # Esto es lo que realmente se ve en un tanque de ondas iluminado
        eta_smooth = cv2.GaussianBlur(eta.astype(np.float32), (5, 5), 1.0)
        laplacian = cv2.Laplacian(eta_smooth, cv2.CV_32F, ksize=5)
        
        # CLAVE: Mapeo con MUCHO contraste
        intensity = 128 + laplacian * 5.0  # Factor 5.0 para alto contraste
        
        # Opción 2: Gradiente directo (más simple pero efectivo)
        # Descomenta si Laplaciano no funciona:
        # grad_x = cv2.Sobel(eta, cv2.CV_32F, 1, 0, ksize=5)
        # grad_y = cv2.Sobel(eta, cv2.CV_32F, 0, 1, ksize=5)
        # grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        # intensity = 128 + grad_magnitude * 2.0
        
        # ========== AGREGAR RUIDO REALISTA ==========
        noise = np.random.normal(0, 5, (height, width))
        
        final = intensity + noise
        final = np.clip(final, 0, 255).astype(np.uint8)
        
        # ========== MEJORAR CONTRASTE ==========
        # Ecualización de histograma adaptativa (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        final = clahe.apply(final)
        
        # Convertir a BGR
        frame_bgr = cv2.cvtColor(final, cv2.COLOR_GRAY2BGR)
        
        # ========== ANOTACIONES ==========
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Texto con fondo para legibilidad
        def draw_text_with_bg(img, text, pos, font_scale, color, bg_color):
            thickness = 2
            (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
            cv2.rectangle(img, (pos[0]-5, pos[1]-text_height-5), 
                         (pos[0]+text_width+5, pos[1]+baseline+5), bg_color, -1)
            cv2.putText(img, text, pos, font, font_scale, color, thickness)
        
        draw_text_with_bg(frame_bgr, f"t={t:.2f}s | f={frequency_hz}Hz", 
                         (10, 25), 0.6, (0, 255, 0), (0, 0, 0))
        
        draw_text_with_bg(frame_bgr, f"lambda={wavelength_mm:.1f}mm", 
                         (10, 55), 0.5, (0, 255, 0), (0, 0, 0))
        
        # Barra de escala
        scale_length_px = 50  # 50mm = 50px
        cv2.line(frame_bgr, (width-70, height-30), (width-20, height-30), (255,255,255), 4)
        cv2.line(frame_bgr, (width-70, height-35), (width-70, height-25), (255,255,255), 2)
        cv2.line(frame_bgr, (width-20, height-35), (width-20, height-25), (255,255,255), 2)
        draw_text_with_bg(frame_bgr, "50mm", (width-70, height-45), 
                         0.4, (255,255,255), (0, 0, 0))
        
        # Marcar fuentes
        cv2.circle(frame_bgr, (int(src1[0]), int(src1[1])), 5, (255, 0, 0), -1)
        cv2.circle(frame_bgr, (int(src2[0]), int(src2[1])), 5, (255, 0, 0), -1)
        
        out.write(frame_bgr)
        
        # Progreso
        if (frame_idx + 1) % fps == 0:
            progress = 100 * (frame_idx + 1) / (duration_sec * fps)
            print(f"   Progreso: {progress:.0f}% ({frame_idx+1}/{duration_sec*fps} frames)")
    
    out.release()
    
    print(f"\n✅ Video generado: {filename}")
    print(f"   Duración: {duration_sec} segundos")
    print(f"   FPS: {fps}")
    print(f"   Resolución: {width}x{height}")
    print(f"\n📋 Para análisis en Streamlit:")
    print(f"   - Calibración: 1.0 px/mm")
    print(f"   - Frecuencia: {frequency_hz} Hz")
    print(f"   - Profundidad: {tank_depth_cm} cm")
    print(f"   - λ esperada: ~{wavelength_mm:.1f} mm")
    print(f"   - Error esperado: < 5%")
    
    return filename


if __name__ == "__main__":
    # Generar video principal
    video_file = generate_visible_wave_video(
        filename="video_10hz_5cm_VISIBLE.mp4",
        duration_sec=10,
        frequency_hz=10.0,
        tank_depth_cm=5.0
    )
    
    if video_file:
        print(f"\n🎉 ¡Listo! Abre {video_file} para verificar que se ven las ondas.")
        print("   Deberías ver claramente los círculos concéntricos y patrones de interferencia.")
    else:
        print("\n❌ Error generando video. Verifica:")
        print("   1. Que opencv-python esté instalado: pip install opencv-python")
        print("   2. Que tengas permisos de escritura en el directorio")
        print("   3. En Windows, instala: pip install opencv-python-headless")
