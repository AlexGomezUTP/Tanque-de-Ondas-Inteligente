# Copilot Instructions - Tanque de Ondas Inteligente

## Arquitectura del Sistema

Sistema de laboratorio para análisis de ondas con hardware (Arduino + Servo + Cámara) y software (Python + Streamlit).

```
┌─────────────────┐     Serial      ┌──────────────────┐
│   Arduino Uno   │◄───────────────►│  servo_control.py │
│ servo_control.ino│  FREQ/AMP/START │                  │
└─────────────────┘                 └────────┬─────────┘
                                             │
┌─────────────────┐                 ┌────────▼─────────┐
│   Cámara USB    │◄───────────────►│    camera.py     │
│   1920x1080     │   OpenCV        │   VideoCapture   │
└─────────────────┘                 └────────┬─────────┘
                                             │
                                    ┌────────▼─────────┐
                                    │     app.py       │
                                    │   (Streamlit)    │
                                    │                  │
                       ┌────────────┼────────────┐     │
                       ▼            ▼            ▼     │
             fourier_analysis  interference   session  │
             (FFT 2D)          _analysis      _state   │
```

## Flujo de Datos Crítico

1. **Arduino ↔ Python**: Protocolo serial texto simple (`FREQ 10\n`, `START\n`)
2. **Cámara → Análisis**: Frame BGR → Grayscale → FFT 2D / Interferencia
3. **Estado**: `st.session_state` mantiene `servo_controller`, `camera`, `measurements`

## Comandos de Desarrollo

```bash
# Ejecutar aplicación
streamlit run app.py

# Verificar puerto Arduino (Linux)
ls /dev/tty*

# Verificar cámara (Linux)
v4l2-ctl --list-devices
```

## Patrones de Código del Proyecto

### Configuración de Hardware
```python
# Puerto serial - ajustar según SO en servo_control.py
PORT = '/dev/ttyUSB0'  # Linux/Mac
PORT = 'COM3'          # Windows

# Calibración cámara en fourier_analysis.py
calibration_pixel_per_mm = 0.1  # Ajustar según setup físico
```

### Estructura de Resultados de Análisis
```python
# FFT retorna siempre este dict (fourier_analysis.py)
{"wavelength_mm": float|None, "snr": float, "confidence": float, "spectrum": ndarray}

# Interferencia retorna (interference_analysis.py)
{"num_fringes": int, "contrast": float, "visibility": str, "spacing_px": float|None}
```

### Protocolo Arduino
Comandos soportados en `servo_control.ino`:
- `FREQ <1-25>` → "Frecuencia configurada: X Hz"
- `AMP <0-1>` → "Amplitud configurada: X"
- `START` → "Movimiento iniciado"
- `STOP` → "Movimiento detenido"
- `STATUS` → Estado actual

## Convenciones del Proyecto

- **Idioma**: Código en inglés, comentarios/UI en español
- **Logging**: Usar `logging.getLogger('NombreClase')` por módulo
- **Tipado**: Type hints en funciones públicas (`-> Dict`, `-> Tuple[bool, np.ndarray, float]`)
- **Clases**: Un analizador por archivo (`WaveAnalyzer`, `InterferenceAnalyzer`, `VideoCapture`)
- **Servo**: Pin 9 fijo, ángulo central 90°, rango ±30°

## Al Modificar Código

1. **Nuevos análisis**: Crear clase en archivo separado, seguir patrón de `fourier_analysis.py`
2. **Nuevos comandos Arduino**: Agregar en `processCommand()` de `.ino` y wrapper en `servo_control.py`
3. **UI Streamlit**: Usar `st.session_state` para persistencia entre reruns
4. **Timestamps**: Siempre en milisegundos desde inicio de captura (`camera.get_frame()` retorna timestamp)

## Dependencias Clave

- `pyserial`: Comunicación Arduino (baudrate 9600)
- `opencv-python`: Captura video, conversión BGR↔Gray
- `scipy.fft`: FFT 2D con `fft2` y `fftshift`
- `scipy.ndimage.label`: Detección de franjas conectadas
