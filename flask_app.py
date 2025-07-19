from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Flask App Initialization
app = Flask(__name__)
CORS(app)

# Global variable to store received coordinates
current_location = {"latitude": None, "longitude": None}

# Target location (latitude, longitude)
target_location = {"latitude": 13.0510461, "longitude": 74.9650028}  # Example: Bangalore coordinates


@app.route('/')
def index():
    return "Welcome to the Location Sharing App!"


@app.route('/share_location')
def share_location():
    return render_template('location.html')


@app.route('/send_location', methods=['POST'])
def send_location():
    global current_location
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if latitude is not None and longitude is not None:
        current_location['latitude'] = latitude
        current_location['longitude'] = longitude
        print(f"Received coordinates: {current_location}")

        # Check if coordinates are within a tolerance range of the target location
        tolerance = 0.001  # Adjust this value as needed
        if (
            abs(current_location['latitude'] - target_location['latitude']) <= tolerance and
            abs(current_location['longitude'] - target_location['longitude']) <= tolerance
        ):
            message = "Within the location"
        else:
            message = "Not within the location"

        print(message)
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": "Invalid data format"}), 400


@app.route('/get_current_location', methods=['GET'])
def get_current_location():
    return jsonify(current_location)


if __name__ == '__main__':
    app.run(debug=True)