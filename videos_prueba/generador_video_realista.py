import cv2
import numpy as np

def generate_realistic_ripple_video(filename="tanque_ondas_realista.mp4"):
    """
    Genera un video MP4 realista simulando el tanque de ondas del proyecto.
    Características:
    - Frecuencia: 10 Hz (Interferencia visible)
    - Dos fuentes puntuales (Interferencia constructiva/destructiva)
    - Efecto Shadowgraphy (Caústicas y alto contraste)
    - Ruido simulado (Grano de cámara y superficie irregular)
    """
    # Configuración de video
    width, height = 640, 480
    fps = 30
    duration_sec = 10  # 10 segundos de prueba

    # Crear escritor de video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

    if not out.isOpened():
        print("Error: No se pudo crear el archivo de video. Intenta instalar openh264 o ffmpeg.")
        return

    # Parámetros Físicos (Aprox. profundidad 5cm)
    # Escala: 640px = 80cm -> 1cm = 8px
    px_per_cm = 8.0

    # Parámetros de Onda
    freq_hz = 10.0             # 10 Hz
    velocity_cm_s = 50.0       # ~50 cm/s
    wavelength_cm = velocity_cm_s / freq_hz  # 5 cm
    wavelength_px = wavelength_cm * px_per_cm # ~40 px

    k = 2 * np.pi / wavelength_px
    omega = 2 * np.pi * freq_hz
    damping = 0.005 # Atenuación con la distancia

    # Malla de coordenadas
    x = np.arange(width)
    y = np.arange(height)
    X, Y = np.meshgrid(x, y)

    # Fuentes (Dos fuentes puntuales separadas 20cm = 160px)
    src1 = (width // 2 - 80, height // 2)
    src2 = (width // 2 + 80, height // 2)

    # Precalcular distancias
    R1 = np.sqrt((X - src1[0])**2 + (Y - src1[1])**2)
    R2 = np.sqrt((X - src2[0])**2 + (Y - src2[1])**2)

    # Ruido estático (irregularidades del fondo/luz)
    noise_static = np.random.normal(0, 5, (height, width)).astype(np.float32)

    print(f"Generando video realista: {filename} ({duration_sec}s)...")

    for frame_idx in range(duration_sec * fps):
        t = frame_idx / fps

        # Función de Onda: A * sin(k*r - w*t) / sqrt(r)
        # Evitamos división por cero sumando 10 a R
        amp1 = 1500 / (np.sqrt(R1) + 10) * np.exp(-damping * R1)
        amp2 = 1500 / (np.sqrt(R2) + 10) * np.exp(-damping * R2)

        wave1 = amp1 * np.sin(k * R1 - omega * t)
        wave2 = amp2 * np.sin(k * R2 - omega * t)

        total_wave = wave1 + wave2

        # Simulación de Shadowgraphy (Mapeo no lineal de intensidad)
        intensity = 128 + total_wave * 3.0

        # Efecto Caústico: Agudizar las partes brillantes
        intensity = np.where(intensity > 128, 128 + (intensity-128)**1.1, intensity)

        # Ruido dinámico (grano de sensor)
        noise_dynamic = np.random.normal(0, 2, (height, width)).astype(np.float32)

        final_img = intensity + noise_static + noise_dynamic

        # Clipping 0-255
        final_img = np.clip(final_img, 0, 255).astype(np.uint8)

        # Convertir a BGR para video
        frame_bgr = cv2.cvtColor(final_img, cv2.COLOR_GRAY2BGR)

        # Agregar Timecode
        cv2.putText(frame_bgr, f"T={t:.2f}s | f={freq_hz}Hz", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        out.write(frame_bgr)

    out.release()
    print(f"Video completado: {filename}")

if __name__ == "__main__":
    generate_realistic_ripple_video()
