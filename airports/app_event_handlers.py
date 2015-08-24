from __future__ import print_function

from bokeh.models.sources import ColumnDataSource
from bokeh.models.widgets import (HBox, VBox, VBoxForm, PreText, DataTable,
                                  AppVBox, AppHBox, CheckboxGroup, Dialog,
                                  AutocompleteInput, Button, TextInput,
                                  Paragraph, Select,
                                  Panel, Tabs, Slider, Dialog)
from bokeh.plotting import figure
import utils
import ui


def update_current_airport(aiport_id, source, routes_source, app, theme):
    ds = app.datasets
    env = app.env
    env['airport'] = utils.get_airport_data(
        aiport_id, ds['airports'], ds['routes'],env['out_routes'], env['active_ap_ids']
    )

    # update the sources with the new data
    routes_source.data = utils.get_routes(env['airport'])
    source.data = utils.create_output(ds['airports'])

    # update the summary text
    app.objects['info_txt'].text = env['airport']['summary']

    curr_ap_btn = app.select_one({'name': 'btn_selected_airport'})
    curr_ap_btn.label = env['airport']['airport'].name.values[0]

    dest_sources = app.select_one({'tags': 'dest_sources'})
    dest_sources.data = utils.create_dests_source(env['airport'], ds['airports'])

    return {'info_txt': app.objects['info_txt']}


def update_selection(app):
    ds = app.datasets
    env = app.env

    source = app.select_one({'tags' : 'main_source'})
    routes_source = app.select_one({'tags' : 'routes_source'})

    # get the selected airport ID and change the selected airport accordingly
    if source.selected['1d']['indices']:
        id_ = source.selected['1d']['indices'][0]
        airport_id = str(int(source.data['id'][id_]))
        env['airport'] = utils.get_airport_data(
            airport_id, ds['airports'], ds['routes'], env['out_routes'], env['active_ap_ids']
        )

        return update_current_airport(airport_id, source, routes_source, app,
                                      app.theme)

    return {}

def update_legend_selection(ticker1, ticker2, app):
    source = app.select_one({'tags': 'legend_source'})
    population = app.datasets['population']
    radius = population['radius'].copy()

    for ind in source.selected['1d']['indices']:
        radius_to_check = float(source.data['radius'][ind]) / 5.
        radius = radius.replace(radius_to_check, 0)

    popdata = population.to_dict(orient='list')
    popdata['radius'] = [float(x) for x in radius]

    frequency_source = app.select_one({'tags': 'population'})
    frequency_source.data = popdata
    return {}


def on_search(searchbox, app):
    txt = app.objects['searchbox'].value or ''

    aps_found = utils.search_airports(txt.lower(), app.datasets['airports'])
    source = app.select_one({'tags': 'airports_found_source'})
    source.data = utils.create_output(aps_found, ['name', 'country', 'city', 'iata'])
    objects = ui.create_dlg_airports_list(source)

    objects['dlg_airports_found'].visible = True
    return objects


def on_selected_airport(searchbox, app):
    """ When an airport is selected (tapped) this function creates a new
    dialog to show the current selected airport information and a starburst
    of the airport connections """
    new_dlg = Dialog(
        title='Selected Airport Info',
        content=HBox(app.objects['info_txt'], app.objects['starburst']),
        visible=True
    )
    return {'dlg_info': new_dlg}


def on_cancel(cancel, app):
    app.objects['searchbox'].value = ''
    return {'searchbox': app.objects['searchbox']}


def airport_row_selected(searchbox, app):
    # TODO: WHY THIS DOESN'T WORK????????
    source = app.select_one({'tags' : 'airports_found_source'})
    print ("NOT WORKING!!!!")


def on_confirm_airport_selection(searchbox, app):
    app.objects['dlg_airports_found'].visible = False

    source = app.select_one({'tags' : 'main_source'})
    routes_source = app.select_one({'tags': 'routes_source'})

    objects = update_current_airport(
        app.selected_aiport_id, source, routes_source, app, app.theme)
    app.objects['searchbox'].value = ''
    objects['searchbox'] = app.objects['searchbox']

    return objects
