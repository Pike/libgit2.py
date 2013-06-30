from . import api

class Base(object):
    pass

class Repository(Base, api.Repository):
    pass

class Config(object):
    _lib = None
    class Inner:
        def create_repository(self):
            return Repository()
        def do_stuff(repo):
            return 'hoho'
    @property
    def lib(self):
        if self._lib is None:
            self._lib = self.Inner()
        return self._lib
conf = Config()
