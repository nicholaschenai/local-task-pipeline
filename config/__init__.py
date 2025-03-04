import os
from pathlib import Path

if '__file__' in globals():
    f_dir = os.path.dirname(__file__)
else:
    f_dir = os.getcwd()  # Fallback to current working directory

LM_CACHE_FOLDER = os.path.join(f_dir, '../lm_cache')
LM_CACHE_DB_PATH = os.path.join(LM_CACHE_FOLDER, "lm_cache.db")

RESULTS_FOLDER = "outputs"
INPUT_FOLDER = "data"
LOG_DIR = Path("./log_files")
