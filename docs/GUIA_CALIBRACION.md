# 📐 Guía de Calibración - Tanque de Ondas Inteligente

## 🎯 Objetivo

Esta guía explica cómo calibrar el sistema para obtener mediciones precisas de longitud de onda en **milímetros reales**, en lugar de valores relativos en píxeles.

---

## 📖 Conceptos Básicos

### ¿Qué es la calibración?

La calibración es el proceso de establecer una relación entre los **píxeles de la imagen** y las **unidades reales de medida** (milímetros).

### Factor de Calibración

El factor de calibración se expresa como: **píxeles por milímetro (px/mm)**

```
Factor de Calibración = Número de píxeles / Distancia real en mm
```

**Ejemplo:**
- Si un objeto de 10 mm ocupa 100 píxeles en la imagen
- Factor de calibración = 100 px / 10 mm = **10 px/mm**

---

## 🔧 Proceso de Calibración Paso a Paso

### Paso 1: Preparar un Objeto de Referencia

Necesitas un objeto de **tamaño conocido** que puedas colocar en el tanque de ondas o en el campo de visión de la cámara.

**Opciones recomendadas:**
- Regla milimetrada
- Moneda (diámetro conocido)
- Objeto impreso con medidas específicas
- Cinta métrica

| Objeto | Medida típica |
|--------|---------------|
| Moneda de 1 peso colombiano | 21 mm de diámetro |
| Regla estándar | Marcas cada 1 mm |
| Tarjeta de crédito | 85.6 mm × 53.98 mm |

### Paso 2: Capturar Imagen de Referencia

1. Coloca el objeto de referencia en el tanque de ondas (sin agua) o en el área de captura
2. Asegúrate de que la cámara esté en la misma posición que usarás para los experimentos
3. Captura una imagen o graba un video corto
4. Carga la imagen/video en la aplicación

### Paso 3: Medir Píxeles del Objeto

Hay varias formas de medir los píxeles:

#### Opción A: Usar un editor de imágenes

1. Guarda un frame de la aplicación (captura de pantalla)
2. Abre la imagen en un editor (GIMP, Photoshop, Paint.NET)
3. Usa la herramienta de medición o cuenta los píxeles manualmente
4. Mide el ancho del objeto de referencia en píxeles

#### Opción B: Usar código Python

```python
import cv2

# Cargar imagen
img = cv2.imread('imagen_referencia.jpg')

# Mostrar imagen con coordenadas
def mostrar_coordenadas(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Coordenadas: ({x}, {y})")

cv2.namedWindow('Imagen')
cv2.setMouseCallback('Imagen', mostrar_coordenadas)
cv2.imshow('Imagen', img)
cv2.waitKey(0)
cv2.destroyAllWindows()
```

1. Haz clic en el borde izquierdo del objeto → Anota X1
2. Haz clic en el borde derecho del objeto → Anota X2
3. Píxeles del objeto = X2 - X1

### Paso 4: Calcular el Factor de Calibración

```
Factor de Calibración (px/mm) = Píxeles medidos / Tamaño real (mm)
```

**Ejemplo práctico:**

| Dato | Valor |
|------|-------|
| Objeto de referencia | Regla |
| Distancia real medida | 50 mm |
| Píxeles medidos | 420 px |
| **Factor de calibración** | 420 / 50 = **8.4 px/mm** |

### Paso 5: Aplicar la Calibración en el Código

Abre el archivo `app.py` y busca la función `analyze_frame`. Modifica el valor de `calibration_pixel_per_mm`:

```python
def analyze_frame(frame: np.ndarray, timestamp: float = 0.0) -> dict:
    """Analiza un frame de video y retorna resultados"""
    # Convertir a escala de grises si es necesario
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame

    # Análisis FFT - AQUÍ SE CONFIGURA LA CALIBRACIÓN
    analyzer = WaveAnalyzer(calibration_pixel_per_mm=8.4)  # ← Cambiar este valor
    fft_result = analyzer.estimate_wavelength(gray)
    
    # ... resto del código
```

También modifica la función `capture_and_analyze_frame` si usas la cámara en tiempo real:

```python
def capture_and_analyze_frame():
    # ...
    # Análisis FFT
    analyzer = WaveAnalyzer(calibration_pixel_per_mm=8.4)  # ← Mismo valor
    # ...
```

### Paso 6: Verificar la Calibración

1. Genera un video de prueba con wavelength conocido:
   ```bash
   python generar_video.py
   ```

2. Carga `video_onda_simple.mp4` (wavelength = 50 px)

3. Analiza un frame y verifica:
   - Con calibración 10 px/mm → Debería mostrar ~5.0 mm
   - Con calibración 8.4 px/mm → Debería mostrar ~5.95 mm

---

## 📊 Tabla de Referencia Rápida

| Calibración (px/mm) | 50 px equivale a | Uso típico |
|---------------------|------------------|------------|
| 5.0 | 10.0 mm | Cámara alejada |
| 8.4 | 5.95 mm | Distancia media |
| 10.0 | 5.0 mm | **Valor por defecto** |
| 15.0 | 3.33 mm | Cámara cercana |
| 20.0 | 2.5 mm | Zoom alto |

---

## 🔬 Calibración Avanzada: Múltiples Zonas

Si la cámara tiene distorsión (especialmente en los bordes), puedes necesitar calibraciones diferentes para distintas zonas de la imagen.

### Verificar distorsión:

1. Coloca una hoja de papel cuadriculado en el tanque
2. Captura una imagen
3. Verifica si los cuadros tienen el mismo tamaño en el centro y los bordes

Si hay diferencia significativa (>10%), considera:
- Usar solo la zona central para mediciones
- Aplicar corrección de distorsión con OpenCV
- Usar una cámara de mejor calidad

---

## 📝 Registro de Calibración

Es recomendable mantener un registro de calibración para cada configuración:

```
Fecha: _______________
Cámara: ______________
Distancia cámara-tanque: _____ cm
Resolución: _____ x _____ píxeles
Objeto de referencia: ______________
Tamaño real: _____ mm
Píxeles medidos: _____ px
Factor de calibración: _____ px/mm
```

---

## ⚠️ Consejos Importantes

1. **Mantén la cámara fija**: Cualquier movimiento invalida la calibración

2. **Recalibra si cambias**:
   - La posición de la cámara
   - El zoom o enfoque
   - La resolución de captura

3. **Verifica periódicamente**: La calibración puede cambiar con el tiempo

4. **Documenta todo**: Guarda fotos de la configuración física

5. **Usa promedios**: Haz varias mediciones y usa el promedio para mayor precisión

---

## 🧮 Fórmulas Útiles

### Convertir píxeles a milímetros:
```
Distancia (mm) = Distancia (px) / Factor de calibración (px/mm)
```

### Convertir milímetros a píxeles:
```
Distancia (px) = Distancia (mm) × Factor de calibración (px/mm)
```

### Calcular longitud de onda real:
```
λ_real (mm) = λ_detectada (px) / Factor de calibración (px/mm)
```

---

## 📚 Referencias

- [OpenCV Camera Calibration](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html)
- [Calibración de Sistemas de Visión](https://en.wikipedia.org/wiki/Camera_resectioning)

---

## 👥 Créditos

**Autores:** Greidy Andrea Cárdenas Correa y Alexánder Mesa Gómez  
**Institución:** Universidad Tecnológica de Pereira  
**Asignatura:** Física III  
**Docente:** Sebastián Velásquez Bonilla  
**Año:** 2025
