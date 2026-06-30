import pandas as pd
import torch
import torch.nn as nn
import joblib
from pathlib import Path

from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from model import SolarEnergyNN

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


FEATURES = [
    "latitude",
    "longitude",
    "hour",
    "day_of_year",

    "temperature_2m",
    "cloud_cover",
    "is_day",
    "wind_speed_10m",
    "shortwave_radiation",
    "direct_radiation",
    "diffuse_radiation",

    "inverter_kw",
    "installed_capacity_kwp",

    "panel_tilt",
    "panel_azimuth"
]


def train_model(
    csv_path=DATA_DIR / "solar_training_data.csv",
    model_path="solar_model.pt",
    scaler_path="solar_scaler.pkl",
    epochs=100,
    batch_size=64,
    learning_rate=0.001
):
    df = pd.read_csv(csv_path)

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_year"] = df["timestamp"].dt.dayofyear

    df = df.dropna(subset=FEATURES + ["energy_output_kw"])

    X = df[FEATURES].values
    y = df["energy_output_kw"].values.reshape(-1, 1)

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32)

    X_test = torch.tensor(X_test, dtype=torch.float32)
    y_test = torch.tensor(y_test, dtype=torch.float32)

    train_loader = DataLoader(
        TensorDataset(X_train, y_train),
        batch_size=batch_size,
        shuffle=True
    )

    model = SolarEnergyNN(input_size=len(FEATURES))

    loss_fn = nn.MSELoss()
    optimiser = torch.optim.Adam(model.parameters(), lr=learning_rate)

    for epoch in range(epochs):
        model.train()
        total_loss = 0

        for batch_X, batch_y in train_loader:
            prediction = model(batch_X)
            loss = loss_fn(prediction, batch_y)

            optimiser.zero_grad()
            loss.backward()
            optimiser.step()

            total_loss += loss.item()

        if epoch % 10 == 0:
            model.eval()
            with torch.no_grad():
                test_loss = loss_fn(model(X_test), y_test).item()

            print(
                f"Epoch {epoch:03d} | "
                f"Train Loss: {total_loss:.4f} | "
                f"Test Loss: {test_loss:.4f}"
            )

    torch.save(model.state_dict(), model_path)
    joblib.dump(scaler, scaler_path)

    print("Training complete.")
    print(f"Saved model to {model_path}")
    print(f"Saved scaler to {scaler_path}")

    return model


if __name__ == "__main__":
    train_model()