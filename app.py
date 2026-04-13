import os

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from jose import JWTError, jwt

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@db:5432/nepse"
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# Auth
SECRET_KEY = "your-secret-key"  # In production, use a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBearer()


class MessageCounter(Base):
    __tablename__ = "message_counter"

    id = Column(Integer, primary_key=True, index=True)
    count = Column(Integer, nullable=False, default=0)
    title = Column(String(128), nullable=False, default="Nepse Trader Backend")
    text = Column(String(256), nullable=False, default="Hello from Python FastAPI backend!")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)


class MessageResponse(BaseModel):
    title: str
    text: str
    count: int


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


app = FastAPI(title="Nepse Trader API")

origins = [
    "http://localhost:4200"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    print(f"Hashing password: {repr(password)}")
    try:
        return pwd_context.hash(password)
    except ValueError as e:
        print(f"ValueError in hash: {e}")
        if "72 bytes" in str(e):
            # Truncate to 72 bytes if too long
            password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
            print(f"Truncated to: {repr(password)}")
            return pwd_context.hash(password)
        else:
            raise


def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str):
    user = db.execute(select(User).where(User.username == username)).scalars().first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.execute(select(User).where(User.username == username)).scalars().first()
    if user is None:
        raise credentials_exception
    return user


def ensure_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        # Message counter
        row = db.execute(select(MessageCounter)).scalars().first()
        if row is None:
            db.add(MessageCounter(count=0))
            db.commit()
        
        # Default user
        user = db.execute(select(User).where(User.username == "admin")).scalars().first()
        if user is None:
            hashed_password = get_password_hash("admin")
            db.add(User(username="admin", hashed_password=hashed_password))
            db.commit()


@app.on_event("startup")
def startup_event():
    try:
        ensure_database()
    except SQLAlchemyError:
        pass


@app.get("/login", response_class=HTMLResponse)
def login_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - Nepse Trader</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }

            .login-container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                width: 100%;
                max-width: 400px;
                text-align: center;
            }

            .login-header {
                margin-bottom: 30px;
            }

            .login-header h2 {
                color: #333;
                font-size: 28px;
                margin-bottom: 10px;
                font-weight: 600;
            }

            .login-header p {
                color: #666;
                font-size: 14px;
            }

            .form-group {
                margin-bottom: 20px;
                text-align: left;
            }

            .form-group label {
                display: block;
                margin-bottom: 5px;
                color: #333;
                font-weight: 500;
                font-size: 14px;
            }

            .form-group input {
                width: 100%;
                padding: 12px 15px;
                border: 2px solid #e1e5e9;
                border-radius: 5px;
                font-size: 16px;
                transition: border-color 0.3s ease;
                background-color: #f8f9fa;
            }

            .form-group input:focus {
                outline: none;
                border-color: #667eea;
                background-color: white;
            }

            .form-group input:valid {
                border-color: #28a745;
            }

            .login-btn {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }

            .login-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }

            .login-btn:active {
                transform: translateY(0);
            }

            .error-message {
                color: #dc3545;
                font-size: 14px;
                margin-top: 10px;
                display: none;
            }

            .footer {
                margin-top: 20px;
                font-size: 12px;
                color: #999;
            }

            @media (max-width: 480px) {
                .login-container {
                    padding: 30px 20px;
                }

                .login-header h2 {
                    font-size: 24px;
                }
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <h2>Welcome Back</h2>
                <p>Please sign in to your account</p>
            </div>
            <form action="/login" method="post" id="loginForm">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required placeholder="Enter your username">
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required placeholder="Enter your password">
                </div>
                <button type="submit" class="login-btn">Sign In</button>
                <div class="error-message" id="errorMessage"></div>
            </form>
            <div class="footer">
                <p>&copy; 2026 Nepse Trader. All rights reserved.</p>
            </div>
        </div>

        <script>
            document.getElementById('loginForm').addEventListener('submit', async function(e) {
                e.preventDefault();

                const username = document.getElementById('username').value.trim();
                const password = document.getElementById('password').value.trim();
                const errorMessage = document.getElementById('errorMessage');
                const submitBtn = document.querySelector('.login-btn');

                // Basic client-side validation
                if (!username || !password) {
                    errorMessage.textContent = 'Please fill in all fields.';
                    errorMessage.style.display = 'block';
                    return;
                }

                // Disable button and show loading
                submitBtn.disabled = true;
                submitBtn.textContent = 'Signing In...';
                errorMessage.style.display = 'none';

                try {
                    const response = await fetch('/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            username: username,
                            password: password
                        })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        // Store the token and redirect to the main application
                        const token = data.access_token;
                        console.log('Token stored:', token);
                        window.location.href = `http://localhost:4200?token=${encodeURIComponent(token)}`;
                    } else {
                        // Show error message
                        errorMessage.textContent = data.detail || 'Login failed. Please try again.';
                        errorMessage.style.display = 'block';
                    }
                } catch (error) {
                    errorMessage.textContent = 'Network error. Please check your connection and try again.';
                    errorMessage.style.display = 'block';
                } finally {
                    // Re-enable button
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Sign In';
                }
            });
        </script>
    </body>
    </html>
    """


@app.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/message", response_model=MessageResponse)
def get_message(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    counter = db.execute(select(MessageCounter)).scalars().first()
    if counter is None:
        counter = MessageCounter(count=0)
        db.add(counter)

    counter.count += 1
    db.commit()
    db.refresh(counter)

    return {
        "title": counter.title,
        "text": counter.text,
        "count": counter.count,
    }
