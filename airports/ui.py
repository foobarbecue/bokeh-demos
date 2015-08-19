from __future__ import print_function
from collections import OrderedDict
from bokeh.models.tools import HoverTool, TapTool
from bokeh.models.glyphs import Circle, Patches, Text, Rect
from bokeh.models.sources import ColumnDataSource
from bokeh.models.actions import Callback
from bokeh.models import Range1d, Plot
from bokeh.models.widgets import (HBox, VBox, VBoxForm, PreText, DataTable,
                                  AppVBox, AppHBox, CheckboxGroup, Dialog,
                                  AutocompleteInput, Button, TextInput,
                                  Paragraph, Select,
                                  TableColumn, StringFormatter, NumberFormatter,
                                  StringEditor, IntEditor, NumberEditor,
                                  Panel, Tabs, Slider, Dialog)
from bokeh.plotting import figure, show
import math
import plot_style_specs as pss

from bokeh.simpleapp import simpleapp

def get_theme(theme):
    rules = {
        'map_color': "lightblue",
        'map_line_color': "lightblue",
        'connections_color': "lightgrey",
        # 'background': 'white',
        'title_text_font': '"Times New Roman", Times, serif',
        'title_text_font_style': "normal",

    }

    if theme == "creme":
        rules['map_color'] = "#8B8378"
        rules['map_line_color'] = "#8B8378"
        rules['connections_color'] = "black"

        rules['background_fill'] = '#FEFFEF'
        rules['border_fill'] = '#FEFFEF'
        rules['title_text_font'] = '"Times New Roman", Times, serif'
        rules['title_text_font_style'] = "italic"

        rules['outline_line_width'] = 7
        rules['outline_line_alpha'] = 0.3
        rules['outline_line_color'] = "#8B8378"

    elif theme == "dark":
        rules['map_color'] = "#2c2c2c"
        rules['map_line_color'] = "#565656"
        rules['connections_color'] = "white"

        rules['background_fill'] = '#474746'
        rules['border_fill'] = '#474746'
        rules['min_border'] = 0
        rules['title_text_font'] = '"Times New Roman", Times, serif'
        rules['title_text_font_style'] = "italic"

        rules['outline_line_width'] = 0
        rules['outline_line_alpha'] = 0.3
        rules['outline_line_color'] = None

        rules['grid'] = {
            'grid_line_color': None,
        }

        rules['axis'] = {
            'major_label_text_font_size': None,
            'major_label_text_color': None,
            'axis_label_text_font_size': '0',
        }

    return rules

def create_airport_map(plot, ap_routes, isolated_aps, theme='default'):
    import utils

    rules = get_theme(theme)
    worldmap = utils.get_worldmap()
    worldmap_src = ColumnDataSource(worldmap)

    # Using PLOTTING interface
    countries = Patches(xs='lons', ys='lats', fill_color=rules['map_color'],
                        fill_alpha='alpha', line_color=rules['map_line_color'],
                        line_width=0.5)
    countries_renderer = plot.add_glyph(worldmap_src, countries,
                                        selection_glyph=countries,
                                       nonselection_glyph=countries)

    # Using PLOTTING interface
    connections_color = rules.pop('connections_color')
    plot.multi_line('xs', 'ys', color='color', line_width=1,
                    line_alpha=0.4, source=ap_routes)

    # # Using GLYPH interface
    circle = Circle(x='lng', y="lat", fill_color='color', line_color='color',
                    fill_alpha='alpha', line_alpha='alpha', radius='radius')
    isol_aps_renderer = plot.add_glyph(isolated_aps, circle, selection_glyph=circle,
                                       nonselection_glyph=circle)

    # circle = Circle(x='lng', y="lat", fill_color='color', line_color='color',
    #                 fill_alpha='alpha', line_alpha='alpha', radius='radius')
    # aps_renderer = plot.add_glyph(source_aps, circle)

    hover = plot.select(dict(type=HoverTool))
    if hover:
        hover.tooltips = OrderedDict([
            ("Name", "@name"),
        ])
        hover.renderers = [countries_renderer]

    tap = plot.select(dict(type=TapTool))
    tap.renderers = [isol_aps_renderer]

    code = """
        sel = cb_obj.get('selected')['1d'];
        sel = sel.indices;

        if (sel.length>0){
            var data = cb_obj.get('data');
            var url = "http://127.0.0.1:5050/data/update/"+data.id[parseInt(sel[0])];
            xhr = $.ajax({
                type: 'GET',
                url: url,
                contentType: "application/json",
                header: {
                  client: "javascript"
                }
            });

            xhr.done(function(details) {
                if (details.connections == 0){
                    alert("Sorry, the selected airport have no connections!");
                }

                // Fill the airport details div with the new airport info
                $("#info_wrapper").removeClass("hidden");
                $("#details_panel").html("<h3>"+details.airport.name+"</h3>");
                $("#details_panel").append("<div>City: " + details.airport.city + "</div>");
                $("#details_panel").append("<div>Country: " + details.airport.country + "</div>");
                $("#details_panel").append("<div>Number of Connections: " + details.connections + "</div>");
                $("#details_panel").append("<div>IATA: " + details.airport.iata + "</div>");
                $("#details_panel").append("<div>ICAO: " + details.airport.icao + "</div>");
                $("#details_panel").append("<div>Id: " + details.airport.id + "</div>");
                $("#details_panel").append("<div>Geolocation: " + details.airport.lng + "," + details.airport.lat + " </div>");
            });

        }

    """
    objs = {}
    tap.action = Callback(code=code, args=objs)


    plot.axis.minor_tick_in=None
    plot.axis.minor_tick_out=None
    plot.axis.major_tick_in=None
    plot.axis.major_tick_line_color = None#"#8B8378"
    plot.axis.major_label_text_color = "#8B8378"
    plot.axis.axis_line_color = None

    plot.axis.major_label_text_font_style = "italic"


    for k, v in rules.items():
        if k not in ['map_line_color', 'map_color', 'grid', 'axis']:
            setattr(plot, k, v)

    for section in ['grid', 'axis']:
        for k, v in rules.get(section, {}).items():
            if k not in ['map_line_color', 'map_color', 'grid', 'axis']:
                plot_attr = getattr(plot, section)
                setattr(plot_attr, k, v)



