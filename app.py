# app.py
from flask import Flask, request, jsonify
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor  # Changed from LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error  # Import accuracy metrics
import numpy as np  # Needed for sqrt for RMSE
import joblib
import os
from datetime import datetime, timedelta  # Import datetime and timedelta for date calculations

app = Flask(__name__)

# Define paths for data and model storage
UPLOAD_FOLDER = 'data'
MODEL_FOLDER = 'model'
# Renamed model and data paths to reflect 'hotel_maintenance'
MODEL_PATH = os.path.join(MODEL_FOLDER, 'hotel_maintenance_model.joblib')
DATA_PATH = os.path.join(MODEL_FOLDER, 'hotel_training_data.pkl')  # Path to save processed DataFrame

# Ensure upload and model folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODEL_FOLDER, exist_ok=True)

# Global variables to hold the trained model and the last loaded training data, and metrics
hotel_model = None  # Renamed from ac_model to hotel_model
loaded_training_df = pd.DataFrame()
# Store metrics globally so they can be displayed by other endpoints (e.g., home)
model_metrics = {
    "r2_score": None,
    "mae": None,
    "rmse": None
}


# Function to load the model and data on application startup
def load_persisted_data():
    global hotel_model  # Referencing hotel_model
    global loaded_training_df
    global model_metrics

    # Load model
    if os.path.exists(MODEL_PATH):
        try:
            hotel_model = joblib.load(MODEL_PATH)  # Loading hotel_model
            print(f"Hotel maintenance model loaded successfully from {MODEL_PATH}")
        except Exception as e:
            print(f"Error loading hotel maintenance model from {MODEL_PATH}: {e}")
            hotel_model = None
    else:
        print("No pre-existing hotel maintenance model found.")

    # Load training data DataFrame
    if os.path.exists(DATA_PATH):
        try:
            loaded_training_df = pd.read_pickle(DATA_PATH)
            print(f"Training data for hotel maintenance loaded successfully from {DATA_PATH}")
            # If the model and data are loaded, recalculate metrics for display on '/'
            if hotel_model is not None and not loaded_training_df.empty:
                features = ['Usage Hours', 'Average_Daily_Usage', 'Device_Year']
                target = 'Days Since Maintenance'
                # Ensure the loaded data still has the required columns before recalculating metrics
                if all(col in loaded_training_df.columns for col in features + [target]):
                    X = loaded_training_df[features]
                    y = loaded_training_df[target]
                    y_pred = hotel_model.predict(X)  # Using hotel_model for prediction
                    model_metrics["r2_score"] = r2_score(y, y_pred)
                    model_metrics["mae"] = mean_absolute_error(y, y_pred)
                    model_metrics["rmse"] = np.sqrt(mean_squared_error(y, y_pred))
                    print("Recalculated metrics for loaded hotel model/data.")
        except Exception as e:
            print(f"Error loading training data for hotel maintenance from {DATA_PATH}: {e}")
            loaded_training_df = pd.DataFrame()
    else:
        print("No pre-existing training data for hotel maintenance found.")


# Call load_persisted_data when the application starts
with app.app_context():
    load_persisted_data()


@app.route('/')
def home():
    """Home endpoint to check if the server is running and display model status/metrics."""
    model_status = "Trained" if hotel_model is not None else "Not Trained"  # Referencing hotel_model
    data_status = "Loaded" if not loaded_training_df.empty else "Not Loaded"

    # Format metrics for display
    r2_display = f"{model_metrics['r2_score']:.4f}" if model_metrics['r2_score'] is not None else "N/A"
    mae_display = f"{model_metrics['mae']:.4f}" if model_metrics['mae'] is not None else "N/A"
    rmse_display = f"{model_metrics['rmse']:.4f}" if model_metrics['rmse'] is not None else "N/A"

    return jsonify({
        "message": "Hotel Maintenance Predictive Analysis API is running!",  # Updated message
        "model_status": model_status,
        "training_data_status": data_status,
        "last_trained_metrics": {
            "r2_score": r2_display,
            "mean_absolute_error": mae_display,
            "root_mean_squared_error": rmse_display
        }
    })


