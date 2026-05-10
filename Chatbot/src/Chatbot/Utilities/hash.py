# =====================================================
# 🔐 HashUtils - utilidades criptográficas
# =====================================================
import hashlib
from pathlib   import Path

class HashUtils:
    @staticmethod
    def sha256_file(filepath: str | Path, block_size: int = 65536) -> str:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")
        sha = hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda: f.read(block_size), b""):
                sha.update(block)
        return sha.hexdigest()
