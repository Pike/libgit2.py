class Repository(object):
    def do_stuff(self):
        return conf.lib.do_stuff()
    pass


class CachedConfig(object):
    _lib = None
    @property
    def lib(self):
        if not self._lib:
            from . import conf
            self._lib = conf.lib
        return self._lib
conf = CachedConfig()
