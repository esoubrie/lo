"""Definition of useful linear operators"""
import numpy as np
from copy import copy
from interface import LinearOperator

def eigen_operator(shape, e, v, **kargs):
    """
    Returns a LinearOperator using eigenvalues and eigenvectors
    as given by sparse.linalg.eigen.
    This LinearOperator can be seen as an approximation of the
    operator on which the eigen function has been run.

    Inputs
    -------
    shape : shape of the matrix
    e : eigenvalues
    v : eigenvectors
    dtype : data type (e.g np.float64)

    Outputs
    -------
    A : LinearOperator
    """
    def matvec(x):
        k = [np.dot(x.T, vi) for vi in v]
        return np.sum([ki * ei * vi for ki, ei, vi in zip(k, e, v)], axis=0)
    return LinearOperator(shape, matvec=matvec, rmatvec=matvec, **kargs)

def ndoperator(shapein, shapeout, matvec, rmatvec=None, dtype=np.float64,
               dtypein=None, dtypeout=None):
    "Transform n-dimensional linear operators into LinearOperators"
    sizein = np.prod(shapein)
    sizeout = np.prod(shapeout)
    shape = (sizeout, sizein)
    def ndmatvec(x):
        return matvec(x.reshape(shapein)).reshape(sizeout)
    if rmatvec is not None:
        def ndrmatvec(x):
            return rmatvec(x.reshape(shapeout)).reshape(sizein)
    else:
        ndrmatvec = None
    return LinearOperator(shape, matvec=ndmatvec, rmatvec=ndrmatvec, 
                          dtype=dtype, dtypein=dtypein, dtypeout=dtypeout)

def masubclass(xin=None, xout=None, shapein=None, shapeout=None, classin=None,
               classout=None, dictin=None, dictout=None,
               matvec=None, rmatvec=None, dtype=np.float64, dtypein=None, dtypeout=None):
    "Wrap linear operation working on ndarray subclasses in MaskedArray style"
    if xin is not None:
        shapein = xin.shape
        classin = xin.__class__
        dictin = xin.__dict__
        dtype = xin.dtype
    if xout is not None:
        shapeout = xout.shape
        classout = xout.__class__
        dictout = xout.__dict__
    sizein = np.prod(shapein)
    sizeout = np.prod(shapeout)
    shape = (sizeout, sizein)
    if matvec is not None:
        def ndmatvec(x):
            xi = classin(x.reshape(shapein))
            xi.__dict__ = dictin
            return matvec(xi).reshape(sizeout)
    else:
        raise ValueError('Requires a matvec function')
    if rmatvec is not None:
        def ndrmatvec(x):
            xo = classout(x.reshape(shapeout))
            xo.__dict__ = dictout
            return rmatvec(xo).reshape(sizein)
    else:
        ndrmatvec = None
    return LinearOperator(shape, matvec=ndmatvec, rmatvec=ndrmatvec, dtype=dtype,
                          dtypein=dtypein, dtypeout=dtypeout)

def ndsubclass(xin=None, xout=None, shapein=None, shapeout=None, classin=None,
               classout=None, dictin=None, dictout=None,
               matvec=None, rmatvec=None, dtype=np.float64, dtypein=None, dtypeout=None):
    "Wrap linear operation working on ndarray subclasses in InfoArray style"
    if xin is not None:
        shapein = xin.shape
        classin = xin.__class__
        dictin = xin.__dict__
        dtype = xin.dtype
    if xout is not None:
        shapeout = xout.shape
        classout = xout.__class__
        dictout = xout.__dict__
    sizein = np.prod(shapein)
    sizeout = np.prod(shapeout)
    shape = (sizeout, sizein)
    if matvec is not None:
        def ndmatvec(x):
            xi = classin(shapein)
            xi.__dict__ = dictin
            xi[:] = x.reshape(shapein)
            return matvec(xi).reshape(sizeout)
    else:
        raise ValueError('Requires a matvec function')
    if rmatvec is not None:
        def ndrmatvec(x):
            xo = classout(shapeout)
            xo.__dict__ = dictout
            xo[:] = x.reshape(shapeout)
            return rmatvec(xo).reshape(sizein)
    else:
        ndrmatvec = None
    return LinearOperator(shape, matvec=ndmatvec, rmatvec=ndrmatvec, dtype=dtype,
                          dtypein=dtypein, dtypeout=dtypeout)

def diag(d, shape=None, dtype=None):
    "Returns a diagonal Linear Operator"
    if shape is None:
        shape = 2 * (d.size,)
    if shape[0] != shape[1]:
        raise ValueError('Diagonal operators must be square')
    def matvec(x):
        return d * x
    if dtype is None:
        dtype = d.dtype
    return LinearOperator(shape, matvec=matvec, rmatvec=matvec, dtype=dtype)

def identity(shape, dtype=np.float64):
    "Returns the identity linear Operator"
    if shape[0] != shape[1]:
        raise ValueError('Identity operators must be square')
    def matvec(x):
        return x
    return LinearOperator(shape, matvec=matvec, rmatvec=matvec, dtype=dtype)

def eye(shape, dtype=np.float64):
    "Returns the identity linear Operator"
    if shape[0] == shape[1]:
       return identity(shape, dtype=dtype)
    else:
        def matvec(x):
            return x[:shape[0]]
        def rmatvec(x):
            return np.concatenate(x, np.zeros(shape[0] - shape[1]))
        return LinearOperator(shape, matvec=matvec, rmatvec=rmatvec, dtype=dtype)

