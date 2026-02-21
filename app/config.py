"""
Constants and configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_VERSION = "1.0.0"
API_TITLE = "BLK Hacking IND Retirement"

# Financial Constants
DEFAULT_EXPECTED_RETURN = 0.07  # 7% annual return
DEFAULT_INFLATION_RATE = 0.03  # 3% inflation
SAFE_WITHDRAWAL_RATE = 0.04  # 4% rule for retirement

# Application Configuration
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
