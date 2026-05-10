# =====================================================
# mainChatBot.py
# =====================================================
from datetime                         import datetime
from Chatbot.Cores.project_path       import ProjectPaths
from Chatbot.Cores.question_structure import QuestionStructure
from Chatbot.Cores.zip_creator        import ZipCreator
from Chatbot.Utilities.ai_response    import IAIngestUtils


class ChatBotApp:
    def __init__(self, root_dir, debug=True):
        self.root_dir = root_dir
        self.debug    = debug
        self.paths    = ProjectPaths(self.root_dir)
        self.ingest   = IAIngestUtils(self.paths)
        print("🟢 ChatBotApp inicializado en:", self.root_dir)
        print("👁️ IAIngest watchdog activo (background)")
    # -------------------------------------------------
    def run_ZipC(self):
        print("\n🤖 Iniciando ChatBot Pipeline\n")
        # 1️⃣ Prompt
        qs = QuestionStructure(self.paths)
        prompt_payload = qs.build()
        print("🟢 Prompt generado")
        print("   → Tiene pregunta:", prompt_payload["has_question"])
        # 2️⃣ ZIP + HASH
        zip_creator = ZipCreator(self.paths)
        zip_path, zip_sha256 = zip_creator.build_zip()
        print("🟢 ZIP creado")
        print("   →", zip_path)
        print("🔐 ZIP SHA256:", zip_sha256)
        # 3️⃣ Estado para HMI / IA / Ingest
        status_payload = {"prompt_ready": True,
                          "zip_ready": True,
                          "has_question": prompt_payload["has_question"],
                          "zip_path": zip_path,
                          "zip_sha256": zip_sha256,
                          "updated_at": datetime.now().isoformat(timespec="seconds"),
                          "status": "ready_for_upload"}
        self.paths.manage_json(filepath=self.paths.chatbot_status_file(), mode="write", data=status_payload)
        print("\n✅ ChatBot listo para IA (esperando respuestas)\n")
    def run_IAI(self):
        # 👁️ SIEMPRE revisar respuestas IA
        processed = self.ingest.run()
        if processed:
            print(f"🤖 IA responses procesadas: {processed}")