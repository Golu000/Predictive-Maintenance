# routes.py

from flask import Blueprint, request, jsonify
import pandas as pd
from models import HotelMaintenanceModel
# --- START: Changes for multi-file handling ---
from config import UPLOAD_FOLDER, HOTEL_CSV_FILES # Import HOTEL_CSV_FILES
# --- END: Changes for multi-file handling ---

# Create a Blueprint for maintenance-related routes
maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')

# Instantiate the HotelMaintenanceModel globally for use across routes
hotel_maintenance_manager = HotelMaintenanceModel()

@maintenance_bp.route('/home')
def home():
    """Home endpoint to check if the server is running and display model status/metrics."""
    return jsonify({
        "message": "Hotel Maintenance Predictive Analysis API is running!",
        "model_status": hotel_maintenance_manager.get_model_status(),
        "training_data_status": hotel_maintenance_manager.get_data_status(),
        "last_trained_metrics": hotel_maintenance_manager.get_metrics()
    })


@maintenance_bp.route('/train', methods=['POST'])
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
            df = pd.read_csv(file)
            r2, mae, rmse = hotel_maintenance_manager.train_model(df)

            return jsonify({
                "message": "CSV data uploaded and hotel maintenance prediction model trained successfully!",
                "success": True,
                "recordsProcessed": len(df),
                "r2_score": round(r2, 4),
                "mean_absolute_error": round(mae, 4),
                "root_mean_squared_error": round(rmse, 4)
            }), 200

        except ValueError as ve:
            print(f"Validation error during hotel maintenance model training: {ve}")
            return jsonify({
                "message": f"Failed to upload data or train hotel maintenance prediction model: {str(ve)}",
                "success": False
            }), 400
        except Exception as e:
            print(f"Error during hotel maintenance model training: {e}")
            return jsonify({
                "message": f"Failed to upload data or train hotel maintenance prediction model: {str(e)}",
                "success": False
            }), 500
    else:
        return jsonify({"message": "Invalid file type. Please upload a CSV file.", "success": False}), 400


# --- START: New route for choosing hotel data file ---
@maintenance_bp.route('/choose-hotel-data', methods=['POST'])
def choose_hotel_data():
    """
    Endpoint to select which hotel's pre-processed CSV file should be loaded
    into the application for subsequent predictions and device information retrieval.
    This API does NOT retrain the model. It only updates the 'loaded_training_df'
    in the HotelMaintenanceModel instance. It also returns the count of 'working'
    devices in the loaded file.

    Expects JSON input with 'hotel_name'.
    Available hotel_names: 'fairfield', 'jw_marriott', 'westin'.
    Example JSON: {"hotel_name": "fairfield"}
    """
    data = request.get_json()
    if not data or 'hotel_name' not in data:
        return jsonify({"message": "Invalid JSON input. 'hotel_name' is required.", "success": False}), 400

    hotel_name = data.get('hotel_name').lower()

    try:
        # Call the new method in the HotelMaintenanceModel to load the data
        records_loaded, working_devices_count, loaded_file_path = hotel_maintenance_manager.load_hotel_data(hotel_name)

        return jsonify({
            "message": f"Data for '{hotel_name.title()}' loaded successfully for prediction and device info.",
            "loaded_file": loaded_file_path,
            "records_loaded": records_loaded,
            "working_devices_in_file": working_devices_count,
            "success": True
        }), 200
    except (ValueError, FileNotFoundError) as e:
        # Catch specific errors from load_hotel_data and return appropriate HTTP status
        print(f"Error choosing hotel data: {e}")
        return jsonify({
            "message": str(e),
            "success": False
        }), 400
    except Exception as e:
        # Catch any unexpected errors
        print(f"Unexpected error choosing hotel data: {e}")
        return jsonify({
            "message": f"Failed to load data for '{hotel_name.title()}': {str(e)}",
            "success": False
        }), 500
