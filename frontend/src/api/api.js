const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

export async function getBestHouseOrientation(payload) {
    const response = await fetch(`${API_URL}/api/best-house-orientation`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        throw new Error("Failed to fetch prediction");
    }

    return response.json();
}