import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted

class Segment(BaseEstimator, TransformerMixin):
    ''' separate predict and transform functions with different overlap '''
    def __init__(self, width = 100, overlap = 0.5):
        self.width = width
        self.overlap = overlap
        self.f_labels = None

    def fit(self, X, y = None):
        self._reset()

        assert self.width > 0
        assert self.overlap >= 0 and self.overlap <= 1

        self.step = int(self.width * (1. - self.overlap))
        self.step = self.step if self.step >= 1 else 1
        return self

    def _reset(self):
        if hasattr(self, 'step'):
            del self.step

    def transform(self, X):
        check_is_fitted(self, 'step')
        if type(X) is np.recarray:
            X_new = self._transform_recarray(X)
        else:
            X_new = self._transform(X)

        return X_new

    def _transform(self, X):
        N = len(X)
        W = []
        for i in range(N):
            W.append(sliding_tensor(X[i], self.width, self.step))
        return np.array(W)

    def _transform_recarray(self, X):
        Xt = self._transform(X['ts'])
        Xh = []
        h_names = [h for h in X.dtype.names if h != 'ts']
        for h in h_names:
            Xh.append(X[h])
        X_new = np.core.records.fromarrays([Xt] + Xh, names = ['ts'] + h_names)
        return X_new


def sliding_window(time_series, step, width):
    '''
    segments time_series with sliding windows
    :param time_series: numpy array shape (T,)
    :param step: number of data points to advance for each window
    :param width: length of window in samples
    :return: segmented time_series, numpy array shape (N, width)
    '''
    assert step >= 1
    assert width >= 1
    w = np.hstack(time_series[i:1 + i - width or None:step] for i in range(0, width))
    return w.reshape((int(len(w)/width),width),order='F')

def sliding_tensor(mv_time_series, width, step):
    '''
    segments multivariate time series with sliding windows
    :param mv_time_series: numpy array shape (T, D) with D time series variables
    :param width: length of window in samples
    :param step: number of data points to advance for each window
    :return: multivariate temporal tensor, numpy array shape (N, W, D)
    '''

    data = []
    D = mv_time_series.shape[1]

    for j in range(D):
        data.append(sliding_window(mv_time_series[:, j], step, width)) # each item is NxW, list length D

    return np.stack(data, axis = 2)