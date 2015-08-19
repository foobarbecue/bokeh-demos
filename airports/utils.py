import pandas as pd
import numpy as np
import world_countries as wc

SUMMARY_KEYS = ['name', 'city', 'country', 'iata', 'icao', 'tz_db', 'alt']

airport_keys = ['id', 'name', 'city', 'country', 'iata', 'icao', 'lat',
                'lng', 'alt', 'dst', 'tz', 'tz_db']
route_keys = ['airline', 'id', 'source_ap', 'source_ap_id',
              'dest_ap', 'dest_ap_id', 'codeshare', 'stops', 'equip']
airline_keys = ['id', 'name', 'alias', 'iata', 'icao', 'callsign',
                'country', 'active']

airports = pd.read_csv('data/airports.dat', names=airport_keys)
routes = pd.read_csv('data/routes.dat', names=route_keys)

# add the columns we need for visualization to the airports df
airports['color'] = ['green' for x in airports.id]
airports['alpha'] = [1. for x in airports.id]
airports['radius'] = [0.3 for x in airports.id]
airports['lname'] = [x.lower() for x in airports.name]
airports['lcity'] = [x.lower() for x in airports.city]
airports['liata'] = [str(x).lower() for x in airports.iata]

sources = set([int(sid)for sid in routes.source_ap_id if sid.isdigit()])
dests = set([int(sid)for sid in routes.dest_ap_id if sid.isdigit()])
active_ap_ids = sources.union(dests)
active_airports = airports[airports.id.isin(map(int, active_ap_ids))]
ghost_airports = airports[~airports.id.isin(active_ap_ids)]

out_routes = routes.groupby('source_ap_id').count().sort('id', ascending=False)
in_routes = routes.groupby('dest_ap_id').count().sort('id', ascending=False)


population = pd.read_csv('data/global-city-population-estimates.csv', delimiter=';', encoding = "utf8")[:400]
population['population'] = population['2015']
# population['color'] = ['green' for x in airports.id]
# population['alpha'] = [1. for x in airports.id]


def pop_radius_mapper(pop):
    if pop > 30000:
        return 2
    elif pop > 25000:
        return 1.5
    elif pop > 20000:
        return 1
    elif pop > 15000:
        return 0.8
    elif pop > 10000:
        return 0.5
    elif pop > 5000:
        return 0.3
    elif pop > 1000:
        return 0.2
    else:
        return 0.1

population['radius'] = [2*pop_radius_mapper(x) for x in population['2015']]

cities = airports.city.values
city_fligh_alpha = airports.alpha

population['color'] = ['#cbdb29' if city in cities else 'red' for city in population['city']]
# import pdb; pdb.set_trace()


cities = airports.groupby('city')

not_found = []
cities_ap_density = []
cities_info = {}
for city in population.city.values:
    cities_info[city] = 0
    if city in cities.groups:
        for city_ap in cities.groups[city]:
            ap = airports[airports.id==airports.id[city_ap]]
            try:
                cities_info[city] += out_routes.id[str(ap.id.values[0])]
            except KeyError:
                pass

            try:
                cities_info[city] += in_routes.id[str(ap.id.values[0])]
            except KeyError:
                pass

        cities_ap_density.append(cities_info[city])
    else:
        cities_ap_density.append(-1)
        not_found.append(city)

print ("MISSING CITIES", not_found)

population['routes'] = cities_ap_density
population['pop_routes_ratio'] = [max(0, pop/float(city_routes)) for (pop,  city_routes) in
                       zip(population['population'], population['routes'])]
population['pop_routes_ratio'] = population['pop_routes_ratio'].replace([np.inf, -np.inf], np.nan)
max_ratio = max(population['pop_routes_ratio'])
population['alpha'] = [min((x/max_ratio)+0.1, 1) for x in population['pop_routes_ratio']]




def get_worldmap():
    grpr = routes.groupby('source_ap_id').count().sort('id', ascending=False)
    countries_ap_grp = airports.groupby('country')
    countries_ap_count = countries_ap_grp.count().sort('id', ascending=False)
    # for max to be canadian flights, second
    _max_aps = 435
    countries_ap_count['alpha'] = map(lambda x: min((float(x)/_max_aps) * 0.7, 0.9), countries_ap_count.id)
    countries_ap_count['country'] = countries_ap_count.index

    world_countries = wc.data.copy()
    worldmap = pd.DataFrame.from_dict(world_countries, orient='index')

    def get_count(country):
        res = countries_ap_count[countries_ap_count['country'] == country]
        return res.id[0] if len(res) else 0

    def get_alpha(country):
        res = countries_ap_count[countries_ap_count['country'] == country]
        if not len(res):
            return 0

        return max(0.3, min((float(res.name[0])/_max_aps) * 0.7, 1))

    worldmap['alpha'] = [get_alpha(country) for country in worldmap.name]
    worldmap['count'] = [get_count(country) for country in worldmap.name]

    return worldmap


