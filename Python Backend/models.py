# models.py

import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import numpy as np
import joblib
import os
from datetime import datetime, timedelta
from config import HOTEL_CSV_FILES, NON_ROOM_DATA
from config import MODEL_PATH, DATA_PATH

class HotelMaintenanceModel:
    """
    Manages the hotel maintenance prediction model, including loading, training,
    prediction, and storing associated data and metrics.
    """
    def __init__(self):
        self.hotel_model = None
        self.loaded_training_df = pd.DataFrame()
        self.model_metrics = {
            "r2_score": None,
            "mae": None,
            "rmse": None
        }
        self._load_persisted_data()

    def _load_persisted_data(self):
        """
        Loads the trained model and training data from disk on initialization.
        Recalculates metrics if both model and data are present.
        """
        # Load model
        if os.path.exists(MODEL_PATH):
            try:
                self.hotel_model = joblib.load(MODEL_PATH)
                print(f"Hotel maintenance model loaded successfully from {MODEL_PATH}")
            except Exception as e:
                print(f"Error loading hotel maintenance model from {MODEL_PATH}: {e}")
                self.hotel_model = None
        else:
            print("No pre-existing hotel maintenance model found.")

        # Load training data DataFrame
        if os.path.exists(DATA_PATH):
            try:
                self.loaded_training_df = pd.read_pickle(DATA_PATH)
                print(f"Training data for hotel maintenance loaded successfully from {DATA_PATH}")
                # If the model and data are loaded, recalculate metrics
                if self.hotel_model is not None and not self.loaded_training_df.empty:
                    features = ['Usage Hours', 'Average_Daily_Usage', 'Device_Year']
                    target = 'Days Since Maintenance'
                    # Ensure the loaded data still has the required columns
                    if all(col in self.loaded_training_df.columns for col in features + [target]):
                        X = self.loaded_training_df[features]
                        y = self.loaded_training_df[target]
                        y_pred = self.hotel_model.predict(X)
                        self.model_metrics["r2_score"] = r2_score(y, y_pred)
                        self.model_metrics["mae"] = mean_absolute_error(y, y_pred)
                        self.model_metrics["rmse"] = np.sqrt(mean_squared_error(y, y_pred))
                        print("Recalculated metrics for loaded hotel model/data.")
            except Exception as e:
                print(f"Error loading training data for hotel maintenance from {DATA_PATH}: {e}")
                self.loaded_training_df = pd.DataFrame()
        else:
            print("No pre-existing training data for hotel maintenance found.")

    def train_model(self, df: pd.DataFrame):
        """
        Trains the Gradient Boosting Regressor model using the provided DataFrame.
        Saves the model and the processed DataFrame, and updates performance metrics.

        Args:
            df (pd.DataFrame): The input DataFrame containing training data.
        """
        features = ['Usage Hours', 'Average_Daily_Usage', 'Device_Year']
        target = 'Days Since Maintenance'
        required_lookup_cols = ['Room Number', 'Appliance Type', 'Last Maintenance Date', 'Status', 'Warranty Year']

        # Validate that all required columns are present
        if not all(col in df.columns for col in features + [target] + required_lookup_cols):
            missing_cols = [col for col in features + [target] + required_lookup_cols if col not in df.columns]
            raise ValueError(f"Missing required columns in CSV: {', '.join(missing_cols)}")

        # Ensure 'Status' column is not null; fill with 'Unknown' if NaN
        df['Status'] = df['Status'].fillna('Unknown')
        # Ensure 'Warranty Year' column exists and is handled
        if 'Warranty Year' not in df.columns:
            df['Warranty Year'] = np.nan

        X = df[features]
        y = df[target]

        # Initialize and train the Gradient Boosting Regressor model
        self.hotel_model = GradientBoostingRegressor(random_state=42)
        self.hotel_model.fit(X, y)

        # Accuracy Calculation
        y_pred = self.hotel_model.predict(X)
        r2 = r2_score(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))

        # Store metrics
        self.model_metrics["r2_score"] = r2
        self.model_metrics["mae"] = mae
        self.model_metrics["rmse"] = rmse

        # Save the trained model and the full DataFrame
        joblib.dump(self.hotel_model, MODEL_PATH)
        self.loaded_training_df = df.copy()
        self.loaded_training_df.to_pickle(DATA_PATH)

        print("\nHotel maintenance model trained successfully!")
        print(f"R-squared (Accuracy): {r2 * 100:.2f}%")
        print(f"Mean Absolute Error (MAE): {mae:.4f} days")
        print(f"Root Mean Squared Error (RMSE): {rmse:.4f} days")
        print(f"Training data saved to {DATA_PATH}")

        return r2, mae, rmse

    def predict_for_room(self, room_number: int) -> list:
        """
        Makes predictions for all devices in a specified room number.

        Args:
            room_number (int): The room number to predict for.

        Returns:
            list: A list of dictionaries, each containing prediction details for a device.
        """
        if self.hotel_model is None or self.loaded_training_df.empty:
            raise RuntimeError("Model or training data not loaded.")

        # Filter for devices in the specified room
        room_devices_df = self.loaded_training_df[self.loaded_training_df['Room Number'] == room_number].copy()

        if room_devices_df.empty:
            return []

        # --- MODIFIED FIX FOR DUPLICATE APPLIANCES (KEEPING ONLY ONE PER DEVICE NAME) ---

        # Convert 'Last Maintenance Date' to datetime objects for proper sorting if not already
        # This handles cases where dates might be mixed types or not yet converted.
        def parse_date(date_str):
            if pd.isna(date_str):
                return pd.NaT  # Not a Time, for missing dates
            for fmt in ('%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%d/%m/%y'):
                try:
                    return datetime.strptime(str(date_str), fmt)
                except ValueError:
                    pass
            # If no format matches, return NaT or handle as an error
            print(f"Warning: Could not parse date '{date_str}'.")
            return pd.NaT

        # Apply the parsing function and handle errors
        room_devices_df['Parsed_Maintenance_Date'] = room_devices_df['Last Maintenance Date'].apply(parse_date)

        # Sort the DataFrame. We want to keep the most recent entry for each Appliance Type.
        # So, sort by 'Parsed_Maintenance_Date' in descending order.
        room_devices_df.sort_values(by='Parsed_Maintenance_Date', ascending=False, inplace=True)

        # Remove duplicate device entries based ONLY on 'Appliance Type'.
        # 'keep='first'' will now retain the entry with the most recent 'Last Maintenance Date'
        # due to the preceding sort.
        room_devices_df.drop_duplicates(subset=['Appliance Type'], keep='first', inplace=True)

        # --- END OF MODIFIED FIX ---

        features_for_prediction = ['Usage Hours', 'Average_Daily_Usage', 'Device_Year']
        results = []

        for index, row in room_devices_df.iterrows():
            current_device_features = pd.DataFrame([row[features_for_prediction].values],
                                                   columns=features_for_prediction)
            predicted_days_since = self.hotel_model.predict(current_device_features)[0]
            predicted_days_since = max(0, predicted_days_since)

            # Use the already parsed date object
            parsed_date_obj = row['Parsed_Maintenance_Date']
            next_maint_date = "N/A"

            if pd.notna(parsed_date_obj):  # Check if the parsed date is valid
                calculated_next_date = parsed_date_obj + timedelta(days=predicted_days_since)
                next_maint_date = calculated_next_date.strftime('%Y-%m-%d')
            else:
                # The warning for unparsable dates is already given during the .apply() step
                pass

            current_year = datetime.now().year
            under_warranty = "no"
            warranty_year_till = row.get('Warranty Year')
            if pd.notna(warranty_year_till) and int(warranty_year_till) >= current_year:
                under_warranty = "yes"

            issue_reported = row['Status'] if pd.notna(row.get('Status')) else "None"
            previous_maintenance_date = parsed_date_obj.strftime('%Y-%m-%d') if pd.notna(parsed_date_obj) else "N/A"

            results.append({
                "device_id": index + 1 ,
                "roomNumber": row['Room Number'],
                "deviceName": row['Appliance Type'],
                "issueReported": issue_reported,
                "deviceYear": str(int(row['Device_Year'])) if pd.notna(row['Device_Year']) else "N/A",
                "under_warranty": under_warranty,
                "warranty_year_till": str(int(warranty_year_till)) if pd.notna(warranty_year_till) else "N/A",
                "previous_maintenance_date": previous_maintenance_date,
                "predictedDaysSinceMaintenance": round(predicted_days_since, 2),
                "nextMaintenanceDate": next_maint_date
            })
        return results

    def get_device_details(self, room_no: int, appliance_type: str) -> dict:
        """
        Retrieves detailed information for a specific device, including predicted next maintenance.

        Args:
            room_no (int): The room number of the device.
            appliance_type (str): The type of appliance.

        Returns:
            dict: A dictionary containing the device's information.
        """
        if self.loaded_training_df.empty:
            raise RuntimeError("Training data not loaded.")
        if self.hotel_model is None:
            raise RuntimeError("Predictive maintenance model not trained.")

        device_data = self.loaded_training_df[
            (self.loaded_training_df['Room Number'] == room_no) &
            (self.loaded_training_df['Appliance Type'] == appliance_type)
        ]

        if device_data.empty:
            return {} # Indicate not found

        device = device_data.iloc[0]

        features_for_prediction = ['Usage Hours', 'Average_Daily_Usage', 'Device_Year']
        current_device_features = pd.DataFrame([device[features_for_prediction].values],
                                               columns=features_for_prediction)
        predicted_days_since = self.hotel_model.predict(current_device_features)[0]
        predicted_days_since = max(0, predicted_days_since)

        last_maint_date_str = device['Last Maintenance Date']
        next_maint_date = "N/A"
        parsed_date_obj = None

        for fmt in ('%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%d/%m/%y'):
            try:
                parsed_date_obj = datetime.strptime(last_maint_date_str, fmt)
                break
            except ValueError:
                pass

        if parsed_date_obj:
            calculated_next_date = parsed_date_obj + timedelta(days=predicted_days_since)
            next_maint_date = calculated_next_date.strftime('%Y-%m-%d')
        else:
            print(f"Warning: No matching date format found for '{last_maint_date_str}'")

        current_year = datetime.now().year
        under_warranty = "No"
        warranty_year_till = device['Warranty Year']
        if pd.notna(device['Warranty Year']) and device['Warranty Year'] >= current_year:
            under_warranty = "Yes"

        issue_reported = device['Status'] if pd.notna(device['Status']) else "None"
        previous_maintenance_date = parsed_date_obj.strftime('%Y-%m-%d') if parsed_date_obj else "N/A"


        device_info = {
            "room_no": int(device['Room Number']),
            "device_id": int(device_data.index[0] + 1),
            "device_name": device['Appliance Type'],
            "issue_reported": issue_reported,
            "device_year": str(int(device['Device_Year'])) if pd.notna(device['Device_Year']) else "N/A",
            "under_warranty": under_warranty,
            "warranty_year_till": str(int(warranty_year_till)) if pd.notna(warranty_year_till) else "N/A",
            "previous_maintenance_date": previous_maintenance_date,
            "next_maintenance_date": next_maint_date
        }
        return device_info

    def get_dashboard_insights(self) -> dict:
        """
        Retrieves dashboard-level insights for hotel appliance maintenance.
        Calculates total devices (unique room number with appliance type),
        running, down, due for maintenance, and pending maintenance list (based on all records).

        Returns:
            dict: A dictionary containing various dashboard statistics.
        """
        if self.hotel_model is None or self.loaded_training_df.empty:
            return {
                "message": "Model or training data not loaded.",
                "smartOperations": {}
            }

        # --- MODIFICATION START: Calculate total_devices as unique (Room Number, Appliance Type) ---
        # Create a temporary DataFrame to calculate unique devices without altering the main DataFrame
        temp_unique_devices_df = self.loaded_training_df[['Room Number', 'Appliance Type']].drop_duplicates()
        total_devices = len(temp_unique_devices_df)
        # --- MODIFICATION END ---

        # The rest of the calculations remain based on the original self.loaded_training_df
        if 'Status' in self.loaded_training_df.columns:
            running_devices = self.loaded_training_df[self.loaded_training_df['Status'].astype(str).str.contains('Working', case=False, na=False)].shape[0]
        else:
            running_devices = 0

        down_devices = len(self.loaded_training_df) - running_devices # Still based on total records, not unique conceptual devices

        due_maintenance_count = 0
        pending_maintenance_list = []
        features_for_prediction = ['Usage Hours', 'Average_Daily_Usage', 'Device_Year']
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for index, row in self.loaded_training_df.iterrows():
            current_device_features = pd.DataFrame([row[features_for_prediction].values],
                                                   columns=features_for_prediction)
            predicted_days_since = self.hotel_model.predict(current_device_features)[0]
            predicted_days_since = max(0, predicted_days_since)

            last_maint_date_str = str(row['Last Maintenance Date'])
            next_maint_date_formatted = "N/A"
            next_maint_date_obj = None

            date_formats = ['%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%d/%m/%y']
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(last_maint_date_str, fmt)
                    calculated_next_date = parsed_date + timedelta(days=predicted_days_since)
                    next_maint_date_formatted = calculated_next_date.strftime('%Y-%m-%d') # Changed to YYYY-MM-DD for consistency
                    next_maint_date_obj = calculated_next_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    break
                except (ValueError, TypeError): # Added TypeError for robustness with pd.NaT etc.
                    pass

            if next_maint_date_obj and next_maint_date_obj <= today:
                due_maintenance_count += 1
                pending_maintenance_list.append({
                    "room_no": row['Room Number'],
                    "device_id": index + 1, # Remains based on original DataFrame index
                    "device_name": row['Appliance Type'],
                    "maintenance_date": next_maint_date_formatted
                })

        # 'under_maintenance_devices' calculation remains as before
        under_maintenance_devices = max(0, down_devices - due_maintenance_count)

        dashboard_data = {
            "total_devices": total_devices,
            "running": running_devices,
            "down": down_devices,
            "due_maintenance": due_maintenance_count,
            "under_maintenance": under_maintenance_devices,
            "Pending_maintenance": pending_maintenance_list,
            "loaded_data_file": self.loaded_file_path
        }
        return dashboard_data

    def get_upcoming_maintenance_devices(self) -> list:
        """
        Retrieves a list of devices that have upcoming maintenance (nextMaintenanceDate > current date).

        Returns:
            list: A list of dictionaries, each representing a device with upcoming maintenance.
        """
        if self.hotel_model is None or self.loaded_training_df.empty:
            raise RuntimeError("Model or training data not loaded.")

        upcoming_maintenance_list = []
        features_for_prediction = ['Usage Hours', 'Average_Daily_Usage', 'Device_Year']
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Using 182 days as an approximation for 6 months
        six_months_from_now = today + timedelta(days=182)

        for index, row in self.loaded_training_df.iterrows():
            current_device_features = pd.DataFrame([row[features_for_prediction].values],
                                                   columns=features_for_prediction)
            predicted_days_since = self.hotel_model.predict(current_device_features)[0]
            predicted_days_since = max(0, predicted_days_since)

            last_maint_date_str = row['Last Maintenance Date']
            next_maint_date_formatted = "N/A"
            next_maint_date_obj = None

            date_formats = ['%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%d/%m/%y']
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(last_maint_date_str, fmt)
                    calculated_next_date = parsed_date + timedelta(days=predicted_days_since)
                    next_maint_date_formatted = calculated_next_date.strftime('%Y-%m-%d') # Standard format
                    next_maint_date_obj = calculated_next_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    break
                except ValueError:
                    pass

            # Check if maintenance is in the future
            if next_maint_date_obj and today < next_maint_date_obj <= six_months_from_now:
                # Determine warranty status
                current_year = datetime.now().year
                under_warranty = "no"
                warranty_year_till = row['Warranty Year']
                if pd.notna(row['Warranty Year']) and row['Warranty Year'] >= current_year:
                    under_warranty = "yes"

                issue_reported = row['Status'] if pd.notna(row['Status']) else "None"
                previous_maintenance_date = parsed_date.strftime('%Y-%m-%d') if parsed_date else "N/A"

                upcoming_maintenance_list.append({
                    "room_no": row['Room Number'],
                    "device_id": index + 1,
                    "device_name": row['Appliance Type'],
                    "issue_reported": issue_reported,
                    "device_year": str(int(row['Device_Year'])) if pd.notna(row['Device_Year']) else "N/A",
                    "under_warranty": under_warranty,
                    "warranty_year_till": str(int(warranty_year_till)) if pd.notna(warranty_year_till) else "N/A",
                    "previous_maintenance_date": previous_maintenance_date,
                    "predictedDaysSinceMaintenance": round(predicted_days_since, 2),
                    "next_maintenance_date": next_maint_date_formatted
                })
        return upcoming_maintenance_list

    def get_current_week_maintenance_devices(self) -> list:
        """
        Retrieves a list of devices that have upcoming maintenance within the current week.

        Returns:
            list: A list of dictionaries, each representing a device with upcoming maintenance.
        """
        if self.hotel_model is None or self.loaded_training_df.empty:
            raise RuntimeError("Model or training data not loaded.")

        upcoming_maintenance_list = []
        features_for_prediction = ['Usage Hours', 'Average_Daily_Usage', 'Device_Year']
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Calculate the start and end of the current week
        # Monday is 0, Sunday is 6
        start_of_current_week = today - timedelta(days=today.weekday())
        end_of_current_week = start_of_current_week + timedelta(days=6)

        for index, row in self.loaded_training_df.iterrows():
            current_device_features = pd.DataFrame([row[features_for_prediction].values],
                                                   columns=features_for_prediction)

            # Ensure features are numeric, handle potential non-numeric values
            for feature in features_for_prediction:
                if pd.api.types.is_numeric_dtype(current_device_features[feature]):
                    current_device_features[feature] = pd.to_numeric(current_device_features[feature], errors='coerce')
                else:
                    # Handle non-numeric features if necessary, e.g., fill with median/mean or drop
                    # For now, we'll assume the model can handle NaNs or they are pre-processed.
                    pass

                    # Drop rows with NaN in features_for_prediction before prediction
            current_device_features = current_device_features.dropna(subset=features_for_prediction)

            if current_device_features.empty:
                print(f"Skipping row {index} due to missing/invalid features for prediction.")
                continue

            predicted_days_since = self.hotel_model.predict(current_device_features)[0]
            predicted_days_since = max(0, predicted_days_since)  # Ensure non-negative days

            last_maint_date_str = str(row['Last Maintenance Date'])  # Ensure it's a string for parsing
            next_maint_date_formatted = "N/A"
            next_maint_date_obj = None

            date_formats = ['%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%d/%m/%y']
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(last_maint_date_str, fmt)
                    calculated_next_date = parsed_date + timedelta(days=predicted_days_since)
                    next_maint_date_formatted = calculated_next_date.strftime('%Y-%m-%d')  # Standard format
                    next_maint_date_obj = calculated_next_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    break
                except ValueError:
                    pass

            if parsed_date is None:
                print(
                    f"Could not parse 'Last Maintenance Date': {last_maint_date_str} for device {row.get('Room Number', index + 1)}")
                continue  # Skip to the next device if date cannot be parsed

            # Check if maintenance is within the current week
            if next_maint_date_obj and start_of_current_week <= next_maint_date_obj <= end_of_current_week:
                # Determine warranty status
                current_year = datetime.now().year
                under_warranty = "no"
                warranty_year_till = row.get('Warranty Year')  # Use .get() for safer access

                # Ensure warranty_year_till is convertible to int before comparison
                if pd.notna(warranty_year_till):
                    try:
                        warranty_year_till_int = int(warranty_year_till)
                        if warranty_year_till_int >= current_year:
                            under_warranty = "yes"
                    except ValueError:
                        warranty_year_till_int = "N/A"  # Handle cases where it's not a valid number
                else:
                    warranty_year_till_int = "N/A"

                issue_reported = row.get('Status', "None")  # Use .get() for safer access
                previous_maintenance_date = parsed_date.strftime('%Y-%m-%d') if parsed_date else "N/A"

                upcoming_maintenance_list.append({
                    "room_no": row.get('Room Number', 'N/A'),
                    "device_id": index + 1,  # Using index + 1 as device_id
                    "device_name": row.get('Appliance Type', 'N/A'),
                    "issue_reported": issue_reported,
                    "device_year": str(int(row['Device_Year'])) if pd.notna(row.get('Device_Year')) else "N/A",
                    "under_warranty": under_warranty,
                    "warranty_year_till": str(warranty_year_till_int) if warranty_year_till_int != "N/A" else "N/A",
                    "previous_maintenance_date": previous_maintenance_date,
                    "predictedDaysSinceMaintenance": round(predicted_days_since, 2),
                    "next_maintenance_date": next_maint_date_formatted
                })
        return upcoming_maintenance_list

    def get_model_status(self) -> str:
        """Returns the current status of the model (Trained/Not Trained)."""
        return "Trained" if self.hotel_model is not None else "Not Trained"

    def get_data_status(self) -> str:
        """Returns the current status of the training data (Loaded/Not Loaded)."""
        return "Loaded" if not self.loaded_training_df.empty else "Not Loaded"

    def get_metrics(self) -> dict:
        """Returns the last calculated model metrics."""
        return {
            "r2_score": f"{self.model_metrics['r2_score']:.4f}" if self.model_metrics['r2_score'] is not None else "N/A",
            "mean_absolute_error": f"{self.model_metrics['mae']:.4f}" if self.model_metrics['mae'] is not None else "N/A",
            "root_mean_squared_error": f"{self.model_metrics['rmse']:.4f}" if self.model_metrics['rmse'] is not None else "N/A"
        }

