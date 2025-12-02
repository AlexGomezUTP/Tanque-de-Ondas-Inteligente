import unittest
import numpy as np
from fourier_analysis import WaveAnalyzer

class TestFourierAnalysis(unittest.TestCase):
    def test_fft_detects_wavelength(self):
        x = np.linspace(0, 256, 256)
        y = np.linspace(0, 256, 256)
        X, Y = np.meshgrid(x, y)
        # Onda de 20 píxeles de longitud de onda, calibración 1 px = 1 mm
        test_image = (127 + 100 * np.sin(2 * np.pi * X / 20)).astype(np.uint8)
        analyzer = WaveAnalyzer(calibration_pixel_per_mm=1.0)
        result = analyzer.estimate_wavelength(test_image)
        self.assertIsNotNone(result['wavelength_mm'])
        self.assertAlmostEqual(result['wavelength_mm'], 20, delta=2)

    def test_fft_snr_confidence(self):
        x = np.linspace(0, 256, 256)
        y = np.linspace(0, 256, 256)
        X, Y = np.meshgrid(x, y)
        test_image = (127 + 100 * np.sin(2 * np.pi * X / 20)).astype(np.uint8)
        analyzer = WaveAnalyzer(calibration_pixel_per_mm=1.0)
        result = analyzer.estimate_wavelength(test_image)
        self.assertGreater(result['snr'], 0)
        self.assertGreaterEqual(result['confidence'], 0)
        self.assertLessEqual(result['confidence'], 1)

if __name__ == '__main__':
    unittest.main()
