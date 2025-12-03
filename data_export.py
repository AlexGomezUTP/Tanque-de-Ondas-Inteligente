"""
TANQUE DE ONDAS - EXPORTACIÓN DE DATOS EXPERIMENTALES
Exporta datos con metadata completa para reproducibilidad científica
"""

import numpy as np
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
import hashlib


@dataclass
class ExperimentMetadata:
    """Metadata completa del experimento"""
    # Identificación
    experiment_id: str
    experiment_date: str
    experiment_time: str
    
    # Configuración del tanque
    tank_depth_cm: float
    tank_width_cm: float
    tank_length_cm: float
    water_temperature_c: Optional[float] = None
    
    # Configuración del servo
    servo_frequency_hz: float = 0.0
    servo_amplitude: float = 0.0
    
    # Calibración
    calibration_px_per_mm: float = 0.0
    calibration_uncertainty: float = 0.0
    calibration_date: str = ""
    
    # Cámara
    camera_resolution: str = ""
    camera_fps: float = 0.0
    camera_id: str = ""
    
    # Análisis
    fft_downsample_factor: int = 4
    analysis_version: str = "1.0.0"
    
    # Notas
    operator: str = ""
    notes: str = ""


@dataclass
class MeasurementRecord:
    """Registro individual de medición"""
    timestamp_ms: float
    frame_number: int
    
    # Resultados FFT
    wavelength_mm: Optional[float] = None
    wavelength_uncertainty_mm: Optional[float] = None
    wavelength_px: Optional[float] = None
    spatial_freq_x: Optional[float] = None
    spatial_freq_y: Optional[float] = None
    snr: float = 0.0
    confidence: float = 0.0
    
    # Resultados de interferencia
    num_fringes: int = 0
    fringe_spacing_px: Optional[float] = None
    contrast: float = 0.0
    visibility: str = ""
    
    # Comparación teórica
    wavelength_theoretical_mm: Optional[float] = None
    error_percent: Optional[float] = None


