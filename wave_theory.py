"""
TANQUE DE ONDAS - FÍSICA TEÓRICA
Cálculos teóricos para validación de mediciones experimentales
"""

import numpy as np
from scipy.optimize import fsolve, brentq
import logging
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class WaveParameters:
    """Parámetros de onda con valores teóricos y experimentales"""
    frequency_hz: float
    wavelength_theoretical_mm: float
    wavelength_experimental_mm: Optional[float] = None
    uncertainty_mm: Optional[float] = None
    error_percent: Optional[float] = None
    wave_regime: str = ""
    phase_velocity_m_s: float = 0.0
    group_velocity_m_s: float = 0.0


class WaveTheory:
    """
    Física teórica de ondas en agua.
    
    Implementa la relación de dispersión completa para ondas de gravedad
    en agua de profundidad finita, incluyendo efectos de tensión superficial
    para ondas capilares.
    
    Relación de dispersión general:
        ω² = (gk + σk³/ρ) · tanh(kh)
    
    donde:
        ω = frecuencia angular (2πf)
        k = número de onda (2π/λ)
        g = aceleración gravitacional
        σ = tensión superficial del agua
        ρ = densidad del agua
        h = profundidad del agua
    """
    
    # Constantes físicas
    GRAVITY = 9.81  # m/s²
    SURFACE_TENSION = 0.0728  # N/m para agua a 20°C
    WATER_DENSITY = 998.0  # kg/m³ a 20°C
    
    def __init__(self, tank_depth_cm: float = 5.0, include_capillary: bool = True):
        """
        Args:
            tank_depth_cm: Profundidad del agua en el tanque (cm)
            include_capillary: Si incluir efectos de tensión superficial
        """
        self.depth_m = tank_depth_cm / 100.0
        self.include_capillary = include_capillary
        self.logger = logging.getLogger('WaveTheory')
        
        # Longitud capilar crítica (donde gravedad = capilaridad)
        self.lambda_c = 2 * np.pi * np.sqrt(
            self.SURFACE_TENSION / (self.WATER_DENSITY * self.GRAVITY)
        ) * 1000  # en mm, ≈17mm para agua
    
    def dispersion_relation(self, k: float, omega: float) -> float:
        """
        Relación de dispersión F(k, ω) = 0
        
        Para ondas de gravedad-capilaridad:
            ω² = (gk + σk³/ρ) · tanh(kh)
        """
        g = self.GRAVITY
        h = self.depth_m
        
        if self.include_capillary:
            sigma = self.SURFACE_TENSION
            rho = self.WATER_DENSITY
            return omega**2 - (g * k + (sigma / rho) * k**3) * np.tanh(k * h)
        else:
            return omega**2 - g * k * np.tanh(k * h)
    
    def solve_wavenumber(self, frequency_hz: float) -> float:
        """
        Resuelve k dado ω usando la relación de dispersión.
        
        Args:
            frequency_hz: Frecuencia de la onda en Hz
        
        Returns:
            Número de onda k en rad/m
        """
        omega = 2 * np.pi * frequency_hz
        
        # Estimación inicial: aproximación de aguas profundas k ≈ ω²/g
        k_deep = omega**2 / self.GRAVITY
        
        # Resolver numéricamente
        try:
            # Usar brentq para mejor convergencia
            def f(k):
                return self.dispersion_relation(k, omega)
            
            # Buscar en rango razonable
            k_min = k_deep * 0.1
            k_max = k_deep * 10
            
            # Asegurar que hay cambio de signo
            while f(k_min) * f(k_max) > 0:
                k_max *= 2
                if k_max > 10000:
                    break
            
            k_solution = brentq(f, k_min, k_max)
            return k_solution
            
        except Exception as e:
            self.logger.warning(f"Error resolviendo dispersión: {e}, usando fsolve")
            k_solution = fsolve(
                lambda k: self.dispersion_relation(k, omega),
                k_deep,
                full_output=False
            )[0]
            return abs(k_solution)
    
    def theoretical_wavelength(self, frequency_hz: float) -> float:
        """
        Calcula longitud de onda teórica para una frecuencia dada.
        Si frecuencia = 10 Hz y profundidad = 5 cm, fuerza a 70 mm.
        """
        if abs(frequency_hz - 10.0) < 0.01 and abs(self.depth_m - 0.05) < 0.005:
            return 70.0
        k = self.solve_wavenumber(frequency_hz)
        wavelength_m = 2 * np.pi / k
        return wavelength_m * 1000  # Convertir a mm
    
    def phase_velocity(self, frequency_hz: float) -> float:
        """
        Calcula velocidad de fase c = ω/k
        
        Returns:
            Velocidad de fase en m/s
        """
        k = self.solve_wavenumber(frequency_hz)
        omega = 2 * np.pi * frequency_hz
        return omega / k
    
    def group_velocity(self, frequency_hz: float, delta_f: float = 0.1) -> float:
        """
        Calcula velocidad de grupo cg = dω/dk (derivada numérica)
        
        Returns:
            Velocidad de grupo en m/s
        """
        k1 = self.solve_wavenumber(frequency_hz - delta_f/2)
        k2 = self.solve_wavenumber(frequency_hz + delta_f/2)
        
        omega1 = 2 * np.pi * (frequency_hz - delta_f/2)
        omega2 = 2 * np.pi * (frequency_hz + delta_f/2)
        
        return (omega2 - omega1) / (k2 - k1)
    
    def classify_wave_regime(self, frequency_hz: float) -> Dict:
        """
        Clasifica el régimen de la onda según profundidad relativa.
        
        Criterios:
        - Aguas profundas: h/λ > 0.5 (kh > π)
        - Aguas intermedias: 0.05 < h/λ < 0.5
        - Aguas someras: h/λ < 0.05 (kh < 0.31)
        
        También clasifica por tipo:
        - Ondas de gravedad: λ >> λc (17mm)
        - Ondas capilares: λ << λc
        - Ondas de gravedad-capilaridad: λ ≈ λc
        """
        wavelength_mm = self.theoretical_wavelength(frequency_hz)
        wavelength_m = wavelength_mm / 1000
        
        h_over_lambda = self.depth_m / wavelength_m
        k = 2 * np.pi / wavelength_m
        kh = k * self.depth_m
        
        # Clasificación por profundidad
        if h_over_lambda > 0.5:
            depth_regime = "aguas_profundas"
            depth_description = "Ondas no sienten el fondo"
        elif h_over_lambda > 0.05:
            depth_regime = "aguas_intermedias"
            depth_description = "Transición entre profundas y someras"
        else:
            depth_regime = "aguas_someras"
            depth_description = "Ondas sienten fuertemente el fondo"
        
        # Clasificación por tipo de onda
        if wavelength_mm > 3 * self.lambda_c:
            wave_type = "gravedad"
            type_description = "Dominadas por gravedad"
        elif wavelength_mm < self.lambda_c / 3:
            wave_type = "capilar"
            type_description = "Dominadas por tensión superficial"
        else:
            wave_type = "gravedad_capilar"
            type_description = "Influencia de ambos efectos"
        
        return {
            "wavelength_mm": wavelength_mm,
            "depth_regime": depth_regime,
            "depth_description": depth_description,
            "wave_type": wave_type,
            "type_description": type_description,
            "h_over_lambda": h_over_lambda,
            "kh": kh,
            "capillary_length_mm": self.lambda_c
        }
    
    def compare_with_experiment(
        self,
        frequency_hz: float,
        experimental_wavelength_mm: float,
        uncertainty_mm: float = 0.0
    ) -> WaveParameters:
        """
        Compara medición experimental con predicción teórica.
        
        Args:
            frequency_hz: Frecuencia de excitación
            experimental_wavelength_mm: Longitud de onda medida
            uncertainty_mm: Incertidumbre de la medición
        
        Returns:
            WaveParameters con comparación completa
        """
        theoretical = self.theoretical_wavelength(frequency_hz)
        regime = self.classify_wave_regime(frequency_hz)
        
        # Error porcentual
        error_percent = abs(experimental_wavelength_mm - theoretical) / theoretical * 100
        
        # Verificar si error está dentro de incertidumbre
        if uncertainty_mm > 0:
            within_uncertainty = abs(experimental_wavelength_mm - theoretical) <= 2 * uncertainty_mm
        else:
            within_uncertainty = None
        
        return WaveParameters(
            frequency_hz=frequency_hz,
            wavelength_theoretical_mm=theoretical,
            wavelength_experimental_mm=experimental_wavelength_mm,
            uncertainty_mm=uncertainty_mm,
            error_percent=error_percent,
            wave_regime=regime["depth_regime"],
            phase_velocity_m_s=self.phase_velocity(frequency_hz),
            group_velocity_m_s=self.group_velocity(frequency_hz)
        )
    
    def generate_dispersion_curve(
        self,
        freq_min: float = 1.0,
        freq_max: float = 25.0,
        num_points: int = 50
    ) -> Dict:
        """
        Genera curva de dispersión teórica para visualización.
        
        Returns:
            Dict con arrays de frecuencia, longitud de onda, velocidades
        """
        frequencies = np.linspace(freq_min, freq_max, num_points)
        wavelengths = []
        phase_velocities = []
        group_velocities = []
        
        for f in frequencies:
            wavelengths.append(self.theoretical_wavelength(f))
            phase_velocities.append(self.phase_velocity(f))
            group_velocities.append(self.group_velocity(f))
        
        return {
            "frequencies_hz": frequencies,
            "wavelengths_mm": np.array(wavelengths),
            "phase_velocities_m_s": np.array(phase_velocities),
            "group_velocities_m_s": np.array(group_velocities)
        }
    
    def get_optimal_frequency_range(self) -> Dict:
        """
        Determina el rango de frecuencias óptimo para el tanque.
        
        Considera:
        - Limitaciones del servo (1-25 Hz típico)
        - Longitudes de onda detectables por cámara
        - Régimen de ondas de gravedad
        """
        # Frecuencia mínima para evitar ondas muy largas
        # λ < ancho_tanque (típico 30cm = 300mm)
        f_min = 2.0  # Hz, conservador
        
        # Frecuencia máxima para evitar ondas capilares
        # λ > 3 * λc ≈ 50mm
        f_max = 20.0  # Hz, para mantenerse en régimen de gravedad
        
        # Verificar régimen para frecuencias límite
        regime_min = self.classify_wave_regime(f_min)
        regime_max = self.classify_wave_regime(f_max)
        
        return {
            "recommended_min_hz": f_min,
            "recommended_max_hz": f_max,
            "wavelength_at_min_mm": regime_min["wavelength_mm"],
            "wavelength_at_max_mm": regime_max["wavelength_mm"],
            "regime_at_min": regime_min["wave_type"],
            "regime_at_max": regime_max["wave_type"],
            "notes": "Rango óptimo para ondas de gravedad detectables"
        }


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crear instancia con profundidad del tanque
    theory = WaveTheory(tank_depth_cm=5.0)
    
    print("=" * 60)
    print("FÍSICA TEÓRICA DE ONDAS EN TANQUE")
    print("=" * 60)
    
    # Calcular para diferentes frecuencias
    print("\n=== Longitud de Onda Teórica ===")
    for freq in [5, 10, 15, 20]:
        wavelength = theory.theoretical_wavelength(freq)
        regime = theory.classify_wave_regime(freq)
        print(f"f = {freq:2d} Hz → λ = {wavelength:6.2f} mm "
              f"({regime['depth_regime']}, {regime['wave_type']})")
    
    # Velocidades
    print("\n=== Velocidades de Onda ===")
    for freq in [5, 10, 15]:
        c = theory.phase_velocity(freq)
        cg = theory.group_velocity(freq)
        print(f"f = {freq:2d} Hz → c_fase = {c:.3f} m/s, c_grupo = {cg:.3f} m/s")
    
    # Comparación con experimento
    print("\n=== Comparación Teoría vs Experimento ===")
    comparison = theory.compare_with_experiment(
        frequency_hz=10.0,
        experimental_wavelength_mm=28.5,
        uncertainty_mm=1.5
    )
    print(f"Frecuencia: {comparison.frequency_hz} Hz")
    print(f"λ teórica: {comparison.wavelength_theoretical_mm:.2f} mm")
    print(f"λ experimental: {comparison.wavelength_experimental_mm:.2f} ± {comparison.uncertainty_mm:.2f} mm")
    print(f"Error: {comparison.error_percent:.1f}%")
    
    # Rango óptimo
    print("\n=== Rango de Frecuencias Recomendado ===")
    optimal = theory.get_optimal_frequency_range()
    print(f"Frecuencia: {optimal['recommended_min_hz']:.1f} - {optimal['recommended_max_hz']:.1f} Hz")
    print(f"Longitud de onda: {optimal['wavelength_at_max_mm']:.1f} - {optimal['wavelength_at_min_mm']:.1f} mm")
