"""
TANQUE DE ONDAS - ANÁLISIS DE INTERFERENCIA
Detección de patrones de franjas de interferencia
"""

import numpy as np
from scipy import ndimage
import logging
from typing import Dict, List, Tuple

class InterferenceAnalyzer:
    # Analiza patrones de interferencia en images de ondas

    def __init__(self):
        self.logger = logging.getLogger('InterferenceAnalyzer')

    def detect_fringes(self, image: np.ndarray, threshold: float = 0.5) -> Tuple[np.ndarray, int]:
        # Detecta franjas en imagen
        # Args:
        #    image: Imagen en escala de grises (0-255)
        #    threshold: Umbral para binarización (0-1)
        # Returns:
        #    (imagen_binaria, num_franjas)

        # Normalizar
        img_norm = image.astype(np.float32) / 255.0

        # Binarizar
        threshold_val = np.mean(img_norm) + threshold * np.std(img_norm)
        binary = (img_norm > threshold_val).astype(np.uint8)

        # Contar regiones conectadas (franjas)
        labeled, num_features = ndimage.label(binary)

        return labeled, num_features

    def estimate_fringe_spacing(self, image: np.ndarray) -> Dict:
        # Estima espaciado entre franjas
        # Returns:
        #    Dict con spacing_px, spacing_mm, orientation

        # Detectar franjas
        labeled, num_fringes = self.detect_fringes(image)

        if num_fringes < 2:
            return {"spacing_px": None, "spacing_mm": None, "num_fringes": 0}

        # Encontrar posiciones de franjas
        positions = []
        for i in range(1, num_fringes + 1):
            mask = (labeled == i)
            if np.any(mask):
                y, x = np.where(mask)
                positions.append(np.mean(x))

        if len(positions) < 2:
            return {"spacing_px": None, "spacing_mm": None, "num_fringes": num_fringes}

        # Calcular espaciado promedio
        positions = np.sort(np.array(positions))
        spacings = np.diff(positions)
        avg_spacing = np.mean(spacings)

        return {
            "spacing_px": avg_spacing,
            "spacing_mm": avg_spacing * 0.1,  # Factor de calibración
            "num_fringes": num_fringes,
            "std_spacing": np.std(spacings)
        }

    def calculate_contrast(self, image: np.ndarray) -> float:
        # Calcula contraste Michelson de la imagen
        # Returns:
        #    Valor de contraste (0-1)

        I_max = np.max(image)
        I_min = np.min(image)

        contrast = (I_max - I_min) / (I_max + I_min + 1e-8)
        return float(contrast)

    def analyze_interference(self, image: np.ndarray) -> Dict:
        # Análisis completo de interferencia
        # Returns:
        #    Dict con todos los parámetros

        fringe_info = self.estimate_fringe_spacing(image)
        contrast = self.calculate_contrast(image)

        return {
            **fringe_info,
            "contrast": contrast,
            "visibility": "Excelente" if contrast > 0.7 else "Buena" if contrast > 0.5 else "Pobre"
        }


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Imagen de prueba con franjas
    x = np.linspace(0, 10, 512)
    y = np.linspace(0, 10, 512)
    X, Y = np.meshgrid(x, y)

    test_image = (127 + 100 * np.sin(2 * np.pi * X / 20)).astype(np.uint8)

    analyzer = InterferenceAnalyzer()
    result = analyzer.analyze_interference(test_image)

    print(f"Num Franjas: {result['num_fringes']}")
    print(f"Espaciado: {result['spacing_px']:.2f} px")
    print(f"Contraste: {result['contrast']:.3f}")
    print(f"Visibilidad: {result['visibility']}")
