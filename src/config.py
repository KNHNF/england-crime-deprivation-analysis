from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_settings() -> dict[str, str]:
    load_dotenv(REPO_ROOT / ".env")

    return {
        "police_data_dir": os.getenv(
            "POLICE_DATA_DIR",
            "data/Crime Data LSOA (june 2023 - may 2026)",
        ),
        "imd_file": os.getenv(
            "IMD_FILE",
            "data/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv",
        ),
        "processed_dir": os.getenv("PROCESSED_DIR", "data/processed/lsoa_crime_deprivation"),
        "figures_dir": os.getenv("FIGURES_DIR", "figures"),
        "mongo_uri": os.getenv("MONGO_URI"),
        "mongo_db": os.getenv("MONGO_DB", "crime_deprivation"),
        "mongo_collection": os.getenv("MONGO_COLLECTION", "Crime_England_Deprivation"),
        
    }


def repo_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path