@app.route('/maintenance/train', methods=['POST'])
def train_model():
    """
    Endpoint to upload a CSV file and train the predictive maintenance model for hotel appliances.
    The CSV should contain 'Room Number', 'Appliance Type', 'Last Maintenance Date',
    'Usage Hours', 'Days Since Maintenance', 'Average_Daily_Usage', 'Device_Year' columns for training.
    The target variable for prediction will be 'Days Since Maintenance'.
    This function also calculates and returns accuracy metrics (R-squared, MAE, RMSE).
    """
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request", "success": False}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file", "success": False}), 400

    if file and file.filename.endswith('.csv'):
        try:
            # Read CSV directly into a pandas DataFrame
            df = pd.read_csv(file)

            # Define features (X) and target (y) based on the CSV structure for hotel maintenance
            features = ['Usage Hours', 'Average_Daily_Usage', 'Device_Year']
            target = 'Days Since Maintenance'

            # Essential columns for lookup later
            required_lookup_cols = ['Room Number', 'Appliance Type', 'Last Maintenance Date']

            # Validate that all required columns are present in the uploaded CSV
            if not all(col in df.columns for col in features + [target] + required_lookup_cols):
                missing_cols = [col for col in features + [target] + required_lookup_cols if col not in df.columns]
                return jsonify({
                    "message": f"Missing required columns in CSV: {', '.join(missing_cols)}",
                    "success": False
                }), 400

            X = df[features]
            y = df[target]

            # Initialize and train the Gradient Boosting Regressor model
            global hotel_model  # Referencing hotel_model
            hotel_model = GradientBoostingRegressor(random_state=42)  # Added random_state for reproducibility
            hotel_model.fit(X, y)

            # --- Accuracy Calculation ---
            # Make predictions on the training data to calculate metrics
            y_pred = hotel_model.predict(X)  # Using hotel_model for prediction

            # Calculate R-squared score
            r2 = r2_score(y, y_pred)
            # Calculate Mean Absolute Error
            mae = mean_absolute_error(y, y_pred)
            # Calculate Mean Squared Error and Root Mean Squared Error
            mse = mean_squared_error(y, y_pred)
            rmse = np.sqrt(mse)

            # Store metrics globally
            global model_metrics
            model_metrics["r2_score"] = r2
            model_metrics["mae"] = mae
            model_metrics["rmse"] = rmse
            # --- End Accuracy Calculation ---

            # Save the trained model to disk for persistence
            joblib.dump(hotel_model, MODEL_PATH)  # Saving hotel_model

            # Store the full DataFrame for lookup in prediction endpoint
            global loaded_training_df
            loaded_training_df = df.copy()  # Make a copy to avoid modifying original df
            loaded_training_df.to_pickle(DATA_PATH)  # Saving hotel_training_data.pkl

            # Print coefficients and metrics for understanding the trained model
            print("\nHotel maintenance model trained successfully!")  # Updated message
            # For GradientBoostingRegressor, there is no simple 'intercept_' or 'coef_' like LinearRegression.
            # You can inspect feature importances if needed:
            # print("Feature Importances:", dict(zip(features, hotel_model.feature_importances_)))

            print(f"R-squared (Accuracy): {r2 * 100:.2f}%")  # Changed to percentage
            print(f"Mean Absolute Error (MAE): {mae:.4f} days")
            print(f"Root Mean Squared Error (RMSE): {rmse:.4f} days")
            print(f"Training data saved to {DATA_PATH}")

            return jsonify({
                "message": "CSV data uploaded and hotel maintenance prediction model trained successfully!",
                # Updated message
                "success": True,
                "recordsProcessed": len(df),
                "r2_score": round(r2, 4),
                "mean_absolute_error": round(mae, 4),
                "root_mean_squared_error": round(rmse, 4)
            }), 200

        except Exception as e:
            print(f"Error during hotel maintenance model training: {e}")  # Updated message
            return jsonify({
                "message": f"Failed to upload data or train hotel maintenance prediction model: {str(e)}",
                # Updated message
                "success": False
            }), 500
    else:
        return jsonify({"message": "Invalid file type. Please upload a CSV file.", "success": False}), 400


