import webbrowser
import pyperclip
from datetime                         import datetime
from Chatbot.Cores.question_structure import QuestionStructure

class AILauncher:
    """
    Abre plataformas de IA y prepara el prompt.
    """
    AI_URLS = {
        "chatgpt": "https://chat.openai.com/",
        "copilot": "https://copilot.microsoft.com/",
        "meta": "https://www.meta.ai/"}
    def __init__(self):
        self.last_launch_time = None
    def open(self, ai_name: str, with_question: str | None = None):
        if ai_name not in self.AI_URLS:
            raise ValueError("IA no soportada")
        # Construir prompt
        prompt = QuestionStructure.base_context()
        if with_question:
            prompt += QuestionStructure.question_structure(with_question)
        # Copiar al portapapeles
        pyperclip.copy(prompt)
        # Abrir navegador
        webbrowser.open(self.AI_URLS[ai_name])
        self.last_launch_time = datetime.now()
        self._print_status(ai_name)
    def _print_status(self, ai_name):
        print("🟢 Contexto generado")
        print("🟢 IA lista →", ai_name)
        print("🟢 Prompt copiado")
        print(f"🧠 Última consulta: {self.last_launch_time.strftime('%H:%M:%S')}")
