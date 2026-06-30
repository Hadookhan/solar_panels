from pathlib import Path
import ast
import pandas as pd

from data_generation import generate_solar_training_csv


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

AREAS = {
    "House_1": DATA_DIR / "House_1" / "Basic_info.csv",
    "House_2": DATA_DIR / "House_2" / "Basic_info.csv",
    "Reactor": DATA_DIR / "Reactor" / "Basic_info.csv",
}


def load_basic_info(area_name, csv_path):
    df = pd.read_csv(csv_path)

    df.columns = df.columns.str.strip()

    print(f"\nReading {csv_path}")
    print(df.head())
    print(df.columns)

    first_row = df.iloc[0]

    inverter_kw = float(first_row["inverter"])

    raw_capacities = first_row["installedCapacity"]

    if isinstance(raw_capacities, str):
        capacities = ast.literal_eval(raw_capacities)
    else:
        capacities = [raw_capacities]

    arrays = []

    for i, capacity in enumerate(capacities):
        arrays.append({
            "array_id": f"array{i + 1}",
            "capacity_kwp": float(capacity)
        })

    return {
        "house_id": area_name,
        "inverter_kw": inverter_kw,
        "arrays": arrays
    }


def generate_all_datasets():
    DATA_DIR.mkdir(exist_ok=True)

    output_file = DATA_DIR / "solar_training_data.csv"

    for area_name, basic_info_path in AREAS.items():
        if not basic_info_path.exists():
            raise FileNotFoundError(f"Missing file: {basic_info_path}")

        config = load_basic_info(area_name, basic_info_path)

        print(f"Generating data for {area_name}...")

        generate_solar_training_csv(
            location=f"Belgium",
            start_date="2024-01-01",
            end_date="2024-01-14",
            house_id=config["house_id"],
            inverter_kw=config["inverter_kw"],
            arrays=config["arrays"],
            filename=output_file,
            tilt_range=range(0, 91, 10),
            azimuth_range=range(0, 360, 30)
        )

    print(f"Finished generating mixed dataset: {output_file}")


if __name__ == "__main__":
    generate_all_datasets()