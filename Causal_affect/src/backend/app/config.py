from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    feature_ca_006_02_enabled: bool = True
    feature_ca_006_03_enabled: bool = True
    feature_ca_006_04_enabled: bool = True
    feature_ca_006_05_enabled: bool = True
    feature_ca_006_06_enabled: bool = True
    cors_origins: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
