"""
TANQUE DE ONDAS - ANÁLISIS DE INTERFERENCIA
Detección de patrones de franjas de interferencia
"""

import numpy as np
from scipy import ndimage
import logging
from typing import Dict, List, Tuple, Optional

# Umbrales de validación para detectar patrones reales
MIN_FRINGES_FOR_PATTERN = 3        # Mínimo de franjas para considerar patrón válido
MIN_CONTRAST_THRESHOLD = 0.15      # Contraste mínimo para franjas visibles
MIN_REGULARITY_SCORE = 0.3         # Regularidad mínima en espaciado
MAX_SPACING_VARIATION = 0.5        # Variación máxima permitida en espaciado (50%)

class InterferenceAnalyzer:
    # Analiza patrones de interferencia en images de ondas

    def __init__(self):
        self.logger = logging.getLogger('InterferenceAnalyzer')

    def detect_fringes(self, image: np.ndarray, threshold: float = 0.5) -> Tuple[np.ndarray, int, List[dict]]:
        """
        Detecta franjas en imagen con validación de tamaño.
        
        Args:
            image: Imagen en escala de grises (0-255)
            threshold: Umbral para binarización (0-1)
        
        Returns:
            (imagen_etiquetada, num_franjas_validas, info_franjas)
        """
        # Normalizar
        img_norm = image.astype(np.float32) / 255.0

        # Binarizar
        threshold_val = np.mean(img_norm) + threshold * np.std(img_norm)
        binary = (img_norm > threshold_val).astype(np.uint8)

        # Contar regiones conectadas (franjas potenciales)
        labeled, num_features = ndimage.label(binary)
        
        # Filtrar franjas por tamaño mínimo (evitar ruido)
        min_fringe_area = image.shape[0] * image.shape[1] * 0.001  # 0.1% de la imagen
        min_fringe_length = min(image.shape) * 0.1  # 10% de dimensión menor
        
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
                    
                    # Una franja debe ser alargada (aspect ratio > 2)
                    if aspect_ratio > 2 and max(height, width) >= min_fringe_length:
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
        
        Returns:
            (contraste, es_valido, mensaje)
        """
        I_max = np.max(image)
        I_min = np.min(image)

        contrast = (I_max - I_min) / (I_max + I_min + 1e-8)
        
        # Verificar si el contraste es estadísticamente significativo
        # Una imagen de ruido puro tiene cierto contraste natural
        
        # Calcular contraste "esperado" por ruido
        std_dev = np.std(image)
        mean_val = np.mean(image)
        
        # En una imagen de ruido gaussiano, el rango es aprox 4-6 sigma
        noise_contrast = 4 * std_dev / (2 * mean_val + 1e-8) if mean_val > 0 else 0
        
        is_significant = contrast > max(noise_contrast * 1.5, MIN_CONTRAST_THRESHOLD)
        
        if contrast < MIN_CONTRAST_THRESHOLD:
            message = f"Contraste muy bajo ({contrast:.2f} < {MIN_CONTRAST_THRESHOLD})"
        elif not is_significant:
            message = f"Contraste no distinguible del ruido"
        else:
            message = f"Contraste válido: {contrast:.2f}"
        
        return float(contrast), is_significant, message

    def analyze_interference(self, image: np.ndarray) -> Dict:
        """
        Análisis completo de interferencia con validación.
        
        Returns:
            Dict con todos los parámetros y estado de validación
        """
        fringe_info = self.estimate_fringe_spacing(image)
        contrast, contrast_valid, contrast_message = self.calculate_contrast(image)
        
        # Determinar visibilidad basada en contraste validado
        if not contrast_valid:
            visibility = "No detectada"
        elif contrast > 0.7:
            visibility = "Excelente"
        elif contrast > 0.5:
            visibility = "Buena"
        elif contrast > 0.3:
            visibility = "Moderada"
        else:
            visibility = "Pobre"
        
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
