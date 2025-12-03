"""
TANQUE DE ONDAS - ANÁLISIS DE ERRORES E INCERTIDUMBRE
Propagación de errores, análisis estadístico y estimación de incertidumbre
"""

import numpy as np
from scipy import stats
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class MeasurementWithUncertainty:
    """Representa una medición con su incertidumbre"""
    value: float
    uncertainty: float
    unit: str = ""
    confidence_level: float = 0.95  # 95% por defecto
    
    def __str__(self) -> str:
        return f"{self.value:.3f} ± {self.uncertainty:.3f} {self.unit}"
    
    @property
    def relative_uncertainty(self) -> float:
        """Incertidumbre relativa (adimensional)"""
        return self.uncertainty / abs(self.value) if self.value != 0 else 0.0
    
    @property
    def relative_uncertainty_percent(self) -> float:
        """Incertidumbre relativa en porcentaje"""
        return self.relative_uncertainty * 100


@dataclass
class StatisticalSummary:
    """Resumen estadístico de un conjunto de mediciones"""
    mean: float
    std_dev: float
    std_error: float
    n_samples: int
    confidence_interval: Tuple[float, float]
    median: float
    min_val: float
    max_val: float
    outliers: List[float] = field(default_factory=list)


class ErrorAnalyzer:
    """
    Análisis de errores e incertidumbre para mediciones de ondas.
    
    Implementa:
    - Propagación de incertidumbre (lineal y cuadrática)
    - Análisis estadístico de múltiples mediciones
    - Detección de outliers
    - Estimación de ruido
    - Intervalos de confianza
    """
    
    def __init__(self):
        self.logger = logging.getLogger('ErrorAnalyzer')
    
    # ==================== PROPAGACIÓN DE INCERTIDUMBRE ====================
    
    def propagate_uncertainty_sum(
        self,
        values: List[float],
        uncertainties: List[float],
        coefficients: Optional[List[float]] = None
    ) -> MeasurementWithUncertainty:
        """
        Propaga incertidumbre para suma/resta: z = Σ(cᵢ·xᵢ)
        
        δz = √(Σ(cᵢ·δxᵢ)²)
        
        Args:
            values: Lista de valores
            uncertainties: Lista de incertidumbres
            coefficients: Coeficientes (default: todos 1)
        """
        if coefficients is None:
            coefficients = [1.0] * len(values)
        
        result = sum(c * v for c, v in zip(coefficients, values))
        uncertainty = np.sqrt(sum(
            (c * u)**2 for c, u in zip(coefficients, uncertainties)
        ))
        
        return MeasurementWithUncertainty(value=result, uncertainty=uncertainty)
    
    def propagate_uncertainty_product(
        self,
        values: List[float],
        uncertainties: List[float],
        exponents: Optional[List[float]] = None
    ) -> MeasurementWithUncertainty:
        """
        Propaga incertidumbre para producto/cociente: z = Π(xᵢ^nᵢ)
        
        δz/z = √(Σ(nᵢ·δxᵢ/xᵢ)²)
        
        Args:
            values: Lista de valores
            uncertainties: Lista de incertidumbres
            exponents: Exponentes (default: todos 1, usar -1 para división)
        """
        if exponents is None:
            exponents = [1.0] * len(values)
        
        result = np.prod([v**n for v, n in zip(values, exponents)])
        
        relative_uncertainty = np.sqrt(sum(
            (n * u / v)**2 for n, u, v in zip(exponents, uncertainties, values)
            if v != 0
        ))
        
        uncertainty = abs(result) * relative_uncertainty
        
        return MeasurementWithUncertainty(value=result, uncertainty=uncertainty)
    
    def propagate_wavelength_from_fft(
        self,
        spatial_frequency: float,
        freq_uncertainty: float,
        calibration_px_per_mm: float,
        cal_uncertainty: float
    ) -> MeasurementWithUncertainty:
        """
        Propaga incertidumbre específica para λ = 1/(f_spatial · calibración)
        
        Args:
            spatial_frequency: Frecuencia espacial en ciclos/pixel
            freq_uncertainty: Incertidumbre en frecuencia espacial
            calibration_px_per_mm: Factor de calibración
            cal_uncertainty: Incertidumbre en calibración
        """
        if spatial_frequency <= 0:
            return MeasurementWithUncertainty(value=0, uncertainty=0, unit="mm")
        
        # λ (mm) = 1 / (f_spatial * cal_px_per_mm)
        wavelength = 1.0 / (spatial_frequency * calibration_px_per_mm)
        
        # Propagación: λ = f^(-1) * cal^(-1)
        rel_unc_freq = freq_uncertainty / spatial_frequency
        rel_unc_cal = cal_uncertainty / calibration_px_per_mm
        
        relative_uncertainty = np.sqrt(rel_unc_freq**2 + rel_unc_cal**2)
        uncertainty = wavelength * relative_uncertainty
        
        return MeasurementWithUncertainty(
            value=wavelength,
            uncertainty=uncertainty,
            unit="mm"
        )
    
    # ==================== ANÁLISIS ESTADÍSTICO ====================
    
    def analyze_measurements(
        self,
        measurements: List[float],
        confidence_level: float = 0.95,
        remove_outliers: bool = True
    ) -> StatisticalSummary:
        """
        Realiza análisis estadístico completo de mediciones.
        
        Args:
            measurements: Lista de mediciones
            confidence_level: Nivel de confianza (0-1)
            remove_outliers: Si detectar y reportar outliers
        
        Returns:
            StatisticalSummary con estadísticas completas
        """
        data = np.array(measurements)
        n = len(data)
        
        if n < 2:
            return StatisticalSummary(
                mean=data[0] if n == 1 else 0,
                std_dev=0,
                std_error=0,
                n_samples=n,
                confidence_interval=(data[0], data[0]) if n == 1 else (0, 0),
                median=data[0] if n == 1 else 0,
                min_val=data[0] if n == 1 else 0,
                max_val=data[0] if n == 1 else 0,
                outliers=[]
            )
        
        # Detectar outliers con IQR
        outliers = []
        clean_data = data
        
        if remove_outliers and n >= 4:
            q1, q3 = np.percentile(data, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outlier_mask = (data < lower_bound) | (data > upper_bound)
            outliers = data[outlier_mask].tolist()
            clean_data = data[~outlier_mask]
            
            if len(clean_data) < 2:
                clean_data = data  # Restaurar si quedan muy pocos
        
        mean = np.mean(clean_data)
        std_dev = np.std(clean_data, ddof=1)  # Desviación estándar muestral
        std_error = std_dev / np.sqrt(len(clean_data))
        
        # Intervalo de confianza usando t-Student
        alpha = 1 - confidence_level
        t_value = stats.t.ppf(1 - alpha/2, df=len(clean_data)-1)
        margin = t_value * std_error
        ci = (mean - margin, mean + margin)
        
        return StatisticalSummary(
            mean=float(mean),
            std_dev=float(std_dev),
            std_error=float(std_error),
            n_samples=len(clean_data),
            confidence_interval=ci,
            median=float(np.median(clean_data)),
            min_val=float(np.min(clean_data)),
            max_val=float(np.max(clean_data)),
            outliers=outliers
        )
    
    # ==================== ANÁLISIS DE RUIDO ====================
    
    def estimate_noise_level(
        self,
        spectrum: np.ndarray,
        exclude_center_radius: int = 10
    ) -> Dict:
        """
        Estima nivel de ruido en espectro FFT.
        
        El ruido se estima desde regiones del espectro donde
        no se esperan señales (alta frecuencia espacial).
        
        Args:
            spectrum: Espectro de potencia 2D
            exclude_center_radius: Radio para excluir del análisis de ruido
        
        Returns:
            Dict con estimaciones de ruido
        """
        h, w = spectrum.shape
        cy, cx = h // 2, w // 2
        
        # Crear máscara para región de ruido (bordes del espectro)
        y, x = np.ogrid[:h, :w]
        distance = np.sqrt((x - cx)**2 + (y - cy)**2)
        
        # Región de ruido: lejos del centro
        noise_mask = distance > max(h, w) * 0.3
        signal_mask = (distance > exclude_center_radius) & (distance < max(h, w) * 0.3)
        
        noise_values = spectrum[noise_mask]
        signal_region = spectrum[signal_mask]
        
        noise_mean = np.mean(noise_values)
        noise_std = np.std(noise_values)
        noise_median = np.median(noise_values)
        
        # Pico en región de señal
        peak_value = np.max(signal_region) if signal_region.size > 0 else 0
        
        # SNR
        snr = peak_value / noise_mean if noise_mean > 0 else 0
        snr_db = 10 * np.log10(snr) if snr > 0 else -np.inf
        
        return {
            "noise_mean": float(noise_mean),
            "noise_std": float(noise_std),
            "noise_median": float(noise_median),
            "peak_signal": float(peak_value),
            "snr_linear": float(snr),
            "snr_db": float(snr_db),
            "quality": self._classify_snr(snr)
        }
    
    def _classify_snr(self, snr: float) -> str:
        """Clasifica calidad de SNR"""
        if snr > 100:
            return "excelente"
        elif snr > 30:
            return "bueno"
        elif snr > 10:
            return "aceptable"
        elif snr > 3:
            return "marginal"
        else:
            return "pobre"
    
    # ==================== ESTIMACIÓN DE INCERTIDUMBRE FFT ====================
    
    def estimate_frequency_uncertainty(
        self,
        spectrum: np.ndarray,
        peak_position: Tuple[int, int],
        method: str = "peak_width"
    ) -> float:
        """
        Estima incertidumbre en la posición del pico FFT.
        
        Métodos:
        - "peak_width": Usa FWHM del pico
        - "subpixel": Usa interpolación parabólica
        
        Returns:
            Incertidumbre en unidades de bins del espectro
        """
        py, px = peak_position
        h, w = spectrum.shape
        
        if method == "peak_width":
            # Extraer perfil horizontal y vertical
            profile_x = spectrum[py, max(0, px-20):min(w, px+21)]
            profile_y = spectrum[max(0, py-20):min(h, py+21), px]
            
            # Estimar FWHM
            fwhm_x = self._estimate_fwhm(profile_x)
            fwhm_y = self._estimate_fwhm(profile_y)
            
            # Incertidumbre ≈ FWHM / (2 * sqrt(2 * ln(2))) / SNR^0.5
            fwhm = np.sqrt(fwhm_x**2 + fwhm_y**2) / 2
            return fwhm / 2.355  # Convertir FWHM a sigma
            
        elif method == "subpixel":
            # Interpolación parabólica para mejor estimación
            # Incertidumbre típica: 0.1-0.5 píxeles
            return 0.3  # Valor conservador
        
        return 1.0  # Default: 1 bin
    
    def _estimate_fwhm(self, profile: np.ndarray) -> float:
        """Estima FWHM de un perfil 1D"""
        if len(profile) < 3:
            return 1.0
        
        max_val = np.max(profile)
        half_max = max_val / 2
        
        above_half = profile > half_max
        if not np.any(above_half):
            return 1.0
        
        indices = np.where(above_half)[0]
        fwhm = indices[-1] - indices[0] + 1
        
        return max(fwhm, 1.0)
    
    # ==================== REPORTE DE INCERTIDUMBRE ====================
    
    def generate_uncertainty_report(
        self,
        wavelength_mm: float,
        wavelength_uncertainty: float,
        theoretical_mm: Optional[float] = None,
        measurements: Optional[List[float]] = None
    ) -> Dict:
        """
        Genera reporte completo de incertidumbre para una medición.
        
        Returns:
            Dict con análisis completo de incertidumbre
        """
        report = {
            "measurement": {
                "value_mm": wavelength_mm,
                "uncertainty_mm": wavelength_uncertainty,
                "relative_uncertainty_percent": (wavelength_uncertainty / wavelength_mm * 100)
                    if wavelength_mm > 0 else 0,
                "formatted": f"{wavelength_mm:.2f} ± {wavelength_uncertainty:.2f} mm"
            }
        }
        
        # Comparación con teoría
        if theoretical_mm is not None:
            deviation = wavelength_mm - theoretical_mm
            z_score = deviation / wavelength_uncertainty if wavelength_uncertainty > 0 else 0
            
            report["theory_comparison"] = {
                "theoretical_mm": theoretical_mm,
                "deviation_mm": deviation,
                "deviation_percent": (deviation / theoretical_mm * 100) if theoretical_mm > 0 else 0,
                "z_score": z_score,
                "within_1sigma": abs(z_score) <= 1,
                "within_2sigma": abs(z_score) <= 2,
                "agreement": "excelente" if abs(z_score) <= 1 else 
                           "bueno" if abs(z_score) <= 2 else
                           "marginal" if abs(z_score) <= 3 else "pobre"
            }
        
        # Estadísticas si hay múltiples mediciones
        if measurements is not None and len(measurements) > 1:
            stats_summary = self.analyze_measurements(measurements)
            report["statistics"] = {
                "mean_mm": stats_summary.mean,
                "std_dev_mm": stats_summary.std_dev,
                "std_error_mm": stats_summary.std_error,
                "n_measurements": stats_summary.n_samples,
                "confidence_interval_95": stats_summary.confidence_interval,
                "outliers_detected": len(stats_summary.outliers),
                "consistency": "alta" if stats_summary.std_dev / stats_summary.mean < 0.05 else
                             "media" if stats_summary.std_dev / stats_summary.mean < 0.1 else "baja"
            }
        
        return report


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    analyzer = ErrorAnalyzer()
    
    print("=" * 60)
    print("ANÁLISIS DE ERRORES E INCERTIDUMBRE")
    print("=" * 60)
    
    # Propagación de incertidumbre
    print("\n=== Propagación de Incertidumbre ===")
    
    # Ejemplo: λ = 1/(f * cal)
    result = analyzer.propagate_wavelength_from_fft(
        spatial_frequency=0.02,       # ciclos/pixel
        freq_uncertainty=0.001,       # ±0.001
        calibration_px_per_mm=10.0,   # 10 px/mm
        cal_uncertainty=0.5           # ±0.5
    )
    print(f"Longitud de onda: {result}")
    print(f"Incertidumbre relativa: {result.relative_uncertainty_percent:.1f}%")
    
    # Análisis estadístico
    print("\n=== Análisis Estadístico ===")
    measurements = [25.2, 24.8, 25.0, 25.5, 24.9, 25.1, 25.3, 30.0, 25.0]  # Incluye outlier
    
    summary = analyzer.analyze_measurements(measurements)
    print(f"Media: {summary.mean:.2f} mm")
    print(f"Desviación estándar: {summary.std_dev:.2f} mm")
    print(f"Error estándar: {summary.std_error:.2f} mm")
    print(f"Intervalo de confianza 95%: ({summary.confidence_interval[0]:.2f}, {summary.confidence_interval[1]:.2f})")
    print(f"Outliers detectados: {summary.outliers}")
    
    # Reporte completo
    print("\n=== Reporte de Incertidumbre ===")
    report = analyzer.generate_uncertainty_report(
        wavelength_mm=25.0,
        wavelength_uncertainty=0.5,
        theoretical_mm=24.5,
        measurements=measurements
    )
    
    print(f"\nMedición: {report['measurement']['formatted']}")
    print(f"Comparación con teoría:")
    print(f"  - Desviación: {report['theory_comparison']['deviation_percent']:.1f}%")
    print(f"  - Z-score: {report['theory_comparison']['z_score']:.2f}")
    print(f"  - Acuerdo: {report['theory_comparison']['agreement']}")
