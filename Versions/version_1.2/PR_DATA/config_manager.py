<<<<<<< HEAD
# OLD: Global variables and hardcoded configs
DATABASE_URL = "sqlite:///app.db"
DEBUG = True
MAX_USERS = 100
API_TIMEOUT = 30
ALLOWED_ORIGINS = ["http://localhost:3000"]

def get_config():
    return {
        "database_url": DATABASE_URL,
        "debug": DEBUG,
        "max_users": MAX_USERS,
        "api_timeout": API_TIMEOUT,
        "allowed_origins": ALLOWED_ORIGINS
    }

# NEW: Environment-based configuration with validation
import os
from typing import List, Optional
from pydantic import BaseSettings, validator, HttpUrl

class Settings(BaseSettings):
    # Required settings with validation
    database_url: str
    secret_key: str
    environment: str = "development"
    
    # Optional settings with defaults
    debug: bool = False
    max_users: int = 100
    api_timeout: int = 30
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    # NEW: Feature flags
    enable_analytics: bool = False
    enable_websockets: bool = True
    maintenance_mode: bool = False
    
    # Validation
    @validator('environment')
    def validate_environment(cls, v):
        if v not in ['development', 'staging', 'production']:
            raise ValueError('Environment must be development, staging, or production')
        return v
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 16:
            raise ValueError('Secret key must be at least 16 characters')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# NEW: Singleton configuration instance
settings = Settings()

# NEW: Type-safe config access
def get_config() -> Settings:
=======
# OLD: Global variables and hardcoded configs
DATABASE_URL = "sqlite:///app.db"
DEBUG = True
MAX_USERS = 100
API_TIMEOUT = 30
ALLOWED_ORIGINS = ["http://localhost:3000"]

def get_config():
    return {
        "database_url": DATABASE_URL,
        "debug": DEBUG,
        "max_users": MAX_USERS,
        "api_timeout": API_TIMEOUT,
        "allowed_origins": ALLOWED_ORIGINS
    }

# NEW: Environment-based configuration with validation
import os
from typing import List, Optional
from pydantic import BaseSettings, validator, HttpUrl

class Settings(BaseSettings):
    # Required settings with validation
    database_url: str
    secret_key: str
    environment: str = "development"
    
    # Optional settings with defaults
    debug: bool = False
    max_users: int = 100
    api_timeout: int = 30
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    # NEW: Feature flags
    enable_analytics: bool = False
    enable_websockets: bool = True
    maintenance_mode: bool = False
    
    # Validation
    @validator('environment')
    def validate_environment(cls, v):
        if v not in ['development', 'staging', 'production']:
            raise ValueError('Environment must be development, staging, or production')
        return v
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 16:
            raise ValueError('Secret key must be at least 16 characters')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# NEW: Singleton configuration instance
settings = Settings()

# NEW: Type-safe config access
def get_config() -> Settings:
>>>>>>> 5f7bd0e (Organised the folder for PR Reviews and also implemented the Online Estimation Part. I have created a seperate file for Online Estimation For now just in case to compare the two versions. Later i will add the Online estimation part to version 1.2.1 and make the current as version 1.2.0)
    return settings