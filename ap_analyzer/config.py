from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)
DEFAULT_PARAMS = {"n_cycles":2,"t1":100,"t2":100,"V0":-80,"V1":100,"V2":10}
