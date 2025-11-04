# app/services/state.py
from threading import Lock

PROCESS_STATUS = {}
PROCESS_LOCK = Lock()
