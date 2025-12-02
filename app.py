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
    .header-main {
        font-size: 2.5em;
        color: #0066cc;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
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
    """Analiza un frame de video y retorna resultados"""
    # Convertir a escala de grises si es necesario
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame

    # Análisis FFT
    analyzer = WaveAnalyzer(calibration_pixel_per_mm=10.0)
    fft_result = analyzer.estimate_wavelength(gray)

    # Análisis de Interferencia
    interference_analyzer = InterferenceAnalyzer()
    interference_result = interference_analyzer.analyze_interference(gray)

    return {
        "frame": frame,
        "gray": gray,
        "timestamp": timestamp,
        "fft_result": fft_result,
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
st.markdown("**Sistema de Análisis de Fenómenos Ondulatorios con Visión Computacional**")
st.divider()

# ========== SIDEBAR - CONTROL ==========
with st.sidebar:
    st.header("⚙️ Control de Hardware")

    if st.button("🔌 Conectar Hardware", use_container_width=True):
        init_hardware()

    if st.session_state.servo_controller and st.session_state.servo_controller.connected:
        st.success("Arduino conectado ✅")

        st.subheader("Parámetros del Motor")
        freq = st.slider("Frecuencia (Hz)", 1.0, 25.0, 10.0, step=0.5)
        amp = st.slider("Amplitud (0-1)", 0.0, 1.0, 0.8, step=0.1)

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("▶️ Iniciar", use_container_width=True):
                st.session_state.servo_controller.set_frequency(freq)
                st.session_state.servo_controller.set_amplitude(amp)
                st.session_state.servo_controller.start()
                st.success("Motor iniciado")

        with col2:
            if st.button("⏹️ Detener", use_container_width=True):
                st.session_state.servo_controller.stop()
                st.info("Motor detenido")

        with col3:
            if st.button("📊 Status", use_container_width=True):
                status = st.session_state.servo_controller.get_status()
                st.write(status)
    else:
        st.warning("Arduino no conectado")

    st.divider()
    st.subheader("🎥 Cámara")

    if st.button("📸 Capturar Frame", use_container_width=True):
        result = capture_and_analyze_frame()
        st.session_state.frames_buffer = [result] if result else []

    st.divider()
    st.subheader("🎬 Cargar Video")
    
    uploaded_file = st.file_uploader("Selecciona un video", type=['mp4', 'avi', 'mov'], key="video_uploader")
    
    if uploaded_file is not None:
        st.session_state.video_file = uploaded_file.getvalue()
        
        # Obtener info del video
        frame, total_frames, fps = load_video_frame(st.session_state.video_file, 0)
        
        if frame is not None and total_frames > 0:
            st.success(f"✅ Video cargado: {total_frames} frames @ {fps:.1f} FPS")
            
            # Slider para seleccionar frame
            frame_idx = st.slider("Seleccionar frame", 0, max(0, total_frames - 1), 0, key="frame_slider")
            
            if st.button("🔍 Analizar Frame Seleccionado", use_container_width=True):
                with st.spinner("Analizando..."):
                    frame, _, _ = load_video_frame(st.session_state.video_file, frame_idx)
                    if frame is not None:
                        timestamp = frame_idx / fps * 1000 if fps > 0 else 0
                        result = analyze_frame(frame, timestamp)
                        st.session_state.frames_buffer = [result]
                        st.rerun()
        else:
            st.error("❌ Error al cargar el video")

# ========== MAIN - VISUALIZACIÓN ==========
st.header("📊 Panel de Análisis")

col1, col2 = st.columns([2, 1])

with col1:
    if st.session_state.frames_buffer:
        result = st.session_state.frames_buffer[0]

        # Mostrar frame
        st.image(result["frame"], caption="Imagen Capturada", use_container_width=True)

        # Resultados FFT
        fft_result = result["fft_result"]
        if fft_result["wavelength_mm"]:
            st.success(f"✅ Longitud de Onda Detectada: **{fft_result['wavelength_mm']:.2f} mm**")
            st.write(f"SNR: {fft_result['snr']:.2f} | Confianza: {fft_result['confidence']:.1%}")
        else:
            st.warning("No se detectó un patrón de onda claro")

        # Resultados Interferencia
        interference_result = result["interference_result"]
        st.write(f"**Análisis de Interferencia:**")
        st.write(f"- Número de franjas: {interference_result['num_fringes']}")
        st.write(f"- Contraste: {interference_result['contrast']:.3f}")
        st.write(f"- Visibilidad: {interference_result['visibility']}")

with col2:
    st.subheader("📈 Métricas")

    if st.session_state.frames_buffer:
        result = st.session_state.frames_buffer[0]
        fft = result["fft_result"]

        st.metric("Longitud de Onda", 
                 f"{fft['wavelength_mm']:.2f} mm" if fft['wavelength_mm'] else "---")
        st.metric("Relación Señal/Ruido", f"{fft['snr']:.2f}")
        st.metric("Confianza", f"{fft['confidence']:.0%}")

# ========== HISTORIAL ==========
st.divider()
st.header("📋 Historial de Mediciones")

if st.session_state.measurements:
    df = pd.DataFrame(st.session_state.measurements)
    st.dataframe(df, use_container_width=True)

    # Descargar datos
    csv = df.to_csv(index=False)
    st.download_button("📥 Descargar CSV", csv, "mediciones.csv")
else:
    st.info("Sin mediciones aún")

# ========== FOOTER ==========
st.divider()
st.markdown('''
---
**Autores:** Greidy Andrea Cárdenas Correa y Alexánder Mesa Gómez  
**Institución:** Universidad Tecnológica de Pereira  
**Asignatura:** Física III  
**Docente:** Sebastián Velásquez Bonilla  
**Año:** 2025
''')
