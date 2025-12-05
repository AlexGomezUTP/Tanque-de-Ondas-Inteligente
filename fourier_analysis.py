"""
TANQUE DE ONDAS - ANÁLISIS DE FOURIER
Análisis FFT 2D para medir longitud de onda con incertidumbre
"""

import numpy as np
from scipy.fft import fft2, fftshift
from scipy.signal import windows
import logging
from typing import Tuple, Dict, Optional, List
from dataclasses import dataclass

# Importar módulos de física (con fallback para compatibilidad)
try:
    from calibration import CalibrationManager, CalibrationData
    from error_analysis import ErrorAnalyzer, MeasurementWithUncertainty
    from wave_theory import WaveTheory
    PHYSICS_MODULES_AVAILABLE = True
except ImportError:
    PHYSICS_MODULES_AVAILABLE = False


# Umbrales de validación para detectar ondas reales
MIN_SNR_THRESHOLD = 5.0          # SNR mínimo para considerar señal válida
MIN_CONFIDENCE_THRESHOLD = 0.10  # Confianza mínima (10%)
MIN_PERIODICITY_SCORE = 0.3      # Score mínimo de periodicidad
MIN_WAVELENGTH_PX = 4.0          # Longitud de onda mínima en píxeles (Nyquist)
MAX_WAVELENGTH_RATIO = 0.5       # λ no puede ser > 50% del tamaño de imagen


