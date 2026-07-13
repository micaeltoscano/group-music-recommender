"""Utilitários de criptografia para os tokens do Spotify."""

from cryptography.fernet import Fernet
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Instância do Fernet baseada na chave de configuração
_fernet: Fernet | None = None

def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        if not settings.fernet_key:
            logger.warning("FERNET_KEY não está definida no ambiente. Usando chave temporária apenas para testes.")
            # Chave temporária gerada dinamicamente para não quebrar a aplicação caso falte no .env
            temp_key = Fernet.generate_key()
            _fernet = Fernet(temp_key)
        else:
            _fernet = Fernet(settings.fernet_key.encode('utf-8'))
    return _fernet

def encrypt(text: str) -> str:
    """Criptografa uma string usando Fernet."""
    if not text:
        return text
    fernet = _get_fernet()
    return fernet.encrypt(text.encode('utf-8')).decode('utf-8')

def decrypt(token_encrypted: str) -> str:
    """Descriptografa uma string usando Fernet."""
    if not token_encrypted:
        return token_encrypted
    fernet = _get_fernet()
    return fernet.decrypt(token_encrypted.encode('utf-8')).decode('utf-8')
