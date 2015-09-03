This Demo folder contains a collection of small scripts with examples about
how to create an interactive application that performs realtime downsampling
over **simulated** stocks prices over period of 15 years using bokeh AjaxDataSource and 
a simple flask server. 

**WARNING**: The data used for this example is simulated!!


Examples included:


flask_server_minutes
====================

Simple flask server that provides a REST service that serves the data necessary
for the bokeh exmaples to work.

**IMPORTANT**: This script must be running for the examples to work correctly

To run the script execute:

>> python flask_server_minutes.py


subsample
=========

Simple support module used by flask_server_minutes to resample data.

This script was not created to run as a standalone script.


simple_ajax
===========

This example show a very simple plot using an AjaxDataSource to display
stock prices data (without any real resampling or interactivity features).

To run the script execute:

>> python simple_ajax.py



stocks_panel
============

This example shows how to use an AjaxDataSource and JSCallbacks to drive
communications with simple AJAX calls resulting in ranges updates and 
data downsampling on the server side (not bokeh-server but the flask 
service served by flask_server_minutes).

It includes a smaller top plot and a main plot below. The smaller top 
plot is intended to be used as general data view where users can select
a period of data. The lower main plot will be updated with resampled data
focusing on the selected period.


To run the script execute:

>> python stocks_panel.py


Instructions: 

1. Run the script as described above. It will open your browser window
with the example.

2. Use the smaller plot on the top to select regions of data to display on 
the main plot below.



custom_stocks_panel
===================

This example shows an improved version of the previous "stocks_panel" example
with a custom interface and theme. It's also possible to change themes and see
how those apply to the overall page UI.

To run the script execute:

>> python custom_stocks_panel.py