@app.route('/maintenance/predict', methods=['POST'])
def predict_maintenance():
    """
    Endpoint to make predictions for devices in a given room for hotel maintenance.
    Expects JSON input with 'Room Number'.
    It will return the predicted 'Days Since Maintenance' for each device in that room,
    along with its 'Appliance Type', 'Last Maintenance Date', and the calculated
    'nextMaintenanceDate'.
    """
    global hotel_model  # Referencing hotel_model
    global loaded_training_df

    if hotel_model is None or loaded_training_df.empty:  # Referencing hotel_model
        return jsonify({
            "message": "Hotel maintenance prediction model or training data not loaded. Please upload a CSV dataset first.",
            # Updated message
            "predictions": [],
            "success": False
        }), 400

    try:
        data = request.get_json()
        if not data or 'Room Number' not in data:
            return jsonify({"message": "Invalid JSON input. 'Room Number' is required.", "success": False}), 400

        room_number = data.get('Room Number')

        if not isinstance(room_number, (int, float)):
            return jsonify({"message": "Room Number must be a number.", "success": False}), 400

        # Filter the loaded training data for the given room number
        room_devices_df = loaded_training_df[loaded_training_df['Room Number'] == room_number].copy()

        if room_devices_df.empty:
            return jsonify({
                "message": f"No devices found for Room Number: {room_number}",
                "predictions": [],
                "success": True  # This is a successful lookup, even if no devices found
            }), 200

        # Define features for prediction (same as used in training)
        features_for_prediction = ['Usage Hours', 'Average_Daily_Usage', 'Device_Year']

        results = []
        # Iterate over each device in the filtered DataFrame
        for index, row in room_devices_df.iterrows():
            # Extract features for the current device (row)
            # Ensure it's a 2D array (DataFrame with one row) for model.predict
            current_device_features = pd.DataFrame([row[features_for_prediction].values],
                                                   columns=features_for_prediction)

            # Make prediction for this single device
            predicted_days_since = hotel_model.predict(current_device_features)[0]  # Using hotel_model for prediction

            # Ensure prediction is non-negative
            predicted_days_since = max(0, predicted_days_since)

            # --- Calculate Next Maintenance Date ---
            last_maint_date_str = row['Last Maintenance Date']
            next_maint_date = "N/A"  # Default in case of parsing error
            try:
                # Parse the date string (e.g., "8/29/2024" or "08/29/24")
                # Using multiple formats for robustness
                # Try MM/DD/YYYY first, then MM/DD/YY
                parsed_date = None
                for fmt in ('%m/%d/%Y', '%m/%d/%y'):
                    try:
                        parsed_date = datetime.strptime(last_maint_date_str, fmt)
                        break  # Found a matching format, exit loop
                    except ValueError:
                        pass  # Try next format

                if parsed_date:
                    # Add the predicted days to the last maintenance date
                    calculated_next_date = parsed_date + timedelta(days=predicted_days_since)
                    # Format it back to a string in a consistent YYYY format
                    next_maint_date = calculated_next_date.strftime('%m/%d/%Y')
                else:
                    print(f"Warning: No matching date format found for '{last_maint_date_str}'")

            except Exception as e:  # Catch general exceptions during date calculation
                print(f"Error parsing date or calculating next maintenance date for '{last_maint_date_str}': {e}")
            # --- End Calculate Next Maintenance Date ---

            results.append({
                "roomNumber": row['Room Number'],
                "applianceType": row['Appliance Type'],
                "lastMaintenanceDate": row['Last Maintenance Date'],
                "predictedDaysSinceMaintenance": round(predicted_days_since, 2),
                "nextMaintenanceDate": next_maint_date  # New property
            })

        return jsonify({
            "message": f"Predictions for Room Number {room_number} successful for hotel maintenance!",
            # Updated message
            "predictions": results,
            "success": True
        }), 200

    except Exception as e:
        print(f"Error during prediction for room {room_number} for hotel maintenance: {e}")  # Updated message
        return jsonify({
            "message": f"Failed to make predictions for hotel maintenance: {str(e)}",  # Updated message
            "predictions": [],
            "success": False
        }), 500


if __name__ == '__main__':
    # Run the Flask app. For production, use a production-ready WSGI server like Gunicorn or uWSGI.
    app.run(debug=True, port=8080)