def create_population_map(plot, ap_routes, isolated_aps, population_source, theme='default'):
    import utils

    rules = get_theme(theme)
    worldmap_src = ColumnDataSource(utils.get_worldmap())

    # Using PLOTTING interface
    countries = Patches(xs='lons', ys='lats', fill_color=rules['map_color'],
                        fill_alpha=1, line_color=rules['map_line_color'],
                        line_alpha=1, line_width=0.5)
    countries_renderer = plot.add_glyph(worldmap_src, countries,
                                        selection_glyph=countries,
                                       nonselection_glyph=countries)

    # Using GLYPH interface
    # import pdb; pdb.set_trace()
    circle = Circle(x='lon', y="lat", fill_color='color', line_color='color',
                    fill_alpha='alpha',
                    line_alpha='alpha',
                    radius='radius'
    )
    isol_aps_renderer = plot.add_glyph(population_source, circle, selection_glyph=circle,
                                       nonselection_glyph=circle)
    #
    #
    hover = plot.select(dict(type=HoverTool))
    if hover:
        hover.tooltips = OrderedDict([
            ("City", "@city"),
            ("Country", "@country"),
            ("Population", "@population"),
            ("Routes", "@routes"),
            ("Ratio", "@pop_routes_ratio")
        ])
        hover.renderers = [isol_aps_renderer]
    #
    # tap = plot.select(dict(type=TapTool))
    # tap.renderers = [isol_aps_renderer]
    #
    # code = """
    #     sel = cb_obj.get('selected')['1d'];
    #     sel = sel.indices;
    #
    #     if (sel.length>0){
    #         var data = cb_obj.get('data');
    #         var url = "http://127.0.0.1:5050/data/update/"+data.id[parseInt(sel[0])];
    #         xhr = $.ajax({
    #             type: 'GET',
    #             url: url,
    #             contentType: "application/json",
    #             header: {
    #               client: "javascript"
    #             }
    #         });
    #
    #         xhr.done(function(details) {
    #             if (details.connections == 0){
    #                 alert("Sorry, the selected airport have no connections!");
    #             }
    #         });
    #
    #     }
    #
    # """
    # objs = {}
    # tap.action = Callback(code=code, args=objs)


    plot.axis.minor_tick_in=None
    plot.axis.minor_tick_out=None
    plot.axis.major_tick_in=None
    plot.axis.major_tick_line_color = None#"#8B8378"
    plot.axis.major_label_text_color = "#8B8378"
    plot.axis.axis_line_color = None

    plot.axis.major_label_text_font_style = "italic"


    for k, v in rules.items():
        if k not in ['map_line_color', 'connections_color', 'map_color', 'grid', 'axis']:
            setattr(plot, k, v)

    for section in ['grid', 'axis']:
        for k, v in rules.get(section, {}).items():
            if k not in ['map_line_color', 'map_color', 'grid', 'axis']:
                plot_attr = getattr(plot, section)
                setattr(plot_attr, k, v)


