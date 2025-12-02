"""
TANQUE DE ONDAS - CONTROL DE SERVO
Interfaz Python para controlar Arduino via puerto serial
"""

import serial
import time
import logging
from typing import Optional

class ServoController:
    # Controla el servo motor SG90 via Arduino

    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 9600, timeout: float = 1.0):
        # Inicializa la conexión serial con Arduino
        # Args:
        #    port: Puerto serial (ej: /dev/ttyUSB0 Linux, COM3 Windows)
        #    baudrate: Velocidad en bps (típicamente 9600)
        #    timeout: Tiempo máximo de espera para lectura

        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connected = False
        self.frequency = 5.0
        self.amplitude = 1.0

        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('ServoControl')

        self.connect()

    def connect(self) -> bool:
        # Establece conexión con Arduino
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1.0)
            time.sleep(2)  # Esperar a que Arduino se reinicie
            self.connected = True
            self.logger.info(f"Conectado a {self.port} @ {self.baudrate} bps")
            return True
        except serial.SerialException as e:
            self.logger.error(f"Error de conexión: {e}")
            self.connected = False
            return False

    def disconnect(self):
        # Cierra conexión con Arduino
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.connected = False
            self.logger.info("Desconectado")

    def send_command(self, command: str) -> Optional[str]:
        # Envía comando a Arduino y espera respuesta
        # Args:
        #    command: Comando a enviar (ej: "FREQ 10")

        # Returns:
        #    Respuesta de Arduino o None si falla

        if not self.connected:
            self.logger.error("No conectado a Arduino")
            return None

        try:
            self.ser.write((command + '\n').encode())
            time.sleep(0.1)  # Delay para buffer

            response = ""
            while self.ser.in_waiting:
                response += self.ser.read().decode()

            return response.strip()
        except Exception as e:
            self.logger.error(f"Error enviando comando: {e}")
            return None

    def set_frequency(self, freq: float) -> bool:
        # Establece frecuencia del movimiento (Hz)
        if freq < 1.0 or freq > 25.0:
            self.logger.warning(f"Frecuencia fuera de rango: {freq} Hz")
            return False

        response = self.send_command(f"FREQ {freq}")
        if response and "configurada" in response:
            self.frequency = freq
            self.logger.info(f"Frecuencia: {freq} Hz")
            return True
        return False

    def set_amplitude(self, amp: float) -> bool:
        # Establece amplitud del movimiento (0-1)
        if amp < 0.0 or amp > 1.0:
            self.logger.warning(f"Amplitud fuera de rango: {amp}")
            return False

        response = self.send_command(f"AMP {amp}")
        if response and "configurada" in response:
            self.amplitude = amp
            self.logger.info(f"Amplitud: {amp}")
            return True
        return False

    def start(self) -> bool:
        # Inicia el movimiento del servo
        response = self.send_command("START")
        if response and "iniciado" in response:
            self.logger.info("Movimiento iniciado")
            return True
        return False

    def stop(self) -> bool:
        # Detiene el movimiento del servo
        response = self.send_command("STOP")
        if response and "detenido" in response:
            self.logger.info("Movimiento detenido")
            return True
        return False

    def get_status(self) -> dict:
        # Obtiene estado actual del servo
        response = self.send_command("STATUS")
        if response:
            self.logger.info(f"Status: {response}")
            return {"raw": response}
        return None


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    # Detectar puerto (ajustar según sistema)
    PORT = '/dev/ttyUSB0'  # Linux/Mac
    # PORT = 'COM3'         # Windows

    controller = ServoController(port=PORT)

    if controller.connected:
        # Configurar parámetros
        controller.set_frequency(10.0)    # 10 Hz
        controller.set_amplitude(0.8)     # 80% amplitud

        # Iniciar movimiento
        controller.start()
        time.sleep(5)

        # Obtener status
        controller.get_status()

        # Detener
        controller.stop()
        controller.disconnect()
