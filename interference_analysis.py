"""
TANQUE DE ONDAS - ANÁLISIS DE INTERFERENCIA
Detección de patrones de franjas de interferencia
"""

import numpy as np
from scipy import ndimage
import logging
from typing import Dict, List, Tuple, Optional

# Umbrales de validación para detectar patrones reales
MIN_FRINGES_FOR_PATTERN = 2        # Aceptar patrones circulares con pocas franjas
MIN_CONTRAST_THRESHOLD = 0.05      # Permitir contraste más bajo
MIN_REGULARITY_SCORE = 0.10        # Aceptar más irregularidad
MAX_SPACING_VARIATION = 1.0        # Permitir variación de espaciado muy alta (100%)

class InterferenceAnalyzer:
    # Analiza patrones de interferencia en images de ondas

    def __init__(self):
        self.logger = logging.getLogger('InterferenceAnalyzer')

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Recorta bordes oscuros, recorta outliers y normaliza a [0,1]."""
        img = image.astype(np.float32)
        h, w = img.shape

        # Recortar 5% de bordes para evitar marcos negros o saturaciones
        margin_h = max(1, int(0.05 * h))
        margin_w = max(1, int(0.05 * w))
        img = img[margin_h:h - margin_h, margin_w:w - margin_w]

        # Recorte de percentiles para reducir saturaciones extremas
        p1, p99 = np.percentile(img, [1, 99])
        if p99 - p1 > 1e-6:
            img = np.clip(img, p1, p99)

        # Normalizar a 0-1
        img = img - img.min()
        img = img / (img.max() + 1e-8)

        # Suavizado ligero para reducir ruido sal/pepa
        img = ndimage.gaussian_filter(img, sigma=1)
        return img

    def detect_fringes(self, image: np.ndarray, threshold: float = 0.5) -> Tuple[np.ndarray, int, List[dict]]:
        """
        Detecta franjas en imagen con validación de tamaño.
        
        Args:
            image: Imagen en escala de grises (0-255)
            threshold: Umbral para binarización (0-1)
        
        Returns:
            (imagen_etiquetada, num_franjas_validas, info_franjas)
        """
        # Imagen ya preprocesada en 0-1
        img_norm = image.astype(np.float32)

        # Binarizar con umbral adaptativo simple
        threshold_val = np.mean(img_norm) + threshold * np.std(img_norm)
        binary = (img_norm > threshold_val).astype(np.uint8)

        # Contar regiones conectadas (franjas potenciales)
        labeled, num_features = ndimage.label(binary)
        
        # Filtrar franjas por tamaño mínimo (evitar ruido)
        min_fringe_area = image.shape[0] * image.shape[1] * 0.0005  # 0.05% de la imagen
        min_fringe_length = min(image.shape) * 0.05  # 5% de dimensión menor
        
        valid_fringes = []
        valid_count = 0
        
        for i in range(1, num_features + 1):
            mask = (labeled == i)
            area = np.sum(mask)
            
            if area >= min_fringe_area:
                # Verificar que sea alargada (como una franja)
                y_indices, x_indices = np.where(mask)
                if len(y_indices) > 0:
                    height = np.max(y_indices) - np.min(y_indices) + 1
                    width = np.max(x_indices) - np.min(x_indices) + 1
                    aspect_ratio = max(height, width) / (min(height, width) + 1)
                    
                    # Permitir franjas más redondeadas (anillos parciales) con aspect ratio > 1.2
                    if aspect_ratio > 1.2 and max(height, width) >= min_fringe_length:
                        valid_count += 1
                        valid_fringes.append({
                            'id': i,
                            'area': area,
                            'center_x': np.mean(x_indices),
                            'center_y': np.mean(y_indices),
                            'aspect_ratio': aspect_ratio
                        })

        return labeled, valid_count, valid_fringes

    def estimate_fringe_spacing(self, image: np.ndarray) -> Dict:
        """
        Estima espaciado entre franjas con validación de regularidad.
        
        Returns:
            Dict con spacing_px, spacing_mm, orientation, regularidad
        """
        # Detectar franjas válidas
        labeled, num_fringes, fringe_info = self.detect_fringes(image)
        
        result = {
            "spacing_px": None,
            "spacing_mm": None,
            "num_fringes": num_fringes,
            "is_valid_pattern": False,
            "regularity_score": 0.0,
            "validation_message": ""
        }

        if num_fringes < MIN_FRINGES_FOR_PATTERN:
            result["validation_message"] = f"Muy pocas franjas ({num_fringes} < {MIN_FRINGES_FOR_PATTERN})"
            return result

        # Encontrar posiciones de franjas
        positions = [f['center_x'] for f in fringe_info]

        if len(positions) < 2:
            result["validation_message"] = "No hay suficientes franjas válidas para calcular espaciado"
            return result

        # Calcular espaciado entre franjas consecutivas
        positions = np.sort(np.array(positions))
        spacings = np.diff(positions)
        
        if len(spacings) == 0:
            result["validation_message"] = "No se pudo calcular espaciado"
            return result
        
        avg_spacing = np.mean(spacings)
        std_spacing = np.std(spacings)
        
        # Calcular regularidad (qué tan uniformes son los espaciados)
        if avg_spacing > 0:
            variation_coef = std_spacing / avg_spacing
            regularity_score = max(0, 1.0 - variation_coef)
        else:
            variation_coef = float('inf')
            regularity_score = 0.0
        
        result["spacing_px"] = avg_spacing
        result["spacing_mm"] = avg_spacing * 0.1  # Factor de calibración
        result["std_spacing"] = std_spacing
        result["regularity_score"] = regularity_score
        
        # Validar patrón
        if variation_coef > MAX_SPACING_VARIATION:
            result["validation_message"] = f"Espaciado muy irregular (variación {variation_coef:.0%} > {MAX_SPACING_VARIATION:.0%})"
        elif regularity_score < MIN_REGULARITY_SCORE:
            result["validation_message"] = f"Patrón no periódico (regularidad {regularity_score:.0%})"
        else:
            result["is_valid_pattern"] = True
            result["validation_message"] = f"✅ Patrón válido con {num_fringes} franjas"

        return result

    def calculate_contrast(self, image: np.ndarray) -> Tuple[float, bool, str]:
        """
        Calcula contraste Michelson de la imagen con validación.
        Para imágenes ya normalizadas (0-1), usa contraste directo.
        Para imágenes sin normalizar (0-255), usa contraste relativo.
        
        Returns:
            (contraste, es_valido, mensaje)
        """
        I_max = float(np.max(image))
        I_min = float(np.min(image))
        
        # Detectar si la imagen está normalizada (0-1) o no (0-255)
        if I_max <= 1.1:  # Imagen normalizada
            # Para 0-1, usar contraste simple
            contrast = I_max - I_min
            threshold = 0.05  # Umbral para 0-1
        else:  # Imagen sin normalizar (0-255 u 8-bit)
            # Para 0-255, usar contraste Michelson
            contrast = (I_max - I_min) / (I_max + I_min + 1e-8)
            threshold = MIN_CONTRAST_THRESHOLD
        
        # Criterio simple: si hay diferencia clara entre máx y mín, hay patrón
        is_significant = contrast > threshold
        
        if is_significant:
            message = f"✅ Contraste detectado: {contrast:.3f}"
        else:
            message = f"⚠️ Contraste bajo: {contrast:.3f}"
        
        return float(contrast), is_significant, message

    def analyze_interference(self, image: np.ndarray) -> Dict:
        """
        Análisis completo de interferencia con validación.
        
        Returns:
            Dict con todos los parámetros y estado de validación
        """
        img_proc = self.preprocess_image(image)

        fringe_info = self.estimate_fringe_spacing(img_proc)
        contrast, contrast_valid, contrast_message = self.calculate_contrast(img_proc)
        
        # Determinar visibilidad basada en contraste validado
        if contrast > 0.7:
            visibility = "Excelente"
            contrast_valid = True  # Forzar válido si contraste muy alto
        elif contrast > 0.5:
            visibility = "Buena"
            contrast_valid = True
        elif contrast > 0.3:
            visibility = "Moderada"
        elif contrast > 0.15:
            visibility = "Pobre"
        else:
            visibility = "No detectada"
        
        # Determinar si es un patrón de interferencia real
        is_real_interference = (
            fringe_info.get("is_valid_pattern", False) and 
            contrast_valid and
            fringe_info.get("num_fringes", 0) >= MIN_FRINGES_FOR_PATTERN
        )
        
        # Construir mensaje de validación
        validation_issues = []
        if not fringe_info.get("is_valid_pattern", False):
            validation_issues.append(fringe_info.get("validation_message", "Patrón no válido"))
        if not contrast_valid:
            validation_issues.append(contrast_message)
        
        if is_real_interference:
            validation_message = "✅ Patrón de interferencia detectado"
        elif validation_issues:
            validation_message = f"⚠️ {'; '.join(validation_issues)}"
        else:
            validation_message = "❌ No se detectó patrón de interferencia"

        return {
            **fringe_info,
            "contrast": contrast,
            "contrast_valid": contrast_valid,
            "visibility": visibility,
            "is_real_interference": is_real_interference,
            "validation_message": validation_message
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
