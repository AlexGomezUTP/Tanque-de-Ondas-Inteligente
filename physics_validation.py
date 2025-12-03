"""
TANQUE DE ONDAS - VALIDACIONES FÍSICAS
Verifica condiciones físicas para mediciones válidas
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ValidationStatus(Enum):
    """Estado de validación"""
    VALID = "válido"
    WARNING = "advertencia"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Resultado de una validación"""
    name: str
    status: ValidationStatus
    value: float
    threshold: float
    message: str
    recommendation: str = ""


class PhysicsValidator:
    """
    Valida condiciones físicas del experimento de ondas.
    
    Verificaciones implementadas:
    1. Número de Froude (ondas lineales vs no lineales)
    2. Profundidad relativa (régimen de ondas)
    3. Aliasing temporal (Nyquist)
    4. Aliasing espacial (resolución de cámara)
    5. Efectos de borde (reflexiones)
    6. Atenuación viscosa
    """
    
    # Constantes físicas
    GRAVITY = 9.81  # m/s²
    KINEMATIC_VISCOSITY = 1.0e-6  # m²/s para agua a 20°C
    
    def __init__(
        self,
        tank_depth_cm: float = 5.0,
        tank_width_cm: float = 30.0,
        tank_length_cm: float = 50.0,
        camera_fps: float = 30.0,
        camera_resolution_px: Tuple[int, int] = (1920, 1080),
        calibration_px_per_mm: float = 10.0
    ):
        self.tank_depth_m = tank_depth_cm / 100.0
        self.tank_width_m = tank_width_cm / 100.0
        self.tank_length_m = tank_length_cm / 100.0
        self.camera_fps = camera_fps
        self.camera_resolution = camera_resolution_px
        self.calibration = calibration_px_per_mm
        self.logger = logging.getLogger('PhysicsValidator')
    
    def validate_all(
        self,
        frequency_hz: float,
        amplitude_mm: float,
        wavelength_mm: float
    ) -> Dict[str, ValidationResult]:
        """
        Ejecuta todas las validaciones físicas.
        
        Args:
            frequency_hz: Frecuencia de excitación
            amplitude_mm: Amplitud de la onda
            wavelength_mm: Longitud de onda medida
        
        Returns:
            Dict con resultados de todas las validaciones
        """
        results = {}
        
        results['froude'] = self.check_froude_number(amplitude_mm, wavelength_mm)
        results['depth_ratio'] = self.check_depth_ratio(wavelength_mm)
        results['temporal_nyquist'] = self.check_temporal_aliasing(frequency_hz)
        results['spatial_nyquist'] = self.check_spatial_aliasing(wavelength_mm)
        results['boundary_effects'] = self.check_boundary_effects(wavelength_mm)
        results['viscous_damping'] = self.check_viscous_damping(frequency_hz, wavelength_mm)
        
        return results
    
    def check_froude_number(
        self,
        amplitude_mm: float,
        wavelength_mm: float
    ) -> ValidationResult:
        """
        Verifica número de Froude para linealidad de ondas.
        
        Fr = a·k = 2π·a/λ
        
        Para ondas lineales: Fr << 1 (típicamente < 0.1)
        
        Ondas no lineales tienen formas distorsionadas y
        la superposición no es válida.
        """
        a = amplitude_mm / 1000.0  # Convertir a metros
        wavelength_m = wavelength_mm / 1000.0
        
        k = 2 * np.pi / wavelength_m
        froude = a * k
        
        threshold = 0.1
        
        if froude < 0.05:
            status = ValidationStatus.VALID
            message = f"Fr = {froude:.3f}: Ondas bien lineales"
            recommendation = ""
        elif froude < threshold:
            status = ValidationStatus.VALID
            message = f"Fr = {froude:.3f}: Ondas aproximadamente lineales"
            recommendation = "Pequeñas no linealidades posibles"
        elif froude < 0.2:
            status = ValidationStatus.WARNING
            message = f"Fr = {froude:.3f}: No linealidades moderadas"
            recommendation = "Reducir amplitud para mejor linealidad"
        else:
            status = ValidationStatus.ERROR
            message = f"Fr = {froude:.3f}: Ondas fuertemente no lineales"
            recommendation = "Reducir amplitud significativamente"
        
        return ValidationResult(
            name="Número de Froude",
            status=status,
            value=froude,
            threshold=threshold,
            message=message,
            recommendation=recommendation
        )
    
    def check_depth_ratio(self, wavelength_mm: float) -> ValidationResult:
        """
        Verifica profundidad relativa h/λ.
        
        - h/λ > 0.5: Aguas profundas (ondas no sienten fondo)
        - 0.05 < h/λ < 0.5: Aguas intermedias
        - h/λ < 0.05: Aguas someras (velocidad = √(gh))
        
        Para laboratorio típico, aguas intermedias es común.
        """
        wavelength_m = wavelength_mm / 1000.0
        h_over_lambda = self.tank_depth_m / wavelength_m
        
        if h_over_lambda > 0.5:
            status = ValidationStatus.VALID
            message = f"h/λ = {h_over_lambda:.2f}: Aguas profundas"
            recommendation = "Relación de dispersión simplificada aplicable"
        elif h_over_lambda > 0.05:
            status = ValidationStatus.VALID
            message = f"h/λ = {h_over_lambda:.2f}: Aguas intermedias"
            recommendation = "Usar relación de dispersión completa"
        else:
            status = ValidationStatus.WARNING
            message = f"h/λ = {h_over_lambda:.2f}: Aguas muy someras"
            recommendation = "Efectos de fondo dominan; considerar ecuación de onda larga"
        
        return ValidationResult(
            name="Profundidad relativa",
            status=status,
            value=h_over_lambda,
            threshold=0.05,
            message=message,
            recommendation=recommendation
        )
    
    def check_temporal_aliasing(self, frequency_hz: float) -> ValidationResult:
        """
        Verifica criterio de Nyquist temporal.
        
        f_Nyquist = FPS / 2
        
        Para evitar aliasing: f_señal < f_Nyquist
        Se recomienda: f_señal < f_Nyquist / 2 (margen de seguridad)
        """
        nyquist_freq = self.camera_fps / 2.0
        safe_freq = nyquist_freq / 2.0
        
        ratio = frequency_hz / nyquist_freq
        
        if frequency_hz < safe_freq:
            status = ValidationStatus.VALID
            message = f"f/{nyquist_freq:.0f}Hz = {ratio:.2f}: Sin aliasing temporal"
            recommendation = ""
        elif frequency_hz < nyquist_freq:
            status = ValidationStatus.WARNING
            message = f"f/{nyquist_freq:.0f}Hz = {ratio:.2f}: Cerca del límite de Nyquist"
            recommendation = f"Aumentar FPS de cámara a >{4*frequency_hz:.0f} Hz"
        else:
            status = ValidationStatus.ERROR
            message = f"f/{nyquist_freq:.0f}Hz = {ratio:.2f}: ¡Aliasing temporal!"
            recommendation = f"Reducir frecuencia a <{safe_freq:.1f} Hz o aumentar FPS"
        
        return ValidationResult(
            name="Nyquist temporal",
            status=status,
            value=frequency_hz,
            threshold=nyquist_freq,
            message=message,
            recommendation=recommendation
        )
    
    def check_spatial_aliasing(self, wavelength_mm: float) -> ValidationResult:
        """
        Verifica criterio de Nyquist espacial.
        
        λ_min_detectable = 2 * (mm/pixel)
        
        Se recomienda: λ > 4 * (mm/pixel) para buena resolución
        """
        mm_per_pixel = 1.0 / self.calibration
        nyquist_wavelength = 2 * mm_per_pixel
        recommended_min = 4 * mm_per_pixel
        
        if wavelength_mm > recommended_min * 2:
            status = ValidationStatus.VALID
            message = f"λ = {wavelength_mm:.1f}mm >> {nyquist_wavelength:.2f}mm: Excelente resolución"
            pixels_per_wave = wavelength_mm * self.calibration
            recommendation = f"~{pixels_per_wave:.0f} píxeles por longitud de onda"
        elif wavelength_mm > recommended_min:
            status = ValidationStatus.VALID
            message = f"λ = {wavelength_mm:.1f}mm > {nyquist_wavelength:.2f}mm: Resolución aceptable"
            recommendation = ""
        elif wavelength_mm > nyquist_wavelength:
            status = ValidationStatus.WARNING
            message = f"λ = {wavelength_mm:.1f}mm: Cerca del límite espacial"
            recommendation = "Aumentar resolución de cámara o usar zoom"
        else:
            status = ValidationStatus.ERROR
            message = f"λ = {wavelength_mm:.1f}mm < {nyquist_wavelength:.2f}mm: ¡Aliasing espacial!"
            recommendation = "Onda no resoluble con configuración actual"
        
        return ValidationResult(
            name="Nyquist espacial",
            status=status,
            value=wavelength_mm,
            threshold=nyquist_wavelength,
            message=message,
            recommendation=recommendation
        )
    
    def check_boundary_effects(self, wavelength_mm: float) -> ValidationResult:
        """
        Verifica efectos de borde/reflexiones.
        
        Las reflexiones en las paredes pueden causar ondas estacionarias
        y patrones de interferencia no deseados.
        
        Criterio: Al menos 3-4 longitudes de onda en la dimensión menor
        """
        wavelength_m = wavelength_mm / 1000.0
        min_dimension = min(self.tank_width_m, self.tank_length_m)
        
        num_wavelengths = min_dimension / wavelength_m
        threshold = 4.0
        
        if num_wavelengths > 6:
            status = ValidationStatus.VALID
            message = f"{num_wavelengths:.1f}λ en tanque: Efectos de borde mínimos"
            recommendation = ""
        elif num_wavelengths > threshold:
            status = ValidationStatus.VALID
            message = f"{num_wavelengths:.1f}λ en tanque: Efectos de borde moderados"
            recommendation = "Analizar región central del tanque"
        elif num_wavelengths > 2:
            status = ValidationStatus.WARNING
            message = f"{num_wavelengths:.1f}λ en tanque: Reflexiones significativas"
            recommendation = "Usar material absorbente en bordes o reducir frecuencia"
        else:
            status = ValidationStatus.ERROR
            message = f"{num_wavelengths:.1f}λ en tanque: Ondas estacionarias dominantes"
            recommendation = "Frecuencia demasiado baja para el tamaño del tanque"
        
        return ValidationResult(
            name="Efectos de borde",
            status=status,
            value=num_wavelengths,
            threshold=threshold,
            message=message,
            recommendation=recommendation
        )
    
    def check_viscous_damping(
        self,
        frequency_hz: float,
        wavelength_mm: float
    ) -> ValidationResult:
        """
        Verifica atenuación viscosa.
        
        Las ondas se atenúan exponencialmente: A(x) = A₀·exp(-αx)
        
        Coeficiente de atenuación para ondas de gravedad:
        α ≈ 2νk²/c donde ν es viscosidad cinemática
        
        Criterio: La onda debe propagarse al menos 5-10λ antes de
        atenuarse significativamente.
        """
        wavelength_m = wavelength_mm / 1000.0
        k = 2 * np.pi / wavelength_m
        
        # Velocidad de fase aproximada (aguas profundas)
        omega = 2 * np.pi * frequency_hz
        c = omega / k  # c = ω/k
        
        # Coeficiente de atenuación
        alpha = 2 * self.KINEMATIC_VISCOSITY * k**2 / c
        
        # Distancia para atenuación a 1/e
        decay_length_m = 1.0 / alpha if alpha > 0 else np.inf
        decay_wavelengths = decay_length_m / wavelength_m
        
        threshold = 10.0  # Al menos 10 longitudes de onda
        
        if decay_wavelengths > 50:
            status = ValidationStatus.VALID
            message = f"Atenuación en {decay_wavelengths:.0f}λ: Despreciable"
            recommendation = ""
        elif decay_wavelengths > threshold:
            status = ValidationStatus.VALID
            message = f"Atenuación en {decay_wavelengths:.0f}λ: Baja"
            recommendation = ""
        elif decay_wavelengths > 5:
            status = ValidationStatus.WARNING
            message = f"Atenuación en {decay_wavelengths:.1f}λ: Moderada"
            recommendation = "Medir cerca de la fuente de ondas"
        else:
            status = ValidationStatus.ERROR
            message = f"Atenuación en {decay_wavelengths:.1f}λ: Severa"
            recommendation = "Ondas muy cortas; aumentar longitud de onda"
        
        return ValidationResult(
            name="Atenuación viscosa",
            status=status,
            value=decay_wavelengths,
            threshold=threshold,
            message=message,
            recommendation=recommendation
        )
    
    def get_recommended_frequency_range(self) -> Dict:
        """
        Calcula rango de frecuencias recomendado basado en las restricciones.
        """
        # Límite inferior: efectos de borde (λ < L/4)
        min_wavelength_m = min(self.tank_width_m, self.tank_length_m) / 4
        # Para aguas profundas: f ≈ √(g/2πλ)
        f_min = np.sqrt(self.GRAVITY / (2 * np.pi * min_wavelength_m))
        
        # Límite superior: Nyquist temporal
        f_max_temporal = self.camera_fps / 4  # Margen de seguridad
        
        # Límite superior: Resolución espacial (λ > 4 mm/px)
        min_detectable_wavelength_m = 4 / self.calibration / 1000
        f_max_spatial = np.sqrt(self.GRAVITY / (2 * np.pi * min_detectable_wavelength_m))
        
        f_max = min(f_max_temporal, f_max_spatial, 25.0)  # 25 Hz límite del servo
        
        return {
            "recommended_min_hz": max(f_min, 2.0),
            "recommended_max_hz": f_max,
            "limiting_factor_min": "efectos de borde" if f_min > 2.0 else "servo mínimo",
            "limiting_factor_max": "temporal" if f_max == f_max_temporal else "espacial",
            "optimal_hz": (f_min + f_max) / 2
        }
    
    def generate_validation_report(
        self,
        frequency_hz: float,
        amplitude_mm: float,
        wavelength_mm: float
    ) -> str:
        """
        Genera reporte de validación legible.
        """
        results = self.validate_all(frequency_hz, amplitude_mm, wavelength_mm)
        
        lines = [
            "=" * 50,
            "   REPORTE DE VALIDACIÓN FÍSICA",
            "=" * 50,
            "",
            f"Configuración:",
            f"  Frecuencia: {frequency_hz} Hz",
            f"  Amplitud: {amplitude_mm} mm",
            f"  Longitud de onda: {wavelength_mm} mm",
            f"  Profundidad tanque: {self.tank_depth_m*100} cm",
            f"  FPS cámara: {self.camera_fps}",
            "",
            "-" * 50,
        ]
        
        num_errors = 0
        num_warnings = 0
        
        for name, result in results.items():
            status_icon = {
                ValidationStatus.VALID: "✅",
                ValidationStatus.WARNING: "⚠️",
                ValidationStatus.ERROR: "❌"
            }[result.status]
            
            if result.status == ValidationStatus.ERROR:
                num_errors += 1
            elif result.status == ValidationStatus.WARNING:
                num_warnings += 1
            
            lines.append(f"\n{status_icon} {result.name}")
            lines.append(f"   {result.message}")
            if result.recommendation:
                lines.append(f"   → {result.recommendation}")
        
        lines.append("")
        lines.append("-" * 50)
        lines.append("RESUMEN:")
        
        if num_errors == 0 and num_warnings == 0:
            lines.append("✅ Todas las validaciones pasaron. Experimento válido.")
        elif num_errors == 0:
            lines.append(f"⚠️ {num_warnings} advertencia(s). Revisar recomendaciones.")
        else:
            lines.append(f"❌ {num_errors} error(es) crítico(s). Ajustar configuración.")
        
        # Agregar recomendación de frecuencia
        rec = self.get_recommended_frequency_range()
        lines.append("")
        lines.append(f"Rango de frecuencia recomendado: {rec['recommended_min_hz']:.1f} - {rec['recommended_max_hz']:.1f} Hz")
        lines.append("=" * 50)
        
        return "\n".join(lines)


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    validator = PhysicsValidator(
        tank_depth_cm=5.0,
        tank_width_cm=30.0,
        tank_length_cm=50.0,
        camera_fps=30.0,
        calibration_px_per_mm=10.0
    )
    
    # Caso de prueba
    print(validator.generate_validation_report(
        frequency_hz=10.0,
        amplitude_mm=5.0,
        wavelength_mm=30.0
    ))
    
    print("\n\n")
    
    # Caso problemático
    print(validator.generate_validation_report(
        frequency_hz=20.0,
        amplitude_mm=15.0,
        wavelength_mm=5.0
    ))
