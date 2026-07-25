# ML Configurations for SuryaNet Feature Engineering and Baseline Models

FORECAST_HORIZON_MINUTES = 360  # 6 Hours lookahead

# Window sizes (in minutes) for rolling operations
ROLLING_WINDOWS = [15, 60]      # Rolling mean and variance windows
PEAK_WINDOWS = [30, 60]         # Rolling max/peak flux windows
GRADIENT_WINDOWS = [5, 15]      # First derivative windows
ACCELERATION_WINDOWS = [5, 15]  # Second derivative windows

# Maximum memory decay cap for minutes_since_last_flare
MAX_FLARE_DISTANCE_MINUTES = 10080  # 7 Days cap

# Flare classes to treat as positive events
# For large historical training runs, use: ["M", "X"]
# For local 7-day test database verification, use: ["C", "M", "X"]
TARGET_FLARE_CLASSES = ["M", "X"]

