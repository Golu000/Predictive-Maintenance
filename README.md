This is a python backend application used for predicting the maintenance of nthe appliances used in the rooms, 
there are 3 datasets provided for training the model and then generating the maintenance date by using rooms numbers.

How to run the python code:
.venv\scripts\activate.bat (for activating the virtual env),
pip install -r requirements.txt (for installing all the required dependencies)
 

How to Import and Use in Postman:
Copy the entire JSON content from the Postman Json.txt.
Open Postman.
Click on File -> Import.
Select the Raw Text tab.
Paste the copied JSON into the text area.
Click Continue, then Import.
You will now have a new collection named "Hotel Maintenance API" in your Postman sidebar with three pre-configured requests.

Important Note for "Train Hotel Maintenance Model" Request:

For the "Train Hotel Maintenance Model" request, you will need to manually adjust the src value for the file key in the Body tab (select form-data).
Change /path/to/your/data/ac_new_data.csv to the actual, absolute path of your ac_new_data.csv (or hotel_maintenance_data.csv) file on your local machine. 
Postman needs the direct file path to upload the CSV.
