from flask import Flask, render_template, request, jsonify
import mysql.connector
import math

app = Flask(__name__)

# MySQL database configuration
db_config = {
    "host": "localhost",
    "user": "root",  # Default user for XAMPP
    "password": "",  # Default password for XAMPP
    "database": "crop_recommendation",
}

# Function to calculate Euclidean distance
def calculate_distance(input_values, crop_values):
    keys = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    distance = 0
    for key in keys:
        distance += (input_values[key] - crop_values[key]) ** 2
    return math.sqrt(distance)

# Function to fetch recommendations dynamically with probabilities
def get_recommendations_dynamic(N, P, K, temperature, humidity, ph, rainfall):
    try:
        # Check if all inputs are zero
        if N == 0 and P == 0 and K == 0 and temperature == 0 and humidity == 0 and ph == 0 and rainfall == 0:
            return [{"crop": "No crops to recommend for zero inputs.", "probability": 0}]
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Fetch all crops
        query = "SELECT * FROM crops"
        cursor.execute(query)
        crops = cursor.fetchall()

        conn.close()

        if not crops:
            return [{"crop": "No crops found in database.", "probability": 0}]

        # Calculate distances for all crops
        input_values = {"N": N, "P": P, "K": K, "temperature": temperature, "humidity": humidity, "ph": ph, "rainfall": rainfall}
        crops_with_distances = []

        distances = []
        for crop in crops:
            crop_values = {
                "N": crop["N"],
                "P": crop["P"],
                "K": crop["K"],
                "temperature": crop["temperature"],
                "humidity": crop["humidity"],
                "ph": crop["ph"],
                "rainfall": crop["rainfall"],
            }
            distance = calculate_distance(input_values, crop_values)
            crops_with_distances.append({"crop": crop["crop"], "distance": distance})
            distances.append(distance)

        if not distances:
            return [{"crop": "No suitable crops found.", "probability": 0}]

        # Find max and min distances for normalization
        max_distance = max(distances)
        min_distance = min(distances)

        # Adjust probabilities with more diverse scaling
        crops_with_distances.sort(key=lambda x: x["distance"])
        seen = set()
        unique_recommendations = []
        
        for crop in crops_with_distances:
            if crop["crop"] not in seen:
                # Calculate probability with diverse scaling
                if max_distance > min_distance:  # Avoid division by zero
                    normalized_distance = (crop["distance"] - min_distance) / (max_distance - min_distance + 1e-5)
                    probability = round((1 - normalized_distance) * 100, 1)
                else:
                    probability = 100  # If all distances are the same

                # Introduce randomness and scaling adjustments
                probability -= round(crop["distance"] * 0.1, 1)  # Add variability based on the distance itself
                probability = max(1, min(probability, 99))  # Ensure range is between 1% and 99%

                # Filter out invalid crop names
                if crop["crop"] and not crop["crop"].lower().startswith("an error occurred"):
                    unique_recommendations.append({"crop": crop["crop"], "probability": probability})
                    seen.add(crop["crop"])

        # Return the top 3 closest unique crops with probabilities
        return unique_recommendations[:3]

    except Exception as e:
        print(f"Error querying database: {e}")
        return [{"crop": "An error occurred while fetching recommendations", "probability": 0}]



# Endpoint to submit ratings
@app.route('/submit-ratings', methods=['POST'])
def submit_ratings():
    try:
        data = request.get_json()
        ratings = data.get('ratings', [])

        # Validate received data
        if not ratings:
            return jsonify({"message": "No ratings to submit."}), 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Process each rating
        for rating in ratings:
            crop = rating.get('crop')
            user_rating = rating.get('rating')

            # Ensure crop and valid rating
            if crop and user_rating and 1 <= int(user_rating) <= 5:  
                query = '''
                INSERT INTO feedbacks (crop, rating)
                VALUES (%s, %s)
                '''
                cursor.execute(query, (crop, int(user_rating)))
            else:
                print(f"Invalid data: {rating}")

        conn.commit()
        conn.close()

        return jsonify({"message": "Ratings submitted successfully."})

    except mysql.connector.Error as db_error:
        print(f"Database error occurred: {db_error}")
        return jsonify({"message": "An error occurred while submitting ratings. Please try again later."}), 500

    except Exception as e:
        print(f"General error occurred: {e}")
        return jsonify({"message": "An error occurred while submitting ratings."}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        # Get form data from the request
        data = request.get_json()
        N = float(data['N'])
        P = float(data['P'])
        K = float(data['K'])
        temperature = float(data['temperature'])
        humidity = float(data['humidity'])
        ph = float(data['ph'])
        rainfall = float(data['rainfall'])

        # Get dynamic recommendations
        recommendations = get_recommendations_dynamic(N, P, K, temperature, humidity, ph, rainfall)

        # Return recommendations as JSON
        return jsonify({"crops": recommendations})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"crops": [{"crop": "An error occurred. Please try again.", "probability": 0}]})

if __name__ == '__main__':
    app.run(debug=True)
