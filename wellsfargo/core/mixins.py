class UnsavableModel(object):
    def save(self):
        raise RuntimeError('Can not save %s. Object must be transient only.' % self.__class__.__name__)