# --- END: New route for choosing hotel data file ---


@maintenance_bp.route('/search', methods=['POST'])
def predict_maintenance():
    """
    Endpoint to make predictions for devices in a given room for hotel maintenance.
    Expects JSON input with 'Room Number'.
    It will return the predicted 'Days Since Maintenance' for each device in that room,
    along with its 'Appliance Type', 'Last Maintenance Date', and the calculated
    'nextMaintenanceDate'.
    """
    try:
        data = request.get_json()
        if not data or 'Room Number' not in data:
            return jsonify({"message": "Invalid JSON input. 'Room Number' is required.", "success": False}), 400

        room_number = data.get('Room Number')

        if not isinstance(room_number, (int, float)):
            return jsonify({"message": "Room Number must be a number.", "success": False}), 400

        predictions = hotel_maintenance_manager.predict_for_room(int(room_number))

        if not predictions:
            return jsonify({
                "message": f"No devices found for Room Number: {room_number}",
                "predictions": [],
                "success": True
            }), 200

        return jsonify({
            "message": f"Predictions for Room Number {room_number} successful for hotel maintenance!",
            "predictions": predictions,
            "success": True
        }), 200

    except RuntimeError as re:
        print(f"Runtime error during prediction: {re}")
        return jsonify({
            "message": str(re),
            "predictions": [],
            "success": False
        }), 400
    except Exception as e:
        print(f"Error during prediction for room {room_number} for hotel maintenance: {e}")
        return jsonify({
            "message": f"Failed to make predictions for hotel maintenance: {str(e)}",
            "predictions": [],
            "success": False
        }), 500


@maintenance_bp.route('/device/info', methods=['GET'])
def get_device_info():
    """
    Endpoint to return device information dynamically based on room_no and appliance_type from
    the loaded training data, including predicted next maintenance date and warranty info.
    Expects 'room_no' and 'appliance_type' as query parameters.
    Example: /maintenance/device/info?room_no=2000&appliance_type=Television
    """
    room_no = request.args.get('room_no', type=int)
    appliance_type = request.args.get('appliance_type')

    if room_no is None or appliance_type is None:
        return jsonify({
            "message": "Missing 'room_no' or 'appliance_type' query parameters.",
            "success": False
        }), 400

    try:
        device_info = hotel_maintenance_manager.get_device_details(room_no, appliance_type)

        if not device_info:
            return jsonify({
                "message": f"Device with Room Number {room_no} and Appliance Type '{appliance_type}' not found.",
                "success": False
            }), 404

        return jsonify(device_info), 200

    except RuntimeError as re:
        print(f"Runtime error getting device info: {re}")
        return jsonify({
            "message": str(re),
            "success": False
        }), 400
    except Exception as e:
        print(f"Error retrieving device info: {e}")
        return jsonify({
            "message": f"Failed to retrieve device info: {str(e)}",
            "success": False
        }), 500


@maintenance_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """
    Endpoint to retrieve dashboard-level insights for hotel appliance maintenance.
    Returns statistics like total devices, devices due for maintenance, and pending maintenance list.
    """
    try:
        dashboard_data = hotel_maintenance_manager.get_dashboard_insights()

        if "message" in dashboard_data: # If model or data not loaded, the method returns a dict with message
             return jsonify(dashboard_data), 400

        # Extract the loaded_data_file from dashboard_data
        loaded_file_name = dashboard_data.get("loaded_data_file", "N/A")

        return jsonify({
            "smartOperations": dashboard_data,
            "loaded_data_file": loaded_file_name  # Include it at the top level for convenience
        }), 200

    except Exception as e:
        print(f"Error generating dashboard data: {e}")
        return jsonify({
            "message": f"Failed to generate dashboard data: {str(e)}",
            "smartOperations": {}
        }), 500


