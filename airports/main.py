from __future__ import print_function

import utils
import ui
from bokeh.plotting import Figure, curdoc
from bokeh.models import ServerCallback
from bokeh.models.sources import ColumnDataSource, AjaxDataSource
from bokeh.models.widgets import (HBox, VBox, PreText, Select, AutocompleteInput)
import utils
from utils import create_output

theme = 'default'

def on_main_source_selected():
    # get the selected airport ID and change the selected airport accordingly
    # TODO this throws an error (if selection is empty?)
    id_ = all_airports.selected['1d']['indices'][0]
    airport_id = str(int(all_airports.data['id'][id_]))
    airport = utils.get_airport_data(airport_id, utils.airports)

    # update the sources with the new data
    ap_routes_source.data = utils.get_routes(airport)
    all_airports.data = create_output(utils.airports)

    # update the summary text
    info_txt.text = airport['summary']

    dest_sources = ColumnDataSource(utils.create_dests_source(airport))
    new_starburst = ui.create_starburst(ap_routes_source, dest_sources, theme=theme)

    right.children=[info_txt, new_starburst]

airport = utils.get_airport_data('3682', utils.airports)
ap_routes = utils.get_routes(airport)
ap_routes_source = ColumnDataSource(ap_routes)
all_airports = ColumnDataSource(create_output(utils.airports), callback=ServerCallback(on_main_source_selected))

AutocompleteInput

# create plot object and add all it's objects
plot = Figure(title="Flights", plot_width=800, plot_height=600,
              tools="pan,box_zoom,box_select,tap,resize,reset")
ui.create_airport_map(plot, ap_routes_source, all_airports, theme=theme)

info_txt = PreText(text=airport['summary'], width=300, height=250)

dest_sources = ColumnDataSource(utils.create_dests_source(airport))
# TODO this needs fixing to use Figure instead of figure
starburst = ui.create_starburst(ap_routes_source, dest_sources, theme=theme)

right = VBox(children=[info_txt, starburst])
app_layout = HBox(children=[plot, right])

curdoc().add(app_layout)