def create_starburst(ap_routes, isolated_aps, theme='default'):
    import utils

    rules = get_theme(theme)
    connections_color = rules.pop('connections_color')

    dists = []
    xs = []
    ys = []
    for (ox, px), (oy, py) in zip(ap_routes.data['xs'], ap_routes.data['ys']):
        dist = math.hypot(px - ox, py - oy)
        dists.append(dist)

    max_radius = max(dists)

    plot = figure(title="", plot_width=300, plot_height=300,
                  tools="pan,box_zoom,box_select,tap,hover,resize,reset",
                  toolbar_location = None,
                  x_range = [ox-max_radius, ox+max_radius],
                  y_range = [oy-max_radius, oy+max_radius],
    )

    chunk = max_radius / 5.
    for i in range(5):
        rad = max_radius - chunk * i
        plot.circle([ox], [oy], radius=rad, fill_color=None, line_color="lightgrey")

    plot.multi_line('xs', 'ys', color='color', line_width=1,
                    line_alpha=0.4, source=ap_routes)


    circle = Circle(x='lng', y="lat", fill_color='color', line_color='color',
                    fill_alpha='alpha', line_alpha='alpha', radius='radius')
    isol_aps_renderer = plot.add_glyph(isolated_aps, circle, selection_glyph=circle,
                                       nonselection_glyph=circle)

    plot.axis.minor_tick_in = None
    plot.axis.minor_tick_out = None
    plot.axis.major_tick_in = None
    plot.axis.major_tick_out = None

    plot.axis.major_label_text_font_size="0pt"

    plot.axis.major_tick_line_color = None
    plot.axis.major_label_text_color = None
    plot.axis.axis_line_color = None

    plot.axis.major_label_text_font_style = "italic"

    plot.border_fill = "whitesmoke"
    plot.min_border = 0


    hover = plot.select(dict(type=HoverTool))
    if hover:
        hover.tooltips = OrderedDict([
            ("ID", "@id"),
            ("Name", "@name"),
            ("city", "@city"),
            ("country", "@country"),
        ])
        hover.renderers = [isol_aps_renderer]


    for k, v in rules.items():
        if k not in ['map_line_color', 'map_color', 'grid', 'axis']:
            setattr(plot, k, v)

    plot.outline_line_width = 2

    return plot


def create_dlg_airports_list(source):
    options = CheckboxGroup(
        labels=['save selection'],
        name='new_annotation_options'
    )


    cols =[
        TableColumn(field='name', title='name', width=130, editor=StringEditor()),
        TableColumn(field='city', title='city', editor=StringEditor(),
                    default_sort='descending'),
        TableColumn(field='country', title='country', width=100, editor=StringEditor(),
                    default_sort='descending'),
        TableColumn(field='iata', title='iata', width=130, editor=StringEditor(),
                    default_sort='descending'),
    ]
    ndt = DataTable(source=source, columns=cols, editable=True, width=500, height=400)

    # annotation = TextInput(
    #     title="Text", name='annotation_txt', value=""
    # )

    main_tab = VBox(options, ndt)
    confirm_chart_button = Button(label="Confirm", type="success", name='btn_airport_selected')



    callback = Callback(
        args={'tr': ndt, 'sr': source},
        code="""
        ind = sr.get('selected')['1d']['indices'][0];
        data = sr.get('data');

        // TODO: TEMP URL!! This should be changed to a more robust pattern
        url = "http://127.0.0.1:5006/select_airport?id=" + data.id[ind];

        xhr = Bokeh.$.ajax({
            type: 'GET',
            url: url,
            contentType: "application/json",
            // data: jsondata,
            header: {
              client: "javascript"
            }
        });

        xhr.done(function(data) {
            console.log('done');
        });
        """
    )
    source.callback = callback

    return {
        'dlg_airports_found': Dialog(title='Select an airport', buttons=[confirm_chart_button],
                                     content=main_tab, visible=False),
        'table_airports': ndt,
        'new_annotation_options': options
    }