def color_mapper(airport, destinations):
    def _(id, country=None):
        if id in airport['airport'].id.values:
            return "red"
        elif id in destinations:
            if country is None:
                return "green"
            elif country in airport['airport'].country.values:
                return '#c28cbd'
            else:
                return '#29bdbc'

        elif id in active_ap_ids:
            return "black"
        else:
            return "black"

    return _

def alpha_mapper(airport, destinations):
    def _(id):
        if id in airport['airport'].id.values:
            return 1.
        elif id in destinations:
            return 1.
        elif id in active_ap_ids:
            return 0.6
        else:
            return 0.4

    return _

def radius_mapper(airport, destinations):
    def _(id):
        try:
            ap_out_routes = out_routes.id[str(id)]
        except KeyError:
            ap_out_routes = 0

        if ap_out_routes > 300:
            return 1.5
        elif ap_out_routes > 200:
            return 1
        elif ap_out_routes > 100:
            return 0.8
        elif ap_out_routes > 50:
            return 0.5
        elif ap_out_routes > 10:
            return 0.2
        else:
            return 0.1
        # if id in airport['airport'].id.values:
        #     return 0.6
        # elif id in destinations:
        #     return 0.5
        # elif id in active_ap_ids:
        #     return 0.2
        # else:
        #     return 0.1

    return _


def search_airports(txt, airports):
    return airports[airports.lname.str.contains(txt) |
                    airports.lcity.str.contains(txt) |
                    airports.liata.str.contains(txt)]


def get_airport_data(airport_id, airports):
    main_ap = airports[airports.id == int(airport_id)]
    connections = routes[routes.source_ap_id == airport_id].sort('dest_ap_id')
    destinations_id = set([int(x) for x in connections.dest_ap_id.values if x.isdigit()])


    out_connections = routes[routes.dest_ap_id == airport_id].sort('source_ap_id')
    origins_id = set([int(x) for x in out_connections.source_ap_id.values if x.isdigit()])

    dmain_ap = dict(main_ap)
    airport = {
        'airport': main_ap,
        'connections': connections,
        'destinations': airports[airports.id.isin(destinations_id)],
        'out_connections': out_routes,
        'origins': airports[airports.id.isin(origins_id)],
        'summary': "Selected Airport:\n\n%s" % "\n".join(
            ["%s: %s" % (k, dmain_ap[k].values[0]) for k in SUMMARY_KEYS]
        )
    }
    airport['summary'] += "\nIncoming routes: %s" % len(origins_id)
    airport['summary'] += "\nOutgoing routes: %s" % len(destinations_id)

    make_color = color_mapper(airport, destinations_id)
    airports['color'] = [make_color(xid, xcountry) for xid, xcountry in zip(airports.id, airports.country)]

    make_alpha = alpha_mapper(airport, destinations_id)
    airports['alpha'] = [make_alpha(xid) for xid in airports.id]

    make_radius = radius_mapper(airport, destinations_id)
    airports['radius'] = [make_radius(xid) for xid in airports.id]

    # import pdb; pdb.set_trace()
    # update the airports destinations df as we've added color and alpha
    conns = set([int(x) for x in connections.dest_ap_id.values if x.isdigit()])
    airport['destinations'] = airports[airports.id.isin(conns)]

    return airport

def get_routes(airport):
    xs, ys, color = [], [], []
    main_ap = airport['airport']
    conn_dests = airport['destinations']

    country = airport['airport'].country.values[0]
    for iata, lng, lat, conn_country in zip(conn_dests.iata, conn_dests.lng, conn_dests.lat, conn_dests.country):
        xs.append([float(main_ap.lng), float(lng)])
        ys.append([float(main_ap.lat), float(lat)])

        if country == conn_country:
            color.append('#c28cbd')
        else:
            color.append('#29bdbc')

    return {'xs': xs, 'ys': ys, "color": color}

def create_output(df, extra_keys=None):
    if extra_keys is None:
        extra_keys = []

    out = {
        'lng': [float(x) for x in df.lng],
        'lat': [float(x) for x in df.lat],
    }

    for key in ['id', 'alpha', 'radius']:
        if key in df.columns:
            out[key] = [float(x) for x in df[key]]

    for key in extra_keys:
        if key in df.columns:
            out[key] = [x for x in df[key]]

    if 'color' in df.columns:
        out['color'] = [x for x in df.color]

    return out


def create_dests_source(airport, airports):
    dest_sources = create_output(airport['destinations'])
    dest_sources['radius'] = [x*8 for x in dest_sources['radius']]
    dest_sources['alpha'] = [0.4 for x in dest_sources['radius']]
    dest_sources['name'] = [airports.name[x] for x in dest_sources['id'] if x in airports.name]
    dest_sources['city'] = [airports.city[x] for x in dest_sources['id'] if x in airports.city]
    dest_sources['country'] = [airports.country[x] for x in dest_sources['id'] if x in airports.country]

    return dest_sources