# --- START: New method for multi-file loading (for choose-hotel-data API) ---
    def load_hotel_data(self, hotel_name: str) -> tuple[int, int, str]:
        """
        Loads a specific hotel's pre-processed CSV data into loaded_training_df
        and calculates the number of working devices.

        Args:
            hotel_name (str): The name of the hotel (e.g., 'fairfield', 'jw_marriott').

        Returns:
            tuple[int, int, str]: A tuple containing (records_loaded, working_devices_count, loaded_file_path).

        Raises:
            ValueError: If the hotel_name is invalid or required columns are missing.
            FileNotFoundError: If the CSV file does not exist.
            Exception: For other file loading errors.
        """
        # Validate if the provided hotel_name is in our predefined list
        if hotel_name.lower() not in HOTEL_CSV_FILES:
            raise ValueError(f"Invalid hotel_name: '{hotel_name}'. Please choose from: {', '.join(HOTEL_CSV_FILES.keys())}")

        csv_file_path = HOTEL_CSV_FILES[hotel_name.lower()]

        # Check if the CSV file actually exists on disk
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"The CSV file for {hotel_name} ('{csv_file_path}') does not exist.")

        try:
            # Read the CSV file into a DataFrame
            df = pd.read_csv(csv_file_path)

            # Essential columns required in the loaded data for other operations
            required_cols = ['Room Number', 'Appliance Type', 'Last Maintenance Date', 'Usage Hours', 'Days Since Maintenance', 'Average_Daily_Usage', 'Device_Year', 'Status', 'Warranty Year']

            # Validate that all required columns are present in the loaded CSV
            if not all(col in df.columns for col in required_cols):
                missing_cols = [col for col in required_cols if col not in df.columns]
                raise ValueError(f"Missing required columns in '{csv_file_path}': {', '.join(missing_cols)}")

            # Update the global loaded_training_df with the newly selected data
            self.loaded_training_df = df.copy()
            self.loaded_file_path = os.path.basename(csv_file_path)
            print(f"Successfully loaded '{csv_file_path}' for hotel '{hotel_name}'.")

            # --- START: Corrected Logic for Counting Working Devices ---
            working_devices_count = 0
            if 'Status' in self.loaded_training_df.columns:
                # Count rows where 'Status' is explicitly 'working' (case-insensitive),
                # or is NaN (empty cell, typically means no issue),
                # or explicitly the string 'none' (case-insensitive).
                working_devices_count = self.loaded_training_df[
                    self.loaded_training_df['Status'].astype(str).str.lower().isin(['working', 'none']) | self.loaded_training_df['Status'].isna()
                ].shape[0]
            else:
                print(f"Warning: 'Status' column not found in '{csv_file_path}'. Cannot count working devices.")
            # --- END: Corrected Logic for Counting Working Devices ---

            return len(self.loaded_training_df), working_devices_count, csv_file_path
        except Exception as e:
            # Catch any other exceptions during file processing/loading
            raise Exception(f"Error loading data for hotel '{hotel_name}' from '{csv_file_path}': {str(e)}")
    # --- END: New method for multi-file loading ---

    def load_non_room_data(self) -> list:
        non_room_csv_file_path = NON_ROOM_DATA

        if not os.path.exists(non_room_csv_file_path):
            raise FileNotFoundError(f"The CSV file for non-room data does not exist at: {non_room_csv_file_path}")

        try:
            # Read the CSV file into a DataFrame
            df = pd.read_csv(non_room_csv_file_path)

            df.dropna(how='all', inplace=True)

            df.reset_index(drop=True, inplace=True)

            non_room_maintenance_list = []

            # Essential columns required in the loaded data for other operations
            required_cols = [
                'DeviceID', 'DeviceType', 'Location', 'DeviceYear', 'WarrantyYear',
                'TotalUsageHours', 'LastMaintenanceDate', 'NextScheduledMaintenanceDates'
            ]

            # Validate that all required columns are present in the loaded CSV
            if not all(col in df.columns for col in required_cols):
                missing_cols = [col for col in required_cols if col not in df.columns]
                raise ValueError(f"Missing required columns in '{non_room_csv_file_path}': {', '.join(missing_cols)}")

            # Iterate through each row of the DataFrame
            for index, row in df.iterrows():
                # Create a dictionary for the current row, mapping CSV columns to desired output keys
                # Use .get() with a default 'N/A' for robustness if a column might sometimes be missing
                # or if its value is NaN (though required_cols check should prevent missing columns)
                non_room_maintenance_list.append({
                    "DeviceID": row.get('DeviceID'),
                    "DeviceType": row.get('DeviceType'),
                    "Location": row.get('Location'),
                    "DeviceYear": str(int(row.get('DeviceYear'))) if pd.notna(row.get('DeviceYear')) else "N/A",
                    "WarrantyYear": str(int(row.get('WarrantyYear'))) if pd.notna(row.get('WarrantyYear')) else "N/A",
                    "TotalUsageHours": row.get('TotalUsageHours'),
                    "LastMaintenanceDate": row.get('LastMaintenanceDate'),
                    "NextScheduledMaintenanceDates": row.get('NextScheduledMaintenanceDates')
                    # "PredictiveMaintenanceStatus": row.get('PredictiveMaintenanceStatus')
                })

            return non_room_maintenance_list

        except FileNotFoundError as e:
            # Re-raise the specific FileNotFoundError for clearer error handling upstream
            raise e
        except ValueError as e:
            # Re-raise the specific ValueError for clearer error handling upstream (e.g., missing columns)
            raise e
        except pd.errors.EmptyDataError:
            raise ValueError(f"The CSV file '{non_room_csv_file_path}' is empty or contains no data.")
        except pd.errors.ParserError:
            raise ValueError(f"Error parsing CSV file '{non_room_csv_file_path}'. Check file format.")
        except Exception as e:
            # Catch any other general exceptions during file processing/loading
            raise Exception(
                f"Error loading data for hotel non-room data from CSV file '{non_room_csv_file_path}': {str(e)}")