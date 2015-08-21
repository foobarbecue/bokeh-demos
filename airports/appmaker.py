import importlib
import yaml
from yaml import SafeLoader, Loader, BaseLoader
import pandas as pd

from bokeh.models.widgets import (HBox, VBox, VBoxForm, PreText, DataTable,
                                  AppVBox, AppHBox, CheckboxGroup, Dialog,
                                  AutocompleteInput, Button, TextInput,
                                  Paragraph, Select,
                                  TableColumn, StringFormatter, NumberFormatter,
                                  StringEditor, IntEditor, NumberEditor,
                                  Panel, Tabs, Slider, Dialog)
from bokeh.models.sources import ColumnDataSource
from bokeh.plotting import figure, show
from bokeh.simpleapp import simpleapp


def cds_constructor(loader, node):
    """
    Use pandas IO tools to easily load local and remote data files
    """
    bits = loader.construct_mapping(node, deep=True)
    # Pandas io read method as the key
    read_method = [key for key in bits.keys()][0]

    # Read value can be a file or url
    read_value = bits.pop(read_method)

    limit = bits.pop('limit', None)

    ds = getattr(pd, read_method)(read_value, **bits)
    print (read_value, limit)
    if limit is not None:
        ds = ds[:int(limit)]
        print ("LIMITED!", len(ds))

    return ds

def figure_constructor(loader, node):
    """
    A YAML constructor for the bokeh.plotting module
    http://bokeh.pydata.org/en/latest/docs/reference/plotting.html
    """
    figure_data = loader.construct_mapping(node, deep=True)

    # Create the figure, using the ``figure`` key
    p = figure(**figure_data['figure'])

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


def app_event_handler(loader, node):
    """
    A YAML constructor for the bokeh.plotting module
    http://bokeh.pydata.org/en/latest/docs/reference/plotting.html
    """
    data = loader.construct_mapping(node, deep=True)
    return data

UILoader.add_constructor("!app_object", app_object_constructor)
UILoader.add_constructor("!figure", figure_constructor)
UILoader.add_constructor("!Event", app_event_handler)
UILoader.add_constructor("!io", cds_constructor)

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

        self.datasets = {}
        self.sources = {}
        self.env = {}

        self.init_datasets()
        self.post_process_datasets()
        self.create_sources()

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

        self.init_app()

        self.add_events()


    def init_app(self):
        """ Init hook that can be used to customize application initialization
        without ovewriting __init__ """

    def init_datasets(self):
        datasets = self.yapp.get('datasets', {})

        for dsname, ds in datasets.items():
            self.datasets[dsname] = ds

    def post_process_datasets(self):
        pass

    def create_sources(self):
        for dsname, ds in self.datasets.items():
            self.sources[dsname] = ColumnDataSource(ds.to_dict(orient='list'), tags=[dsname])

    @property
    def name(self):
        return self.app.name

    @property
    def widgets(self):
        return self.app.widgets

    def add_events(self):
        handlers = self.yapp.get('event_handlers', {})
        module = ''

        if handlers:
            module = handlers.pop('module', '')
            if module:
                module = importlib.import_module(module)

        def load_foo(fooname):
            if module:
                return getattr(module, fooname)
            else:
                return globals()[fooname]

        for evt_handler in handlers.values():
            key = ''
            for k in ['tags', 'name']:
                if k in evt_handler:
                    key = k

            assert key, "Event handlers must specify at least 'tags' or 'name' field!"

            object_name = evt_handler[key]

            foo = load_foo(evt_handler['handler'])
            foo = self.app.update([({key:  object_name}, [evt_handler['property']])])(foo)

            print("decorated", evt_handler[key])

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
