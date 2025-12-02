import unittest
import numpy as np
from interference_analysis import InterferenceAnalyzer

class TestInterferenceAnalysis(unittest.TestCase):
    def test_interference_detects_fringes(self):
        x = np.linspace(0, 256, 512)
        y = np.linspace(0, 256, 512)
        X, Y = np.meshgrid(x, y)
        # Franjas verticales bien definidas
        test_image = (127 + 100 * np.sin(2 * np.pi * X / 20)).astype(np.uint8)
        analyzer = InterferenceAnalyzer()
        # Forzar umbral bajo para asegurar detección
        labeled, num_fringes = analyzer.detect_fringes(test_image, threshold=0.2)
        self.assertGreater(num_fringes, 0)
        result = analyzer.analyze_interference(test_image)
        self.assertGreaterEqual(result['contrast'], 0)
        self.assertLessEqual(result['contrast'], 1)
        self.assertIn(result['visibility'], ['Excelente', 'Buena', 'Pobre'])

if __name__ == '__main__':
    unittest.main()
