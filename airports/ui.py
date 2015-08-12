from __future__ import print_function
from collections import OrderedDict
from bokeh.models.tools import HoverTool, TapTool
from bokeh.models.glyphs import Circle, Patches, Text
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
    plot.multi_line('xs', 'ys', color=connections_color, line_width=1,
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
        if k not in ['map_line_color', 'map_color']:
            setattr(plot, k, v)

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

    plot = figure(title="", plot_width=200, plot_height=200,
                  tools="pan,box_zoom,box_select,tap,hover,resize,reset",
                  toolbar_location = None,
                  x_range = [ox-max_radius, ox+max_radius],
                  y_range = [oy-max_radius, oy+max_radius],
    )

    chunk = max_radius / 5.
    for i in range(5):
        rad = max_radius - chunk * i
        plot.circle([ox], [oy], radius=rad, fill_color=None, line_color="lightgrey")

    plot.multi_line('xs', 'ys', color=connections_color, line_width=1,
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
        console.log("FIRED!");
        console.log(ind);

        url = "/select_airport?id=" + data.id[ind];
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


def create_legend(source):#, value_string, color_string, bar_color):
    # Plot and axes
    xdr = Range1d(0, 220)
    ydr = Range1d(0, 120)

    plot = Plot(
        x_range=xdr,
        y_range=ydr,
        title="",
        plot_width=200,
        plot_height=200,
        min_border=0,
        **pss.PLOT_FORMATS
    )
    # Add the writing
    legend = Text(x=5, y=150, text=['Legend:'], x_offset = 10,  y_offset=5, **pss.FONT_PROPS_LG)

    country = Text(x='x', y='y', text='name', x_offset = 15,  y_offset=5, **pss.FONT_PROPS_SM)
    # percent = Text(x=15, y=10, text=value_string, text_color=color_string, **FONT_PROPS_LG)  # nopep8
    # percent_sign = Text(x=69, y=10, text=['%'], text_color=color_string, **FONT_PROPS_LG)  # nopep8
    # line_one = Text(x=90, y=28, text=['of people had'], **FONT_PROPS_SM)
    # line_two_p1 = Text(x=90, y=14, text=['access in'], **FONT_PROPS_SM)
    # line_two_p2 = Text(x=136, y=14, text='year', **FONT_PROPS_SM)
    plot.add_glyph(source, legend)
    plot.add_glyph(source, country, selection_glyph=country)

    circle = Circle(x='x', y="y", fill_color='green', line_color='green',
                    # fill_alpha='alpha', line_alpha='alpha',
                    radius='radius')
    isol_aps_renderer = plot.add_glyph(source, circle, selection_glyph=circle,
                                       nonselection_glyph=circle)

    # plot.add_glyph(source, percent, selection_glyph=percent)
    # plot.add_glyph(source, Text(), selection_glyph=percent_sign)
    # plot.add_glyph(line_one)
    # plot.add_glyph(line_two_p1)
    # plot.add_glyph(source, Text(), selection_glyph=line_two_p2)

    # Add the orange box with year
    # shadow = Triangle(x=150, y=109, size=25, fill_color=ORANGE_SHADOW, line_color=None)  # nopep8
    # plot.add_glyph(shadow)
    # # Add the blue bar
    # rect = Rect(x=75, y=99, width=150, height=5, fill_color=bar_color, line_color=None)  # nopep8
    # plot.add_glyph(rect)
    # box = Rect(x=200, y=100, width=100, height=40, fill_color=ORANGE, line_color=None)  # nopep8
    # plot.add_glyph(box)
    # year = Text(x=160, y=85, text='year', text_font_size='18pt', text_color="#FFFFF", text_font_style="bold")  # nopep8
    # plot.add_glyph(source, Text(), selection_glyph=year)

    return plot