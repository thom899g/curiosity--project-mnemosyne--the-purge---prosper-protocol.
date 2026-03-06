"""
Firebase client for state management and real-time data.
Implements robust error handling and reconnection logic.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.client import Client as FirestoreClient
from google.cloud.firestore_v1.document import DocumentReference
from typing import Dict, Any, Optional, List
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime, timedelta

logger = structlog.get_logger()

class FirebaseClient:
    """Firebase client with automatic initialization and error recovery"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new