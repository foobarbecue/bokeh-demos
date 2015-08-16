from __future__ import print_function
from threading import Thread
import requests
from requests.exceptions import ConnectionError

import utils
import ui
from bokeh.plotting import figure, show
from bokeh.io import output_file
from bokeh.models.sources import ColumnDataSource, AjaxDataSource
from bokeh.models.widgets import (HBox, VBox, VBoxForm, PreText, CheckboxGroup,
                                  Select, AppHBox, AppVBox, AppVBoxForm,
                                    Paragraph, Dialog,
                                  AutocompleteInput, Button, TextInput)


from bokeh.embed import components, autoload_server
from bokeh.resources import Resources
from bokeh.templates import RESOURCES

from flask import render_template, request

import utils
from utils import create_output


from bokeh.simpleapp import simpleapp
from bokeh.server.app import bokeh_app

from bokeh.plotting import curdoc, cursession

# TODO: WE CAN AVOID THISS!!!!
from flask import jsonify

POLL_TIME = 1000

selected_aiport_id = '3682'
airport = utils.get_airport_data(selected_aiport_id, utils.airports)
ap_routes = utils.get_routes(airport)
ap_routes_source = ColumnDataSource(ap_routes, tags=['routes_source'])
all_airports = ColumnDataSource(create_output(utils.airports), tags=['main_source'])
airports_found_source = ColumnDataSource(tags=['airports_found_source'])


legend_source = ColumnDataSource(
    {'name': ['>300', '200-300', '100-200', '50-100', '10-50', '1-10', '>=1'],
            'x': [25] * 7,
            'y': [31, 47, 59, 70, 80, 90, 100],
            'radius': [8*x for x in [1.5, 1, 0.8, 0.5, 0.3, 0.2, 0.1]]
    },
    tags=['legend_source']
)

# Widgets
btn_search = Button(label='search', name='search_button')
btn_cancel_search = Button(label='cancel', name='cancel_search')

select_city_size = CheckboxGroup(
        labels=['1', '1-10', '10-50', '50-100', '100-200', '200-300', '>300'],
        name='select_city_size', inline=True,
    )

cumulate_paths = CheckboxGroup(labels=['cumulate paths'],
                               name='paths', inline=True,
                               )

label_city_filter = Paragraph(text='Filter city by number of routes:',
                              name='label_city_filter',
                              height=25)

btn_selected_airport = Button(label=airport['airport'].name.values[0],
                              name='btn_selected_airport')
# select_city_size = Select(name='select_city_size', value='all',
#                           options=['1', '1-10', '10-50', '50-100', '100-200', '200-300', '>300'])


@simpleapp(btn_search, btn_cancel_search, select_city_size, label_city_filter, btn_selected_airport,
           cumulate_paths)
def app(search_button):
    # retrieve the theme to be used..
    theme = 'creme' #request.args.get('theme', 'default')

    searchbox = TextInput()#completions=[x for x in utils.airports.name.values])

    # create plot object and add all it's objects
    plot = figure(title="Flights", plot_width=900, plot_height=600,
                  tools="pan,box_zoom,box_select,tap,resize,reset")
    ui.create_airport_map(plot, ap_routes_source, all_airports, theme=theme)

    info_txt = PreText(text=airport['summary'], width=200, height=250)
    dlg_info = Dialog(title='Selected Airport Info', #buttons=[confirm_chart_button],
                        content=HBox(info_txt), visible=False)

    dest_sources = ColumnDataSource(utils.create_dests_source(airport, utils.airports))
    starburst = ui.create_starburst(ap_routes_source, dest_sources, theme=theme)


    legend = ui.create_legend(legend_source, theme)
    objects = {
        'main_map': plot,
        'info_txt': info_txt,
        'starburst': starburst,
        'searchbox': searchbox,
        'dlg_info': dlg_info,
        'legend': legend,
    }
    objects.update(ui.create_dlg_airports_list(airports_found_source))
    return objects

@app.layout
def stock2_layout(app):
    search = AppHBox(app=app, children=['search_button', 'cancel_search'])
    sidebar = AppVBox(app=app, children=['searchbox', search,
                                         # Paragraph(height=20),
                                         # 'label_city_filter',
                                         # 'select_city_size',
                                         # 'cumulate_paths',
                                         # Paragraph(height=10),
                                         'btn_selected_airport',
                                         Paragraph(height=1),
                                         'legend',
                                         # Paragraph(height=5),
                                         # 'info_txt',
                                         'starburst'])
    app = AppHBox(app=app, children=['dlg_airports_found', 'dlg_info',
                                     sidebar, 'main_map'])
    return app

