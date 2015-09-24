
#How to run the demos

All the demos currently run with the custom sandbox/appmaker2 Bokeh experimental
branch. Before running the demos:
 
* ensure to git checkout your bokeh repository on that branch
* rebuild bokehjs. It's recommended to clean, reinstall node modules and
rebuild with gulp by running:

    1. cd bokehjs
    2. rm -r node_modules
    3. npm install
    4. gulp build

* run python setup.py develop --install_js
  

Airports_Map
============

* cd into the demo folder:

>> cd <path_to_repo>/bokeh_cmd/airports_map

* run the bokeh develop cmd:

>> python <path_to_your_bokeh_installation>/scripts/bokeh develop .


Airports Histogram
==================

* cd into the demo folder:

>> cd <path_to_repo>/bokeh_cmd/airports_histogram

* run the bokeh develop cmd:

>> python <path_to_your_bokeh_installation>/scripts/bokeh develop .
