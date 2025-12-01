# Tanque de Ondas Inteligente - Sistema de Control y Análisis

## 📋 Descripción General

Sistema completo de laboratorio para medición de fenómenos ondulatorios usando:
- **Hardware:** Arduino Uno + Micro Servo SG90 + Cámara USB + LED 5600K
- **Software:** Python + Streamlit (interfaz web)
- **Análisis:** FFT 2D + Interferencia

## 🚀 Instalación

### 1. Requisitos Previos
- Python 3.8+
- Arduino IDE (para cargar firmware)
- Micro Servo SG90 conectado al Pin 9 del Arduino

### 2. Clonar/Descargar Proyecto
```bash
git clone <repositorio>
cd tanque-ondas
```

### 3. Instalar Dependencias Python
```bash
pip install -r requirements.txt
```

### 4. Cargar Firmware Arduino
1. Abre Arduino IDE
2. Copia contenido de `servo_control.ino`
3. Sube a Arduino Uno
4. Verifica conexión en puerto Serial Monitor

### 5. Ejecutar App Streamlit
```bash
streamlit run app.py
```

Se abrirá en: `http://localhost:8501`

## 📚 Uso

### Flujo Típico de Experimento

1. **Conectar Hardware** (botón en sidebar)
   - Verifica Arduino y Cámara conectados

2. **Configurar Parámetros**
   - Frecuencia (1-25 Hz)
   - Amplitud (0-1)

3. **Iniciar Movimiento** ▶️
   - Motor comienza a oscilar

4. **Capturar Frames** 📸
   - Sistema analiza y muestra wavelength

5. **Descargar Resultados** 📥
   - Exporta CSV con mediciones

## 🔧 Estructura de Archivos

```
tanque-ondas/
├── servo_control.ino           # Firmware Arduino
├── servo_control.py            # Interfaz Python-Arduino
├── camera.py                   # Captura de video
├── fourier_analysis.py         # Análisis FFT 2D
├── interference_analysis.py    # Análisis de interferencia
├── app.py                      # App Streamlit principal
├── requirements.txt            # Dependencias Python
└── README.md                   # Este archivo
```

## ⚙️ Configuración

### Puerto Serial Arduino
Edita `servo_control.py`:
```python
PORT = '/dev/ttyUSB0'  # Linux/Mac
# PORT = 'COM3'        # Windows - ajusta según puerto
```

### Factor de Calibración Cámara
En `fourier_analysis.py`:
```python
calibration_pixel_per_mm = 0.1  # Ajusta según tu setup
```

## 📊 Interpretación de Resultados

- **Wavelength:** Distancia entre máximos de interferencia
- **SNR:** Relación señal-ruido (>5 es buena)
- **Confianza:** Qué tan seguro es el resultado (>80% es aceptable)
- **Contraste:** Visibilidad de franjas (0-1)

## 🐛 Solución de Problemas

### Arduino no se conecta
```bash
# Verifica puerto:
ls /dev/tty*  # Linux/Mac
# o usa Arduino IDE Tools→Port para ver puerto
```

### Cámara no funciona
```bash
# Verifica disponibilidad:
v4l2-ctl --list-devices  # Linux
```

### Latencia alta en FFT
- Reduce resolución en `camera.py`
- Aumenta factor downsampling en `fourier_analysis.py`

## 📝 Notas Técnicas

- **FFT 2D:** Detecta periodicidad espacial en imagen
- **Downsampling:** Reduce cálculo sin perder información relevante
- **Ventana Hann:** Reduce artefactos en bordes
- **Timestamp:** Crítico para sincronización

## 📚 Referencias

- [OpenCV Documentation](https://docs.opencv.org/)
- [SciPy FFT](https://docs.scipy.org/doc/scipy/reference/fft.html)
- [Streamlit Docs](https://docs.streamlit.io/)

## 👥 Autores

**Greidy Andrea Cárdenas Correa**  
**Alexánder Mesa Gómez**

Universidad Tecnológica de Pereira  
Física III - 2025
