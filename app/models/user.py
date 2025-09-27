import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import Config
import bcrypt
from datetime import datetime

class User:
    """Model para gerenciamento de usuários no banco de dados"""
    
    @staticmethod
    def get_db_connection():
        """
        Estabelece conexão com o banco de dados PostgreSQL (Neon)
        Retorna um cursor que transforma resultados em dicionários
        """
        return psycopg2.connect(
            Config.DATABASE_URL,
            cursor_factory=RealDictCursor
        )
    
    @staticmethod
    def create_table():
        """
        Cria a tabela de usuários se ela não existir
        Executado automaticamente ao iniciar a aplicação
        """
        conn = User.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_email 
                ON users(email)
            ''')
            
            conn.commit()
            print("Tabela 'users' criada/verificada com sucesso")
            
        except Exception as e:
            conn.rollback()
            print(f"Erro ao criar tabela: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Gera hash seguro da senha usando bcrypt
        
        Args:
            password: Senha em texto plano
            
        Returns:
            Hash da senha em string
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verifica se a senha corresponde ao hash armazenado
        
        Args:
            password: Senha em texto plano fornecida pelo usuário
            password_hash: Hash armazenado no banco de dados
            
        Returns:
            True se a senha está correta, False caso contrário
        """
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    
    @staticmethod
    def create_user(email: str, password: str, name: str):
        """
        Cria um novo usuário no banco de dados
        
        Args:
            email: Email do usuário (deve ser único)
            password: Senha em texto plano (será hasheada)
            name: Nome completo do usuário
            
        Returns:
            Dicionário com dados do usuário criado ou None se falhar
        """
        conn = User.get_db_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = User.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (email, password_hash, name)
                VALUES (%s, %s, %s)
                RETURNING id, email, name, created_at
            ''', (email.lower().strip(), password_hash, name.strip()))
            
            user = cursor.fetchone()
            conn.commit()
            
            print(f"Usuário criado: {user['email']}")
            return user
            
        except psycopg2.IntegrityError as e:
            conn.rollback()
            print(f"Email já existe: {email}")
            return None
            
        except Exception as e:
            conn.rollback()
            print(f"Erro ao criar usuário: {e}")
            raise
            
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def find_by_email(email: str):
        """
        Busca usuário por email
        
        Args:
            email: Email do usuário
            
        Returns:
            Dicionário com dados do usuário ou None se não encontrado
        """
        conn = User.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT * FROM users WHERE email = %s',
                (email.lower().strip(),)
            )
            user = cursor.fetchone()
            return user
            
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def find_by_id(user_id: int):
        """
        Busca usuário por ID
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com dados do usuário (sem password_hash) ou None
        """
        conn = User.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, email, name, created_at, updated_at 
                FROM users 
                WHERE id = %s
            ''', (user_id,))
            
            user = cursor.fetchone()
            return user
            
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def update_user(user_id: int, **kwargs):
        """
        Atualiza dados do usuário
        
        Args:
            user_id: ID do usuário
            **kwargs: Campos a serem atualizados (name, email, password)
            
        Returns:
            Dicionário com dados atualizados ou None se falhar
        """
        conn = User.get_db_connection()
        cursor = conn.cursor()
        
        try:
            allowed_fields = {'name', 'email', 'password'}
            updates = []
            values = []
            
            for key, value in kwargs.items():
                if key in allowed_fields and value is not None:
                    if key == 'password':
                        updates.append('password_hash = %s')
                        values.append(User.hash_password(value))
                    else:
                        updates.append(f'{key} = %s')
                        values.append(value)
            
            if not updates:
                return None
            
            updates.append('updated_at = CURRENT_TIMESTAMP')
            values.append(user_id)
            
            query = f'''
                UPDATE users 
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, email, name, updated_at
            '''
            
            cursor.execute(query, values)
            user = cursor.fetchone()
            conn.commit()
            
            return user
            
        except psycopg2.IntegrityError:
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()