def create_size_legend(source, theme):#, value_string, color_string, bar_color):
    # Plot and axes
    xdr = Range1d(0, 220)
    ydr = Range1d(0, 120)

    plot = Plot(
        x_range=xdr,
        y_range=ydr,
        title="",
        plot_width=120,
        plot_height=180,
        min_border=0,
        **pss.PLOT_FORMATS
    )
    # Add the writing

    FONT_PROPS_XSM = dict(pss.FONT_PROPS_XSM)
    FONT_PROPS_XSM['text_color']='#000000'

    legend = Text(x=5, y=100, text=['''City population:'''], x_offset = 15, **pss.FONT_PROPS_SM)
    plot.add_glyph(source, legend, selection_glyph=legend)
    smlegend = Text(x=5, y=90, text=['''in milions'''], x_offset = 65, **pss.FONT_PROPS_XSM)
    plot.add_glyph(source, smlegend, selection_glyph=smlegend)

    country = Text(x='x', y='y', text='name', x_offset = 25,  y_offset=5, **FONT_PROPS_XSM)
    plot.add_glyph(source, country, selection_glyph=country)

    rules = get_theme(theme)

    if theme == "dark":
        line_color = '#221f1f'
        fill_color = '#ffffff'
    else:
        line_color = 'black'
        fill_color = 'black'
    circle = Circle(x='x', y="y", fill_color=fill_color, line_color=line_color,
                    # fill_alpha='alpha', line_alpha='alpha',
                    radius='radius')
    isol_aps_renderer = plot.add_glyph(source, circle, selection_glyph=circle,
                                       nonselection_glyph=circle)


    tap = TapTool(plot=plot)#, renderers=[rect_renderer])
    # hover = HoverTool(plot=plot, renderers=[rect_renderer], tooltips=tooltips)
    plot.tools.extend([tap])

    for k, v in rules.items():
        if k not in ['map_line_color', 'map_color', 'connections_color', 'grid', 'axis']:
            setattr(plot, k, v)

    # plot.outline_line_width = 2
    plot.background_fill = '#565656'
    #afafaf

    return plot

def create_alpha_legend(source, theme):#, value_string, color_string, bar_color):
    # Plot and axes
    xdr = Range1d(0, 220)
    ydr = Range1d(0, 120)

    plot = Plot(
        x_range=xdr,
        y_range=ydr,
        title="",
        plot_width=120,
        plot_height=180,
        min_border=0,
        **pss.PLOT_FORMATS
    )
    # Add the writing

    legend = Text(x=5, y=100, text=['''Flight frequency'''], x_offset = 15, **pss.FONT_PROPS_SM)
    plot.add_glyph(source, legend, selection_glyph=legend)
    legend = Text(x=5, y=90, text=['''by passenger:'''], x_offset = 15, **pss.FONT_PROPS_SM)
    plot.add_glyph(source, legend, selection_glyph=legend)
    smlegend = Text(x=5, y=80, text=['''in milions'''], x_offset = 65, **pss.FONT_PROPS_XSM)
    plot.add_glyph(source, smlegend, selection_glyph=smlegend)

    country = Text(x='x', y='y', text='name', x_offset = 25,  y_offset=5, **pss.FONT_PROPS_XSM)
    plot.add_glyph(source, country, selection_glyph=country)

    rules = get_theme(theme)

    circle = Rect(x='x', y="y", width=10, height=10,
                  # fill_color='#722F37', line_color='#722F37',
                  fill_color='#cbdb29', line_color='#cbdb29',
                    fill_alpha='alpha', line_alpha='alpha',
                    )
    isol_aps_renderer = plot.add_glyph(source, circle, selection_glyph=circle,
                                       nonselection_glyph=circle)

    tap = TapTool(plot=plot)#, renderers=[rect_renderer])
    # hover = HoverTool(plot=plot, renderers=[rect_renderer], tooltips=tooltips)
    plot.tools.extend([tap])


    for k, v in rules.items():
        if k not in ['map_line_color', 'map_color', 'connections_color', 'grid', 'axis']:
            setattr(plot, k, v)


    # plot.outline_line_width = 2
    plot.background_fill = '#2c2c2c'

    return plot


