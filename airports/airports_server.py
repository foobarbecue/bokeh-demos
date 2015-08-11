from __future__ import print_function
from threading import Thread
import requests
from requests.exceptions import ConnectionError

import utils
import ui
from bokeh.plotting import figure, show
from bokeh.io import output_file
from bokeh.models.sources import ColumnDataSource, AjaxDataSource
from bokeh.models.widgets import (HBox, VBox, VBoxForm, PreText,
                                  Select, AppHBox, AppVBox, AppVBoxForm)


from bokeh.embed import components
from bokeh.resources import Resources
from bokeh.templates import RESOURCES

from flask import render_template, request

import utils
from utils import create_output


from bokeh.simpleapp import simpleapp

POLL_TIME = 1000

airport = utils.get_airport_data('3682', utils.airports)
ap_routes = utils.get_routes(airport)
ap_routes_source = ColumnDataSource(ap_routes, tags=['routes_source'])
all_airports = ColumnDataSource(create_output(utils.airports), tags=['main_source'])


@simpleapp()
def app():
    # retrieve the theme to be used..
    theme = 'default' #request.args.get('theme', 'default')

    # create plot object and add all it's objects
    plot = figure(title="Flights", plot_width=800, plot_height=600,
                  tools="pan,box_zoom,box_select,tap,resize,reset")
    ui.create_airport_map(plot, ap_routes_source, all_airports, theme=theme)

    info_txt = PreText(text=airport['summary'], width=300, height=250)

    dest_sources = ColumnDataSource(utils.create_dests_source(airport))
    starburst = ui.create_starburst(ap_routes_source, dest_sources, theme=theme)
    return {
        'main_map': plot,
        'info_txt': info_txt,
        'starburst': starburst,
        }

@app.layout
def stock2_layout(app):
    right = AppVBox(app=app, children=['info_txt', 'starburst'])
    app = AppHBox(app=app, children=['main_map', right])
    return app

@app.update([({'tags' : 'main_source'}, ['selected'])])
def update_selection(ticker1, ticker2, app):
    # select the sources we want to change uppon selection
    theme = 'default'

    source = app.select_one({'tags' : 'main_source'})
    routes_source = app.select_one({'tags' : 'routes_source'})

    # get the selected airport ID and change the selected airport accordingly
    id_ = source.selected['1d']['indices'][0]
    airport_id = str(int(source.data['id'][id_]))
    airport = utils.get_airport_data(airport_id, utils.airports)

    # update the sources with the new data
    routes_source.data = utils.get_routes(airport)
    source.data = create_output(utils.airports)

    # update the summary text
    app.objects['info_txt'].text = airport['summary']

    dest_sources = ColumnDataSource(utils.create_dests_source(airport))
    starburst = ui.create_starburst(routes_source, dest_sources, theme=theme)

    return {
        'info_txt': app.objects['info_txt'],
        'starburst': starburst,
    }

app.route("/dashboard")

if __name__ == "__main__":
    print()
    print("To see the example go to: http://127.0.0.1:5050/dashboard")
    print()
    print()
    app.run(port=5050, debug=True)

