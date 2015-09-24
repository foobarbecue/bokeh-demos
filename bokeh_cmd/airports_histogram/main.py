
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

def get_country_color(ap_count):
    if ap_count < 100:
        return "#8e4d9e" # purple
    elif ap_count < 250:
        return "#2cbdb9" # strong cyan
    else:
        return "#b9bf3d" # Moderate yellow

def get_country_color_by_gdp(ap_count):
    if ap_count < 500000000000:
        return "#8e4d9e" # purple
    elif ap_count < 999999999999:
        return "#2cbdb9" # strong cyan
    else:
        return "#b9bf3d" # Moderate yellow

countries_ap_count['color'] = [get_country_color(x) for x in countries_ap_count.ap_count]

cac = {k: {'radius': v, 'color': color} for k, v, color in zip(cac['country'], cac['radius'], cac['color'])}
cac['United States of America'] = cac['United States']
cac['Russian Federation'] = cac['Russia']
cac['Democratic Republic of the Congo'] = cac['Congo (Brazzaville)']
cac['Congo'] = cac['Congo (Brazzaville)']
cac['Iran (Islamic Republic of)'] = cac['Iran']
cac['Republic of Korea'] = cac['Korea']
cac['Viet Nam'] = cac['Vietnam']
cac['Bolivia (Plurinational State of)'] = cac['Bolivia']
cac['Venezuela (Bolivarian Republic of)'] = cac['Venezuela']
cac['Syrian Arab Republic'] = cac['Syria']
cac['United Republic of Tanzania'] = cac['Tanzania']
cac['China, Hong Kong SAR'] = cac['Hong Kong']
cac["Lao People's Democratic Republic"] = cac['Laos']

gdp = {k: v for k, v in zip(gdpds['country'], gdpds['2014'])}

default = {'radius': 1, 'color': 'green'}
for x in population['country']:
    if x not in cac:
        print "NOT FOUND", x

scatter_ds = ColumnDataSource(data={
    'population': population['population'],
    'routes': population['routes'],
    'radius': [cac.get(x, default)['radius'] * 50 for x in population['country']],
    'color': [get_country_color_by_gdp(gdp.get(x, -1)) for x in population['country']],
    # 'color': [cac.get(x, default)['color'] for x in population['country']],
    'gdp': [gdp.get(x, -1) for x in population['country']],
    'country': population['country'],
    'city': population['city'],
})


TOOLS="pan,wheel_zoom,box_zoom,box_select,hover,crosshair,lasso_select,reset"

# create the scatter plot
p = figure(tools=TOOLS, plot_width=500, plot_height=500, title=None, min_border=10, min_border_left=50)
p.circle('routes', 'population', size=9, color="color", alpha=0.5, name="scatter", source=scatter_ds)

renderer = p.select(dict(name="scatter"))

box_select_tool = p.select(dict(type=BoxSelectTool))
box_select_tool.select_every_mousemove = False
lasso_select_tool = p.select(dict(type=LassoSelectTool))
lasso_select_tool.select_every_mousemove = False

hover = p.select(dict(type=HoverTool))
if hover:
    hover.tooltips = OrderedDict([
        ("City", "@city"),
        ("Country", "@country"),
        ("Population", "@population"),
        ("Routes", "@routes"),
        # ("country", "@country"),
    ])

# create the horizontal histogram
hhist, hedges = np.histogram(population['routes'], bins=20)
hzeros = np.zeros(len(hedges)-1)
hmax = max(hhist)*1.1

ph = figure(toolbar_location=None, plot_width=p.plot_width, plot_height=200, x_range=p.x_range,
            y_range=(hmax, 0), title=None, min_border=10, min_border_left=50)
ph.quad(bottom=0, left=hedges[:-1], right=hedges[1:], top=hhist, color="#6b6b6b", line_color="#4c4c4c")
ph.quad(bottom=0, left=hedges[:-1], right=hedges[1:], top=hzeros, color="#6b6b6b", alpha=0.5, line_color=None, name="hhist")
ph.quad(bottom=0, left=hedges[:-1], right=hedges[1:], top=hzeros, color="#6b6b6b", alpha=0.1, line_color=None, name="hhist2")
ph.xgrid.grid_line_color = None

ph_source = ph.select(dict(name="hhist"))[0].data_source
ph_source2 = ph.select(dict(name="hhist2"))[0].data_source

# create the vertical histogram
# vhist, vedges = np.histogram(y, bins=20)
vhist, vedges = np.histogram(population['population'], bins=20)
vzeros = np.zeros(len(vedges)-1)
vmax = max(vhist)*1.1

# need to adjust for toolbar height, unfortunately
th = 42

pv = figure(toolbar_location=None, plot_width=200, plot_height=p.plot_height+th-10, x_range=(0, vmax),
            y_range=p.y_range, title=None, min_border=10, min_border_top=th)
pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], right=vhist, color="#6b6b6b", line_color="#4c4c4c")
pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], right=vzeros, color="#6b6b6b", alpha=0.5, line_color=None, name="vhist")
pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], right=vzeros, color="#6b6b6b", alpha=0.1, line_color=None, name="vhist2")
pv.ygrid.grid_line_color = None

pv_source = pv.select(dict(name="vhist"))[0].data_source
pv_source2 = pv.select(dict(name="vhist2"))[0].data_source

legend_source = ColumnDataSource(
    {
        'label': ['> 250', '100 - 250', '< 100'],
        'y': [90, 60, 30],
        'x': [35] * 3,
        'fill_color': ["#8e4d9e", "#2cbdb9", "#b9bf3d"]
    }
)

def create_size_legend(source, theme='dark'):
    # Plot and axes
    xdr = Range1d(0, 220)
    ydr = Range1d(0, 120)

    plot = Plot(x_range=xdr, y_range=ydr, title="", plot_width=200, plot_height=100,
                min_border=10, min_border_left=40, **pss.PLOT_FORMATS)
    # Add the writing

    # legend = Text(x=5, y=110, text=['''Country Airports:'''], x_offset = 15, **pss.FONT_PROPS_SM)
    # plot.add_glyph(source, legend, selection_glyph=legend)

    country = Text(x='x', y='y', text='label', x_offset = 25,  y_offset=5,
                   text_color='#231f20', text_font_style='bold', text_font_size='9pt',
                   # **pss.FONT_PROPS_SM
    )
    plot.add_glyph(source, country, selection_glyph=country)

    if theme == "dark":
        line_color = '#221f1f'
        fill_color = '#ffffff'
    else:
        line_color = 'black'
        fill_color = 'black'
    circle = Circle(x='x', y="y", fill_color="fill_color", line_color="fill_color",
                    # fill_alpha='alpha', line_alpha='alpha',
                    size=10)
    isol_aps_renderer = plot.add_glyph(source, circle, selection_glyph=circle,
                                       nonselection_glyph=circle)

    # tap = TapTool(plot=plot, renderers=[isol_aps_renderer])
    # plot.tools.extend([tap])

    plot.background_fill = '#6b6b6b'

    return plot

legend = create_size_legend(legend_source)

columns = [
    TableColumn(field="city", title="city", editor=StringEditor(), width=80),
    TableColumn(field="country", title="country", editor=StringEditor(), width=80),
    # TableColumn(field="population",         title="population",         editor=IntEditor()),
    # TableColumn(field="routes",          title="routes",    editor=IntEditor()),\
    TableColumn(field="gdp",          title="gdp",    editor=NumberEditor(), formatter=NumberFormatter(format="0.0")),
]
data_table = DataTable(source=scatter_ds, columns=columns, editable=True, width=300, height=p.plot_height+th-10+100)


# set up callbacks
def on_selection_change(obj, attr, old, new):
    inds = np.array(new['1d']['indices'])
    if len(inds) == 0 or len(inds) == len(x):
        hhist = hzeros
        vhist = vzeros
        hhist2 = hzeros
        vhist2 = vzeros
    else:
        hhist, _ = np.histogram(x[inds], bins=hedges)
        vhist, _ = np.histogram(y[inds], bins=vedges)
        negative_inds = np.ones_like(x, dtype=np.bool)
        negative_inds[inds] = False
        hhist2, _ = np.histogram(x[negative_inds], bins=hedges)
        vhist2, _ = np.histogram(y[negative_inds], bins=vedges)

    ph_source.data["top"] = hhist
    pv_source.data["right"] = vhist
    ph_source2.data["top"] = -hhist2
    pv_source2.data["right"] = -vhist2

    cursession().store_objects(ph_source, pv_source, ph_source2, pv_source2)

# scatter_ds.on_change('selected', on_selection_change)

layout = vplot(
    hplot(Paragraph(text='Flight Data Dashboard', width=400, height=10, classes=['apptitle'])
          , classes=['topbar']),
     hplot(
        vplot(
            Paragraph(height=30),
            Paragraph(text='Flight Data Overview', width=400, height=20, classes=['plottitle']),
            hplot(p, pv),
            hplot(ph, Paragraph(height=90), legend)), Paragraph(width=30),
        Paragraph(width=10),
        Paragraph(width=30, height=900, classes=['tablebox']),
        vplot(Paragraph(height=30),
              Paragraph(text='Table View', width=320, height=30, classes=['plottitle']),
              Paragraph(height=30),
              data_table,
              Paragraph(height=80),
              classes=['tablebox']),
        Paragraph(width=150, height=900, classes=['tablebox']),
    )

)


curdoc().clear()
curdoc().add(layout)
