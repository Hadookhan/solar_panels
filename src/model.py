import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib


class SolarEnergyNN(nn.Module):
    def __init__(self, input_size):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),

            nn.Linear(64, 64),
            nn.ReLU(),

            nn.Linear(64, 32),
            nn.ReLU(),

            nn.Linear(32, 1)
        )

    def forward(self, x):
        return self.net(x)


def train_solar_model(
    csv_path="solar_training_data.csv",
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

    features = [
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

    target = "energy_output_kw"

    df = df.dropna(subset=features + [target])

    X = df[features].values
    y = df[target].values.reshape(-1, 1)

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42
    )

    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32)

    X_test = torch.tensor(X_test, dtype=torch.float32)
    y_test = torch.tensor(y_test, dtype=torch.float32)

    train_data = TensorDataset(X_train, y_train)
    train_loader = DataLoader(
        train_data,
        batch_size=batch_size,
        shuffle=True
    )

    model = SolarEnergyNN(input_size=len(features))

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
                test_prediction = model(X_test)
                test_loss = loss_fn(test_prediction, y_test).item()

            print(
                f"Epoch {epoch:03d} | "
                f"Train Loss: {total_loss:.4f} | "
                f"Test Loss: {test_loss:.4f}"
            )

    torch.save(model.state_dict(), model_path)
    joblib.dump(scaler, scaler_path)

    print(f"Model saved to {model_path}")
    print(f"Scaler saved to {scaler_path}")

    return model