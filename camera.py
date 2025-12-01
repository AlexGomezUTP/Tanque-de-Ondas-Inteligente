

TANQUE DE ONDAS - CAPTURA DE VIDEO
Módulo para capturar y procesar video de la cámara


import cv2
import numpy as np
from datetime import datetime
import logging
from typing import Optional, Tuple

class VideoCapture:
    # Captura video de cámara USB en tiempo real

    def __init__(self, camera_id: int = 0, width: int = 1920, height: int = 1080, fps: int = 30):
        # Inicializa captura de video
        # Args:
        #    camera_id: ID de cámara (típicamente 0 para principal)
        #    width: Ancho en píxeles
        #    height: Alto en píxeles
        #    fps: Frames por segundo

        self.cap = cv2.VideoCapture(camera_id)
        self.width = width
        self.height = height
        self.fps = fps

        # Configurar parámetros de cámara
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimizar buffer

        self.frame_count = 0
        self.start_time = datetime.now()

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('VideoCapture')

        if self.cap.isOpened():
            self.logger.info(f"Cámara abierta: {width}x{height} @ {fps} fps")
        else:
            self.logger.error("Error al abrir cámara")

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray], float]:
        # Captura siguiente frame
        # Returns:
        #    (éxito, frame, timestamp_ms)

        ret, frame = self.cap.read()

        if ret:
            self.frame_count += 1
            elapsed_ms = (datetime.now() - self.start_time).total_seconds() * 1000
            return ret, frame, elapsed_ms
        else:
            self.logger.warning("Error al capturar frame")
            return ret, None, 0.0

    def get_grayscale(self) -> Tuple[bool, Optional[np.ndarray], float]:
        # Captura frame en escala de grises
        ret, frame, ts = self.get_frame()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return ret, gray, ts
        return ret, None, ts

    def get_roi(self, x1: int, y1: int, x2: int, y2: int) -> Tuple[bool, Optional[np.ndarray], float]:
        # Captura región de interés (ROI)
        # Args:
        #    x1, y1, x2, y2: Coordenadas del rectángulo ROI

        ret, frame, ts = self.get_grayscale()
        if ret:
            roi = frame[y1:y2, x1:x2]
            return ret, roi, ts
        return ret, None, ts

    def release(self):
        # Libera recursos de cámara
        self.cap.release()
        self.logger.info(f"Cámara liberada. Total frames: {self.frame_count}")


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    cam = VideoCapture(camera_id=0)

    frame_count = 0
    while frame_count < 100:
        ret, frame, ts = cam.get_frame()
        if ret:
            cv2.imshow('Video', frame)
            print(f"Frame {frame_count} @ {ts:.1f} ms")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            frame_count += 1

    cam.release()
    cv2.destroyAllWindows()
