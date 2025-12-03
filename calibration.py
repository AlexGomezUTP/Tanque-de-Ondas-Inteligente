"""
TANQUE DE ONDAS - MÓDULO DE CALIBRACIÓN
Gestiona calibración espacial, temporal y cálculo de incertidumbre
"""

import numpy as np
import logging
import json
from datetime import datetime
from typing import Tuple, Dict, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class CalibrationData:
    """Datos de calibración con incertidumbre"""
    pixel_per_mm: float
    uncertainty_pixel_per_mm: float
    reference_length_mm: float
    measured_pixels: float
    calibration_date: str
    method: str
    notes: str = ""
    
    @property
    def mm_per_pixel(self) -> float:
        """Conversión inversa: mm por píxel"""
        return 1.0 / self.pixel_per_mm if self.pixel_per_mm > 0 else 0.0
    
    @property
    def uncertainty_mm_per_pixel(self) -> float:
        """Incertidumbre en mm/pixel"""
        if self.pixel_per_mm > 0:
            # Propagación de incertidumbre: δ(1/x) = δx/x²
            return self.uncertainty_pixel_per_mm / (self.pixel_per_mm ** 2)
        return 0.0


class CalibrationManager:
    """
    Gestiona calibración espacial y temporal del sistema de ondas.
    
    La calibración espacial es CRÍTICA para obtener mediciones
    de longitud de onda en unidades físicas (mm).
    
    Métodos de calibración soportados:
    1. Objeto de referencia conocido (regla, patrón)
    2. Múltiples mediciones para reducir incertidumbre
    3. Calibración automática con patrón de cuadrícula
    """
    
    def __init__(self, config_path: str = "calibration_config.json"):
        self.logger = logging.getLogger('CalibrationManager')
        self.config_path = Path(config_path)
        self.current_calibration: Optional[CalibrationData] = None
        self._load_calibration()
    
    def _load_calibration(self) -> bool:
        """Carga calibración guardada si existe"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                self.current_calibration = CalibrationData(**data)
                self.logger.info(f"Calibración cargada: {self.current_calibration.pixel_per_mm:.4f} px/mm")
                return True
            except Exception as e:
                self.logger.warning(f"Error cargando calibración: {e}")
        return False
    
    def save_calibration(self) -> bool:
        """Guarda calibración actual a archivo"""
        if self.current_calibration is None:
            return False
        try:
            with open(self.config_path, 'w') as f:
                json.dump(asdict(self.current_calibration), f, indent=2)
            self.logger.info("Calibración guardada correctamente")
            return True
        except Exception as e:
            self.logger.error(f"Error guardando calibración: {e}")
            return False
    
    def calibrate_with_reference(
        self,
        reference_length_mm: float,
        measured_pixels: float,
        uncertainty_pixels: float = 2.0,
        notes: str = ""
    ) -> Tuple[float, float]:
        """
        Calibra usando un objeto de referencia de longitud conocida.
        
        Args:
            reference_length_mm: Longitud real del objeto en mm
            measured_pixels: Distancia medida en píxeles
            uncertainty_pixels: Incertidumbre en la medición de píxeles (±)
            notes: Notas sobre la calibración
        
        Returns:
            (pixel_per_mm, uncertainty)
        
        Ejemplo:
            Si una regla de 100mm mide 500 píxeles:
            >>> cal.calibrate_with_reference(100.0, 500.0)
            (5.0, 0.1)  # 5 px/mm ± 0.1
        """
        if reference_length_mm <= 0 or measured_pixels <= 0:
            raise ValueError("Las mediciones deben ser positivas")
        
        pixel_per_mm = measured_pixels / reference_length_mm
        
        # Propagación de incertidumbre: δ(a/b) = (a/b) * √[(δa/a)² + (δb/b)²]
        # Asumimos incertidumbre del 0.5% en la referencia física
        uncertainty_reference = reference_length_mm * 0.005
        
        relative_uncertainty = np.sqrt(
            (uncertainty_pixels / measured_pixels) ** 2 +
            (uncertainty_reference / reference_length_mm) ** 2
        )
        
        uncertainty_pixel_per_mm = pixel_per_mm * relative_uncertainty
        
        self.current_calibration = CalibrationData(
            pixel_per_mm=pixel_per_mm,
            uncertainty_pixel_per_mm=uncertainty_pixel_per_mm,
            reference_length_mm=reference_length_mm,
            measured_pixels=measured_pixels,
            calibration_date=datetime.now().isoformat(),
            method="single_reference",
            notes=notes
        )
        
        self.save_calibration()
        self.logger.info(
            f"Calibración: {pixel_per_mm:.4f} ± {uncertainty_pixel_per_mm:.4f} px/mm"
        )
        
        return pixel_per_mm, uncertainty_pixel_per_mm
    
    def calibrate_with_multiple_measurements(
        self,
        reference_length_mm: float,
        measurements_pixels: List[float],
        notes: str = ""
    ) -> Tuple[float, float]:
        """
        Calibra usando múltiples mediciones para reducir incertidumbre.
        
        Args:
            reference_length_mm: Longitud real del objeto en mm
            measurements_pixels: Lista de mediciones en píxeles
            notes: Notas sobre la calibración
        
        Returns:
            (pixel_per_mm, uncertainty)
        
        La incertidumbre se reduce con √N mediciones.
        Se recomienda mínimo 5 mediciones.
        """
        if len(measurements_pixels) < 2:
            raise ValueError("Se requieren al menos 2 mediciones")
        
        measurements = np.array(measurements_pixels)
        mean_pixels = np.mean(measurements)
        std_pixels = np.std(measurements, ddof=1)  # Desviación estándar muestral
        
        # Error estándar de la media
        sem = std_pixels / np.sqrt(len(measurements))
        
        pixel_per_mm = mean_pixels / reference_length_mm
        
        # Propagación de incertidumbre
        uncertainty_reference = reference_length_mm * 0.005
        relative_uncertainty = np.sqrt(
            (sem / mean_pixels) ** 2 +
            (uncertainty_reference / reference_length_mm) ** 2
        )
        uncertainty_pixel_per_mm = pixel_per_mm * relative_uncertainty
        
        self.current_calibration = CalibrationData(
            pixel_per_mm=pixel_per_mm,
            uncertainty_pixel_per_mm=uncertainty_pixel_per_mm,
            reference_length_mm=reference_length_mm,
            measured_pixels=mean_pixels,
            calibration_date=datetime.now().isoformat(),
            method=f"multiple_measurements_n{len(measurements)}",
            notes=f"N={len(measurements)}, std={std_pixels:.2f}px. {notes}"
        )
        
        self.save_calibration()
        self.logger.info(
            f"Calibración (N={len(measurements)}): "
            f"{pixel_per_mm:.4f} ± {uncertainty_pixel_per_mm:.4f} px/mm"
        )
        
        return pixel_per_mm, uncertainty_pixel_per_mm
    
    def convert_pixels_to_mm(
        self,
        value_pixels: float,
        uncertainty_pixels: float = 0.0
    ) -> Tuple[float, float]:
        """
        Convierte píxeles a mm incluyendo propagación de incertidumbre.
        
        Args:
            value_pixels: Valor en píxeles
            uncertainty_pixels: Incertidumbre en píxeles
        
        Returns:
            (value_mm, total_uncertainty_mm)
        """
        if self.current_calibration is None:
            raise ValueError("Sistema no calibrado. Ejecute calibración primero.")
        
        cal = self.current_calibration
        value_mm = value_pixels / cal.pixel_per_mm
        
        # Propagación de incertidumbre: δ(a/b) = (a/b) * √[(δa/a)² + (δb/b)²]
        if value_pixels > 0:
            rel_uncertainty_measurement = uncertainty_pixels / value_pixels if uncertainty_pixels > 0 else 0
            rel_uncertainty_calibration = cal.uncertainty_pixel_per_mm / cal.pixel_per_mm
            
            total_rel_uncertainty = np.sqrt(
                rel_uncertainty_measurement ** 2 +
                rel_uncertainty_calibration ** 2
            )
            uncertainty_mm = value_mm * total_rel_uncertainty
        else:
            uncertainty_mm = 0.0
        
        return value_mm, uncertainty_mm
    
    def get_calibration_info(self) -> Dict:
        """Retorna información de calibración actual"""
        if self.current_calibration is None:
            return {
                "calibrated": False,
                "message": "Sistema no calibrado"
            }
        
        cal = self.current_calibration
        return {
            "calibrated": True,
            "pixel_per_mm": cal.pixel_per_mm,
            "uncertainty_pixel_per_mm": cal.uncertainty_pixel_per_mm,
            "mm_per_pixel": cal.mm_per_pixel,
            "uncertainty_mm_per_pixel": cal.uncertainty_mm_per_pixel,
            "relative_uncertainty_percent": (cal.uncertainty_pixel_per_mm / cal.pixel_per_mm) * 100,
            "reference_length_mm": cal.reference_length_mm,
            "calibration_date": cal.calibration_date,
            "method": cal.method,
            "notes": cal.notes
        }
    
    def validate_calibration_quality(self) -> Dict:
        """
        Evalúa la calidad de la calibración actual.
        
        Returns:
            Dict con evaluación de calidad
        """
        if self.current_calibration is None:
            return {"valid": False, "quality": "none", "message": "No calibrado"}
        
        cal = self.current_calibration
        rel_uncertainty = cal.uncertainty_pixel_per_mm / cal.pixel_per_mm
        
        if rel_uncertainty < 0.01:  # < 1%
            quality = "excelente"
            message = "Calibración de alta precisión"
        elif rel_uncertainty < 0.03:  # < 3%
            quality = "buena"
            message = "Calibración aceptable para mediciones"
        elif rel_uncertainty < 0.05:  # < 5%
            quality = "aceptable"
            message = "Considere recalibrar para mayor precisión"
        else:
            quality = "pobre"
            message = "Se recomienda recalibrar el sistema"
        
        # Verificar antigüedad
        try:
            cal_date = datetime.fromisoformat(cal.calibration_date)
            days_old = (datetime.now() - cal_date).days
            if days_old > 7:
                message += f". Calibración tiene {days_old} días de antigüedad."
        except:
            days_old = None
        
        return {
            "valid": True,
            "quality": quality,
            "relative_uncertainty_percent": rel_uncertainty * 100,
            "message": message,
            "days_old": days_old
        }


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    cal = CalibrationManager()
    
    # Calibración simple con objeto de referencia
    print("=== Calibración con referencia simple ===")
    px_per_mm, uncertainty = cal.calibrate_with_reference(
        reference_length_mm=100.0,  # Regla de 100mm
        measured_pixels=500.0,       # Mide 500 píxeles
        uncertainty_pixels=3.0,      # ±3 píxeles de error
        notes="Calibración con regla metálica"
    )
    print(f"Resultado: {px_per_mm:.4f} ± {uncertainty:.4f} px/mm")
    
    # Calibración con múltiples mediciones
    print("\n=== Calibración con múltiples mediciones ===")
    measurements = [498, 502, 500, 499, 501, 500, 498, 502]
    px_per_mm, uncertainty = cal.calibrate_with_multiple_measurements(
        reference_length_mm=100.0,
        measurements_pixels=measurements
    )
    print(f"Resultado: {px_per_mm:.4f} ± {uncertainty:.4f} px/mm")
    
    # Convertir medición
    print("\n=== Conversión de medición ===")
    wavelength_px = 45.0  # Longitud de onda medida en píxeles
    wavelength_mm, uncertainty_mm = cal.convert_pixels_to_mm(wavelength_px, 2.0)
    print(f"λ = {wavelength_mm:.2f} ± {uncertainty_mm:.2f} mm")
    
    # Info y calidad
    print("\n=== Información de calibración ===")
    info = cal.get_calibration_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("\n=== Calidad de calibración ===")
    quality = cal.validate_calibration_quality()
    print(f"  Calidad: {quality['quality']}")
    print(f"  Mensaje: {quality['message']}")
