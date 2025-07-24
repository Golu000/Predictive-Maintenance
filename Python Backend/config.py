# config.py

import os

# Define paths for data and model storage
UPLOAD_FOLDER = 'data'
MODEL_FOLDER = 'model'
MODEL_FILENAME = 'hotel_maintenance_model.joblib'
DATA_FILENAME = 'hotel_training_data.pkl'

MODEL_PATH = os.path.join(MODEL_FOLDER, MODEL_FILENAME)
DATA_PATH = os.path.join(MODEL_FOLDER, DATA_FILENAME)

# --- START: Changes for multi-file handling ---
# Define paths to the pre-processed updated CSV files for different hotels
# These files are assumed to be in the same directory as your app or provide their full path
HOTEL_CSV_FILES = {
    'fairfield': 'FairField.csv',
    'jwmarriott': 'JW Marriott.csv',
    'westin': 'Westin.csv'
}

NON_ROOM_DATA = 'non-room-hotel.csv'

# --- END: Changes for multi-file handling ---

# Ensure upload and model folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODEL_FOLDER, exist_ok=True)
