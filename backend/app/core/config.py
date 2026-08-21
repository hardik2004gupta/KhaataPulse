from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://khaatapulse:khaatapulse@localhost:5432/khaatapulse"

    # Application
    app_env: str = "development"

    # Policy thresholds — configuration-driven per CLAUDE.md §25
    auto_action_limit: int = 10000       # INR: auto-execute below this amount
    max_contacts_7d: int = 3             # maximum contacts per customer per 7 days
    contact_cooldown_hours: int = 24     # hours between contacts
    kill_switch: bool = False            # global automation kill switch

    # LLM (Phase 2+)
    llm_api_key: str = ""
    llm_model: str = "claude-opus-5-20251101"

    # Risk Sieve (Phase 2+) — CLAUDE.md §8, §25
    risk_threshold: float = 0.30          # P(failure) >= threshold → LangGraph
    risk_model_version: str = "logistic-v1"

    # Simulator
    default_cohort_size: int = 3000
    simulator_version: str = "v1"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
