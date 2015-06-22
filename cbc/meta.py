'''I refuse to write the same thing over and over again in meta.yaml.
And yeah, conda supports Jinja2, but ugh... No.
'''

import os
import conda_build.metadata
import yaml
from configparser import SafeConfigParser, ExtendedInterpolation
from collections import OrderedDict
from .environment import Environment

class SpecError(Exception):
    pass

class Spec(object):
    def __init__(self, filename, env):
        
        if not os.path.exists(filename):
            raise OSError('"{0}" does not exist.'.format(filename));
        
        self.filename = filename
        
        if not isinstance(env, Environment):
            raise SpecError('Expecting instance of cbc.environment.Environment, got: "{0}"'.format(type(env)))
        
        self.env = env
        self.keywords = ['build_ext', 'cgi']
        
        
        self.fields = self.convert_conda_fields(conda_build.metadata.FIELDS)
        self.config = SafeConfigParser(interpolation=ExtendedInterpolation(), allow_no_value=True)
        # Include built-in Conda metadata fields
        self.config.read_dict(self.fields)
        # Include user-defined build fields
        self.config.read(self.filename)
        # Convert ConfigParser -> dict
        self.spec = self.as_dict(self.config)
        
        self.spec_metadata = {}
        for keyword in self.keywords:
            if self.spec[keyword]:
                self.spec_metadata[keyword] = self.spec[keyword]  

        # Convert dict to YAML-compatible dict
        self.conda_metadata = self.scrub(self.spec, self.keywords)

    def conda_write_meta(self):
        with open(os.path.join(self.env.config['meta']), 'w+') as metafile:
            yaml.safe_dump(self.conda_metadata, metafile, default_flow_style=False, line_break=True, indent=4)

    def convert_conda_fields(self, fields):
        temp = OrderedDict()
        for fkey, fval in fields.items():
            temp[fkey] = { x: '' for x in fval}

        return temp

    def scrub(self, obj, force_remove=[]):
        obj_c = obj.copy()
        if isinstance(obj_c, dict):
            for key,val in obj_c.items():
                for reserved in force_remove:
                    if reserved in key:
                        del obj[reserved]
                        continue
                if isinstance(val, dict):
                    val = self.scrub(val)
                if val is None or val == {} or not val:
                    del obj[key]

        return obj


    def as_dict(self, config):
        """
        Converts a ConfigParser object into a dictionary.

        The resulting dictionary has sections as keys which point to a dict of the
        sections options as key => value pairs.
        """
        the_dict = {}
        for section in config.sections():
            the_dict[section] = {}
            for key, val in config.items(section):
                for cast in (int, float, bool, str):
                    try:
                        the_dict[section][key] = cast(val)
                    except ValueError:
                        pass

        return the_dict

    