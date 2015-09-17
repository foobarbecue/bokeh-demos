"""
This file demonstrates embedding a bokeh applet into a flask
application. See the README.md file in this dirrectory for
instructions on running.
"""
from __future__ import print_function

import logging
logging.basicConfig(level=logging.INFO)

from bokeh.pluginutils import app_document
from bokeh.models.widgets.layouts import SimpleApp

from flask import Flask, render_template, request


app = Flask('sampleapp')

bokeh_url = "http://localhost:5006"
applet_url = "http://localhost:5050"

@app_document("airports_example", bokeh_url)
def make_stock_applet(ais):
    app = SimpleApp.create(ais.app.name, ais.app.widgets)
    return app

@app.route("/")
def applet():
    import airports_server as ais
    applet = make_stock_applet(ais)
    return render_template(
        "airports_embeded.html",
        app_url = bokeh_url + "/bokeh/jsgenerate/VBox/StockApp/StockApp",
        app_tag = applet._tag
    )

@app.route("/yaml")
def applet_yaml():
    import airports_server_yaml as ais
    theme = ais.YAPP.theme = request.args.get('theme', 'dark')
    applet = make_stock_applet(ais)
    return render_template(
        "airports_embeded.html",
        app_url = bokeh_url + "/bokeh/jsgenerate/VBox/StockApp/StockApp",
        app_tag = applet._tag,
        theme = theme,
    )

if __name__ == "__main__":
    print("\nView this example at: %s\n" % applet_url)
    app.debug = True
    app.run(host='0.0.0.0', port=5050)
