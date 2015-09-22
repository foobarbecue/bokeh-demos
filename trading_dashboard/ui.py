import os
import six
from bokeh.resources import Resources
from bokeh.templates import RESOURCES
from bokeh.embed import components
from jinja2 import Template
import webbrowser

from bokeh.embed import autoload_server

# plots can be a single PlotObject, a list/tuple, or even a dictionary
INLINE = Resources(mode="inline", minified=False,)
assets = {
    'resources': RESOURCES.render(
        js_raw=INLINE.js_raw,
        css_raw=INLINE.css_raw,
        js_files=INLINE.js_files,
        css_files=INLINE.css_files,
    ),

}

LIVE_COLOR = "#8e4d9e" # "#396285"
CLOSE_COLOR = "#2cbdb9" # "#CE603D"
HIST_COLOR = "#b9bf3d" #CAB2D6

def style_plot(p, theme='dark'):
    p.background_fill = '#2b2b2b'
    p.border_fill = '#2b2b2b'
    p.title_text_color = "#0f918b"
    p.title_text_font = "Verdana"
    p.title_text_font_size = '16pt'

    p.axis.axis_label_text_color = "#c6c5c5"
    p.axis.axis_label_text_font_size = '9pt'
    p.axis.axis_label_text_font = "Verdana"
    p.axis.axis_label_text_font_style="bold"
    # Semi-bold, 9pt, #c6c5c5

    p.axis.major_label_text_color = "#c6c5c5"
    p.axis.major_label_text_font_size="9pt"
    p.axis.major_label_text_font_style="normal"
    p.axis.major_label_text_font = "Verdana"

    p.axis.minor_tick_line_color = "#c6c5c5"

    p.grid.grid_line_alpha = 0.5
    p.grid.grid_line_dash = [6, 4]

def create_and_open(p, session, theme='dark'):
    # plots = {
    #     'mainp': p
    # }

    assets = dict(script = autoload_server(p, session))
    # assets['script'], assets['components'] = components(plots, INLINE)

    assets['table_style'] = u"""
    /* ---- 4 Slick Grid ----*/

    div.bk-data-table{
        padding-top: 15px;
    }

    div.bk-slick-row.odd{
        background: #666666;
        border: 1px solid #000000;
        color: #9f9e9e;
    }
    div.bk-slick-row.even{
        background: #666666;
        border: 1px solid #000000;
        color: #9f9e9e;
    }

    div.bk-slick-cell {
        margin-top: 1px;
        border: none;
        font-size: 12.5px;
        letter-spacing: 0.02em;
        border-right: 1px solid #000000;
        color: #9f9e9e;
    }
    div.bk-slick-row:hover,
    div.bk-slick-row:hover + div{
      border-top: 2px solid #588ED7;
      margin-top: -2px;
      height: 23px;
    }
    div.bk-slick-row:hover + div{
      margin-top: -2px;
      height: 23px;
    }
    div.bk-slick-row:hover > div:first-child{
      font-weight: bolder;
    }

    div.bk-slick-header-columns{
        border-bottom: 0px solid silver;
    }

    div.bk-cell-index {
        background-color: #666666;
    }

    div.bk-slick-header-column {
         background-image: none;
        background-color: #9f9e9e;
    }

    div.bk-data-table div.bk-ui-state-default{
        border: 1px solid #9f9e9e;
    }



    div.bk-slick-viewport{
      border-left: 0px solid #999;
    }
    /*.bk-slick-row.visited {*/
        /*font-weight:200;*/
      /*-webkit-font-smoothing:antialiased;*/
      /*color: #C8B067;*/
    /*}*/

    div.bk-slick-header-column:hover{
    background: #e2edc9;
    background: -moz-linear-gradient(top,  #e2edc9 0%, #c7ceb7 50%, #cfe0c3 100%);
    background: -webkit-gradient(linear, left top, left bottom, color-stop(0%,#e2edc9), color-stop(50%,#c7ceb7), color-stop(100%,#cfe0c3));
    background: -webkit-linear-gradient(top,  #e2edc9 0%,#c7ceb7 50%,#cfe0c3 100%);
    background: -o-linear-gradient(top,  #e2edc9 0%,#c7ceb7 50%,#cfe0c3 100%);
    background: -ms-linear-gradient(top,  #e2edc9 0%,#c7ceb7 50%,#cfe0c3 100%);
    background: linear-gradient(to bottom,  #e2edc9 0%,#c7ceb7 50%,#cfe0c3 100%);
    filter: progid:DXImageTransform.Microsoft.gradient( startColorstr='#e2edc9', endColorstr='#cfe0c3',GradientType=0 );
    }

    /* ---- end 4 Slick Grid ----*/
"""

    themes = dict(
        light=u"""
        div#sidebar{
            background-color: #bfbebe;
            width: 400px;
            padding: 5px;
        }
        input[type=text]{
            background-color: #bfbebe;
            width: 80px;
            display: inline;
            padding: 5px;
            height: 20px;

        }
        select.bk-widget-form-input{
            background-color: #adadad;
            width: auto;
            display: inline;
            height: 25px;
        }
        """,
        dark=u"""
        div#sidebar{
            background-color: #666666;
            width: 400px;
            padding: 5px;
        }
        input[type=text]{
            background-color: #adadad;
            width: 80px;
            display: inline;
            padding: 5px;
            height: 20px;
        }
        select.bk-widget-form-input{
            background-color: #adadad;
            width: auto;
            display: inline;
            height: 25px;
        }
        """
    )
    assets['theme'] = themes[theme]

    template = Template(u'''<!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="utf-8">
            <title>Bokeh Scatter Plots</title>

            <style>
                body{
                    margin: 0;
                    background-color: #474746;
                }
                #main_container{
                    padding: 0 10%;
                }
                {{ theme }}
                div.bk-slider-horizontal{
                    width: 90%;
                    height: 15px;
                    min-width: 100px;
                    padding: 0 5px;
                }
                label {
                    display: inline;
                    margin-bottom: 5px;
                    padding-top: 12px;
                    font-weight: bold;
                    padding-left: 15px;
                }
                button.bk-bs-btn {
                    height: 25px;
                    padding: 3px 5px;
                    margin-top: 9px;
                }
                div.bk-widget-form-group {
                    margin-bottom: 0;
                }


                {{ table_style }}
            </style>
        </head>
        <body>

            <div id="main_container">
                {{ script }}
            </div>
        </body>
    </html>
    ''')

    html_file = 'embed_multiple.html'
    with open(html_file, 'w') as textfile:
        textfile.write(template.render(**assets).encode('utf-8'))
    url = 'file:{}'.format(six.moves.urllib.request.pathname2url(os.path.abspath(html_file)))
    webbrowser.open(url)


