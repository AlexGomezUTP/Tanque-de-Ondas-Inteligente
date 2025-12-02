"""
TANQUE DE ONDAS - ANÁLISIS DE FOURIER
Análisis FFT 2D para medir longitud de onda
"""

import numpy as np
from scipy.fft import fft2, fftshift
from scipy.signal import windows
import logging
from typing import Tuple, Dict, Optional

class WaveAnalyzer:
    # Analiza patrones de onda usando FFT 2D

    def __init__(self, calibration_pixel_per_mm: float = 0.1):
        # Inicializa analizador
        # Args:
        #    calibration_pixel_per_mm: Factor de calibración (píxeles por mm)

        self.calibration = calibration_pixel_per_mm
        self.logger = logging.getLogger('WaveAnalyzer')

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

    def find_peak_frequency(self, spectrum: np.ndarray) -> Tuple[float, float, float]:
        # Encuentra pico dominante en espectro
        # Returns:
        #    (freq_x, freq_y, magnitude) en ciclos/píxel

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

        return freq_x, freq_y, peak_value

    def estimate_wavelength(self, image: np.ndarray, downsample: int = 4) -> Dict:
        # Estima longitud de onda a partir de imagen
        # Returns:
        #    Dict con: wavelength_mm, snr, confidence

        # Preprocesar
        processed = self.preprocess_image(image, downsample)

        # FFT
        spectrum = self.compute_fft2d(processed)

        # Encontrar pico
        freq_x, freq_y, peak_mag = self.find_peak_frequency(spectrum)

        # Frecuencia espacial total (en ciclos/píxel del downsampled)
        spatial_freq = np.sqrt(freq_x**2 + freq_y**2)

        if spatial_freq < 1e-8:
            return {"wavelength_mm": None, "wavelength_px": None, "snr": 0, "confidence": 0, "spectrum": spectrum}

        # Wavelength en píxeles del downsampled
        wavelength_px_downsampled = 1.0 / spatial_freq

        # Corregir por downsample para obtener wavelength en píxeles originales
        wavelength_px = wavelength_px_downsampled * downsample

        # Convertir a mm usando factor de calibración
        # calibration_pixel_per_mm indica cuántos píxeles hay por mm
        wavelength_mm = wavelength_px / self.calibration

        # SNR (relación pico/ruido)
        noise_level = np.median(spectrum)
        snr = peak_mag / (noise_level + 1e-8)
        confidence = min(1.0, snr / 100.0)  # Normalizar a 0-1

        return {
            "wavelength_mm": wavelength_mm,
            "wavelength_px": wavelength_px,
            "snr": snr,
            "confidence": confidence,
            "freq_x": freq_x,
            "freq_y": freq_y,
            "spectrum": spectrum
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
    test_image = np.sin(2 * np.pi * X / 20).astype(np.uint8)

    analyzer = WaveAnalyzer(calibration_pixel_per_mm=0.1)
    result = analyzer.estimate_wavelength(test_image)

    print(f"Wavelength: {result['wavelength_mm']:.2f} mm")
    print(f"SNR: {result['snr']:.2f}")
    print(f"Confianza: {result['confidence']:.2%}")
