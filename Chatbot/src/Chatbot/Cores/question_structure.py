# =====================================================
# 🧠 QuestionStructure - ChatBot (FINAL)
# =====================================================
# Responsabilidad única:
# - Construir el prompt final para IA externa
# - Leer la pregunta generada por la HMI
# - Guardar el prompt listo para copiar / usar
#
# Compatible con:
# - HMI
# - EngineBot.exe
# - Ejecución .py
# =====================================================

from datetime                   import datetime

class QuestionStructure:
    # =================================================
    # 🔹 INIT (AQUÍ estaba el bug)
    # =================================================
    def __init__(self, paths):
        self.paths = paths
    # =================================================
    # 🔹 Templates internos
    # =================================================
    @staticmethod
    def _base_context():
        return """ Contexto:
                    Voy a subir uno o más archivos ZIP.
                    Cada ZIP contiene información estructurada de mercado, generada automáticamente.

                    Contenido esperado dentro del ZIP:
                    - Market Data (velas OHLC, volumen, spread, order book)
                    - Process Data (indicadores técnicos procesados)
                    - Master Data (fusión multi-timeframe, señales agregadas)
                    - ML Outputs (predicciones, scores, probabilidades)
                    - OrderBook (profundidad y presión bid/ask)

                    Instrucciones:
                    - Espera a que TODOS los ZIP estén completamente cargados antes de responder.
                    - Analiza exclusivamente la información contenida en los ZIP.
                    - NO utilices conocimiento externo ni precios históricos fuera de los datos recibidos.
                    - NO inventes niveles, precios, zonas ni señales.

                    Análisis requerido:
                    - Determina si el mercado muestra:
                    - Continuación de tendencia
                    - Reversión de tendencia
                    - Lateralidad / rango
                    - Evalúa la confluencia entre Análisis Técnico (TA) y modelos de Machine Learning (ML).
                    - Señala explícitamente:
                        - Confirmación TA + ML
                        - Contradicción TA vs ML
                        - Neutralidad (sin confluencia suficiente)

                    Reglas de seguridad:
                    - Todos los niveles numéricos deben estar en el mismo orden de magnitud
                    que el precio actual del activo presente en el ZIP.
                    - Si no existen datos suficientes para definir soportes, resistencias o señales,
                    debes indicarlo claramente y NO estimarlos.
                    - Si no hay confluencia clara, la recomendación debe ser NO OPERAR.

                    Salida esperada:
                    - Escenario Bullish (condiciones necesarias para activarse)
                    - Escenario Bearish (condiciones necesarias para activarse)
                    - Que tendría que pasar para:
                    - Entrar en compra
                    - Entrar en venta
                    - Resumen en modo scalping / intradía
                    - Zonas de soporte y resistencia NUMERICAS,
                    solo si pueden justificarse directamente con los datos del ZIP
                    (ejemplo: resistencia en 95680, soporte en 94120)
                    Al final de tu respuesta debes generar un archivo JSON DESCARGABLE
                    con el nombre exacto:
                    FORMATO DE SALIDA OBLIGATORIO:
                    IA_Response_YYYYMMDD_HHMMSS.json (Fecha actual)
                    El contenido del JSON debe seguir ESTRICTAMENTE este esquema:
                    {
                    "ia_id": "string (ejemplo: chatgpt)",
                    "zip_sha256": "<DEBES COPIAR EXACTAMENTE el hash del ZIP proporcionado>",
                    "trend": "bullish | bearish | range",
                    "confidence": 0.0-1.0,
                    "trade_allowed": true | false,
                    "sl": number,
                    "tp": number,
                    "reason": "explicación breve y técnica"
                    }
                    REGLAS DURAS:
                    - Si trade_allowed = false → sl = 0 y tp = 0
                    - Si trade_allowed = true → sl > 0 y tp > 0
                    - NO omitas ningún campo
                    - NO uses null
                    - NO inventes precios fuera del rango del ZIP
                    - Si no hay trade claro, trade_allowed = false
                    Este JSON será procesado automáticamente por el sistema por lo que lo tienes que mandar a descargar automaticamente
                    acabando tu respuesta para el ususario. El JSON debe contener ÚNICAMENTE el resumen estructurado.
                    NO incluyas texto humano dentro del JSON.
                    Si el formato no se cumple, la respuesta será descartada.
                    """
    @staticmethod
    def _question_block(question):
        return f"""Pregunta:{question}"""
    # =================================================
    # 🔹 Builder principal
    # =================================================
    def build(self):
        question_path = self.paths.chatbot_question_file()
        data = self.paths.manage_json(filepath=question_path, mode="read", default={})
        # -----------------------------
        # Contexto base (siempre)
        # -----------------------------
        base_context = self._base_context()
        prompt = base_context
        question_raw = data.get("question")
        question_clean = None
        # -----------------------------
        # Acoplar pregunta si existe
        # -----------------------------
        if isinstance(question_raw, str) and question_raw.strip():
            question_clean = question_raw.strip()
            prompt += "\n\n" + self._question_block(question_clean)
        # -----------------------------
        # Payload final estructurado
        # -----------------------------
        payload = {"prompt": prompt,
                   "prompt_context": base_context,
                   "prompt_question": question_clean,
                   "has_question": bool(question_clean),
                   "created_at": datetime.now().isoformat(timespec="seconds"),
                   "source": "HMI",
                   "status": "ready_for_copy"}
        # -----------------------------
        # Guardar prompt listo
        # -----------------------------
        self.paths.manage_json(filepath=self.paths.chatbot_prompt_file(), mode="write", data=payload, default={})
        return payload
