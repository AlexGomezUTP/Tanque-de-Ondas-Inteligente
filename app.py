"""
TANQUE DE ONDAS - APP STREAMLIT
Interfaz web para control y análisis de experimento
"""

import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import os
import json
import logging
from pathlib import Path

# Importar módulos personalizados
from servo_control import ServoController
from camera import VideoCapture
from fourier_analysis import WaveAnalyzer
from interference_analysis import InterferenceAnalyzer

# Importar nuevos módulos de física
try:
    from calibration import CalibrationManager
    from wave_theory import WaveTheory
    from physics_validation import PhysicsValidator, ValidationStatus
    from data_export import DataExporter, ExperimentMetadata, MeasurementRecord
    from error_analysis import ErrorAnalyzer
    PHYSICS_MODULES_AVAILABLE = True
except ImportError as e:
    PHYSICS_MODULES_AVAILABLE = False
    print(f"Advertencia: Módulos de física no disponibles: {e}")

# ========== CONFIGURACIÓN STREAMLIT ==========
st.set_page_config(
    page_title="Tanque de Ondas Inteligente",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== ESTILOS PERSONALIZADOS ==========
st.markdown('''
<style>
    /* Importar fuentes de Google */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    /* Variables de color */
    :root {
        --primary-color: #0066cc;
        --secondary-color: #00a8e8;
        --accent-color: #00c9ff;
        --success-color: #00d084;
        --warning-color: #ffb800;
        --error-color: #ff4b6e;
        --dark-bg: #1a1a2e;
        --light-bg: #f5f7fa;
        --card-bg: #ffffff;
        --text-primary: #2d3436;
        --text-secondary: #636e72;
    }
    
    /* Estilo general */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    /* Header principal con gradiente */
    .header-main {
        font-family: 'Poppins', sans-serif;
        font-size: 3em;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .subtitle {
        font-family: 'Poppins', sans-serif;
        font-size: 1.2em;
        color: var(--text-secondary);
        text-align: center;
        margin-bottom: 30px;
        font-weight: 300;
    }
    
    /* Sidebar mejorado */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d3436 0%, #1a1a2e 100%);
        padding: 20px;
    }
    
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label {
        color: #ffffff !important;
        font-family: 'Poppins', sans-serif;
    }
    
    section[data-testid="stSidebar"] p {
        color: #b2bec3 !important;
    }
    
    /* Tarjetas con sombra y hover */
    .element-container {
        transition: transform 0.3s ease;
    }
    
    .metric-box {
        background: var(--card-bg);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        border-left: 4px solid var(--primary-color);
        transition: all 0.3s ease;
    }
    
    .metric-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
    }
    
    /* Botones mejorados */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 0.95em;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Métricas con estilo */
    div[data-testid="stMetricValue"] {
        font-family: 'Poppins', sans-serif;
        font-size: 2em;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    div[data-testid="stMetricLabel"] {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: var(--text-primary);
        font-size: 0.9em;
    }
    
    /* Sliders personalizados */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Dataframe mejorado */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
    }
    
    /* Info boxes con iconos */
    .stAlert {
        border-radius: 10px;
        border-left-width: 5px;
        font-family: 'Poppins', sans-serif;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* Divider elegante */
    hr {
        margin: 30px 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
    }
    
    /* Panel de análisis con gradiente sutil */
    .analysis-panel {
        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(245,247,250,0.95) 100%);
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* File uploader mejorado */
    section[data-testid="stFileUploadDropzone"] {
        border: 2px dashed #667eea;
        border-radius: 10px;
        background: rgba(102, 126, 234, 0.05);
        transition: all 0.3s ease;
    }
    
    section[data-testid="stFileUploadDropzone"]:hover {
        border-color: #764ba2;
        background: rgba(118, 75, 162, 0.08);
    }
    
    /* Imagen con borde redondeado */
    .stImage > img {
        border-radius: 15px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
    }
    
    /* Footer elegante */
    .footer {
        font-family: 'Poppins', sans-serif;
        text-align: center;
        color: var(--text-secondary);
        padding: 30px;
        margin-top: 50px;
        background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(245,247,250,0.9) 100%);
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
    }
    
    /* Animación de carga */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .stSpinner > div {
        border-color: #667eea !important;
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    /* Tabs mejorados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 10px;
        padding: 10px 20px;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Tarjetas de información con iconos */
    .info-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        margin: 10px 0;
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .info-card:hover {
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.12);
        transform: translateX(5px);
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        font-family: 'Poppins', sans-serif;
    }
    
    .badge-success {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
    }
    
    .badge-warning {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .badge-info {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
    }
</style>
''', unsafe_allow_html=True)

# ========== INICIALIZAR SESIÓN ==========
if 'servo_controller' not in st.session_state:
    st.session_state.servo_controller = None
    st.session_state.camera = None
    st.session_state.measurements = []
    st.session_state.recording = False
    st.session_state.frames_buffer = []
    st.session_state.video_file = None
    st.session_state.current_frame_idx = 0
    
    # Nuevos estados para física
    st.session_state.tank_depth_cm = 5.0
    st.session_state.calibration_px_per_mm = 10.0
    st.session_state.calibration_uncertainty = 0.5
    st.session_state.current_frequency = 10.0
    st.session_state.current_amplitude = 0.8
    
    # Inicializar módulos de física si disponibles
    if PHYSICS_MODULES_AVAILABLE:
        st.session_state.calibration_manager = CalibrationManager()
        st.session_state.wave_theory = WaveTheory(tank_depth_cm=5.0)
        st.session_state.physics_validator = PhysicsValidator()
        st.session_state.data_exporter = DataExporter()
    else:
        st.session_state.calibration_manager = None
        st.session_state.wave_theory = None
        st.session_state.physics_validator = None
        st.session_state.data_exporter = None

# ========== FUNCIONES AUXILIARES ==========
def init_hardware():
    """Inicializa hardware (Arduino + Cámara) y muestra estado real de conexión"""
    with st.spinner("Conectando hardware..."):
        arduino_ok = False
        camera_ok = False
        messages = []
        
        # Intentar conectar Arduino
        try:
            port = '/dev/ttyUSB0' if os.name != 'nt' else 'COM3'
            st.session_state.servo_controller = ServoController(port=port)
            if st.session_state.servo_controller.connected:
                arduino_ok = True
                messages.append("✅ Arduino conectado correctamente")
            else:
                messages.append("❌ Arduino: No se pudo establecer conexión")
        except Exception as e:
            messages.append(f"❌ Arduino: {e}")
            st.session_state.servo_controller = None
        
        # Intentar conectar Cámara
        try:
            st.session_state.camera = VideoCapture(camera_id=0)
            if st.session_state.camera.cap.isOpened():
                camera_ok = True
                messages.append("✅ Cámara conectada correctamente")
            else:
                messages.append("❌ Cámara: No se detectó ninguna cámara")
                st.session_state.camera = None
        except Exception as e:
            messages.append(f"❌ Cámara: {e}")
            st.session_state.camera = None
        
        # Mostrar resultados
        for msg in messages:
            if msg.startswith("✅"):
                st.success(msg)
            else:
                st.error(msg)
        
        if arduino_ok and camera_ok:
            st.success("🎉 Todo el hardware conectado correctamente")
        elif arduino_ok or camera_ok:
            st.warning("⚠️ Hardware parcialmente conectado")
        else:
            st.error("❌ No se pudo conectar ningún hardware")
        
        return arduino_ok or camera_ok

def capture_and_analyze_frame():
    # Captura frame y realiza análisis FFT
    if st.session_state.camera is None:
        st.error("Cámara no conectada")
        return None

    ret, frame, ts = st.session_state.camera.get_frame()
    if not ret:
        st.error("Error al capturar frame")
        return None

    # Convertir a escala de grises
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Análisis FFT
    analyzer = WaveAnalyzer(calibration_pixel_per_mm=0.1)
    fft_result = analyzer.estimate_wavelength(gray)

    # Análisis de Interferencia
    interference_analyzer = InterferenceAnalyzer()
    interference_result = interference_analyzer.analyze_interference(gray)

    return {
        "frame": frame,
        "gray": gray,
        "timestamp": ts,
        "fft_result": fft_result,
        "interference_result": interference_result
    }

def analyze_frame(frame: np.ndarray, timestamp: float = 0.0) -> dict:
    """Analiza un frame de video y retorna resultados con física avanzada"""
    # Convertir a escala de grises si es necesario
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame

    # Análisis FFT con nuevos módulos
    analyzer = WaveAnalyzer(
        calibration_pixel_per_mm=st.session_state.calibration_px_per_mm,
        calibration_uncertainty=st.session_state.calibration_uncertainty,
        tank_depth_cm=st.session_state.tank_depth_cm
    )
    
    # Usar frecuencia actual si está disponible
    excitation_freq = st.session_state.get('current_frequency', None)
    fft_result = analyzer.estimate_wavelength(gray, excitation_frequency_hz=excitation_freq)

    # Análisis de Interferencia
    interference_analyzer = InterferenceAnalyzer()
    interference_result = interference_analyzer.analyze_interference(gray)

    # Convertir resultado a dict compatible
    fft_dict = fft_result.to_dict() if hasattr(fft_result, 'to_dict') else {
        "wavelength_mm": fft_result.wavelength_mm,
        "wavelength_uncertainty_mm": fft_result.wavelength_uncertainty_mm,
        "snr": fft_result.snr,
        "confidence": fft_result.confidence,
        "quality": fft_result.quality,
        "wavelength_theoretical_mm": fft_result.wavelength_theoretical_mm,
        "error_percent": fft_result.error_percent,
        "spectrum": fft_result.spectrum
    }

    return {
        "frame": frame,
        "gray": gray,
        "timestamp": timestamp,
        "fft_result": fft_dict,
        "interference_result": interference_result
    }

def load_video_frame(video_bytes, frame_idx: int = 0):
    """Carga un frame específico de un video"""
    import tempfile
    
    # Guardar video temporalmente
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name
    
    cap = cv2.VideoCapture(tmp_path)
    
    if not cap.isOpened():
        os.unlink(tmp_path)
        return None, 0, 0
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Ir al frame específico
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    
    cap.release()
    os.unlink(tmp_path)
    
    if ret:
        return frame, total_frames, fps
    return None, total_frames, fps

# ========== INTERFAZ PRINCIPAL ==========
st.markdown('<div class="header-main">🌊 Tanque de Ondas Inteligente</div>', unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <span class='badge badge-info'>Visión Computacional</span>
    <span class='badge badge-success'>Análisis FFT 2D</span>
    <span class='badge badge-warning'>Control Arduino</span>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ========== SIDEBAR - CONTROL ==========
with st.sidebar:
    st.markdown("## ⚙️ Control de Hardware")
    st.markdown("---")

    if st.button("🔌 Conectar Hardware", type="primary", use_container_width=True):
        init_hardware()

    # ARDUINO SECTION
    st.markdown("### 🤖 Arduino")
    if st.session_state.servo_controller and st.session_state.servo_controller.connected:
        st.markdown("<span class='badge badge-success'>✅ Conectado</span>", unsafe_allow_html=True)
        st.markdown("")

        st.markdown("**⚡ Parámetros del Motor**")
        freq = st.slider("🔄 Frecuencia (Hz)", 1.0, 25.0, st.session_state.current_frequency, step=0.5)
        amp = st.slider("📏 Amplitud", 0.0, 1.0, st.session_state.current_amplitude, step=0.1)
        
        # Guardar valores actuales
        st.session_state.current_frequency = freq
        st.session_state.current_amplitude = amp

        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Iniciar", use_container_width=True):
                st.session_state.servo_controller.set_frequency(freq)
                st.session_state.servo_controller.set_amplitude(amp)
                st.session_state.servo_controller.start()
                st.success("✓ Motor iniciado")

        with col2:
            if st.button("⏹️ Detener", use_container_width=True):
                st.session_state.servo_controller.stop()
                st.info("✓ Motor detenido")

        if st.button("📊 Ver Estado", use_container_width=True):
            status = st.session_state.servo_controller.get_status()
            st.code(status)
    else:
        st.markdown("<span class='badge badge-warning'>⚠ Desconectado</span>", unsafe_allow_html=True)
        # Permitir configurar frecuencia para análisis de video
        st.markdown("**Frecuencia de referencia:**")
        freq = st.slider("🔄 Frecuencia (Hz)", 1.0, 25.0, st.session_state.current_frequency, step=0.5, key="freq_ref")
        st.session_state.current_frequency = freq

    st.markdown("---")
    
    # CONFIGURACIÓN FÍSICA
    st.markdown("### 🔬 Configuración Física")
    
    with st.expander("📐 Parámetros del Tanque", expanded=False):
        tank_depth = st.number_input(
            "Profundidad (cm)", 
            min_value=1.0, 
            max_value=50.0, 
            value=st.session_state.tank_depth_cm,
            step=0.5,
            help="Profundidad del agua en el tanque"
        )
        st.session_state.tank_depth_cm = tank_depth
        
        if st.session_state.wave_theory:
            st.session_state.wave_theory = WaveTheory(tank_depth_cm=tank_depth)
        
        # Mostrar λ teórica para frecuencia actual
        if PHYSICS_MODULES_AVAILABLE and st.session_state.wave_theory:
            theoretical_wavelength = st.session_state.wave_theory.theoretical_wavelength(
                st.session_state.current_frequency
            )
            st.info(f"λ teórica @ {st.session_state.current_frequency} Hz: **{theoretical_wavelength:.1f} mm**")
    
    with st.expander("📏 Calibración", expanded=False):
        cal_px_mm = st.number_input(
            "Calibración (px/mm)",
            min_value=0.1,
            max_value=100.0,
            value=st.session_state.calibration_px_per_mm,
            step=0.5,
            help="Píxeles por milímetro - calibrar con objeto de referencia"
        )
        cal_uncertainty = st.number_input(
            "Incertidumbre (±px/mm)",
            min_value=0.01,
            max_value=10.0,
            value=st.session_state.calibration_uncertainty,
            step=0.1
        )
        st.session_state.calibration_px_per_mm = cal_px_mm
        st.session_state.calibration_uncertainty = cal_uncertainty
        
        st.caption(f"Resolución: {1/cal_px_mm:.3f} mm/px")
    
    st.markdown("---")
    
    # CÁMARA SECTION
    st.markdown("### 📷 Cámara")
    
    if st.session_state.camera and st.session_state.camera.is_opened():
        st.markdown("<span class='badge badge-success'>✅ Lista</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='badge badge-warning'>⚠ No disponible</span>", unsafe_allow_html=True)
    
    st.markdown("")
    if st.button("📸 Capturar Imagen", use_container_width=True):
        result = capture_and_analyze_frame()
        st.session_state.frames_buffer = [result] if result else []
        if result:
            st.success("✓ Imagen capturada")

    st.markdown("---")
    
    # VIDEO SECTION
    st.markdown("### 🎬 Cargar Video")
    
    uploaded_file = st.file_uploader(
        "Formatos: MP4, AVI, MOV",
        type=['mp4', 'avi', 'mov'],
        key="video_uploader",
        help="Selecciona un archivo de video para analizar frame por frame"
    )
    
    if uploaded_file is not None:
        st.session_state.video_file = uploaded_file.getvalue()
        
        # Obtener info del video
        frame, total_frames, fps = load_video_frame(st.session_state.video_file, 0)
        
        if frame is not None and total_frames > 0:
            st.markdown(f"""
            <div style='background: rgba(17, 153, 142, 0.1); padding: 10px; border-radius: 8px; margin: 10px 0;'>
                <p style='margin: 0; font-size: 0.9em;'>
                    ✓ <strong>{total_frames}</strong> frames<br/>
                    ⏱ <strong>{fps:.1f}</strong> FPS<br/>
                    ⏳ <strong>{total_frames/fps:.1f}</strong> segundos
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Slider para seleccionar frame
            frame_idx = st.slider(
                "🎞 Frame", 
                0, 
                max(0, total_frames - 1), 
                0, 
                key="frame_slider",
                help=f"Selecciona el frame a analizar (0-{total_frames-1})"
            )
            
            if st.button("🔍 Analizar Frame", type="primary", use_container_width=True):
                with st.spinner("Procesando..."):
                    frame, _, _ = load_video_frame(st.session_state.video_file, frame_idx)
                    if frame is not None:
                        timestamp = frame_idx / fps * 1000 if fps > 0 else 0
                        result = analyze_frame(frame, timestamp)
                        st.session_state.frames_buffer = [result]
                        st.rerun()
        else:
            st.error("❌ Error al cargar el video")

# ========== MAIN - VISUALIZACIÓN ==========
st.markdown("## 📊 Panel de Análisis")

if st.session_state.frames_buffer:
    result = st.session_state.frames_buffer[0]
    
    # Layout principal
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 📸 Imagen Analizada")
        st.image(result["frame"], use_container_width=True)
    
    with col2:
        st.markdown("### 📈 Métricas Principales")
        fft = result["fft_result"]
        
        # Métrica principal con incertidumbre
        if fft.get('wavelength_mm'):
            uncertainty = fft.get('wavelength_uncertainty_mm', 0)
            st.markdown(f"""
            <div class='info-card' style='border-left-color: #11998e;'>
                <h2 style='color: #11998e; margin: 0;'>🌊 {fft['wavelength_mm']:.2f} ± {uncertainty:.2f} mm</h2>
                <p style='color: #666; margin: 5px 0 0 0;'>Longitud de Onda Experimental</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Comparación con teoría
            if fft.get('wavelength_theoretical_mm'):
                theoretical = fft['wavelength_theoretical_mm']
                error = fft.get('error_percent', 0)
                error_color = '#11998e' if error < 5 else '#ffb800' if error < 15 else '#f5576c'
                st.markdown(f"""
                <div class='info-card' style='border-left-color: {error_color};'>
                    <p style='margin: 0;'>λ teórica: <strong>{theoretical:.2f} mm</strong></p>
                    <p style='margin: 5px 0 0 0; color: {error_color};'>Error: <strong>{error:.1f}%</strong></p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='info-card' style='border-left-color: #f5576c;'>
                <p style='color: #f5576c; margin: 0;'>❌ No detectada</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Métricas secundarias
        col_snr, col_conf = st.columns(2)
        with col_snr:
            st.metric("📡 SNR", f"{fft.get('snr', 0):.2f}")
        with col_conf:
            st.metric("🎯 Confianza", f"{fft.get('confidence', 0):.0%}")
        
        # Calidad de medición
        quality = fft.get('quality', 'desconocido')
        quality_colors = {
            'excelente': 'badge-success',
            'bueno': 'badge-success', 
            'aceptable': 'badge-warning',
            'marginal': 'badge-warning',
            'pobre': 'badge-info'
        }
        badge_class = quality_colors.get(quality, 'badge-info')
        st.markdown(f"<span class='badge {badge_class}'>Calidad: {quality.capitalize()}</span>", unsafe_allow_html=True)
    
    # Resultados detallados en tabs
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["🔬 Análisis FFT", "🌐 Interferencia", "📚 Fundamento Teórico"])
    
    with tab1:
        fft_result = result["fft_result"]
        
        st.markdown("""
        <div class='info-card'>
            <h4>🔍 Transformada de Fourier 2D</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Parámetros detectados:**")
            if fft_result.get("wavelength_mm"):
                uncertainty = fft_result.get('wavelength_uncertainty_mm', 0)
                st.markdown(f"- Longitud de onda: `{fft_result['wavelength_mm']:.2f} ± {uncertainty:.2f} mm`")
                st.markdown(f"- SNR: `{fft_result.get('snr', 0):.2f}`")
                st.markdown(f"- Confianza: `{fft_result.get('confidence', 0):.1%}`")
                st.markdown(f"- Calidad: `{fft_result.get('quality', 'N/A')}`")
                
                if fft_result.get('wavelength_theoretical_mm'):
                    st.markdown("---")
                    st.markdown("**Comparación con teoría:**")
                    st.markdown(f"- λ teórica: `{fft_result['wavelength_theoretical_mm']:.2f} mm`")
                    st.markdown(f"- Error: `{fft_result.get('error_percent', 0):.1f}%`")
            else:
                st.warning("Sin patrón periódico detectado")
        
        with col_b:
            if fft_result.get("spectrum") is not None:
                st.markdown("**Espectro de potencia:**")
                # Visualizar espectro
                spectrum_display = np.log1p(fft_result["spectrum"])
                spectrum_display = (spectrum_display - spectrum_display.min()) / (spectrum_display.max() - spectrum_display.min())
                st.image(spectrum_display, caption="Espectro FFT (log scale)", use_container_width=True)
    
    with tab2:
        interference_result = result["interference_result"]
        
        st.markdown("""
        <div class='info-card'>
            <h4>🌊 Análisis de Patrones de Interferencia</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col_c, col_d = st.columns(2)
        with col_c:
            st.markdown("**Características detectadas:**")
            st.markdown(f"- Franjas: `{interference_result['num_fringes']}`")
            st.markdown(f"- Contraste: `{interference_result['contrast']:.3f}`")
            st.markdown(f"- Visibilidad: `{interference_result['visibility']}`")
        
        with col_d:
            if interference_result.get('spacing_px'):
                st.markdown("**Espaciado:**")
                st.markdown(f"- `{interference_result['spacing_px']:.2f}` píxeles")
                
                # Indicador visual de calidad
                contrast = interference_result['contrast']
                if contrast > 0.5:
                    st.markdown("<span class='badge badge-success'>✓ Alta calidad</span>", unsafe_allow_html=True)
                elif contrast > 0.3:
                    st.markdown("<span class='badge badge-warning'>⚠ Calidad media</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='badge badge-info'>ℹ Baja calidad</span>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("""
        ### 📐 Relación de Dispersión
        
        Las ondas en agua siguen la **relación de dispersión**:
        
        $$\\omega^2 = gk \\cdot \\tanh(kh)$$
        
        Donde:
        - $\\omega = 2\\pi f$ es la frecuencia angular
        - $k = 2\\pi/\\lambda$ es el número de onda
        - $g = 9.81$ m/s² es la gravedad
        - $h$ es la profundidad del agua
        
        ---
        
        ### 🌊 Regímenes de Onda
        
        | Régimen | Condición | Aproximación |
        |---------|-----------|--------------|
        | **Aguas profundas** | $h/\\lambda > 0.5$ | $\\omega^2 = gk$ |
        | **Aguas intermedias** | $0.05 < h/\\lambda < 0.5$ | Ecuación completa |
        | **Aguas someras** | $h/\\lambda < 0.05$ | $c = \\sqrt{gh}$ |
        
        ---
        
        ### 📏 Incertidumbre Experimental
        
        La incertidumbre en la medición de λ proviene de:
        1. **Calibración espacial** (px → mm)
        2. **Resolución del espectro FFT**
        3. **Ruido de la imagen**
        
        Se propaga usando:
        $$\\delta\\lambda = \\lambda \\cdot \\sqrt{\\left(\\frac{\\delta f}{f}\\right)^2 + \\left(\\frac{\\delta C}{C}\\right)^2}$$
        """)
        
        # Mostrar parámetros actuales si physics modules disponibles
        if PHYSICS_MODULES_AVAILABLE and st.session_state.wave_theory:
            st.markdown("---")
            st.markdown("### 📊 Parámetros del Experimento Actual")
            
            freq = st.session_state.current_frequency
            depth = st.session_state.tank_depth_cm
            
            regime = st.session_state.wave_theory.classify_wave_regime(freq)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Frecuencia:** {freq} Hz")
                st.markdown(f"**Profundidad:** {depth} cm")
                st.markdown(f"**λ teórica:** {regime['wavelength_mm']:.1f} mm")
            with col2:
                st.markdown(f"**Régimen:** {regime['depth_regime'].replace('_', ' ').title()}")
                st.markdown(f"**h/λ:** {regime['h_over_lambda']:.3f}")
                st.markdown(f"**Tipo:** {regime['wave_type'].replace('_', '-').title()}")

else:
    # Mensaje cuando no hay resultados
    st.markdown("""
    <div class='info-card' style='text-align: center; padding: 50px;'>
        <h3 style='color: #667eea;'>👋 Bienvenido</h3>
        <p style='color: #666; margin-top: 15px;'>
            Conecta la cámara y captura una imagen, o carga un video para comenzar el análisis
        </p>
    </div>
    """, unsafe_allow_html=True)

# ========== HISTORIAL ==========
st.markdown("---")
st.markdown("## 📋 Historial de Mediciones")

if st.session_state.measurements:
    st.markdown(f"""
    <div class='info-card'>
        <p style='margin: 0;'>📊 Total de mediciones: <strong>{len(st.session_state.measurements)}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    df = pd.DataFrame(st.session_state.measurements)
    st.dataframe(df, use_container_width=True, height=300)

    # Botón de descarga mejorado
    csv = df.to_csv(index=False)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        st.download_button(
            "📥 Descargar CSV",
            csv,
            "mediciones.csv",
            "text/csv",
            use_container_width=True
        )
else:
    st.markdown("""
    <div class='info-card' style='text-align: center; border-left-color: #4facfe;'>
        <p style='color: #666; margin: 0;'>📭 Sin mediciones guardadas aún</p>
    </div>
    """, unsafe_allow_html=True)

# ========== FOOTER ==========
st.markdown("---")
st.markdown('''
<div class='footer'>
    <h4 style='color: #667eea; margin-bottom: 15px;'>🎓 Proyecto Académico</h4>
    <p><strong>Autores:</strong> Greidy Andrea Cárdenas Correa y Alexánder Mesa Gómez</p>
    <p><strong>Institución:</strong> Universidad Tecnológica de Pereira</p>
    <p><strong>Asignatura:</strong> Física III | <strong>Docente:</strong> Sebastián Velásquez Bonilla</p>
    <p style='margin-top: 15px; color: #999;'>© 2025 | Desarrollado con ❤️ usando Streamlit & OpenCV</p>
</div>
''', unsafe_allow_html=True)
