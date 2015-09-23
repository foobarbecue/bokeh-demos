from collections import OrderedDict
import numpy as np
import pandas as pd
from bokeh.models import BoxSelectTool, LassoSelectTool, Paragraph, HoverTool
from bokeh.plotting import (
    curdoc, cursession, figure, output_server, show, hplot, vplot
)
from bokeh.models.sources import ColumnDataSource
from bokeh.models.widgets import DataTable, TableColumn, StringFormatter, NumberFormatter, StringEditor, IntEditor, NumberEditor, SelectEditor

from bokeh.models.glyphs import Circle, Patches, Text, Rect
from bokeh.models import Plot, Range1d

import utils
import plot_style_specs as pss

# Prepare data
airports = utils.airports = pd.read_csv(
    '../data/airports.dat',
    names=['id', 'name', 'city', 'country', 'iata', 'icao', 'lat', 'lng', 'alt', 'dst', 'tz', 'tz_db']
)
routes = utils.routes = pd.read_csv(
    '../data/routes.dat',
    names=['airline', 'id', 'source_ap', 'source_ap_id', 'dest_ap', 'dest_ap_id', 'codeshare', 'stops', 'equip']
)
population = utils.population = pd.read_csv(
    '../data/global-city-population-estimates.csv', delimiter=';', encoding='utf-8'
)[:600]

gdpds = utils.population = pd.read_csv(
    '../data/ny.gdp.mktp.cd_Indicator_en_csv_v2.csv', encoding='utf-8'
)


sources = set([int(sid)for sid in routes.source_ap_id if sid.isdigit()])
dests = set([int(sid)for sid in routes.dest_ap_id if sid.isdigit()])
active_ap_ids = sources.union(dests)
out_routes = routes.groupby('source_ap_id').count().sort('id', ascending=False)
in_routes = routes.groupby('dest_ap_id').count().sort('id', ascending=False)

cities = airports.city.values
population['color'] = ['#cbdb29' if city in cities else 'red' for city in population['city']]

cities = airports.groupby('city')

population['population'] = population['2015']
population['radius'] = [2*utils.pop_radius_mapper(x) for x in population['2015']]

population['routes'] = utils.compute_cities_routes_density(population, cities, airports,
                                                           out_routes, in_routes)
population['pop_routes_ratio'] = [max(0, pop/float(city_routes)) for (pop,  city_routes) in
                       zip(population['population'], population['routes'])]
population['pop_routes_ratio'] = population['pop_routes_ratio'].replace([np.inf, -np.inf], np.nan)

max_ratio = max(population['pop_routes_ratio'])
population['alpha'] = [min((x/max_ratio)+0.1, 1) for x in population['pop_routes_ratio']]


grpr = routes.groupby('source_ap_id').count().sort('id', ascending=False)
countries_ap_grp = airports.groupby('country')
cac = countries_ap_count = countries_ap_grp.count().sort('id', ascending=False)
# for max to be canadian flights, second
_max_aps = 435
countries_ap_count['radius'] = map(lambda x: min((float(x)/_max_aps) * 0.7, 0.9), countries_ap_count.id)
countries_ap_count['country'] = countries_ap_count.index
countries_ap_count['ap_count'] = countries_ap_count.id