def fftn(shapein, dtypein=np.float64, dtypeout=np.complex128, s=None, axes=None):
    "fftn LinearOperator"
    import numpy.fft
    if s is None:
        shapeout = shapein
    else:
        shapeout = s
    def matvec(x):
        return np.fft.fftn(x, s=s, axes=axes)
    def rmatvec(x):
        return np.fft.ifftn(x, s=s, axes=axes)
    return ndoperator(shapein, shapeout, matvec, rmatvec, dtypein=dtypein,
                      dtypeout=dtypeout)

def fft2(shapein, dtypein=np.float64, dtypeout=np.complex128, s=None, axes=(-2, -1)):
    "fft2 LinearOperator"
    import numpy.fft
    if len(shapein) != 2:
        raise ValueError('Error expected 2 dimensional shape')
    if s is None:
        shapeout = shapein
    else:
        shapeout = s
    def matvec(x):
        return np.fft.fftn(x, s=s, axes=axes)
    def rmatvec(x):
        return np.fft.ifftn(x, s=s, axes=axes)
    return ndoperator(shapein, shapeout, matvec, rmatvec, 
                      dtypein=dtypein, dtypeout=dtypeout)

def convolve(shapein, kernel, mode='full'):
    """ Linear Operator to convolve two N-dimensional arrays

    See Also:
      scipy.signal.convolve
    """
    from scipy.signal import convolve
    #if len(shapein) != 2:
    #    raise ValueError('Error expected 2 dimensional shape')
    if mode == 'full':
        shapeout = [s + ks - 1 for s, ks in zip(shapein, kernel.shape)]
    if mode == 'valid':
        shapeout = [s - ks - 1 for s, ks in zip(shapein, kernel.shape)]
    if mode == 'same':
        shapeout = shapein
    def matvec(x):
        return convolve(x, kernel, mode=mode)
    def rmatvec(x):
        if mode == 'full':
            rmode = 'valid'
        elif mode == 'valid':
            rmode = 'full'
        elif mode == 'same':
            rmode = 'same'
        return convolve(x, kernel, mode=rmode)
    return ndoperator(shapein, shapeout, matvec, rmatvec, dtype=kernel.dtype)

def mask(mask, dtype=np.float64):
    "Masking as a LinearOperator"
    shapein = mask.shape
    shapeout = mask.shape
    def matvec(x):
        y = copy(x)
        y[mask==True] = 0
        return y
    return ndoperator(shapein, shapeout, matvec, matvec, dtype=dtype)

def decimate(mask, dtype=np.float64):
    "Masking as a LinearOperator"
    shapein = mask.shape
    shapeout = np.sum(mask == False)
    def matvec(x):
        return x[mask==False]
    def rmatvec(x):
        y = np.zeros(shapein, dtype=dtype)
        y[mask==False] = x
        return y
    return ndoperator(shapein, shapeout, matvec, rmatvec, dtype=dtype)

def diff(shapein, axis=-1, dtype=np.float64):
    shapeout = np.asarray(shapein)
    shapeout[axis] -= 1
    def matvec(x):
        return np.diff(x, axis=axis)
    def rmatvec(x):
        shape = list(x.shape)
        shape[axis] = 1
        border = np.zeros(shape)
        out = np.concatenate((border, x, border), axis=axis)
        return - np.diff(out, axis=axis)
    return ndoperator(shapein, shapeout, matvec, rmatvec, dtype=dtype)

def binning(shapein, factor, axis=-1, dtype=np.float64):
    shapeout = np.asarray(copy(shapein))
    shapeout[axis] /= factor
    def matvec(x):
        return bin(x, factor, axis=axis)
    def rmatvec(x):
        return replicate(x, factor, axis=axis)
    return ndoperator(shapein, shapeout, matvec=matvec, rmatvec=rmatvec, 
                      dtype=dtype)

def bin(arr, factor, axis=-1):
    shapeout = np.asarray(arr.shape)
    shapeout[axis] /= factor
    outarr = np.zeros(shapeout)
    s0 = [slice(None),] * arr.ndim
    s1 = [slice(None),] * arr.ndim
    for i in xrange(arr.shape[axis]):
        s0[axis] = i
        s1[axis] = np.floor(i / factor)
        outarr[s1] += arr[s0]
    return outarr

def replicate(arr, factor, axis=-1):
    shapeout = np.asarray(arr.shape)
    shapeout[axis] *= factor
    outarr = np.zeros(shapeout)
    s0 = [slice(None),] * arr.ndim
    s1 = [slice(None),] * arr.ndim
    for i in xrange(shapeout[axis]):
        s0[axis] = i
        s1[axis] = np.floor(i / factor)
        outarr[s0] = arr[s1]
    return outarr

def axis_mul(shapein, vect, axis=-1, dtype=np.float64):
    shapeout = shapein
    def matvec(x):
        y = np.empty(x.shape)
        s = [slice(None), ] * x.ndim
        for i in xrange(x.shape[axis]):
            s[axis] = i
            y[s] = x[s] * vect
        return y
    return ndoperator(shapein, shapeout, matvec=matvec, rmatvec=matvec,
                      dtype=dtype)

def mul(shapein, num, dtype=np.float64):
    if not np.isscalar(num):
        raise ValueError('mul expect a scalar as input')
    def matvec(x):
        y = num * x
        return y
    return ndoperator(shapein, shapein, matvec=matvec, rmatvec=matvec,
                      dtype=dtype)