def create_route_freq_legend(source, theme):
    # Plot and axes
    xdr = Range1d(0, 220)
    ydr = Range1d(0, 120)

    plot = Plot(
        x_range=xdr,
        y_range=ydr,
        title="",
        plot_width=120,
        plot_height=180,
        min_border=0,
        **pss.PLOT_FORMATS
    )
    # Add the writing

    legend = Text(x=5, y=100, text=['''Flight frequency'''], x_offset = 15, **pss.FONT_PROPS_SM)
    plot.add_glyph(source, legend, selection_glyph=legend)
    legend = Text(x=5, y=90, text=['''by passenger:'''], x_offset = 15, **pss.FONT_PROPS_SM)
    plot.add_glyph(source, legend, selection_glyph=legend)
    smlegend = Text(x=5, y=80, text=['''in milions'''], x_offset = 65, **pss.FONT_PROPS_XSM)
    plot.add_glyph(source, smlegend, selection_glyph=smlegend)

    country = Text(x='x', y='y', text='name', x_offset = 35,  y_offset=5, **pss.FONT_PROPS_XSM)
    plot.add_glyph(source, country, selection_glyph=country)

    rules = get_theme(theme)

    circle = Rect(x='x', y="y", width=20, height=10,
                  # fill_color='#722F37', line_color='#722F37',
                  fill_color='#29bdbc', line_color='#29bdbc',
                    fill_alpha='alpha', line_alpha='alpha',
                    )
    isol_aps_renderer = plot.add_glyph(source, circle, selection_glyph=circle,
                                       nonselection_glyph=circle)

    rect = Rect(x='x_int', y="y", width=20, height=10,
                  # fill_color='#722F37', line_color='#722F37',
                  fill_color='#c28cbd', line_color='#c28cbd',
                    fill_alpha='alpha', line_alpha='alpha',
                    )
    isol_aps_renderer = plot.add_glyph(source, rect, selection_glyph=rect,
                                       nonselection_glyph=rect)

    tap = TapTool(plot=plot)#, renderers=[rect_renderer])
    # hover = HoverTool(plot=plot, renderers=[rect_renderer], tooltips=tooltips)
    plot.tools.extend([tap])


    for k, v in rules.items():
        if k not in ['map_line_color', 'map_color', 'connections_color', 'grid', 'axis']:
            setattr(plot, k, v)


    # plot.outline_line_width = 2
    plot.background_fill = '#2c2c2c'

    return plot


import yaml
from yaml import SafeLoader, Loader, BaseLoader

def cds_constructor(loader, node):
    """
    Use pandas IO tools to easily load local and remote data files
    """
    bits = loader.construct_mapping(node, deep=True)
    # Pandas io read method as the key
    read_method = [key for key in bits.keys()][0]

    # Read value can be a file or url
    read_value = [value for value in bits.values()][0]

    #return a dataframe
    return getattr( pd, read_method)(read_value)

def figure_constructor(loader, node):
    """
    A YAML constructor for the bokeh.plotting module
    http://bokeh.pydata.org/en/latest/docs/reference/plotting.html
    """
    figure_data = loader.construct_mapping(node, deep=True)

    # Create the figure, using the ``figure`` key
    p = figure(
        **figure_data['figure']
    )

    # Add glyphs to the figure using the ``glyphs`` key
    glyphs = figure_data.get('glyphs', [])

    for glyph in glyphs:
        tmp = list(glyph.values())[0]
        if 'source' in tmp:
            # Convert source to column data source
            tmp['source'] = ColumnDataSource(
                tmp['source']
            )
        getattr(p, list(glyph.keys())[0])(**tmp)

    return p

def widget_factory(widget_class):
    def _(loader, node):
        data = loader.construct_mapping(node, deep=True)
        return widget_classt(**data)
    return _


class UILoader(SafeLoader):
    def __init__(self, *args, **kws):
        self._objects = {}
        super(UILoader, self).__init__(*args, **kws)

    @classmethod
    def add_widget_constructor(cls, widget_class):
        tag = "!%s" % widget_class.__name__

        def constructor(loader, node):
            data = loader.construct_mapping(node, deep=True)
            for k, v in data.items():
                if isinstance(v, basestring) and \
                        (v.startswith('{{') and v.endswith('}}')):
                    stripped = v[2:-2].strip().split(" ")
                    if len(stripped) >= 2:
                        box, items = stripped[0], stripped[1:]
                        if box.lower() == 'hbox':
                            box = HBox
                        elif box.lower() == 'vbox':
                            box = VBox
                        else:
                            raise ValueError("Impossible to parse value: %s" % v)

                        loaded_widgets = [loader._objects.get(item, item) for item in items]
                        clean = box(*loaded_widgets)
                    else:
                        clean = stripped[0]

                    data[k] = clean

            widget = widget_class(**data)
            loader._objects[data['name']] = widget

            return widget

        cls.add_constructor(tag, constructor)


