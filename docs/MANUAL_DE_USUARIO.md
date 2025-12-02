# 📖 Manual de Usuario - Tanque de Ondas Inteligente

## 🌊 Descripción General

El **Tanque de Ondas Inteligente** es una aplicación web diseñada para analizar fenómenos ondulatorios mediante visión computacional. Permite capturar imágenes de un tanque de ondas físico o cargar videos pregrabados para medir propiedades como la longitud de onda, patrones de interferencia y contraste.

---

## 🖥️ Interfaz de Usuario

La aplicación está dividida en dos secciones principales:

### 📌 Barra Lateral (Sidebar)

Contiene todos los controles de la aplicación:

1. **Control de Hardware**
2. **Cámara**
3. **Cargar Video**

### 📌 Panel Principal

Muestra los resultados del análisis:

1. **Panel de Análisis** - Imagen y resultados
2. **Métricas** - Valores numéricos principales
3. **Historial de Mediciones** - Registro de análisis anteriores

---

## 🔧 Sección: Control de Hardware

### Botón "Conectar Hardware"

Este botón intenta establecer conexión con:

- **Arduino**: Controlador del servo motor que genera las ondas
- **Cámara USB**: Para captura de video en tiempo real

#### Estados posibles:

| Mensaje | Significado |
|---------|-------------|
| ✅ Arduino conectado correctamente | El Arduino está conectado y respondiendo |
| ✅ Cámara conectada correctamente | La cámara USB fue detectada |
| ❌ Arduino: No se pudo establecer conexión | No hay Arduino conectado o puerto incorrecto |
| ❌ Cámara: No se detectó ninguna cámara | No hay cámara USB conectada |
| ⚠️ Hardware parcialmente conectado | Solo uno de los dispositivos está conectado |

### Parámetros del Motor (solo si Arduino está conectado)

- **Frecuencia (Hz)**: Controla la velocidad de oscilación del generador de ondas (1-25 Hz)
- **Amplitud (0-1)**: Controla la intensidad del movimiento (0 = mínimo, 1 = máximo)

### Botones de Control del Motor

| Botón | Función |
|-------|---------|
| ▶️ Iniciar | Comienza el movimiento del servo con los parámetros configurados |
| ⏹️ Detener | Detiene el movimiento del servo |
| 📊 Status | Muestra el estado actual del controlador |

---

## 📸 Sección: Cámara

### Botón "Capturar Frame"

Captura una imagen instantánea de la cámara conectada y realiza automáticamente el análisis de ondas.

**Requisitos:**
- La cámara debe estar conectada (usar primero "Conectar Hardware")

---

## 🎬 Sección: Cargar Video

Esta sección permite analizar videos pregrabados sin necesidad de hardware conectado.

### Pasos para cargar un video:

1. **Arrastrar o seleccionar archivo**: Formatos soportados: MP4, AVI, MOV
2. **Verificar carga**: Aparecerá un mensaje verde indicando el número de frames y FPS
3. **Seleccionar frame**: Usar el deslizador para elegir qué frame analizar
4. **Analizar**: Presionar el botón "🔍 Analizar Frame Seleccionado"

### Información mostrada del video:

- Número total de frames
- Velocidad de reproducción (FPS)
- Frame actualmente seleccionado

---

## 📊 Panel de Análisis

### Imagen Capturada

Muestra la imagen que está siendo analizada (ya sea de la cámara o del video cargado).

### Resultados del Análisis FFT

| Parámetro | Descripción |
|-----------|-------------|
| **Longitud de Onda** | Distancia entre crestas consecutivas de la onda (en mm) |
| **SNR** | Relación Señal/Ruido - indica qué tan claro es el patrón detectado |
| **Confianza** | Porcentaje de certeza en la medición (0-100%) |

### Análisis de Interferencia

| Parámetro | Descripción |
|-----------|-------------|
| **Número de franjas** | Cantidad de franjas de interferencia detectadas |
| **Contraste** | Valor entre 0 y 1 que indica la nitidez del patrón |
| **Visibilidad** | Clasificación: Excelente (>0.7), Buena (>0.5), Pobre (<0.5) |

---

## 📈 Métricas

Panel lateral derecho que muestra los valores principales en formato grande y fácil de leer:

- **Longitud de Onda**: En milímetros
- **Relación Señal/Ruido**: Valor numérico del SNR
- **Confianza**: Porcentaje de confiabilidad

---

## 📋 Historial de Mediciones

Tabla que almacena las mediciones realizadas durante la sesión. Incluye botón para **descargar los datos en formato CSV**.

> **Nota**: El historial se reinicia al recargar la página.

---

## 🎯 Flujo de Trabajo Recomendado

### Opción A: Con Hardware Conectado

1. Conectar Arduino y cámara USB al computador
2. Hacer clic en "🔌 Conectar Hardware"
3. Verificar que ambos dispositivos estén conectados (mensajes verdes)
4. Ajustar frecuencia y amplitud del motor
5. Iniciar el movimiento del servo
6. Esperar a que se formen patrones de ondas en el tanque
7. Hacer clic en "📸 Capturar Frame"
8. Revisar los resultados en el Panel de Análisis

### Opción B: Con Video Pregrabado

1. En la sección "🎬 Cargar Video", seleccionar un archivo de video
2. Esperar a que se cargue (mensaje verde con info del video)
3. Usar el deslizador para navegar entre frames
4. Seleccionar un frame donde el patrón de ondas sea visible
5. Hacer clic en "🔍 Analizar Frame Seleccionado"
6. Revisar los resultados en el Panel de Análisis

---

## ⚠️ Solución de Problemas

### El Arduino no se conecta

- Verificar que el cable USB esté bien conectado
- En Linux: el puerto suele ser `/dev/ttyUSB0` o `/dev/ttyACM0`
- En Windows: verificar el puerto COM en el Administrador de Dispositivos
- Asegurarse de que el Arduino tenga cargado el firmware `servo_control.ino`

### La cámara no se detecta

- Verificar que la cámara USB esté conectada
- En Linux: ejecutar `ls /dev/video*` para ver cámaras disponibles
- Cerrar otras aplicaciones que puedan estar usando la cámara

### El video no se carga

- Verificar que el formato sea MP4, AVI o MOV
- El archivo no debe superar los 200 MB
- Probar con otro archivo de video

### Los resultados no parecen correctos

- Asegurarse de que el patrón de ondas sea visible en la imagen
- Verificar que la calibración esté correcta (ver documento de calibración)
- Usar frames donde las ondas estén bien definidas

---

## 📚 Documentación Adicional

- **[Guía de Calibración](./GUIA_CALIBRACION.md)**: Cómo ajustar el factor de calibración para obtener medidas reales en milímetros
- **[README.md](../README.md)**: Información general del proyecto

---

## 👥 Créditos

**Autores:** Greidy Andrea Cárdenas Correa y Alexánder Mesa Gómez  
**Institución:** Universidad Tecnológica de Pereira  
**Asignatura:** Física III  
**Docente:** Sebastián Velásquez Bonilla  
**Año:** 2025
