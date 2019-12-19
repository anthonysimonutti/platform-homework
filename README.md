# Canary Platform Homework

## Introduction
Imagine a system where hundreds of thousands of Canary like hardware devices are concurrently uploading temperature and humidity sensor data.

The API to facilitate this system accepts creation of sensor records, in addition to retrieval.

These `GET` and `POST` requests can be made at `/devices/<uuid>/readings/`.

Retreival of sensor data should return a list of sensor values such as:

```
    [{
        'date_created': <int>,
        'device_uuid': <uuid>,
        'type': <string>,
        'value': <int>
    }]
```

The API supports optionally querying by sensor type, in addition to a date range.

A client can also access metrics such as the min, max, median, mode and mean over a time range.

These metric requests can be made by a `GET` request to `/devices/<uuid>/readings/<metric>/`

When requesting min, max and median, a single sensor reading dictionary should be returned as seen above.

When requesting the mean or mode, the response should be:

```
    {
        'value': <mean/mode>
    }
```

Finally, the API also supports the retrieval of the 1st and 3rd quartile over a specific date range.

This request can be made via a `GET` to `/devices/<uuid>/readings/quartiles/` and should return

```
    {
        'quartile_1': <int>,
        'quartile_3': <int>
    }
```

The API is backed by a SQLite database.

## Getting Started
This service requires Python3. To get started, create a virtual environment using Python3.

Then, install the requirements using `pip install -r requirements.txt`.

Finally, run the API via `python app.py`.

## Design Decisions

Everything was implemented pretty straightforward but there are a few specific notes to point out.

Normally when calculating a median when you come across an even list you combine the middle two
values and return the average of them. Here however the median is expected to return a single sensor reading so when
encountering an even number of readings I return the lower of the two medians.

When calculating the mean I rounded it to 4 decimal places.

When calculating modes it was possible to find multiple modes. Instead of returning a random value from the list
of multimodes I return them all as a list; otherwise if there is just a single mode I return it as an integer.

When calucalting the quartiles we do not include the median value, so we split the sorted
dataset into two halves and found the median for the upper and lower halves.
Unlike the median endpoint we are not returning a reading but the absolute median so if we have an even
number of medians calculate the average of the two like normal.

## Testing
Tests can be run via `pytest -v`.

## Tasks
Your task is to fork this repo and complete the following:

- [x] Add field validation. Only *temperature* and *humidity* sensors are allowed with values between *0* and *100*.
- [x] Add logic for query parameters for *type* and *start/end* dates.
- [x] Implement the min endpoint.
- [x] Implement the max endpoint.
- [x] Implement the median endpoint.
- [x] Implement the mean endpoint.
- [x] Implement the mode endpoint.
- [x] Implement the quartile endpoint.
- [x] Add and implement the stubbed out unit tests for your changes.
- [ ] Update the README with any design decisions you made and why.

When you're finished, send your git repo link to Michael Klein at michael@canary.is. If you have any questions, please do not hesitate to reach out!
