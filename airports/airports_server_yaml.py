from __future__ import print_function

import numpy as np
from bokeh.models.sources import ColumnDataSource
from flask import render_template, request, jsonify
from bokeh.simpleapp import SimpleApp
from bokeh.server.app import bokeh_app
from bokeh.server.crossdomain import crossdomain
from bokeh.plotting import curdoc, cursession

import appmaker
import ui
import utils

selected_aiport_id = '3682'

class YAPP(appmaker.YamlApp):
    theme = 'dark'

    def init_app(self):
        # Set the initial airport (Atlanta)
        # TODO: THIS IS A VERY WEAK PATTERN! Apps should have a namespace for
        # variables!!
        SimpleApp.selected_aiport_id = selected_aiport_id
        SimpleApp.theme = 'dark'
        SimpleApp.datasets = self.datasets
        SimpleApp.env = self.env


    def post_process_datasets(self):
        airports = self.datasets['airports']

        airports['color'] = ['green' for x in airports.id]
        airports['alpha'] = [1. for x in airports.id]
        airports['radius'] = [0.3 for x in airports.id]
        airports['lname'] = [x.lower() for x in airports.name]
        airports['lcity'] = [x.lower() for x in airports.city]
        airports['liata'] = [str(x).lower() for x in airports.iata]

        routes = self.datasets['routes']
        self.env['sources'] = sources = set([int(sid)for sid in routes.source_ap_id if sid.isdigit()])
        self.env['dests'] = dests = set([int(sid)for sid in routes.dest_ap_id if sid.isdigit()])
        self.env['active_ap_ids'] = active_ap_ids = sources.union(dests)
        # active_airports = airports[airports.id.isin(map(int, active_ap_ids))]


        self.env['out_routes'] = out_routes = routes.groupby('source_ap_id').count().sort('id', ascending=False)
        self.env['in_routes'] = in_routes = routes.groupby('dest_ap_id').count().sort('id', ascending=False)


        population = self.datasets['population']
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

        self.env['airport'] = airport = utils.get_airport_data(selected_aiport_id, airports, routes,
                                         out_routes, active_ap_ids)
        ap_routes = utils.get_routes(airport)

        self.sources['ap_routes_source'] = ColumnDataSource(ap_routes, tags=['routes_source'])
        self.sources['all_airports'] = ColumnDataSource(utils.create_output(airports), tags=['main_source'])
        self.sources['airports_found_source'] = ColumnDataSource(tags=['airports_found_source'])
        self.sources['dest_sources'] = ColumnDataSource(utils.create_dests_source(airport, airports),
                                                        tags=['dest_sources'])
        self.sources['worldmap_src'] = ColumnDataSource(utils.get_worldmap(airports, routes))

    def app_objects(self, objects):
        objects.update(
            {
                'starburst': ui.create_starburst(self.sources['ap_routes_source'],
                                                 self.sources['dest_sources'],
                                                 theme=self.theme),
                'legend': ui.create_size_legend(
                    # legend_source,
                    self.sources['frequency_legend'],
                    self.theme),
                'alpha_legend': ui.create_alpha_legend(
                    # apha_legend_source,
                    self.sources['alpha_legend'],
                    self.theme),
                'route_freq_legend': ui.create_route_freq_legend(
                    # route_freq_legend_source,
                    self.sources['route_freq_legend'],
                    self.theme),
            }
        )
        ui.create_airport_map(objects['net_map'], self.sources['ap_routes_source'],
                              self.sources['all_airports'], self.sources['worldmap_src'],
                              theme=self.theme)

        ui.create_population_map(objects['freq_map'], self.sources['population'],
                                 self.sources['worldmap_src'], theme=self.theme)
        objects.update(ui.create_dlg_airports_list(
            self.sources['airports_found_source']))

        objects['info_txt'].text = self.env['airport']['summary']
        objects['btn_selected_airport'].label = self.env['airport']['airport'].name.values[0]

        return objects

app = YAPP('app.yaml', '/ydashboard')


@bokeh_app.route("/select_airport", methods=['GET', 'OPTIONS'])
@crossdomain(origin="*", methods=['GET', 'POST'], headers=None)
def get_airport_selection():
    SimpleApp.selected_aiport_id = request.args['id']
    return jsonify({"msg": "OK"})


if __name__ == "__main__":
    print()
    print("To see the example go to: http://127.0.0.1:5050/dashboard")
    print()
    print()
    app.run(port=5050, debug=True)

