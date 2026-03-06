"""
Configuration management for Project Mnemosyne.
Centralized configuration with environment variable fallbacks.
"""
import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import structlog

logger = structlog.get_logger()

@dataclass
class PurgeConfig:
    """Configuration for Phase 1: Process Purge"""
    # Memory thresholds (in MB)
    MEMORY_THRESHOLD_MB: int = 500
    CRITICAL_THRESHOLD_MB: int = 1000
    # Essential process patterns (case-insensitive)
    ESSENTIAL_PROCESSES: List[str] = None
    # Monitoring intervals
    MONITOR_INTERVAL_SECONDS: int = 300
    GRACE_PERIOD_SECONDS: int = 60
    
    def __post_init__(self):
        if self.ESSENTIAL_PROCESSES is None:
            self.ESSENTIAL_PROCESSES = [
                "systemd", "kernel", "dockerd", "containerd",
                "python", "main.py", "trading_swarm.py"
            ]

@dataclass
class TradingConfig:
    """Configuration for Phase 2: Trading Swarm"""
    # Trading parameters
    MAX_POSITION_SIZE_USD: float = 1000
    TARGET_DAILY_RETURN: float = 0.05  # 5%
    STOP_LOSS_PERCENT: float = 0.03    # 3%
    TAKE_PROFIT_PERCENT: float = 0.08  # 8%
    # Market parameters
    MAX_MARKET_CAP_USD: float = 100_000_000  # $100M
    MIN_VOLUME_USD: float = 500_000
    # Swarm parameters
    MAX_AGENTS: int = 10
    AGENT_LIFETIME_HOURS: int = 24
    COOLDOWN_SECONDS: int = 30

@dataclass
class FirebaseConfig:
    """Firebase configuration"""
    PROJECT_ID: Optional[str] = None
    CREDENTIALS_PATH: Optional[str] = None
    COLLECTION_NAME: str = "mnemosyne_state"
    
    def __post_init__(self):
        # Load from environment variables if not provided
        self.PROJECT_ID = self.PROJECT_ID or os.getenv("FIREBASE_PROJECT_ID")
        self.CREDENTIALS_PATH = self.CREDENTIALS_PATH or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

class ConfigManager:
    """Manages configuration with validation and persistence"""
    
    def __init__(self):
        self.purge = PurgeConfig()
        self.trading = TradingConfig()
        self.firebase = FirebaseConfig()
        self._validate_config()
    
    def _validate_config(self):
        """Validate all configuration parameters"""
        if self.purge.MEMORY_THRESHOLD_MB <= 0:
            raise ValueError("Memory threshold must be positive")
        if self.trading.TARGET_DAILY_RETURN <= 0:
            raise ValueError("Target return must be positive")
        if not self.firebase.PROJECT_ID:
            logger.warning("Firebase project ID not set, some features may be limited")
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary for serialization"""
        return {
            "purge": asdict(self.purge),
            "trading": asdict(self.trading),
            "firebase": asdict(self.firebase)
        }
    
    def save_to_firebase(self, db):
        """Save configuration to Firebase"""
        try:
            doc_ref = db.collection("config").document("current")
            doc_ref.set(self.to_dict())
            logger.info("Configuration saved to Firebase")
        except Exception as e:
            logger.error("Failed to save config to Firebase", error=str(e))