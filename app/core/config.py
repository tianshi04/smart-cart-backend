from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    """
    Manages application-wide settings by loading them from environment variables
    and/or a .env file.

    Utilizes Pydantic's BaseSettings for robust validation and type hinting.
    """

    # --- Database Configuration ---
    # Asynchronous PostgreSQL connection URL.
    # Example: "postgresql+asyncpg://user:password@host:port/dbname"
    DATABASE_URL: str

    # --- JWT Authentication ---
    # Secret key for encoding and decoding JWTs.
    # It's crucial to keep this secret and change it for production.
    # You can generate a strong secret using: openssl rand -hex 32
    SECRET_KEY: str = "a_very_secret_key_that_should_be_changed"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- PayOS Integration ---
    PAYOS_CLIENT_ID: str = "your_client_id"
    PAYOS_API_KEY: str = "your_api_key"
    PAYOS_CHECKSUM_KEY: str = "your_checksum_key"

    # --- Cloudflare R2 Storage ---
    CLOUDFLARE_R2_ACCOUNT_ID: str = "your_r2_account_id"
    CLOUDFLARE_R2_ACCESS_KEY_ID: str = "your_r2_access_key_id"
    CLOUDFLARE_R2_SECRET_ACCESS_KEY: str = "your_r2_secret_access_key"
    CLOUDFLARE_R2_BUCKET_NAME: str = "your_r2_bucket_name"
    CLOUDFLARE_R2_PUBLIC_URL: str = "https://pub-<YOUR_ACCOUNT_ID>.r2.dev/<YOUR_BUCKET_NAME>" # Example: https://pub-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.r2.dev/your-bucket-name

    # Pydantic settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",  # Specifies the file to load environment variables from
        env_file_encoding="utf-8",
        case_sensitive=False,  # Environment variable names are case-insensitive
    )


# Create a single, reusable instance of the settings
settings = Settings()