@app.update([({'tags' : 'main_source'}, ['selected'])])
def update_selection(ticker1, ticker2, app):
    # select the sources we want to change uppon selection
    theme = 'creme'

    source = app.select_one({'tags' : 'main_source'})
    routes_source = app.select_one({'tags' : 'routes_source'})

    # get the selected airport ID and change the selected airport accordingly
    id_ = source.selected['1d']['indices'][0]
    airport_id = str(int(source.data['id'][id_]))
    airport = utils.get_airport_data(airport_id, utils.airports)

    objs = update_current_airport(airport_id, source, routes_source, app, theme)

    return objs


@app.update([({'tags' : 'legend_source'}, ['selected'])])
def update_legend_selection(ticker1, ticker2, app):
    # select the sources we want to change uppon selection
    theme = 'creme'

    source = app.select_one({'tags' : 'legend_source'})
    main_source = app.select_one({'tags' : 'main_source'})
    ind = source.selected['1d']['indices'][0]

    data = source.data
    radius_to_check = float(source.data['radius'][ind]) / 8.

    for i, value in enumerate(main_source.data['radius']):
        if float(value) == radius_to_check:
            main_source.data['color'][i] = None

    # return {}
    # routes_source = app.select_one({'tags' : 'routes_source'})
    #
    # # get the selected airport ID and change the selected airport accordingly
    # id_ = source.selected['1d']['indices'][0]
    # airport_id = str(int(source.data['id'][id_]))
    # airport = utils.get_airport_data(airport_id, utils.airports)
    #
    # objs = update_current_airport(airport_id, source, routes_source, app, theme)
    #
    # return objs

@app.update([({'name' : 'search_button'}, ['clicks'])])
def on_search(searchbox, app):
    txt = app.objects['searchbox'].value or ''

    aps_found = utils.search_airports(txt.lower(), utils.airports)


    source = app.select_one({'tags' : 'airports_found_source'})
    # source = app.objects['airports_found_source']
    source.data = create_output(aps_found, ['name', 'country', 'city', 'iata'])

    objects = ui.create_dlg_airports_list(source)

    objects['dlg_airports_found'].visible = True
    return objects


@app.update([({'name' : 'btn_selected_airport'}, ['clicks'])])
def on_selected_airport(searchbox, app):
    new_dlg = Dialog(title='Selected Airport Info', #buttons=[confirm_chart_button],
                        content=HBox(app.objects['info_txt']), visible=True)
    return {'dlg_info': new_dlg}


@app.update([({'name' : 'cancel_search'}, ['clicks'])])
def on_cancel(searchbox, app):
    app.objects['searchbox'].value = ''
    return {'searchbox': app.objects['searchbox']}


@app.update([({'tags' : 'airports_found_source'}, ['selected'])])
def airport_row_selected(searchbox, app):
    # TODO: WHY THIS DOESN'T WORK????????
    source = app.select_one({'tags' : 'airports_found_source'})
    print ("NOT WORKING!!!!")


@app.update([({'name' : 'btn_airport_selected'}, ['clicks'])])
def on_confirm_airport_selection(searchbox, app):
    theme = 'creme'
    app.objects['dlg_airports_found'].visible = False

    source = app.select_one({'tags' : 'main_source'})
    routes_source = app.select_one({'tags' : 'routes_source'})
    objects = update_current_airport(selected_aiport_id, source, routes_source, app, theme)
    app.objects['searchbox'].value = ''
    objects['searchbox'] = app.objects['searchbox']
    return objects


def update_current_airport(aiport_id, source, routes_source, app, theme):
    airport = utils.get_airport_data(aiport_id, utils.airports)

    # update the sources with the new data
    routes_source.data = utils.get_routes(airport)
    source.data = create_output(utils.airports)

    # update the summary text
    app.objects['info_txt'].text = airport['summary']
    curr_ap_btn = app.select_one({'name': 'btn_selected_airport'})
    curr_ap_btn.label = airport['airport'].name.values[0]

    dest_sources = ColumnDataSource(utils.create_dests_source(airport, utils.airports))
    starburst = ui.create_starburst(routes_source, dest_sources, theme=theme)

    return {
        'info_txt': app.objects['info_txt'],
        'starburst': starburst,
    }


app.route("/dashboard")

@bokeh_app.route("/select_airport")
def get_airport_selection():
    global selected_aiport_id
    selected_aiport_id = request.args['id']
    return jsonify({"msg": "OK"})



if __name__ == "__main__":
    print()
    print("To see the example go to: http://127.0.0.1:5050/dashboard")
    print()
    print()
    app.run(port=5050, debug=True)