def app_object_constructor(loader, node):
    """
    A YAML constructor for the bokeh.plotting module
    http://bokeh.pydata.org/en/latest/docs/reference/plotting.html
    """
    data = loader.construct_mapping(node, deep=True)
    loaded_widget = loader._objects[data['name']]

    child = data.get('child', None)
    if child is not None:
        loaded_widget._child = child

    tabs = data.get('tabs', None)
    if tabs is not None:
        loaded_widget._tabs = tabs

    content = data.get('content', None)
    if content is not None:
        loaded_widget._content = content

    return loaded_widget

UILoader.add_constructor("!app_object", app_object_constructor)
UILoader.add_constructor("!figure", figure_constructor)

widgets = [TextInput, PreText, Dialog, Panel, Tabs, Paragraph, AppVBox, AppHBox,
           Button, CheckboxGroup]

for klass in widgets:
    UILoader.add_widget_constructor(klass)


def load_from_yaml(yaml_path):
    with open (yaml_path, 'r') as source:
        text = source.read()

    data = yaml.load (text, Loader=UILoader)
    if 'widgets' not in data:
        data['widgets'] = {}

    return data

def add_app_box(yaml_box, app, yaml_layout):
    yaml_box.app = app

    for i, v in enumerate(yaml_box.children):
        if isinstance(v, basestring) and not v in app.objects:
            yaml_box.children[i] = yaml_layout[v]


def get_obj(name, app, layout, return_object=False):
    if isinstance(name, basestring) and not name in app.objects:
        if name.startswith('{{') and name.endswith('}}'):
            stripped = name[2:-2].strip().split(" ")
            if len(stripped) >= 2:
                box, items = stripped[0], stripped[1:]
                if box.lower() == 'hbox':
                    box = HBox
                elif box.lower() == 'vbox':
                    box = VBox
                else:
                    raise ValueError("Impossible to parse value: %s" % v)

                loaded_widgets = [get_obj(item, app, layout, True) for item in items]
                return box(*loaded_widgets)
            else:
                raise ValueError("Invalid value %s" % name)
        else:
            return layout[name]

    if return_object and isinstance(name, basestring):
        return app.objects[name]

    return name


def create_app(name, route, yaml_path, constructor=None):
    yapp = load_from_yaml(yaml_path)


    @simpleapp(**yapp['widgets'].values())
    def app(search_button):
        objects = dict(yapp['ui'])

        if callable(constructor):
            return construct(objects)

    @app.layout
    def create_layout(app):
        layout = yapp['layout']
        for k, v in layout.items():
            if k != 'app' and isinstance(v, (AppHBox, AppVBox)):
                ui.add_app_box(v, app, layout)

        for k, v in layout.items():
            if k != 'app' and isinstance(v, Panel):
                v.child = ui.get_obj(v.child, app, layout)

        for k, v in layout.items():
            if k != 'app' and isinstance(v, Tabs):
                v.tabs = [ui.get_obj(x, app, layout, True) for x in v.tabs]

        for k, v in layout.items():
            if k != 'app' and isinstance(v, Dialog):
                v.content = ui.get_obj(v.content, app, layout)

        add_app_box(layout['app'], app, layout)

        return layout['app']

    app.route(route)

class YamlApp(object):
    def __init__(self, yaml_path, route=None):
        self.yaml_path = yaml_path
        self.yapp = load_from_yaml(yaml_path)


        @simpleapp(*self.yapp['widgets'].values())
        def napp(*args):
            objects = dict(self.yapp['ui'])

            return self.app_objects(objects, *args)


        @napp.layout
        def create_layout(app):
            return self.create_layout(app)

        # TODO: We should validate and raise an error if no route is specified
        napp.route(route or self.yapp.get('route', '/'))
        self.app = napp

        self.add_events()

    @property
    def name(self):
        return self.app.name


    @property
    def widgets(self):
        return self.app.widgets

    def app_objects(self, objects):
        return objects

    def create_layout(self, app):
        layout = self.yapp['layout']
        for k, v in layout.items():
            if k != 'app' and isinstance(v, (AppHBox, AppVBox)):
                add_app_box(v, app, layout)

        for k, v in layout.items():
            if k != 'app' and isinstance(v, Panel):
                v.child = get_obj(v.child, app, layout)

        for k, v in layout.items():
            if k != 'app' and isinstance(v, Tabs):
                v.tabs = [get_obj(x, app, layout, True) for x in v.tabs]

        for k, v in layout.items():
            if k != 'app' and isinstance(v, Dialog):
                v.content = get_obj(v.content, app, layout)

        add_app_box(layout['app'], app, layout)

        return layout['app']