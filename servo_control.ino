/*
 * TANQUE DE ONDAS - SERVO CONTROL
 * Micro Servo SG90 Control via Arduino Uno
 * Genera movimiento sinusoidal a frecuencia variable
 */

#include <Servo.h>
#include <math.h>

// ========== CONFIGURACIÓN ==========
#define SERVO_PIN 9
#define BAUD_RATE 9600
#define MAX_FREQUENCY 25.0
#define MIN_FREQUENCY 1.0
#define CENTER_ANGLE 90    // Posición central del servo
#define AMPLITUDE_ANGLE 30 // Rango de movimiento (±30°)

// ========== VARIABLES GLOBALES ==========
Servo waveServo;
float frequency = 5.0;        // Hz (default)
float amplitude = 1.0;        // Amplitud relativa (0-1)
bool isRunning = false;
unsigned long lastUpdate = 0;
const float TIME_STEP = 20;   // ms between updates (50 Hz update rate)

void setup() {
  Serial.begin(BAUD_RATE);
  waveServo.attach(SERVO_PIN);
  waveServo.write(CENTER_ANGLE);

  Serial.println("=== TANQUE DE ONDAS - SERVO CONTROL ===");
  Serial.println("Comandos disponibles:");
  Serial.println("  FREQ <valor>     - Establecer frecuencia (1-25 Hz)");
  Serial.println("  AMP <valor>      - Establecer amplitud (0-1)");
  Serial.println("  START            - Iniciar movimiento");
  Serial.println("  STOP             - Detener movimiento");
  Serial.println("  STATUS           - Mostrar estado actual");
  Serial.println("=====================================");
}

void loop() {
  // Procesar comandos seriales
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    processCommand(command);
  }

  // Actualizar posición del servo si está activo
  if (isRunning && (millis() - lastUpdate >= TIME_STEP)) {
    updateServoPosition();
    lastUpdate = millis();
  }
}

/*
 * Procesa comandos recibidos por puerto serial
 */
void processCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  if (cmd.startsWith("FREQ")) {
    float newFreq = cmd.substring(5).toFloat();
    if (newFreq >= MIN_FREQUENCY && newFreq <= MAX_FREQUENCY) {
      frequency = newFreq;
      Serial.print("Frecuencia configurada: ");
      Serial.print(frequency);
      Serial.println(" Hz");
    } else {
      Serial.println("ERROR: Rango de frecuencia 1-25 Hz");
    }
  }
  else if (cmd.startsWith("AMP")) {
    float newAmp = cmd.substring(4).toFloat();
    if (newAmp >= 0.0 && newAmp <= 1.0) {
      amplitude = newAmp;
      Serial.print("Amplitud configurada: ");
      Serial.println(amplitude);
    } else {
      Serial.println("ERROR: Rango de amplitud 0-1");
    }
  }
  else if (cmd == "START") {
    isRunning = true;
    lastUpdate = millis();
    Serial.println("Movimiento iniciado");
  }
  else if (cmd == "STOP") {
    isRunning = false;
    waveServo.write(CENTER_ANGLE);
    Serial.println("Movimiento detenido");
  }
  else if (cmd == "STATUS") {
    Serial.print("Estado: ");
    Serial.println(isRunning ? "CORRIENDO" : "DETENIDO");
    Serial.print("Frecuencia: ");
    Serial.print(frequency);
    Serial.println(" Hz");
    Serial.print("Amplitud: ");
    Serial.println(amplitude);
  }
  else {
    Serial.println("ERROR: Comando no reconocido");
  }
}

/*
 * Calcula posición del servo usando función sinusoidal
 * Actualiza servo cada TIME_STEP ms
 */
void updateServoPosition() {
  // Tiempo en segundos
  float timeSeconds = millis() / 1000.0;

  // Onda sinusoidal: y = A * sin(2π * f * t)
  float angle = CENTER_ANGLE + (AMPLITUDE_ANGLE * amplitude * sin(2.0 * PI * frequency * timeSeconds));

  // Limitar ángulos (0-180°)
  if (angle < 0) angle = 0;
  if (angle > 180) angle = 180;

  waveServo.write((int)angle);
}
