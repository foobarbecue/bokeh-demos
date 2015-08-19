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
                                    Paragraph, Dialog, Panel, Tabs,
                                  AutocompleteInput, Button, TextInput)


from bokeh.embed import components, autoload_server
from bokeh.resources import Resources
from bokeh.templates import RESOURCES

from flask import render_template, request

import utils
from utils import create_output


from bokeh.simpleapp import simpleapp
from bokeh.server.app import bokeh_app
from bokeh.server.crossdomain import crossdomain

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
            'x': [35] * 7,
            'y': [13, 26, 37, 46, 53, 61, 68],
            'radius': [8*x for x in [1.5, 1, 0.8, 0.5, 0.3, 0.2, 0.1]]
    },
    tags=['legend_source']
)

apha_legend_source = ColumnDataSource(
    {'name': ['>300', '200-300', '100-200', '50-100', '10-50', '1-10', '>=1'],
            'x': [35] * 7,
            'y': [x * 10 for x in range(1, 8)],
            'alpha': [x * 0.1 for x in range(1, 8)],
    },
    tags=['alpha_legend_source']
)

route_freq_legend_source = ColumnDataSource(
    {'name': ['>300', '200-300', '100-200', '50-100', '10-50', '1-10', '>=1'],
        'x': [35] * 7,
        'x_int': [55] * 7,
        'y': [x * 10 for x in range(1, 8)],
        'alpha': [x * 0.1 for x in range(1, 8)],
    },
    tags=['route_freq_legend_source']
)

class YAPP(ui.YamlApp):
    theme = 'dark'

    def app_objects(self, objects):
        dest_sources = ColumnDataSource(utils.create_dests_source(airport, utils.airports))
        starburst = ui.create_starburst(ap_routes_source, dest_sources, theme=self.theme)

        legend = ui.create_size_legend(legend_source, self.theme)
        alpha_legend = ui.create_alpha_legend(apha_legend_source, self.theme)

        objects.update(
            {
                'starburst': starburst,
                'legend': legend,
                'alpha_legend': alpha_legend,
                'route_freq_legend': ui.create_route_freq_legend(route_freq_legend_source, self.theme),
            }
        )
        ui.create_airport_map(objects['net_map'], ap_routes_source,
                              all_airports, theme=self.theme)

        pop = utils.population
        columns = ['lon', 'lat', 'radius', 'alpha', 'routes', 'pop_routes_ratio']
        popdata = {k: [float(x) for x in pop[k]] for k in columns}
        popdata.update({k: [x for x in pop[k]] for k in ['population', 'city', 'country', 'color']})
        population_source = ColumnDataSource(popdata)

        ui.create_population_map(
            objects['freq_map'], ap_routes_source, all_airports,
            population_source, theme=self.theme)

        objects.update(ui.create_dlg_airports_list(airports_found_source))
        objects['info_txt'].text = airport['summary']
        objects['btn_selected_airport'].label = airport['airport'].name.values[0]
        return objects

    def add_events(self):
        @self.app.update([({'tags' : 'main_source'}, ['selected'])])
        def update_selection(app):
            source = app.select_one({'tags' : 'main_source'})
            routes_source = app.select_one({'tags' : 'routes_source'})

            # get the selected airport ID and change the selected airport accordingly
            id_ = source.selected['1d']['indices'][0]
            airport_id = str(int(source.data['id'][id_]))
            airport = utils.get_airport_data(airport_id, utils.airports)

            objs = update_current_airport(
                airport_id, source, routes_source, app, self.theme)

            return objs

        @self.app.update([({'tags' : 'legend_source'}, ['selected'])])
        def update_legend_selection(ticker1, ticker2, app):
            source = app.select_one({'tags' : 'legend_source'})
            main_source = app.select_one({'tags' : 'main_source'})
            ind = source.selected['1d']['indices'][0]

            data = source.data
            radius_to_check = float(source.data['radius'][ind]) / 8.

            for i, value in enumerate(main_source.data['radius']):
                if float(value) == radius_to_check:
                    main_source.data['color'][i] = None


        @self.app.update([({'name' : 'search_button'}, ['clicks'])])
        def on_search(searchbox, app):
            txt = app.objects['searchbox'].value or ''

            aps_found = utils.search_airports(txt.lower(), utils.airports)
            source = app.select_one({'tags' : 'airports_found_source'})
            source.data = create_output(aps_found,
                                        ['name', 'country', 'city', 'iata'])

            objects = ui.create_dlg_airports_list(source)

            objects['dlg_airports_found'].visible = True
            return objects


        @self.app.update([({'name' : 'btn_selected_airport'}, ['clicks'])])
        def on_selected_airport(searchbox, app):
            new_dlg = Dialog(
                title='Selected Airport Info',
                content=HBox(app.objects['info_txt'],
                             app.objects['starburst'],
                             ),
                visible=True
            )
            return {'dlg_info': new_dlg}


        @self.app.update([({'name' : 'cancel_search'}, ['clicks'])])
        def on_cancel(cancel, app):
            app.objects['searchbox'].value = ''
            return {'searchbox': app.objects['searchbox']}


        @self.app.update([({'tags' : 'airports_found_source'}, ['selected'])])
        def airport_row_selected(searchbox, app):
            # TODO: WHY THIS DOESN'T WORK????????
            source = app.select_one({'tags' : 'airports_found_source'})
            print ("NOT WORKING!!!!")


        @self.app.update([({'name' : 'btn_airport_selected'}, ['clicks'])])
        def on_confirm_airport_selection(searchbox, app):
            app.objects['dlg_airports_found'].visible = False

            source = app.select_one({'tags' : 'main_source'})
            routes_source = app.select_one({'tags': 'routes_source'})

            objects = update_current_airport(
                selected_aiport_id, source, routes_source, app, self.theme)
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


app = YAPP('app.yaml', '/ydashboard')


@bokeh_app.route("/select_airport", methods=['GET', 'OPTIONS'])
@crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
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