@dataclass
class WaveAnalysisResult:
    """Resultado completo del análisis de ondas con incertidumbre"""
    # Mediciones principales
    wavelength_mm: Optional[float] = None
    wavelength_uncertainty_mm: Optional[float] = None
    wavelength_px: Optional[float] = None
    
    # Frecuencia espacial
    spatial_frequency: Optional[float] = None
    freq_uncertainty: Optional[float] = None
    freq_x: Optional[float] = None
    freq_y: Optional[float] = None
    
    # Calidad
    snr: float = 0.0
    snr_db: float = 0.0
    confidence: float = 0.0
    quality: str = "desconocido"
    
    # Validación de ondas
    is_valid_wave: bool = False            # ¿Se detectó onda real?
    periodicity_score: float = 0.0         # Puntuación de periodicidad (0-1)
    validation_message: str = ""           # Mensaje explicativo
    rejection_reasons: Optional[List[str]] = None  # Razones de rechazo
    
    # Comparación teórica
    wavelength_theoretical_mm: Optional[float] = None
    error_percent: Optional[float] = None
    within_uncertainty: Optional[bool] = None
    
    # Espectro
    spectrum: Optional[np.ndarray] = None
    peak_position: Optional[Tuple[int, int]] = None
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario (excluyendo spectrum para serialización)"""
        return {
            "wavelength_mm": self.wavelength_mm,
            "wavelength_uncertainty_mm": self.wavelength_uncertainty_mm,
            "wavelength_px": self.wavelength_px,
            "snr": self.snr,
            "confidence": self.confidence,
            "quality": self.quality,
            "is_valid_wave": self.is_valid_wave,
            "periodicity_score": self.periodicity_score,
            "validation_message": self.validation_message,
            "rejection_reasons": self.rejection_reasons,
            "wavelength_theoretical_mm": self.wavelength_theoretical_mm,
            "error_percent": self.error_percent,
            "freq_x": self.freq_x,
            "freq_y": self.freq_y
        }


class WaveAnalyzer:
    """
    Analiza patrones de onda usando FFT 2D con cálculo de incertidumbre.
    
    Mejoras sobre versión básica:
    - Integración con módulo de calibración
    - Cálculo de incertidumbre en mediciones
    - Comparación con teoría física
    - Clasificación de calidad de medición
    """

    def __init__(
        self,
        calibration_pixel_per_mm: float = 10.0,
        calibration_uncertainty: float = 0.5,
        tank_depth_cm: float = 5.0
    ):
        """
        Inicializa analizador de ondas.
        
        Args:
            calibration_pixel_per_mm: Factor de calibración (píxeles por mm)
            calibration_uncertainty: Incertidumbre en calibración (px/mm)
            tank_depth_cm: Profundidad del agua en el tanque
        """
        self.calibration = calibration_pixel_per_mm
        self.calibration_uncertainty = calibration_uncertainty
        self.tank_depth_cm = tank_depth_cm
        self.logger = logging.getLogger('WaveAnalyzer')
        
        # Módulos de física avanzada
        self._error_analyzer = None
        self._wave_theory = None
        
        if PHYSICS_MODULES_AVAILABLE:
            self._error_analyzer = ErrorAnalyzer()
            self._wave_theory = WaveTheory(tank_depth_cm=tank_depth_cm)
    
    def set_calibration(
        self,
        pixel_per_mm: float,
        uncertainty: float = 0.5
    ) -> None:
        """Actualiza calibración"""
        self.calibration = pixel_per_mm
        self.calibration_uncertainty = uncertainty
        self.logger.info(f"Calibración actualizada: {pixel_per_mm:.2f} ± {uncertainty:.2f} px/mm")

    def preprocess_image(self, image: np.ndarray, downsample: int = 4) -> np.ndarray:
        # Preprocesa imagen
        # Args:
        #    image: Imagen en escala de grises
        #    downsample: Factor de downsampling
        # Returns:
        #    Imagen preprocesada

        # Downsampling para reducir cálculo
        if downsample > 1:
            image = image[::downsample, ::downsample]

        # Normalizar
        image = image.astype(np.float32)
        image = (image - image.min()) / (image.max() - image.min() + 1e-8)

        # Aplicar ventana Hann para reducir artefactos
        window = windows.hann(image.shape[0])[:, np.newaxis] * windows.hann(image.shape[1])[np.newaxis, :]
        image = image * window

        return image

    def compute_fft2d(self, image: np.ndarray) -> np.ndarray:
        # Calcula FFT 2D
        # Returns:
        #    spectrum_power (desplazado con DC en el centro)

        # FFT 2D
        fft_result = fft2(image)
        fft_shift = fftshift(fft_result)

        # Espectro de potencia
        spectrum = np.abs(fft_shift) ** 2

        return spectrum

    def find_peak_frequency(self, spectrum: np.ndarray) -> Tuple[float, float, float, Tuple[int, int]]:
        """
        Encuentra pico dominante en espectro.
        
        Returns:
            (freq_x, freq_y, magnitude, peak_position) en ciclos/píxel
        """
        h, w = spectrum.shape
        center_y, center_x = h // 2, w // 2

        # Máscara central (excluye DC y componentes muy bajas)
        mask = np.ones_like(spectrum)
        mask[center_y-5:center_y+5, center_x-5:center_x+5] = 0

        masked_spectrum = spectrum * mask
        peak_idx = np.unravel_index(np.argmax(masked_spectrum), masked_spectrum.shape)

        peak_value = spectrum[peak_idx]

        # Calcular frecuencia desde la distancia al centro
        # En el espectro desplazado, la frecuencia = distancia_al_centro / tamaño_imagen
        dist_y = peak_idx[0] - center_y
        dist_x = peak_idx[1] - center_x

        freq_x = dist_x / w  # ciclos/píxel
        freq_y = dist_y / h  # ciclos/píxel

        return freq_x, freq_y, peak_value, peak_idx

    def validate_periodicity(self, spectrum: np.ndarray, peak_position: Tuple[int, int]) -> Tuple[float, List[str]]:
        """
        Valida si hay periodicidad real en la imagen analizando el espectro.
        
        Criterios:
        1. El pico debe ser significativamente mayor que el ruido de fondo
        2. Debe haber armónicos (picos secundarios en múltiplos de la frecuencia)
        3. El pico debe estar localizado (no disperso)
        
        Returns:
            (periodicity_score, list_of_issues)
        """
        h, w = spectrum.shape
        center_y, center_x = h // 2, w // 2
        py, px = peak_position
        
        issues = []
        score = 1.0
        
        # 1. Verificar que el pico no sea ruido
        peak_value = spectrum[py, px]
        
        # Calcular ruido de fondo (mediana del espectro, excluyendo centro)
        mask = np.ones_like(spectrum, dtype=bool)
        mask[center_y-10:center_y+10, center_x-10:center_x+10] = False
        noise_level = np.median(spectrum[mask])
        noise_std = np.std(spectrum[mask])
        
        # El pico debe ser al menos 3 sigma sobre el ruido
        if peak_value < noise_level + 3 * noise_std:
            issues.append("Pico no distinguible del ruido de fondo")
            score *= 0.3
        
        # 2. Verificar localización del pico (FWHM pequeño)
        margin = 15
        profile_x = spectrum[py, max(0, px-margin):min(w, px+margin+1)]
        profile_y = spectrum[max(0, py-margin):min(h, py+margin+1), px]
        
        def check_peak_sharpness(profile):
            if len(profile) < 3:
                return False, "Perfil muy corto"
            max_val = np.max(profile)
            half_max = max_val / 2
            above_half = np.sum(profile > half_max)
            # Un pico bien definido debe ser angosto
            return above_half < len(profile) * 0.5, f"Ancho: {above_half}/{len(profile)}"
        
        sharp_x, _ = check_peak_sharpness(profile_x)
        sharp_y, _ = check_peak_sharpness(profile_y)
        
        if not (sharp_x and sharp_y):
            issues.append("Pico muy disperso (no hay frecuencia dominante clara)")
            score *= 0.5
        
        # 3. Verificar que no sea imagen uniforme (DC dominante)
        dc_region = spectrum[center_y-3:center_y+4, center_x-3:center_x+4]
        dc_power = np.sum(dc_region)
        total_power = np.sum(spectrum)
        
        if dc_power > 0.9 * total_power:
            issues.append("Imagen casi uniforme (sin variación espacial)")
            score *= 0.1
        
        # 4. Verificar distribución de energía en el espectro
        # Si la energía está muy concentrada en bajas frecuencias, probablemente no hay ondas
        y, x = np.ogrid[:h, :w]
        distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        
        low_freq_mask = distance < min(h, w) * 0.1
        mid_freq_mask = (distance >= min(h, w) * 0.1) & (distance < min(h, w) * 0.3)
        
        low_freq_energy = np.sum(spectrum[low_freq_mask])
        mid_freq_energy = np.sum(spectrum[mid_freq_mask])
        
        if mid_freq_energy < low_freq_energy * 0.01:
            issues.append("Sin patrones periódicos detectables")
            score *= 0.2
        
        return max(0.0, min(1.0, score)), issues
    
    def estimate_frequency_uncertainty(
        self,
        spectrum: np.ndarray,
        peak_position: Tuple[int, int]
    ) -> float:
        """
        Estima incertidumbre en la frecuencia espacial usando ancho del pico.
        
        Returns:
            Incertidumbre en ciclos/píxel
        """
        py, px = peak_position
        h, w = spectrum.shape
        
        # Extraer perfiles en X e Y
        margin = 15
        profile_x = spectrum[py, max(0, px-margin):min(w, px+margin+1)]
        profile_y = spectrum[max(0, py-margin):min(h, py+margin+1), px]
        
        # Estimar FWHM (Full Width at Half Maximum)
        def estimate_fwhm(profile):
            if len(profile) < 3:
                return 2.0
            max_val = np.max(profile)
            half_max = max_val / 2
            above_half = profile > half_max
            if not np.any(above_half):
                return 2.0
            indices = np.where(above_half)[0]
            return max(indices[-1] - indices[0] + 1, 1.0)
        
        fwhm_x = estimate_fwhm(profile_x)
        fwhm_y = estimate_fwhm(profile_y)
        
        # Incertidumbre en frecuencia (en bins)
        fwhm_avg = (fwhm_x + fwhm_y) / 2
        sigma_bins = fwhm_avg / 2.355  # FWHM = 2.355 * sigma
        
        # Convertir a ciclos/píxel
        uncertainty = sigma_bins / max(h, w)
        
        return max(uncertainty, 1.0 / max(h, w))  # Mínimo: 1 bin

    def estimate_wavelength(
        self,
        image: np.ndarray,
        downsample: int = 4,
        excitation_frequency_hz: Optional[float] = None
    ) -> WaveAnalysisResult:
        """
        Estima longitud de onda con incertidumbre y comparación teórica.
        
        Args:
            image: Imagen en escala de grises
            downsample: Factor de downsampling
            excitation_frequency_hz: Frecuencia del servo (para comparar con teoría)
        
        Returns:
            WaveAnalysisResult con mediciones completas e incertidumbre
        """
        result = WaveAnalysisResult()
        
        # Preprocesar
        processed = self.preprocess_image(image, downsample)

        # FFT
        spectrum = self.compute_fft2d(processed)
        result.spectrum = spectrum

        # Encontrar pico
        freq_x, freq_y, peak_mag, peak_pos = self.find_peak_frequency(spectrum)
        result.freq_x = freq_x
        result.freq_y = freq_y
        result.peak_position = peak_pos

        # Frecuencia espacial total (en ciclos/píxel del downsampled)
        spatial_freq = np.sqrt(freq_x**2 + freq_y**2)
        result.spatial_frequency = spatial_freq

        if spatial_freq < 1e-8:
            result.quality = "sin_señal"
            return result

        # Estimar incertidumbre en frecuencia
        freq_uncertainty = self.estimate_frequency_uncertainty(spectrum, peak_pos)
        result.freq_uncertainty = freq_uncertainty

        # Wavelength en píxeles del downsampled
        wavelength_px_downsampled = 1.0 / spatial_freq

        # Corregir por downsample para obtener wavelength en píxeles originales
        wavelength_px = wavelength_px_downsampled * downsample
        result.wavelength_px = wavelength_px

        # Convertir a mm usando factor de calibración
        wavelength_mm = wavelength_px / self.calibration
        result.wavelength_mm = wavelength_mm

        # Calcular incertidumbre en longitud de onda
        if self._error_analyzer and PHYSICS_MODULES_AVAILABLE:
            measurement = self._error_analyzer.propagate_wavelength_from_fft(
                spatial_frequency=spatial_freq / downsample,  # En original
                freq_uncertainty=freq_uncertainty / downsample,
                calibration_px_per_mm=self.calibration,
                cal_uncertainty=self.calibration_uncertainty
            )
            result.wavelength_uncertainty_mm = measurement.uncertainty
        else:
            # Estimación simplificada de incertidumbre
            rel_uncertainty = np.sqrt(
                (freq_uncertainty / spatial_freq)**2 +
                (self.calibration_uncertainty / self.calibration)**2
            )
            result.wavelength_uncertainty_mm = wavelength_mm * rel_uncertainty

        # Calcular SNR
        noise_level = np.median(spectrum)
        result.snr = peak_mag / (noise_level + 1e-8)
        result.snr_db = 10 * np.log10(result.snr) if result.snr > 0 else 0
        result.confidence = min(1.0, result.snr / 100.0)
        
        # Clasificar calidad
        if result.snr > 100:
            result.quality = "excelente"
        elif result.snr > 30:
            result.quality = "bueno"
        elif result.snr > 10:
            result.quality = "aceptable"
        elif result.snr > 3:
            result.quality = "marginal"
        else:
            result.quality = "pobre"
        
        # ========== VALIDACIÓN DE ONDAS REALES ==========
        rejection_reasons = []
        
        # Validar periodicidad
        periodicity_score, periodicity_issues = self.validate_periodicity(spectrum, peak_pos)
        result.periodicity_score = periodicity_score
        rejection_reasons.extend(periodicity_issues)
        
        # Verificar SNR mínimo
        if result.snr < MIN_SNR_THRESHOLD:
            rejection_reasons.append(f"SNR muy bajo ({result.snr:.1f} < {MIN_SNR_THRESHOLD})")
        
        # Verificar confianza mínima
        if result.confidence < MIN_CONFIDENCE_THRESHOLD:
            rejection_reasons.append(f"Confianza muy baja ({result.confidence:.1%} < {MIN_CONFIDENCE_THRESHOLD:.0%})")
        
        # Verificar longitud de onda física razonable
        if wavelength_px < MIN_WAVELENGTH_PX:
            rejection_reasons.append(f"Longitud de onda menor al límite de Nyquist ({wavelength_px:.1f} < {MIN_WAVELENGTH_PX} px)")
        
        # Verificar que λ no sea mayor que la imagen (artefacto)
        img_size = min(processed.shape) * downsample
        if wavelength_px > img_size * MAX_WAVELENGTH_RATIO:
            rejection_reasons.append(f"Longitud de onda demasiado grande (>{MAX_WAVELENGTH_RATIO:.0%} de la imagen)")
        
        # Determinar si es onda válida
        result.is_valid_wave = (
            len(rejection_reasons) == 0 and 
            periodicity_score >= MIN_PERIODICITY_SCORE and
            result.snr >= MIN_SNR_THRESHOLD
        )
        
        result.rejection_reasons = rejection_reasons if rejection_reasons else None
        
        if result.is_valid_wave:
            result.validation_message = f"✅ Onda detectada con confianza {result.confidence:.0%}"
        elif rejection_reasons:
            result.validation_message = f"⚠️ Análisis no confiable: {'; '.join(rejection_reasons[:2])}"
        else:
            result.validation_message = "❌ No se detectaron ondas en la imagen"

        # Comparación con teoría si hay frecuencia de excitación
        if excitation_frequency_hz and self._wave_theory:
            theoretical = self._wave_theory.theoretical_wavelength(excitation_frequency_hz)
            result.wavelength_theoretical_mm = theoretical
            result.error_percent = abs(wavelength_mm - theoretical) / theoretical * 100
            
            if result.wavelength_uncertainty_mm:
                result.within_uncertainty = (
                    abs(wavelength_mm - theoretical) <= 2 * result.wavelength_uncertainty_mm
                )

        return result
    
    def estimate_wavelength_simple(
        self,
        image: np.ndarray,
        downsample: int = 4
    ) -> Dict:
        """
        Versión simplificada para compatibilidad con código existente.
        
        Returns:
            Dict con: wavelength_mm, wavelength_px, snr, confidence, spectrum
        """
        result = self.estimate_wavelength(image, downsample)
        
        return {
            "wavelength_mm": result.wavelength_mm,
            "wavelength_px": result.wavelength_px,
            "wavelength_uncertainty_mm": result.wavelength_uncertainty_mm,
            "snr": result.snr,
            "confidence": result.confidence,
            "quality": result.quality,
            "freq_x": result.freq_x,
            "freq_y": result.freq_y,
            "spectrum": result.spectrum
        }
    
    def analyze_multiple_frames(
        self,
        frames: List[np.ndarray],
        excitation_frequency_hz: Optional[float] = None
    ) -> Dict:
        """
        Analiza múltiples frames y calcula estadísticas.
        
        Returns:
            Dict con estadísticas de las mediciones
        """
        wavelengths = []
        snrs = []
        
        for frame in frames:
            result = self.estimate_wavelength(frame, excitation_frequency_hz=excitation_frequency_hz)
            if result.wavelength_mm is not None:
                wavelengths.append(result.wavelength_mm)
                snrs.append(result.snr)
        
        if not wavelengths:
            return {"error": "No se pudieron medir longitudes de onda"}
        
        wavelengths = np.array(wavelengths)
        
        return {
            "n_frames": len(wavelengths),
            "wavelength_mean_mm": float(np.mean(wavelengths)),
            "wavelength_std_mm": float(np.std(wavelengths, ddof=1)),
            "wavelength_sem_mm": float(np.std(wavelengths, ddof=1) / np.sqrt(len(wavelengths))),
            "wavelength_min_mm": float(np.min(wavelengths)),
            "wavelength_max_mm": float(np.max(wavelengths)),
            "snr_mean": float(np.mean(snrs)),
            "wavelength_theoretical_mm": self._wave_theory.theoretical_wavelength(excitation_frequency_hz)
                if excitation_frequency_hz and self._wave_theory else None
        }


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Crear imagen de prueba (patrón de onda simulado)
    from scipy import ndimage
    x = np.linspace(0, 10, 256)
    y = np.linspace(0, 10, 256)
    X, Y = np.meshgrid(x, y)

    # Onda sinusoidal con wavelength ~20 píxeles
    test_image = (127 + 100 * np.sin(2 * np.pi * X / 0.8)).astype(np.uint8)

    # Usar calibración realista: 10 px/mm
    analyzer = WaveAnalyzer(
        calibration_pixel_per_mm=10.0,
        calibration_uncertainty=0.5,
        tank_depth_cm=5.0
    )
    
    print("=" * 50)
    print("ANÁLISIS FFT 2D CON INCERTIDUMBRE")
    print("=" * 50)
    
    # Análisis completo
    result = analyzer.estimate_wavelength(test_image, excitation_frequency_hz=10.0)

    print(f"\nResultados:")
    print(f"  Longitud de onda: {result.wavelength_mm:.2f} ± {result.wavelength_uncertainty_mm:.2f} mm")
    print(f"  SNR: {result.snr:.2f} ({result.snr_db:.1f} dB)")
    print(f"  Confianza: {result.confidence:.1%}")
    print(f"  Calidad: {result.quality}")
    
    if result.wavelength_theoretical_mm:
        print(f"\nComparación con teoría:")
        print(f"  λ teórica: {result.wavelength_theoretical_mm:.2f} mm")
        print(f"  Error: {result.error_percent:.1f}%")
        print(f"  Dentro de incertidumbre: {result.within_uncertainty}")
    
    # Versión simplificada (compatible)
    print("\n--- Versión simplificada (dict) ---")
    simple_result = analyzer.estimate_wavelength_simple(test_image)
    print(f"Wavelength: {simple_result['wavelength_mm']:.2f} mm")
    print(f"SNR: {simple_result['snr']:.2f}")
