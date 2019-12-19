from flask import Flask, render_template, request, Response
from flask.json import jsonify
import json
import sqlite3
import time

app = Flask(__name__)

# Setup the SQLite DB
conn = sqlite3.connect('database.db')
conn.execute('CREATE TABLE IF NOT EXISTS readings (device_uuid TEXT, type TEXT, value INTEGER, date_created INTEGER)')
conn.close()

def find_median(sorted_list, absolute=True):
    """
    Find the median given a sorted list; if absolute is true and there are an even
    number of items in the list return a calculated median; otherwise return the lower of the two medians.

    :param absolute: wether or not to return the absolute median
    :type boolean:
    """
    n = len(sorted_list)
    if n % 2 == 0:
        if absolute:
            median = (sorted_list[n // 2 - 1] + sorted_list[n // 2]) / 2
        else:
            median = sorted_list[n // 2 - 1]
    else:
        median = sorted_list[n // 2]
    return median

def do_db_request(query):
    """
    Run the query on the sql database and return the rows requested

    :param query: SQL query
    :type string:
    :param commit: Wether or not to commit to the database
    :type boolean:
    """
    # Set the db that we want and open the connection
    if app.config['TESTING']:
        conn = sqlite3.connect('test_database.db')
    else:
        conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(query)
    rows = cur.fetchall()
    return rows

@app.route('/devices/<string:device_uuid>/readings/', methods = ['POST', 'GET'])
def request_device_readings(device_uuid):
    """
    This endpoint allows clients to POST or GET data specific sensor types.

    POST Parameters:
    * type -> The type of sensor (temperature or humidity)
    * value -> The integer value of the sensor reading
    * date_created -> The epoch date of the sensor reading.
        If none provided, we set to now.

    Optional Query Parameters:
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    * type -> The type of sensor value a client is looking for
    """
    if request.method == 'POST':
        # Grab the post parameters
        post_data = json.loads(request.data)
        sensor_type = post_data.get('type')
        value = post_data.get('value')
        date_created = post_data.get('date_created', int(time.time()))

        if sensor_type not in ['temperature', 'humidity']:
            return 'type {} not supported'.format(sensor_type), 400

        if int(value) > 100 or int(value) < 0:
            return 'value {} not supported'.format(value), 400

        # Set the db that we want and open the connection
        if app.config['TESTING']:
            conn = sqlite3.connect('test_database.db')
        else:
            conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Insert data into db
        cur.execute('insert into readings (device_uuid,type,value,date_created) VALUES (?,?,?,?)',
                    (device_uuid, sensor_type, value, date_created))

        conn.commit()

        # Return success
        return 'success', 201
    else:
        # Check optional parameters
        optional_query = ''
        if 'type' in request.args:
            optional_query += ' and type="{}"'.format(request.args['type'])

        if 'start' in request.args and 'end' in request.args:
            optional_query += ' and date_created between {} and {}'.format(request.args['start'], request.args['end'])

        # Execute the query
        rows = do_db_request('select * from readings where device_uuid="{}"{}'.format(device_uuid, optional_query))

        # Return the JSON
        return jsonify([dict(zip(['device_uuid', 'type', 'value', 'date_created'], row)) for row in rows]), 200

@app.route('/devices/<string:device_uuid>/readings/min/', methods = ['GET'])
def request_device_readings_min(device_uuid):
    """
    This endpoint allows clients to GET the min sensor reading for a device.

    Mandatory Query Parameters:
    * type -> The type of sensor value a client is looking for

    Optional Query Parameters
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    """
    # Check mandatory parameters
    if 'type' not in request.args:
        return 'type is a required query parameter', 400

    # Check optional parameters
    optional_query = ''
    if 'start' in request.args and 'end' in request.args:
        optional_query = ' and date_created between {} and {}'.format(request.args['start'], request.args['end'])

    rows = do_db_request('select * from readings where device_uuid="{}" and type="{}"{}'.format(device_uuid, request.args['type'], optional_query))

    min = {}
    for reading in [dict(zip(['device_uuid', 'type', 'value', 'date_created'], row)) for row in rows]:
        if reading.get('value') < min.get('value', 101):
            min = reading

    if min:
        return jsonify(min), 200
    else:
        return "minimum not found", 404

@app.route('/devices/<string:device_uuid>/readings/max/', methods = ['GET'])
def request_device_readings_max(device_uuid):
    """
    This endpoint allows clients to GET the max sensor reading for a device.

    Mandatory Query Parameters:
    * type -> The type of sensor value a client is looking for

    Optional Query Parameters
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    """
    # Check mandatory parameters
    if 'type' not in request.args:
        return 'type is a required query parameter', 400

    # Check optional parameters
    optional_query = ''
    if 'start' in request.args and 'end' in request.args:
        optional_query = ' and date_created between {} and {}'.format(request.args['start'], request.args['end'])

    rows = do_db_request('select * from readings where device_uuid="{}" and type="{}"{}'.format(device_uuid, request.args['type'], optional_query))

    max = {}
    for reading in [dict(zip(['device_uuid', 'type', 'value', 'date_created'], row)) for row in rows]:
        if reading.get('value') > max.get('value', -1):
            max = reading

    if max:
        return jsonify(max), 200
    else:
        return "maximum not found", 404

@app.route('/devices/<string:device_uuid>/readings/median/', methods = ['GET'])
def request_device_readings_median(device_uuid):
    """
    This endpoint allows clients to GET the median sensor reading for a device.

    Mandatory Query Parameters:
    * type -> The type of sensor value a client is looking for

    Optional Query Parameters
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    """
    # NOTE: The README wants the median to return a single sensor reading so when
    #       encountering an even number of readings I return the lower of the two
    #       medians.
    # Check mandatory parameters
    if 'type' not in request.args:
        return 'type is a required query parameter', 400

    # Check optional parameters
    optional_query = ''
    if 'start' in request.args and 'end' in request.args:
        optional_query = ' and date_created between {} and {}'.format(request.args['start'], request.args['end'])

    rows = do_db_request('select * from readings where device_uuid="{}" and type="{}"{}'.format(device_uuid, request.args['type'], optional_query))

    median = {}
    readings = sorted([dict(zip(['device_uuid', 'type', 'value', 'date_created'], row)) for row in rows], key = lambda i: i['value'])
    median = find_median(readings, absolute=False)

    if median:
        return jsonify(median), 200
    else:
        return "median not found", 404

@app.route('/devices/<string:device_uuid>/readings/mean/', methods = ['GET'])
def request_device_readings_mean(device_uuid):
    """
    This endpoint allows clients to GET the mean sensor readings for a device.

    Mandatory Query Parameters:
    * type -> The type of sensor value a client is looking for

    Optional Query Parameters
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    """
    # NOTE: I rounded the mean to 4 decimal places. Seemed accurate enough for the purposes of this excercise
    # Check mandatory parameters
    if 'type' not in request.args:
        return 'type is a required query parameter', 400

    # Check optional parameters
    optional_query = ''
    if 'start' in request.args and 'end' in request.args:
        optional_query = ' and date_created between {} and {}'.format(request.args['start'], request.args['end'])

    rows = do_db_request('select * from readings where device_uuid="{}" and type="{}"{}'.format(device_uuid, request.args['type'], optional_query))

    mean = 0
    readings = [dict(zip(['device_uuid', 'type', 'value', 'date_created'], row)) for row in rows]
    for reading in readings:
        mean += reading['value']
    mean = round(mean / len(readings), 4)

    return jsonify({"value": mean}), 200

@app.route('/devices/<string:device_uuid>/readings/mode/', methods = ['GET'])
def request_device_readings_mode(device_uuid):
    """
    This endpoint allows clients to GET the mode sensor reading value for a device.

    Mandatory Query Parameters:
    * type -> The type of sensor value a client is looking for

    Optional Query Parameters
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    """
    # NOTE: The README did not make any specific mention of multimodes. For the purposes
    #       of this excercise we assume if there is not a single mode we return a list
    #       of the multimode
    # Check mandatory parameters
    if 'type' not in request.args:
        return 'type is a required query parameter', 400

    # Check optional parameters
    optional_query = ''
    if 'start' in request.args and 'end' in request.args:
        optional_query = ' and date_created between {} and {}'.format(request.args['start'], request.args['end'])

    rows = do_db_request('select * from readings where device_uuid="{}" and type="{}"{}'.format(device_uuid, request.args['type'], optional_query))

    freq_map = {}
    readings = [dict(zip(['device_uuid', 'type', 'value', 'date_created'], row)) for row in rows]
    for reading in readings:
        if reading['value'] in freq_map:
            freq_map[reading['value']] += 1
        else:
            freq_map[reading['value']] = 1

    max = -1
    count_map = {}
    for k, v in freq_map.items():
        if v in count_map:
            count_map[v].append(k)
        else:
            count_map[v] = [k]
        if v > max:
            max = v

    if not count_map:
        return "no mode found", 404

    if len(count_map[v]) == 1:
        return jsonify({"value": count_map[v][0]}), 200
    else:
        # We found more than one mode
        return jsonify({"value": count_map[v]}), 200

@app.route('/devices/<string:device_uuid>/readings/quartiles/', methods = ['GET'])
def request_device_readings_quartiles(device_uuid):
    """
    This endpoint allows clients to GET the 1st and 3rd quartile
    sensor reading value for a device.

    Mandatory Query Parameters:
    * type -> The type of sensor value a client is looking for
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    """
    # NOTE: When calucalting the quartiles we do not include the median value,
    #       so we split the sorted dataset into two halves and found the median
    #       for the upper and lower halves. Unlike the median endpoint we are
    #       not returning a reading but the absolute median so if we have an even
    #       number of medians calculate the average of the two.
    # Check mandatory parameters
    if 'type' not in request.args:
        return 'type is a required query parameter', 400

    if 'start' not in request.args or 'end' not in request.args:
        return 'start/end are required query parameters', 400

    rows = do_db_request('select * from readings where device_uuid="{}" and type="{}" and date_created between {} and {}'.format(
        device_uuid, request.args['type'], request.args['start'], request.args['end']))

    readings = sorted([row['value'] for row in rows])
    n = len(readings)
    if n % 2 == 0:
        first_half = readings[:n // 2]
        second_half = readings[n // 2:]
    else:
        first_half = readings[:n // 2]
        second_half = readings[n // 2 + 1:]

    first_quartile = find_median(first_half, absolute=True)
    third_quartile = find_median(second_half, absolute=True)

    return jsonify({'quartile_1': first_quartile, 'quartile_3': third_quartile}), 200


if __name__ == '__main__':
    app.run()