class DataExporter:
    """
    Exporta datos experimentales en formatos estándar con metadata completa.
    
    Formatos soportados:
    - CSV: Para análisis en hojas de cálculo
    - JSON: Para procesamiento programático
    - HDF5: Para grandes volúmenes de datos (opcional)
    
    Garantiza reproducibilidad científica incluyendo:
    - Configuración completa del experimento
    - Parámetros de calibración
    - Versión del software de análisis
    - Checksums de integridad
    """
    
    def __init__(self, output_dir: str = "data_exports"):
        self.logger = logging.getLogger('DataExporter')
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def create_experiment_session(
        self,
        tank_depth_cm: float = 5.0,
        tank_width_cm: float = 30.0,
        tank_length_cm: float = 50.0,
        servo_frequency_hz: float = 10.0,
        servo_amplitude: float = 0.8,
        calibration_px_per_mm: float = 10.0,
        calibration_uncertainty: float = 0.5,
        camera_resolution: str = "1920x1080",
        camera_fps: float = 30.0,
        operator: str = "",
        notes: str = ""
    ) -> ExperimentMetadata:
        """Crea sesión de experimento con metadata"""
        
        now = datetime.now()
        experiment_id = f"EXP_{now.strftime('%Y%m%d_%H%M%S')}"
        
        return ExperimentMetadata(
            experiment_id=experiment_id,
            experiment_date=now.strftime("%Y-%m-%d"),
            experiment_time=now.strftime("%H:%M:%S"),
            tank_depth_cm=tank_depth_cm,
            tank_width_cm=tank_width_cm,
            tank_length_cm=tank_length_cm,
            servo_frequency_hz=servo_frequency_hz,
            servo_amplitude=servo_amplitude,
            calibration_px_per_mm=calibration_px_per_mm,
            calibration_uncertainty=calibration_uncertainty,
            calibration_date=now.strftime("%Y-%m-%d"),
            camera_resolution=camera_resolution,
            camera_fps=camera_fps,
            operator=operator,
            notes=notes
        )
    
    def export_to_csv(
        self,
        metadata: ExperimentMetadata,
        measurements: List[MeasurementRecord],
        filename: Optional[str] = None
    ) -> str:
        """
        Exporta datos a CSV con metadata en comentarios.
        
        Formato compatible con:
        - Excel, LibreOffice Calc
        - Python pandas
        - R
        - MATLAB
        """
        if filename is None:
            filename = f"{metadata.experiment_id}_data.csv"
        
        filepath = self.output_dir / filename
        
        # Convertir mediciones a DataFrame
        records = [asdict(m) for m in measurements]
        df = pd.DataFrame(records)
        
        # Escribir archivo con comentarios de metadata
        with open(filepath, 'w', encoding='utf-8') as f:
            # Header con metadata
            f.write("# ============================================\n")
            f.write(f"# TANQUE DE ONDAS - DATOS EXPERIMENTALES\n")
            f.write("# ============================================\n")
            f.write(f"# Experiment ID: {metadata.experiment_id}\n")
            f.write(f"# Date: {metadata.experiment_date}\n")
            f.write(f"# Time: {metadata.experiment_time}\n")
            f.write("#\n")
            f.write("# === TANK CONFIGURATION ===\n")
            f.write(f"# Tank depth (cm): {metadata.tank_depth_cm}\n")
            f.write(f"# Tank dimensions (cm): {metadata.tank_width_cm} x {metadata.tank_length_cm}\n")
            if metadata.water_temperature_c:
                f.write(f"# Water temperature (°C): {metadata.water_temperature_c}\n")
            f.write("#\n")
            f.write("# === SERVO CONFIGURATION ===\n")
            f.write(f"# Frequency (Hz): {metadata.servo_frequency_hz}\n")
            f.write(f"# Amplitude: {metadata.servo_amplitude}\n")
            f.write("#\n")
            f.write("# === CALIBRATION ===\n")
            f.write(f"# Calibration (px/mm): {metadata.calibration_px_per_mm} ± {metadata.calibration_uncertainty}\n")
            f.write(f"# Calibration date: {metadata.calibration_date}\n")
            f.write("#\n")
            f.write("# === CAMERA ===\n")
            f.write(f"# Resolution: {metadata.camera_resolution}\n")
            f.write(f"# FPS: {metadata.camera_fps}\n")
            f.write("#\n")
            f.write(f"# Operator: {metadata.operator}\n")
            f.write(f"# Notes: {metadata.notes}\n")
            f.write(f"# Analysis version: {metadata.analysis_version}\n")
            f.write(f"# Total measurements: {len(measurements)}\n")
            f.write("# ============================================\n")
            f.write("#\n")
            
            # Escribir datos
            df.to_csv(f, index=False)
        
        self.logger.info(f"Datos exportados a: {filepath}")
        return str(filepath)
    
    def export_to_json(
        self,
        metadata: ExperimentMetadata,
        measurements: List[MeasurementRecord],
        include_raw_frames: bool = False,
        raw_frames: Optional[List[np.ndarray]] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Exporta datos a JSON estructurado.
        
        Ideal para:
        - APIs y servicios web
        - Procesamiento con Python/JavaScript
        - Almacenamiento en bases de datos NoSQL
        """
        if filename is None:
            filename = f"{metadata.experiment_id}_data.json"
        
        filepath = self.output_dir / filename
        
        data = {
            "format_version": "1.0",
            "export_timestamp": datetime.now().isoformat(),
            "metadata": asdict(metadata),
            "measurements": [asdict(m) for m in measurements],
            "statistics": self._calculate_statistics(measurements)
        }
        
        # Agregar frames si se solicitan (como listas base64 o referencias)
        if include_raw_frames and raw_frames:
            data["raw_frames_info"] = {
                "included": False,
                "count": len(raw_frames),
                "note": "Raw frames guardados en archivo HDF5 separado"
            }
        
        # Calcular checksum
        data_str = json.dumps(data, sort_keys=True, default=str)
        data["checksum_md5"] = hashlib.md5(data_str.encode()).hexdigest()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.logger.info(f"Datos exportados a: {filepath}")
        return str(filepath)
    
    def _calculate_statistics(self, measurements: List[MeasurementRecord]) -> Dict:
        """Calcula estadísticas resumen de las mediciones"""
        if not measurements:
            return {}
        
        wavelengths = [m.wavelength_mm for m in measurements if m.wavelength_mm is not None]
        snrs = [m.snr for m in measurements if m.snr > 0]
        confidences = [m.confidence for m in measurements]
        
        stats = {
            "total_measurements": len(measurements),
            "valid_wavelength_measurements": len(wavelengths)
        }
        
        if wavelengths:
            stats["wavelength_mm"] = {
                "mean": float(np.mean(wavelengths)),
                "std": float(np.std(wavelengths)),
                "min": float(np.min(wavelengths)),
                "max": float(np.max(wavelengths)),
                "median": float(np.median(wavelengths))
            }
        
        if snrs:
            stats["snr"] = {
                "mean": float(np.mean(snrs)),
                "min": float(np.min(snrs)),
                "max": float(np.max(snrs))
            }
        
        if confidences:
            stats["confidence"] = {
                "mean": float(np.mean(confidences)),
                "min": float(np.min(confidences)),
                "max": float(np.max(confidences))
            }
        
        return stats
    
    def export_summary_report(
        self,
        metadata: ExperimentMetadata,
        measurements: List[MeasurementRecord],
        theoretical_wavelength_mm: Optional[float] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Genera reporte resumen legible para documentación.
        """
        if filename is None:
            filename = f"{metadata.experiment_id}_report.txt"
        
        filepath = self.output_dir / filename
        
        stats = self._calculate_statistics(measurements)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("   REPORTE DE EXPERIMENTO - TANQUE DE ONDAS\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Experimento: {metadata.experiment_id}\n")
            f.write(f"Fecha: {metadata.experiment_date} {metadata.experiment_time}\n")
            f.write(f"Operador: {metadata.operator or 'No especificado'}\n\n")
            
            f.write("-" * 40 + "\n")
            f.write("CONFIGURACIÓN DEL TANQUE\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Profundidad: {metadata.tank_depth_cm} cm\n")
            f.write(f"  Dimensiones: {metadata.tank_width_cm} x {metadata.tank_length_cm} cm\n")
            f.write(f"  Frecuencia del servo: {metadata.servo_frequency_hz} Hz\n")
            f.write(f"  Amplitud: {metadata.servo_amplitude}\n\n")
            
            f.write("-" * 40 + "\n")
            f.write("CALIBRACIÓN\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Factor: {metadata.calibration_px_per_mm} ± {metadata.calibration_uncertainty} px/mm\n")
            f.write(f"  Fecha calibración: {metadata.calibration_date}\n\n")
            
            f.write("-" * 40 + "\n")
            f.write("RESULTADOS\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Total de mediciones: {stats.get('total_measurements', 0)}\n")
            f.write(f"  Mediciones válidas: {stats.get('valid_wavelength_measurements', 0)}\n\n")
            
            if 'wavelength_mm' in stats:
                wl = stats['wavelength_mm']
                f.write(f"  Longitud de onda (experimental):\n")
                f.write(f"    Media: {wl['mean']:.2f} mm\n")
                f.write(f"    Desv. estándar: {wl['std']:.2f} mm\n")
                f.write(f"    Rango: [{wl['min']:.2f}, {wl['max']:.2f}] mm\n\n")
                
                if theoretical_wavelength_mm:
                    error = abs(wl['mean'] - theoretical_wavelength_mm) / theoretical_wavelength_mm * 100
                    f.write(f"  Longitud de onda (teórica): {theoretical_wavelength_mm:.2f} mm\n")
                    f.write(f"  Error experimental: {error:.1f}%\n\n")
            
            if 'snr' in stats:
                f.write(f"  SNR promedio: {stats['snr']['mean']:.1f}\n")
            
            if 'confidence' in stats:
                f.write(f"  Confianza promedio: {stats['confidence']['mean']:.1%}\n")
            
            f.write("\n")
            f.write("-" * 40 + "\n")
            f.write("NOTAS\n")
            f.write("-" * 40 + "\n")
            f.write(f"  {metadata.notes or 'Sin notas adicionales'}\n\n")
            
            f.write("=" * 60 + "\n")
            f.write(f"Reporte generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Versión del análisis: {metadata.analysis_version}\n")
        
        self.logger.info(f"Reporte exportado a: {filepath}")
        return str(filepath)
    
    def load_from_json(self, filepath: str) -> Tuple[ExperimentMetadata, List[MeasurementRecord]]:
        """Carga datos desde archivo JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metadata = ExperimentMetadata(**data['metadata'])
        measurements = [MeasurementRecord(**m) for m in data['measurements']]
        
        return metadata, measurements


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    exporter = DataExporter()
    
    # Crear sesión de experimento
    metadata = exporter.create_experiment_session(
        tank_depth_cm=5.0,
        servo_frequency_hz=10.0,
        servo_amplitude=0.8,
        calibration_px_per_mm=10.0,
        calibration_uncertainty=0.5,
        operator="Estudiante de Física",
        notes="Experimento de calibración inicial"
    )
    
    print(f"Experimento creado: {metadata.experiment_id}")
    
    # Simular mediciones
    measurements = []
    for i in range(10):
        m = MeasurementRecord(
            timestamp_ms=i * 100,
            frame_number=i,
            wavelength_mm=25.0 + np.random.normal(0, 0.5),
            wavelength_uncertainty_mm=0.5,
            wavelength_px=250 + np.random.normal(0, 5),
            snr=50 + np.random.normal(0, 10),
            confidence=0.85 + np.random.normal(0, 0.05),
            wavelength_theoretical_mm=24.5
        )
        m.error_percent = abs(m.wavelength_mm - 24.5) / 24.5 * 100
        measurements.append(m)
    
    # Exportar
    csv_path = exporter.export_to_csv(metadata, measurements)
    json_path = exporter.export_to_json(metadata, measurements)
    report_path = exporter.export_summary_report(
        metadata, measurements,
        theoretical_wavelength_mm=24.5
    )
    
    print(f"\nArchivos generados:")
    print(f"  CSV: {csv_path}")
    print(f"  JSON: {json_path}")
    print(f"  Reporte: {report_path}")
