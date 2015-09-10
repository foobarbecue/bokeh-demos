import pandas as pd

from flask import Flask, jsonify, request
from bokeh.server.crossdomain import crossdomain

import utils
from utils import create_output


# Prepare data
airports = utils.airports = pd.read_csv(
    'data/airports.dat',
    names=['id', 'name', 'city', 'country', 'iata', 'icao', 'lat', 'lng', 'alt', 'dst', 'tz', 'tz_db']
)
routes = utils.routes = pd.read_csv(
    'data/routes.dat',
    names=['airline', 'id', 'source_ap', 'source_ap_id', 'dest_ap', 'dest_ap_id', 'codeshare', 'stops', 'equip']
)

sources = set([int(sid)for sid in routes.source_ap_id if sid.isdigit()])
dests = set([int(sid)for sid in routes.dest_ap_id if sid.isdigit()])
active_ap_ids = sources.union(dests)

out_routes = routes.groupby('source_ap_id').count().sort('id', ascending=False)
# (selected_aiport_id, airports, routes, out_routes, active_ap_ids)

airport = utils.get_airport_data('3682', utils.airports,
                                 routes, out_routes, active_ap_ids)
ap_routes = utils.get_routes(airport)
_source_aps = create_output(airport['destinations'])
_all_aps = create_output(utils.airports)


app = Flask(__name__)

@app.route('/data/ap_routes', methods=['GET', 'OPTIONS'])
@crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
def ap_routes_view():
    return jsonify(ap_routes)

@app.route('/data/source_aps', methods=['GET', 'OPTIONS'])
@crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
def source_aps_view():
    return jsonify(_source_aps)

@app.route('/data/all_aps', methods=['GET', 'OPTIONS'])
@crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
def all_aps_view():
    return jsonify(_all_aps)

@app.route('/data/update/<newid>', methods=['GET', 'OPTIONS'])
@crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
def update(newid):
    global airport
    global ap_routes
    global _source_aps
    global _isolated_aps
    global _all_aps

    # airport = utils.get_airport_data(str(newid), utils.airports)
    airport = utils.get_airport_data(str(newid), utils.airports,
                                 routes, out_routes, active_ap_ids)
    ap_routes = utils.get_routes(airport)

    _all_aps = create_output(utils.airports)

    ap = airport['airport']
    ind = ap.index.values[0]
    dd = {k: v[ind] for k, v in dict(ap).items()}

    return jsonify(
        {
         'connections': len(airport['destinations']),
         'airport': dd
        }
    )


if __name__ == "__main__":
    app.run(port=5050, debug=True)


