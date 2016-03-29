from __future__ import print_function

import os.path
import random
from functools import partial, update_wrapper, wraps
import datetime as dt
from flask import Flask, json, Response
import h5py
import numpy as np
import pandas as pd
import dask.array as da
from subsample import coarsen
from StringIO import StringIO
from six import string_types
from datetime import timedelta

try:
    from flask import Flask, jsonify, make_response, request, current_app
except ImportError:
    raise ImportError("You need Flask to run this example!")


FACTOR_BASE = 15000
fromtimestamp = dt.datetime.fromtimestamp

app = Flask(__name__)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    """
    Decorator to set crossdomain configuration on a Flask view
    For more details about it refer to:
    http://flask.pocoo.org/snippets/56/
    """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))

    if headers is not None and not isinstance(headers, string_types):
        headers = ', '.join(x.upper() for x in headers)

    if not isinstance(origin, string_types):
        origin = ', '.join(origin)

    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        @wraps(f)
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            requested_headers = request.headers.get(
                'Access-Control-Request-Headers'
            )
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            elif requested_headers:
                h['Access-Control-Allow-Headers'] = requested_headers
            return resp
        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)

    return decorator


def to_seconds(ts):
    if isinstance(ts, dt.datetime):
        return (ts - dt.datetime(1970, 1, 1)).total_seconds() * 1000
    else:
        return 1000 * ((ts - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's'))


def create_sim_data(date, low, high, freq=60, max_period=84600):
    res = []
    ts = dt.datetime.strptime(date, '%Y-%m-%d')
    next_day = ts + dt.timedelta(seconds=max_period)
    while ts < next_day:
        res.append((ts, random.uniform(low, high)))
        ts = ts + dt.timedelta(seconds=freq)

    return res

aapl = pd.read_csv('data/aapl_hours_raw.csv')

# create data if doesn't exist..
if not os.path.exists('data/aapl_minutes_raw.csv'):
    print("High resolution data file not found... Creating a new one (this may take some time...).")

    haapl = pd.read_csv('data/aapl.csv')

    print ("Simulating new data...")
    res = map(create_sim_data, haapl.Date, haapl.Low, haapl.High)
    newdt = pd.DataFrame({'Date': [to_seconds(item[0]) for sublist in res for item in sublist],
                          'Price': [item[1] for sublist in res for item in sublist]})
    print ("Creating new file: data/aapl_minutes_raw.csv")
    newdt.to_csv('data/aapl_minutes_raw.csv')
    print ("Done!")


aapl_min = pd.read_csv('data/aapl_minutes_raw.csv')


# build some data
factor = len(aapl) // FACTOR_BASE
resampled = coarsen(np.mean, np.asarray(aapl.Price), factor)
tss = coarsen(np.min, np.asarray(aapl.Date), factor)
ftss = [fromtimestamp(x//1000).strftime("%Y-%m-%d %H:%M:%S") for x in tss]

curr_ds = dict(
    Date=[x for x in tss],
    DateFmt=[ts for ts in ftss],
    Price=[float(x) for x in resampled],
)

details = {
    "start": curr_ds['DateFmt'][0],
    "end": curr_ds['DateFmt'][-1],
    "factor": factor,
    "samples_no": len(curr_ds['DateFmt']),
    "original_samples_no": len(aapl),
}


@app.route('/subsample/<start>/<end>', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
def subsample(start, end):
    start = int(start)
    end = int(end)
    global curr_ds
    global details

    # use minutes dataset if timedelta of selected period is "short" enough
    # (note that this "short enough" is just arbitrary for this example)
    if end-start < 43383600000:
        xs = aapl_min[(aapl_min.Date > start) & (aapl_min.Date < end)]
    else:
        xs = aapl[(aapl.Date > start) & (aapl.Date < end)]

    factor = len(xs) // FACTOR_BASE
    if factor <= 1:
        tss = xs.Date
        resampled = xs.Price
    else:
        resampled = coarsen(np.mean, np.asarray(xs.Price), factor)
        tss = coarsen(np.min, np.asarray(xs.Date), factor)

    curr_ds = dict(
        Date=[x for x in tss],
        Price=[float(x) for x in resampled],
        DateFmt=[fromtimestamp(x//1000) for x in tss],
    )
    details = {
        "start": curr_ds['DateFmt'][0],
        "end": curr_ds['DateFmt'][-1],
        "factor": factor,
        "samples_no": len(tss),
        "original_samples_no": len(xs),
    }
    return json.jsonify(curr_ds)


@app.route('/data', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
def get_data():
    return json.jsonify(curr_ds)


@app.route('/alldata', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
def get_alldata():
    global curr_ds
    global details
    curr_ds = dict(
        Date=list(tss),
        DateFmt=list(ftss),
        Price=[float(x) for x in resampled],
    )
    details = {
        "start": curr_ds['DateFmt'][0],
        "end": curr_ds['DateFmt'][-1],
        "factor": factor,
        "samples_no": len(curr_ds['DateFmt']),
        "original_samples_no": len(aapl),
    }
    return json.jsonify(curr_ds)


@app.route('/details', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
def get_details():
    return json.jsonify(details)


@app.route('/alldata.csv', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
def get_csv_data():
    df = pd.DataFrame(curr_ds)

    dfbuffer = StringIO()
    df.to_csv(dfbuffer, encoding='utf-8', index=False)
    dfbuffer.seek(0)
    values = dfbuffer.getvalue()
    return Response(values, mimetype='text/csv')



if __name__ == '__main__':
    app.run(debug=True)