@maintenance_bp.route('/upcoming-maintenance', methods=['GET'])
def get_upcoming_maintenance():
    """
    Endpoint to retrieve a list of devices that have upcoming maintenance (nextMaintenanceDate > current date).
    """
    try:
        upcoming_devices = hotel_maintenance_manager.get_upcoming_maintenance_devices()

        if not upcoming_devices:
            return jsonify({
                "message": "No devices found with upcoming maintenance.",
                "upcoming_maintenance_devices": [],
                "success": True
            }), 200

        return jsonify({
            "message": "Successfully retrieved devices with upcoming maintenance.",
            "upcoming_maintenance_devices": upcoming_devices,
            "success": True
        }), 200

    except RuntimeError as re:
        print(f"Runtime error getting upcoming maintenance devices: {re}")
        return jsonify({
            "message": str(re),
            "upcoming_maintenance_devices": [],
            "success": False
        }), 400
    except Exception as e:
        print(f"Error retrieving upcoming maintenance devices: {e}")
        return jsonify({
            "message": f"Failed to retrieve upcoming maintenance devices: {str(e)}",
            "upcoming_maintenance_devices": [],
            "success": False
        }), 500


@maintenance_bp.route('/upcoming-weekly-maintenance', methods=['GET'])
def get_weekly_maintenance():
    """
    Endpoint to retrieve a list of devices that have upcoming maintenance (nextMaintenanceDate > current date).
    """
    try:
        weekly_devices = hotel_maintenance_manager.get_current_week_maintenance_devices()

        if not weekly_devices:
            return jsonify({
                "message": "No devices found for current week maintenance.",
                "weekly_devices": [],
                "success": True
            }), 200

        return jsonify({
            "message": "Successfully retrieved devices for current week maintenance.",
            "weekly_devices": weekly_devices,
            "success": True
        }), 200

    except RuntimeError as re:
        print(f"Runtime error getting current week maintenance devices: {re}")
        return jsonify({
            "message": str(re),
            "weekly_devices": [],
            "success": False
        }), 400
    except Exception as e:
        print(f"Error retrieving current week maintenance devices: {e}")
        return jsonify({
            "message": f"Failed to retrieve current week maintenance devices: {str(e)}",
            "weekly_devices": [],
            "success": False
        }), 500


@maintenance_bp.route('/non-room-data', methods=['GET'])
def non_room_data():
    """
    Endpoint to select which hotel's pre-processed CSV file should be loaded
    into the application for subsequent predictions and device information retrieval.
    This API does NOT retrain the model. It only updates the 'loaded_training_df'
    in the HotelMaintenanceModel instance. It also returns the count of 'working'
    devices in the loaded file.

    Expects JSON input with 'hotel_name'.
    Available hotel_names: 'fairfield', 'jw_marriott', 'westin'.
    Example JSON: {"hotel_name": "fairfield"}
    """
    # data = request.get_json()
    # if not data or 'hotel_name' not in data:
    #     return jsonify({"message": "Invalid JSON input. 'hotel_name' is required.", "success": False}), 400
    #
    # hotel_name = data.get('hotel_name').lower()

    try:
        # Call the new method in the HotelMaintenanceModel to load the data
        non_room_maintenance = hotel_maintenance_manager.load_non_room_data()

        if not non_room_maintenance:
            return jsonify({
                "message": "No devices found for non room maintenance.",
                "non_room_maintenance": [],
                "success": True
            }), 200

        return jsonify({
            "message": "Successfully retrieved devices for non room maintenance.",
            "non_room_maintenance": non_room_maintenance,
            "success": True
        }), 200

    except RuntimeError as re:
        print(f"Runtime error getting  non room devices: {re}")
        return jsonify({
            "message": str(re),
            "non_room_maintenance": [],
            "success": False
        }), 400
    except Exception as e:
        print(f"Error retrieving non room devices: {e}")
        return jsonify({
            "message": f"Failed to retrieve non room maintenance devices: {str(e)}",
            "non_room_maintenance": [],
            "success": False
        }), 500