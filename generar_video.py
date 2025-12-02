import cv2
import numpy as np

def crear_video_prueba(filename="video_prueba_ondas.mp4"):
    # Configuración
    width, height = 640, 480
    fps = 30
    seconds = 5
    
    # Iniciar escritor de video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    # Crear malla de coordenadas
    x = np.arange(width)
    y = np.arange(height)
    X, Y = np.meshgrid(x, y)
    
    # Simular dos fuentes de ondas (Interferencia)
    print(f"Generando {filename}...")
    for t in range(seconds * fps):
        # Ecuación de onda matemática
        # Fuente 1 (Izquierda) y Fuente 2 (Derecha)
        R1 = np.sqrt((X - 200)**2 + (Y - 240)**2)
        R2 = np.sqrt((X - 440)**2 + (Y - 240)**2)
        
        # Frecuencia angular (w) y número de onda (k)
        w = 0.5 
        k = 0.1
        
        # Superposición de ondas
        Z = 100 * np.sin(k*R1 - w*t) + 100 * np.sin(k*R2 - w*t)
        
        # Convertir a imagen (0-255)
        img = np.clip(Z + 127, 0, 255).astype(np.uint8)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        
        out.write(img_bgr)
        
    out.release()
    print("¡Video generado exitosamente!")

if __name__ == "__main__":
    crear_video_prueba()
