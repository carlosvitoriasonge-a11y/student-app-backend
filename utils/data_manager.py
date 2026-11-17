import os
import json
import shutil
import tempfile
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Trava global: um salvamento por vez dentro do processo do servidor.
# Evita que dois pedidos simultâneos escrevam no mesmo arquivo ao mesmo tempo.
_lock = threading.Lock()

# Quantas versões anteriores de cada arquivo ficam guardadas em data/backups/
BACKUP_KEEP = 10


def _rotate_backup(path: Path):
    """Guarda a versão atual do arquivo em data/backups/ antes de sobrescrever.

    Mantém até BACKUP_KEEP versões: <arquivo>.1.bak é a mais recente.
    """
    if not path.exists():
        return
    backup_dir = DATA_DIR / "backups"
    backup_dir.mkdir(exist_ok=True)

    oldest = backup_dir / f"{path.name}.{BACKUP_KEEP}.bak"
    if oldest.exists():
        oldest.unlink()
    for i in range(BACKUP_KEEP - 1, 0, -1):
        src = backup_dir / f"{path.name}.{i}.bak"
        if src.exists():
            src.replace(backup_dir / f"{path.name}.{i + 1}.bak")
    shutil.copy2(path, backup_dir / f"{path.name}.1.bak")


def load_json(filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data):
    """Salva de forma segura:

    1. Faz backup da versão anterior (rotação em data/backups/)
    2. Escreve num arquivo temporário na mesma pasta
    3. Troca o temporário pelo oficial com os.replace (troca atômica:
       se o processo cair no meio, o arquivo oficial fica intacto)
    """
    path = DATA_DIR / filename
    with _lock:
        _rotate_backup(path)
        fd, tmp_name = tempfile.mkstemp(
            dir=DATA_DIR, prefix=path.name + ".", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, path)
        except BaseException:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise
