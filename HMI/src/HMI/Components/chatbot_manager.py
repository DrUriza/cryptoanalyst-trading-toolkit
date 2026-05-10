# =====================================================
# 🤖 ChatBotManager
# =====================================================
# Responsable de:
# - Guardar preguntas del usuario
# - Generar contexto base para IA
# - Preparar estado para ZIP + Prompt
# =====================================================
import os
from datetime import datetime
from dash     import html, Input, Output, State, no_update

class ChatBotManager:
    def __init__(self, app, paths):
        self.app   = app
        self.paths = paths
    # -------------------------------------------------
    # Registrar callbacks
    # -------------------------------------------------
    def register_callbacks(self):
        @self.app.callback(Output("chatbot-output", "children"),
                           Output("chatbot-input", "value"), 
                           Input("btn-chatbot-send", "n_clicks"),
                           State("chatbot-input", "value"),
                           prevent_initial_call=True)
        def save_user_question(n_clicks, question):
            if not question or not question.strip():
                return no_update, no_update
            os.makedirs(self.paths.CHATBOT_DIR, exist_ok=True)
            question_path = os.path.join(self.paths.CHATBOT_DIR, "user_question.json")
            payload = {"question": question.strip(), "created_at": datetime.now().isoformat(timespec="seconds"), "status": "ready_for_prompt"}
            self.paths.manage_json(filepath=question_path, mode="write", data=payload,default={})
            return (html.Div([html.Div("🟢 Pregunta guardada"), 
                              html.Div("🟢 Contexto listo"),
                              html.Div("📦 Esperando ZIPs + IA")]),"")
