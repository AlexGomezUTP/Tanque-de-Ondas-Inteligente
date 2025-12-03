# Guía de Laboratorio: Ondas en un Tanque

## 📚 Introducción

Este experimento permite estudiar **ondas mecánicas en agua**, verificando experimentalmente la **relación de dispersión** y explorando conceptos fundamentales de física ondulatoria.

---

## 🎯 Objetivos de Aprendizaje

Al completar esta práctica, el estudiante será capaz de:

1. **Medir** la longitud de onda de ondas superficiales usando análisis de Fourier
2. **Comparar** resultados experimentales con predicciones teóricas
3. **Analizar** incertidumbres experimentales y su propagación
4. **Clasificar** ondas según el régimen de profundidad (profundas/someras)
5. **Interpretar** espectros de frecuencia espacial

---

## 📐 Fundamento Teórico

### Relación de Dispersión

Las ondas de gravedad en agua siguen la relación:

$$\omega^2 = gk \cdot \tanh(kh)$$

Donde:
- $\omega = 2\pi f$ es la frecuencia angular
- $k = 2\pi/\lambda$ es el número de onda
- $g = 9.81$ m/s² es la aceleración gravitacional
- $h$ es la profundidad del agua

### Regímenes de Onda

| Régimen | Condición | Longitud de onda |
|---------|-----------|------------------|
| **Aguas profundas** | $kh > \pi$ ($h/\lambda > 0.5$) | $\lambda = \frac{gT^2}{2\pi}$ |
| **Aguas intermedias** | $0.31 < kh < \pi$ | Usar relación completa |
| **Aguas someras** | $kh < 0.31$ ($h/\lambda < 0.05$) | $\lambda = T\sqrt{gh}$ |

### Velocidad de Fase y Grupo

- **Velocidad de fase**: $c = \frac{\omega}{k} = \frac{\lambda}{T}$
- **Velocidad de grupo**: $c_g = \frac{d\omega}{dk}$

Para aguas profundas: $c_g = \frac{c}{2}$

---

## 🔬 Procedimiento Experimental

### Materiales
- Tanque de ondas con agua
- Generador de ondas (servo motor)
- Cámara digital
- Software de análisis (esta aplicación)
- Regla o patrón de calibración

### Parte 1: Calibración (15 min)

1. **Calibración espacial:**
   - Coloque una regla milimetrada en el tanque (visible para la cámara)
   - Capture una imagen
   - Mida la distancia en píxeles de un segmento conocido (ej: 100 mm)
   - Calcule: `calibración = píxeles / mm`
   - Repita 5 veces y calcule promedio y desviación estándar

2. **Verificación:**
   - ¿Cuál es la incertidumbre relativa de su calibración?
   - ¿Es menor al 5%? Si no, recalibre.

### Parte 2: Medición de Longitud de Onda (30 min)

1. **Configure el experimento:**
   - Profundidad del agua: ___ cm
   - Frecuencia del generador: ___ Hz

2. **Para cada frecuencia (5, 10, 15, 20 Hz):**
   - Espere que se establezca el patrón de ondas (~30 s)
   - Capture 5 imágenes
   - Registre la longitud de onda medida
   - Anote el SNR y la confianza

3. **Complete la tabla:**

| f (Hz) | λ medida (mm) | σ (mm) | λ teórica (mm) | Error (%) |
|--------|---------------|--------|----------------|-----------|
| 5      |               |        |                |           |
| 10     |               |        |                |           |
| 15     |               |        |                |           |
| 20     |               |        |                |           |

### Parte 3: Análisis de Datos (20 min)

1. Grafique λ vs f (experimental y teórico)
2. Grafique el error porcentual vs f
3. Identifique el régimen de onda para cada frecuencia

---

## ❓ Preguntas de Análisis

### Conceptuales

1. ¿Por qué la relación entre λ y f no es lineal para ondas de gravedad?

2. Si duplica la frecuencia, ¿se reduce la longitud de onda a la mitad? Explique.

3. ¿En qué régimen de profundidad están sus ondas? ¿Cómo lo determinó?

4. ¿Por qué usamos análisis de Fourier en lugar de medir directamente con una regla?

### Cuantitativos

5. Para h = 5 cm y f = 10 Hz, calcule:
   - La longitud de onda teórica
   - La velocidad de fase
   - El valor de kh (¿profundas o someras?)

6. Si su calibración tiene incertidumbre del 3% y la medición de frecuencia espacial tiene incertidumbre del 2%, ¿cuál es la incertidumbre total en λ?

7. Sus mediciones dan λ = 25.0 ± 1.5 mm y la teoría predice λ = 24.2 mm. ¿Son compatibles? Justifique usando el concepto de z-score.

### Experimentales

8. ¿Qué factores podrían causar que sus mediciones difieran de la teoría?

9. ¿Cómo afecta el SNR a la confiabilidad de sus mediciones?

10. Si el contraste de las franjas es bajo, ¿qué podría hacer para mejorarlo?

---

## 📊 Criterios de Evaluación

| Aspecto | Excelente (5) | Bueno (4) | Aceptable (3) | Insuficiente (1-2) |
|---------|---------------|-----------|---------------|--------------------|
| **Calibración** | σ < 2% | σ < 5% | σ < 10% | σ > 10% |
| **Mediciones** | Error < 5% | Error < 10% | Error < 20% | Error > 20% |
| **Análisis** | Completo con propagación de incertidumbre | Correcto sin incertidumbre | Parcial | Incompleto |
| **Preguntas** | Todas correctas con justificación | Mayoría correctas | 50% correctas | < 50% |

---

## 🔧 Solución de Problemas

### "No se detecta patrón de ondas"
- Verifique que las ondas sean visibles a simple vista
- Aumente el contraste de la imagen
- Asegure iluminación uniforme
- Reduzca vibraciones externas

### "SNR muy bajo"
- Mejore la iluminación
- Use fondo contrastante
- Aumente la amplitud del generador
- Verifique enfoque de la cámara

### "Error experimental alto (>20%)"
- Recalibre el sistema
- Verifique la profundidad del agua
- Asegure que las ondas sean estables
- Revise la frecuencia del generador

---

## 📚 Referencias

1. Crawford, F.S. (1968). *Waves*. Berkeley Physics Course, Vol. 3.
2. French, A.P. (1971). *Vibrations and Waves*. MIT Introductory Physics.
3. Dean, R.G. & Dalrymple, R.A. (1991). *Water Wave Mechanics for Engineers and Scientists*.

---

## ✍️ Informe de Laboratorio

Entregue un informe que incluya:

1. **Resumen** (100 palabras máx.)
2. **Datos de calibración** con análisis de incertidumbre
3. **Tabla de resultados** con mediciones y errores
4. **Gráficas** (λ vs f, error vs f)
5. **Análisis de régimen de ondas**
6. **Respuestas a preguntas** (mínimo 5)
7. **Conclusiones** relacionando con los objetivos
8. **Fuentes de error** y sugerencias de mejora

**Formato:** PDF, máximo 8 páginas
**Fecha de entrega:** Una semana después de la práctica
