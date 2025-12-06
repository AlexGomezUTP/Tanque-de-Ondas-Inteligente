"""
TANQUE DE ONDAS - GENERADOR DE VIDEO DE PRUEBA
Crea videos sintéticos con parámetros conocidos para validar análisis
"""

import cv2
import numpy as np

def crear_video_onda_simple(filename="video_onda_simple.mp4", wavelength_px=50):
    """
    Crea video con onda plana simple de wavelength conocido.
    Útil para verificar que el análisis FFT detecta correctamente.
    
    Args:
        filename: Nombre del archivo de salida
        wavelength_px: Longitud de onda en píxeles (valor conocido para verificar)
    """
    width, height = 640, 480
    fps = 30
    seconds = 3
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    x = np.arange(width)
    y = np.arange(height)
    X, Y = np.meshgrid(x, y)
    
    # Número de onda k = 2π / λ
    k = 2 * np.pi / wavelength_px
    w = 0.3  # Frecuencia angular (velocidad de propagación)
    
    print(f"Generando {filename}...")
    print(f"  → Wavelength configurado: {wavelength_px} px")
    print(f"  → Esperado en análisis FFT: ~{wavelength_px} px")
    
    for t in range(seconds * fps):
        # Onda plana propagándose en dirección X
        Z = 127 + 100 * np.sin(k * X - w * t)
        
        img = np.clip(Z, 0, 255).astype(np.uint8)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        out.write(img_bgr)
        
    out.release()
    print(f"  ✅ Video generado: {filename}")
    return wavelength_px


def crear_video_interferencia(filename="video_interferencia.mp4", wavelength_px=60, separacion_fuentes=240):
    """
    Crea video con patrón de interferencia de dos fuentes puntuales.
    
    Args:
        filename: Nombre del archivo de salida
        wavelength_px: Longitud de onda en píxeles
        separacion_fuentes: Distancia entre las dos fuentes en píxeles
    """
    width, height = 640, 480
    fps = 30
    seconds = 5
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    x = np.arange(width)
    y = np.arange(height)
    X, Y = np.meshgrid(x, y)
    
    # Posición de las dos fuentes (centradas verticalmente)
    centro_x = width // 2
    centro_y = height // 2
    fuente1_x = centro_x - separacion_fuentes // 2
    fuente2_x = centro_x + separacion_fuentes // 2
    
    # Número de onda
    k = 2 * np.pi / wavelength_px
    w = 0.5
    
    print(f"Generando {filename}...")
    print(f"  → Wavelength: {wavelength_px} px")
    print(f"  → Separación fuentes: {separacion_fuentes} px")
    print(f"  → Fuente 1: ({fuente1_x}, {centro_y})")
    print(f"  → Fuente 2: ({fuente2_x}, {centro_y})")
    
    for t in range(seconds * fps):
        # Distancia desde cada fuente
        R1 = np.sqrt((X - fuente1_x)**2 + (Y - centro_y)**2)
        R2 = np.sqrt((X - fuente2_x)**2 + (Y - centro_y)**2)
        
        # Superposición de ondas circulares
        Z = 100 * np.sin(k * R1 - w * t) + 100 * np.sin(k * R2 - w * t)
        
        img = np.clip(Z + 127, 0, 255).astype(np.uint8)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        out.write(img_bgr)
        
    out.release()
    print(f"  ✅ Video generado: {filename}")
    return wavelength_px


def crear_video_franjas(filename="video_franjas.mp4", num_franjas=10):
    """
    Crea video con franjas de interferencia estáticas (patrón conocido).
    Ideal para verificar detección de franjas.
    
    Args:
        filename: Nombre del archivo de salida
        num_franjas: Número de franjas en la imagen
    """
    width, height = 640, 480
    fps = 30
    seconds = 2
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    x = np.arange(width)
    y = np.arange(height)
    X, Y = np.meshgrid(x, y)
    
    # Espaciado entre franjas
    espaciado = width / num_franjas
    wavelength_px = espaciado
    
    print(f"Generando {filename}...")
    print(f"  → Número de franjas: {num_franjas}")
    print(f"  → Espaciado: {espaciado:.1f} px")
    print(f"  → Wavelength esperado: {wavelength_px:.1f} px")
    
    for t in range(seconds * fps):
        # Franjas verticales con ligero movimiento
        phase = t * 0.05
        Z = 127 + 120 * np.sin(2 * np.pi * X / wavelength_px + phase)
        
        img = np.clip(Z, 0, 255).astype(np.uint8)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        out.write(img_bgr)
        
    out.release()
    print(f"  ✅ Video generado: {filename}")
    return num_franjas, wavelength_px


def crear_video_prueba(filename="video_prueba_ondas.mp4"):
    """Función original - crea video de interferencia por defecto"""
    return crear_video_interferencia(filename, wavelength_px=63, separacion_fuentes=240)


if __name__ == "__main__":
    print("=" * 60)
    print("GENERADOR DE VIDEOS DE PRUEBA - TANQUE DE ONDAS")
    print("=" * 60)
    print()
    
    # 1. Video con onda simple (fácil de verificar wavelength)
    wl1 = crear_video_onda_simple("video_onda_simple.mp4", wavelength_px=50)
    print()
    
    # 2. Video con interferencia de dos fuentes
    wl2 = crear_video_interferencia("video_interferencia.mp4", wavelength_px=60, separacion_fuentes=240)
    print()
    
    # 3. Video con franjas conocidas
    nf, wl3 = crear_video_franjas("video_franjas.mp4", num_franjas=10)
    print()
    
    # 4. Video por defecto (compatibilidad)
    crear_video_prueba("video_prueba_ondas.mp4")
    print()
    
    print("=" * 60)
    print("VALORES ESPERADOS PARA VERIFICACIÓN:")
    print("=" * 60)
    print(f"  video_onda_simple.mp4    → Wavelength: {wl1} px")
    print(f"  video_interferencia.mp4  → Wavelength: {wl2} px")
    print(f"  video_franjas.mp4        → Franjas: {nf}, Espaciado: {wl3:.1f} px")
    print(f"  video_prueba_ondas.mp4   → Wavelength: ~63 px")
    print()
    print("Usa estos valores para verificar que el análisis FFT funciona correctamente.")
    print("=" * 60)
