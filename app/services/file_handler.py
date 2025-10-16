import os
import shutil
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from datetime import datetime

class FileHandler:
    """Gerenciador de upload e armazenamento de arquivos"""
    
    UPLOAD_DIR = "uploads"
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    
    @staticmethod
    def init_upload_dir():
        """Cria diretório de uploads se não existir"""
        os.makedirs(FileHandler.UPLOAD_DIR, exist_ok=True)
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Verifica se o arquivo tem extensão permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in FileHandler.ALLOWED_EXTENSIONS
    
    @staticmethod
    def save_uploaded_file(file: FileStorage, user_id: int) -> tuple[str, str]:
        """
        Salva arquivo enviado pelo usuário
        
        Args:
            file: Arquivo do Flask (FileStorage)
            user_id: ID do usuário que está fazendo upload
            
        Returns:
            tuple: (caminho_absoluto, nome_do_arquivo)
            
        Raises:
            ValueError: Se o arquivo não for permitido
        """
        FileHandler.init_upload_dir()
        
        # Validar tipo de arquivo
        if not FileHandler.allowed_file(file.filename):
            raise ValueError(f"Tipo de arquivo não permitido. Use: {', '.join(FileHandler.ALLOWED_EXTENSIONS)}")
        
        # Criar nome único e seguro
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{user_id}_{timestamp}_{original_filename}"
        
        # Caminho completo
        file_path = os.path.join(FileHandler.UPLOAD_DIR, unique_filename)
        
        # Salvar arquivo
        file.save(file_path)
        
        return os.path.abspath(file_path), unique_filename
    
    @staticmethod
    def delete_file(filepath: str) -> bool:
        """
        Deleta arquivo do sistema
        
        Args:
            filepath: Caminho do arquivo
            
        Returns:
            bool: True se deletado com sucesso
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Erro ao deletar arquivo: {e}")
            return False
    
    @staticmethod
    def get_file_size(filepath: str) -> int:
        """Retorna tamanho do arquivo em bytes"""
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return 0