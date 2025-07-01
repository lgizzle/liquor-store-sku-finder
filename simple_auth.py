import sqlite3
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from auth_config import AuthConfig

class SimpleAuth:
    def __init__(self):
        self.config = AuthConfig()
        self.init_db()
    
    def init_db(self):
        """Initialize the users database"""
        with sqlite3.connect(self.config.DATABASE_PATH, check_same_thread=False) as conn:
            cursor = conn.cursor()
        
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    is_superadmin BOOLEAN DEFAULT 0,
                    reset_token_hash TEXT,
                    reset_token_expires TIMESTAMP
                )
            ''')
            conn.commit()
    
    def create_superadmin_if_not_exists(self):
        """Create superadmin account on first run"""
        superadmin_email = self.config.SUPERADMIN_EMAIL
        
        if self.get_user_by_email(superadmin_email):
            return  # Superadmin already exists
        
        try:
            with sqlite3.connect(self.config.DATABASE_PATH, check_same_thread=False) as conn:
                cursor = conn.cursor()
                password_hash = generate_password_hash(self.config.SUPERADMIN_PASSWORD)
                
                cursor.execute('''
                    INSERT INTO users (email, password_hash, is_superadmin)
                    VALUES (?, ?, 1)
                ''', (superadmin_email, password_hash))
                
                conn.commit()
                print(f"Created superadmin account: {superadmin_email}")
                
        except Exception as e:
            print(f"Error creating superadmin: {e}")
    
    def create_user(self, email, password):
        """Create a new user account"""
        if self.get_user_by_email(email):
            return {'success': False, 'error': 'Email already exists'}
        
        password_hash = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect(self.config.DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (email, password_hash)
                VALUES (?, ?)
            ''', (email, password_hash))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Account created successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def verify_user(self, email, password):
        """Verify user credentials"""
        user = self.get_user_by_email(email)
        if not user:
            return {'success': False, 'error': 'Invalid email or password'}
        
        if not user['is_active']:
            return {'success': False, 'error': 'Account is disabled'}
        
        if check_password_hash(user['password_hash'], password):
            return {'success': True, 'user': user}
        else:
            return {'success': False, 'error': 'Invalid email or password'}
    
    def get_user_by_email(self, email):
        """Get user by email address"""
        try:
            conn = sqlite3.connect(self.config.DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            conn.close()
            
            return dict(user) if user else None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    def get_all_users(self):
        """Get all users (superadmin only)"""
        try:
            with sqlite3.connect(self.config.DATABASE_PATH, check_same_thread=False) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, email, created_at, is_active, is_superadmin
                    FROM users ORDER BY created_at DESC
                ''')
                
                users = [dict(row) for row in cursor.fetchall()]
                return users
                
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    
    def toggle_user_status(self, user_id, is_active):
        """Enable/disable user account"""
        try:
            with sqlite3.connect(self.config.DATABASE_PATH, check_same_thread=False) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE users SET is_active = ? WHERE id = ?
                ''', (is_active, user_id))
                
                conn.commit()
                return {'success': True}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def reset_user_password(self, user_id, new_password):
        """Reset user password (superadmin function)"""
        try:
            with sqlite3.connect(self.config.DATABASE_PATH, check_same_thread=False) as conn:
                cursor = conn.cursor()
                password_hash = generate_password_hash(new_password)
                
                cursor.execute('''
                    UPDATE users 
                    SET password_hash = ?, reset_token_hash = NULL, reset_token_expires = NULL
                    WHERE id = ?
                ''', (password_hash, user_id))
                
                conn.commit()
                return {'success': True}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_reset_token(self, email):
        """Generate password reset token"""
        user = self.get_user_by_email(email)
        if not user:
            return {'success': False, 'error': 'Email not found'}
        
        reset_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
        expires = datetime.now() + timedelta(hours=1)  # Token expires in 1 hour
        
        try:
            with sqlite3.connect(self.config.DATABASE_PATH, check_same_thread=False) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE users 
                    SET reset_token_hash = ?, reset_token_expires = ?
                    WHERE email = ?
                ''', (token_hash, expires, email))
                
                conn.commit()
            
            # Send reset email
            if self.send_reset_email(email, reset_token):
                return {'success': True, 'message': 'Password reset email sent'}
            else:
                return {'success': False, 'error': 'Failed to send email'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def reset_password(self, token, new_password):
        """Reset password using token"""
        try:
            conn = sqlite3.connect(self.config.DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM users 
                WHERE reset_token = ? AND reset_token_expires > ?
            ''', (token, datetime.now()))
            
            user = cursor.fetchone()
            if not user:
                conn.close()
                return {'success': False, 'error': 'Invalid or expired token'}
            
            # Update password and clear reset token
            password_hash = generate_password_hash(new_password)
            cursor.execute('''
                UPDATE users 
                SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL
                WHERE id = ?
            ''', (password_hash, user['id']))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Password reset successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_reset_email(self, email, token):
        """Send password reset email"""
        try:
            # Get base URL from config (defaults to localhost for dev)
            base_url = getattr(self.config, 'BASE_URL', 'http://localhost:5001')
            
            msg = MIMEMultipart()
            msg['From'] = self.config.FROM_EMAIL
            msg['To'] = email
            msg['Subject'] = f'{self.config.APP_NAME} - Password Reset'
            
            # Simple HTML email
            html_body = f'''
            <html>
            <body>
                <h2>{self.config.APP_NAME} - Password Reset</h2>
                <p>You requested a password reset for your account.</p>
                <p>Click the link below to reset your password (expires in 1 hour):</p>
                <p><a href="{base_url}/reset-password/{token}">Reset Password</a></p>
                <p>If you didn't request this, please ignore this email.</p>
            </body>
            </html>
            '''
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.config.MAIL_SERVER, self.config.MAIL_PORT)
            server.starttls()
            server.login(self.config.MAIL_USERNAME, self.config.MAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
