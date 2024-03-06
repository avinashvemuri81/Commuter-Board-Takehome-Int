from flask import Flask, render_template, request
import requests
from datetime import datetime
from pytz import timezone

app = Flask(__name__)
# Could make classes for MBTACLient, Route, Trip, ... but because this is a small program,
# I wrote my code functionally as is common for many small flask apps


def get_stops():
    # Get all stops 
    # Demonstrate error handling for this api request, could apply timeout but some were randomly slow during testing so didnt
    try:
        response = requests.get('https://api-v3.mbta.com/stops', timeout=10.0)
        response.raise_for_status()
        data = response.json().get('data', [])
        stops = [{'id': stop['id'], 'name': stop['attributes']['name']} for stop in data]
        return stops
    except requests.exceptions.RequestException as err:
        print(f"API request failed with error: {err}")
        return []

@app.route('/')
def index():
    try:
        stops = get_stops()
        return render_template('index.html', stops=stops)
    except requests.exceptions.RequestException as err:
        print ("Something went wrong",err)
        return render_template('error.html', error_message=str(err))

def get_location(location_id):
    # Get a location by ID 
    location_response = requests.get(f'https://api-v3.mbta.com/stops/{location_id}')
    location_response.raise_for_status()
    location_data = location_response.json().get('data', {})
    location_name = location_data.get('attributes', {}).get('name', 'N/A') if location_data else 'N/A'
    return location_name

def get_all_routes():
    # Get routes 
    response = requests.get('https://api-v3.mbta.com/routes')
    response.raise_for_status()
    data = response.json().get('data', [])
    routes = {route['id']: route for route in data}
    return routes

def get_trip(trip_id):
    # Get a trip by ID 
    trip_response = requests.get(f'https://api-v3.mbta.com/trips/{trip_id}')
    trip_response.raise_for_status()
    trip_data = trip_response.json().get('data', {})
    return trip_data

def get_predictions(location_id, direction_id, routes):
    # Get predictions for a location and direction 
    response = requests.get(f'https://api-v3.mbta.com/predictions?filter[stop]={location_id}&filter[direction_id]={direction_id}')
    response.raise_for_status()
    data = response.json().get('data', [])
    predictions = []
    for prediction in data:
        vehicle = prediction['relationships'].get('vehicle')
        vehicle_id = vehicle['data']['id'] if vehicle and vehicle['data'] else 'N/A'
        route_id = prediction['relationships']['route']['data']['id']
        route_data = routes.get(route_id, {})
        route_type = route_data.get('attributes', {}).get('type', '')
        route_name = route_data.get('attributes', {}).get('name', '')
        if 'Amtrak' in route_name and route_type == 'Rail':
            carrier = 'Amtrak'
        else:
            carrier = 'MBTA'
        trip_id = prediction['relationships']['trip']['data']['id']
        trip_data = get_trip(trip_id)
        destination = trip_data.get('attributes', {}).get('headsign', 'N/A') if trip_data else 'N/A'
        departure_time = prediction['attributes']['departure_time']
        if departure_time:
            departure_time = datetime.fromisoformat(departure_time.replace("Z", "+00:00"))
            departure_time = departure_time.astimezone(timezone('US/Eastern'))
            departure_time = departure_time.strftime('%I:%M %p')
        prediction = {
            'carrier': carrier,
            'time': departure_time,
            'destination': destination,
            'train': vehicle_id,
            'track': prediction['relationships']['stop']['data']['id'],
            'status': prediction['attributes']['status']
        }
        predictions.append(prediction)
    return predictions

@app.route('/commuter_board', methods=['POST'])
def commuter_board():
    # Render commuter board for a location
    try:
        location_id = request.form.get('location')
        location_name = get_location(location_id)
        routes = get_all_routes()
        departures = get_predictions(location_id, direction_id=1, routes=routes)
        arrivals = get_predictions(location_id, direction_id=0, routes=routes)
        return render_template('commuter_board.html', departures=departures, arrivals=arrivals, location=location_name)
    except requests.exceptions.RequestException as err:
        print ("Something went wrong",err)
        return render_template('error.html', error_message=str(err))

if __name__ == '__main__':
    app.run(debug=True)