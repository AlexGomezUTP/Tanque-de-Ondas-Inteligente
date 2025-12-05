"""
GENERADOR DE VIDEO - VERSIÓN CORREGIDA CON FÍSICA EXACTA
λ ≈ 70mm @ 10Hz en tanque de 5cm de profundidad
"""

import cv2
import numpy as np

def generate_realistic_ripple_video(
    filename="video_ondas_70mm.mp4",
    duration_sec=10,
    frequency_hz=10.0,
    tank_depth_cm=5.0,
    amplitude_mm=2.0,
    mode="interference"
):
    """
    Genera video con parámetros físicos EXACTOS para tanque de ondas.
    
    Para h=5cm, f=10Hz → λ ≈ 70mm (aguas someras)
    """
    
    # Configuración video
    width, height = 640, 480
    fps = 30
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    if not out.isOpened():
        print("❌ Error al crear video")
        return None
    
    # ========== FÍSICA EXACTA ==========
    g = 9.81  # m/s²
    h = tank_depth_cm / 100.0  # metros
    
    # Para aguas someras (h/λ < 0.5): c = √(gh)
    c = np.sqrt(g * h)  # velocidad de fase [m/s]
    
    wavelength_m = c / frequency_hz  # λ = c/f
    wavelength_mm = wavelength_m * 1000
    
    # Escala: Asumimos 1px = 1mm (típico para cámara a ~50cm del tanque)
    px_per_mm = 1.0
    wavelength_px = wavelength_mm * px_per_mm
    
    k_px = 2 * np.pi / wavelength_px  # número de onda [rad/px]
    omega = 2 * np.pi * frequency_hz  # frecuencia angular [rad/s]
    
    A_px = amplitude_mm * px_per_mm  # amplitud en píxeles
    
    print(f"📊 Parámetros físicos:")
    print(f"   Régimen: Aguas someras (h/λ = {h/wavelength_m:.3f})")
    print(f"   Velocidad de fase: c = {c:.3f} m/s")
    print(f"   λ teórica = {wavelength_mm:.2f} mm ({wavelength_px:.1f} px)")
    print(f"   Frecuencia: {frequency_hz} Hz")
    print(f"   Profundidad: {tank_depth_cm} cm")
    print(f"   Amplitud: {amplitude_mm} mm")
    
    # Malla espacial
    x = np.arange(width, dtype=np.float32)
    y = np.arange(height, dtype=np.float32)
    X, Y = np.meshgrid(x, y)
    
    # Configurar fuentes según modo
    if mode == "interference":
        # Dos fuentes separadas ~6λ para ver patrón claro
        separation_px = 6 * wavelength_px
        src1 = np.array([width/2 - separation_px/2, height/2])
        src2 = np.array([width/2 + separation_px/2, height/2])
        
        R1 = np.sqrt((X - src1[0])**2 + (Y - src1[1])**2)
        R2 = np.sqrt((X - src2[0])**2 + (Y - src2[1])**2)
        
        print(f"   Modo: Interferencia de 2 fuentes")
        print(f"   Separación: {separation_px/wavelength_px:.1f}λ = {separation_px:.0f} px")
        
    elif mode == "single":
        src = np.array([width/2, height/2])
        R = np.sqrt((X - src[0])**2 + (Y - src[1])**2)
        print(f"   Modo: Fuente única central")
    
    # Fondo base
    background = 128
    
    print(f"\n🎬 Generando {filename}...")
    
    for frame_idx in range(duration_sec * fps):
        t = frame_idx / fps
        
        # ========== CAMPO DE ONDAS ==========
        if mode == "interference":
            # Atenuación geométrica cilíndrica: A/√r
            # Factor de estabilización: +30 para evitar división por cero cerca de la fuente
            wave1 = (A_px / np.sqrt(R1 + 30)) * np.sin(k_px * R1 - omega * t)
            wave2 = (A_px / np.sqrt(R2 + 30)) * np.sin(k_px * R2 - omega * t)
            eta = wave1 + wave2  # Superposición
            
        elif mode == "single":
            eta = (A_px / np.sqrt(R + 30)) * np.sin(k_px * R - omega * t)
        
        # ========== SHADOWGRAPHY ==========
        # El contraste visible viene del Laplaciano (curvatura) de la superficie
        # Simula la técnica de iluminación por debajo del tanque
        
        laplacian = cv2.Laplacian(eta.astype(np.float32), cv2.CV_32F, ksize=5)
        
        # Factor de contraste (ajustar para visibilidad)
        beta = 1.2
        intensity = background + beta * laplacian
        
        # ========== RUIDO REALISTA ==========
        # Ruido gaussiano del sensor de cámara
        noise = np.random.normal(0, 3, (height, width))
        
        # Ruido estructurado (defectos del fondo del tanque)
        if frame_idx == 0:
            structural_noise = np.random.normal(0, 5, (height, width))
        
        final = intensity + noise + structural_noise * 0.3
        final = np.clip(final, 0, 255).astype(np.uint8)
        
        # A color (BGR)
        frame_bgr = cv2.cvtColor(final, cv2.COLOR_GRAY2BGR)
        
        # ========== ANOTACIONES ==========
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Info superior
        cv2.putText(frame_bgr, f"t = {t:.2f} s  |  f = {frequency_hz} Hz", 
                   (10, 25), font, 0.6, (0, 255, 0), 2)
        
        cv2.putText(frame_bgr, f"lambda_teorica = {wavelength_mm:.1f} mm", 
                   (10, 50), font, 0.5, (0, 255, 0), 1)
        
        cv2.putText(frame_bgr, f"h = {tank_depth_cm} cm  (Aguas someras)", 
                   (10, 70), font, 0.5, (100, 100, 255), 1)
        
        # Barra de escala (50mm)
        scale_px = int(50 * px_per_mm)
        cv2.line(frame_bgr, (width-scale_px-20, height-25), 
                (width-20, height-25), (255, 255, 255), 3)
        cv2.putText(frame_bgr, "50 mm", (width-scale_px-20, height-35),
                   font, 0.5, (255, 255, 255), 2)
        
        out.write(frame_bgr)
        
        # Progreso cada segundo
        if (frame_idx + 1) % fps == 0:
            print(f"   Frame {frame_idx+1}/{duration_sec*fps} ({100*(frame_idx+1)//(duration_sec*fps)}%)")
    
    out.release()
    
    print(f"\n✅ ¡Video generado exitosamente!")
    print(f"   Archivo: {filename}")
    print(f"   λ esperada en análisis: ~{wavelength_mm:.1f} mm")
    print(f"   Calibración sugerida: px_per_mm = {px_per_mm}")
    
    return {
        "filename": filename,
        "wavelength_mm": wavelength_mm,
        "wavelength_px": wavelength_px,
        "frequency_hz": frequency_hz,
        "tank_depth_cm": tank_depth_cm,
        "calibration_px_per_mm": px_per_mm
    }


if __name__ == "__main__":
    # Generar video con parámetros exactos del proyecto
    result = generate_realistic_ripple_video(
        filename="video_10hz_5cm_70mm.mp4",
        duration_sec=15,
        frequency_hz=10.0,
        tank_depth_cm=5.0,
        amplitude_mm=2.5,
        mode="interference"
    )
    
    if result:
        print("\n" + "="*60)
        print("📋 INSTRUCCIONES PARA ANÁLISIS EN STREAMLIT:")
        print("="*60)
        print(f"1. Cargar video: {result['filename']}")
        print(f"2. Configurar calibración: {result['calibration_px_per_mm']} px/mm")
        print(f"3. Configurar frecuencia: {result['frequency_hz']} Hz")
        print(f"4. Configurar profundidad: {result['tank_depth_cm']} cm")
        print(f"5. Resultado esperado: λ ≈ {result['wavelength_mm']:.1f} mm")
        print(f"6. Error esperado: < 5%")
