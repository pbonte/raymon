import numpy as np
from abc import abstractmethod
import raymon.types as rt


class Transform:

    @abstractmethod
    def __call__(self, data):
        pass


class Histogram(Transform):

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, img):
        counts, edges = np.histogram(a=img.data, **self.kwargs)
        hist = rt.Histogram(counts=counts, edges=edges)
        return hist


class ChannelSelect(Transform):

    def __init__(self, store, **kwargs):
        super().__init__(store)
        self.kwargs = kwargs

    def __call__(self, data):
        hist = rt.Numpy(data=data.data[:, :, self.kwargs['channel']])
        return hist


tfs = {
    'Histogram': Histogram,
}