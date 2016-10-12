from .utils import Singleton
from .externals.moduleman.registrant import BRegistrant
from .externals.moduleman.loader import FileLoader
from .externals.moduleman.loader import DirLoader
from .externals.settings.settings import SettingsBase
from .myhttp import HttpPool

import os

version = "2.2"

class Settings(SettingsBase):
    def get_config_file(self):
	return "wfuzz.ini"

    def set_defaults(self):
	return dict(
	    plugins=[("bing_apikey", '')],
	    kbase=[("discovery.blacklist", '.jpg-.gif-.png-.jpeg-.mov-.avi-.flv-.ico')],
	    connection=[("concurrent", '10'),
		("conn_delay", '90'),
		("req_delay", '90'),
		("retries", '3'),
		("User-Agent", "Wfuzz/%s" % version)
	    ],
	    general=[("default_printer", 'raw'),("cancel_on_plugin_except","1"),
                ("concurrent_plugins", '3'),
                ("encode_space", '1')
            ],
	)

class Facade:
    __metaclass__ = Singleton 

    def __init__(self):
	self.__printers = None
	self.__plugins = None
	self.__encoders = None
	self.__iterators = None
	self.__payloads = None

	self.sett = Settings()

        self.http_pool = HttpPool(int(self.sett.get("connection","retries")))

    def get_path(self, directory = None):
        abspath = os.path.abspath(__file__)
        ret = os.path.dirname(abspath)

        return os.path.join(ret, directory) if directory else ret

    def _load(self, cat):
	try:
	    if cat == "printers":
		if not self.__printers:
		    self.__printers = BRegistrant(FileLoader(**{"filename": "printers.py", "base_path": self.get_path("plugins")}))
		return self.__printers
	    elif cat == "plugins" or cat == "parsers":
		if not self.__plugins:
		    self.__plugins = BRegistrant(DirLoader(**{"base_dir": "scripts", "base_path": self.get_path("plugins")}))
		return self.__plugins
	    if cat == "encoders":
		if not self.__encoders:
		    self.__encoders = BRegistrant(FileLoader(**{"filename": "encoders.py", "base_path": self.get_path("plugins")}))
		return self.__encoders
	    if cat == "iterators":
		if not self.__iterators:
		    self.__iterators = BRegistrant(FileLoader(**{"filename": "iterations.py", "base_path": self.get_path("plugins")}))
		return self.__iterators
	    if cat == "payloads":
		if not self.__payloads:
		    self.__payloads = BRegistrant(DirLoader(**{"base_dir": "payloads", "base_path": self.get_path("plugins")}))
		return self.__payloads
	    else:
		raise FuzzException(FuzzException.FATAL, "Non-existent plugin category %s" % which)
	except Exception, e:
	    raise FuzzException(FuzzException.FATAL, "Error loading plugins: %s" % str(e))

    def proxy(self, which):
	return self._load(which)

    def __getattr__(self, name):
        if name in ["printers", "payloads", "iterators", "encoders", "parsers"]:
            return self.proxy(name)
        else:
            raise AttributeError

    def get_printer(self, name):
	try:
	    return self._load("printers").get_plugin("printers/" + name)
	except KeyError:
	    raise FuzzException(FuzzException.FATAL, name + " printer does not exists (-e printers for a list of available printers)")

    def get_payload(self, name):
	try:
	    return self._load("payloads").get_plugin("payloads/" + name + "/" + name)
	except KeyError:
	    raise FuzzException(FuzzException.FATAL, name + " payload does not exists (-e payloads for a list of available payloads)")

    def get_iterator(self, name):
	try:
	    return self._load("iterators").get_plugin("iterations/" + name)
	except KeyError:
	    raise FuzzException(FuzzException.FATAL, name + " iterator does not exists (-m iterators for a list of available iterators)")

    def get_encoder(self, name):
	try:
	    return self._load("encoders").get_plugin("encoders/" + name)()
	except KeyError:
	    raise FuzzException(FuzzException.FATAL, name + " encoder does not exists (-e encodings for a list of available encoders)")

    def get_parsers(self, filterstr):
	try:
	    return self._load("plugins").get_plugins(filterstr)
	except Exception, e:
	    raise FuzzException(FuzzException.FATAL, "Error selecting scripts: %s" % str(e))