"""Objects to handle the coordinates and coordinate system.
Note they are an atribute at :obj:`xcompact3d_toolbox.parameters.ParametersExtras`,
so they work together with all the other parameters. They are presented here for reference.
"""
from __future__ import annotations

from typing import Type

import numpy as np
import traitlets

from .param import param


class Coordinate(traitlets.HasTraits):
    """A coordinate.
    
    Thanks to traitlets_, the attributes can be type checked, validated and also trigger
    ‘on change’ callbacks. It means that:

    - :obj:`grid_size` is validated to just accept the values expected by XCompact3d
      (see :obj:`xcompact3d_toolbox.mesh.Coordinate.possible_grid_size`);
    - :obj:`delta` is updated after any change on :obj:`grid_size` or :obj:`length`;
    - :obj:`length` is updated after any change on :obj:`delta` (:obj:`grid_size` remais constant);
    - :obj:`grid_size` is reduced automatically by 1 when :obj:`is_periodic` changes to :obj:`True`
      and it is added by 1 when :obj:`is_periodic` changes back to :obj:`False`
      (see :obj:`xcompact3d_toolbox.mesh.Coordinate.possible_grid_size`);

    All these functionalities aim to make a user-friendly interface, where the consistency
    between different coordinate parameters is ensured even when they change at runtime.

    .. _traitlets: https://traitlets.readthedocs.io/en/stable/index.html

    Parameters
    ----------
    length : float
        Length of the coordinate (default is 1.0).
    grid_size : int
        Number of mesh points (default is 17).
    delta : float
        Mesh resolution (default is 0.0625).
    is_periodic : bool
        Specifies if the boundary condition is periodic (True) or not (False) (default is False).

    Notes
    -----
        There is no need to specify both :obj:`length` and :obj:`delta`, because they are
        a function of each other, the missing value is automatically computed from the other.

    Returns
    -------
    :obj:`xcompact3d_toolbox.mesh.Coordinate`
        Coordinate    
    """

    length = traitlets.Float(default_value=1.0, min=0.0, max=1e10)
    grid_size = traitlets.Int(default_value=17)
    delta = traitlets.Float(default_value=0.0625, min=0.0)
    is_periodic = traitlets.Bool(default_value=False)

    _sub_grid_size = traitlets.Int(default_value=16)
    _possible_grid_size = traitlets.List(trait=traitlets.Int())

    def __init__(self, **kwargs):
        """Initializes the Coordinate class.

        Parameters
        ----------
        **kwargs
            Keyword arguments for attributes, like :obj:`grid_size`, :obj:`length` and so on.

        Raises
        -------
        KeyError
            Exception is raised when an Keyword arguments is not a valid attribute.

        Examples
        --------

        >>> from xcompact3d_toolbox.mesh import Coordinate
        >>> coord = Coordinate(length = 1.0, grid_size = 9, is_periodic = False)
        """

        self._possible_grid_size = _possible_size_not_periodic
        self.set(**kwargs)

    def __array__(self) -> Type(np.ndarray):
        """This method makes the coordinate automatically work as a numpy
        like array in any function from numpy.

        Returns
        -------
        :obj:`numpy.ndarray`
            A numpy array.
        
        Examples
        --------

        >>> from xcompact3d_toolbox.mesh import Coordinate
        >>> import numpy
        >>> coord = Coordinate(length = 1.0, grid_size = 9)
        >>> numpy.sin(coord)
        array([0.        , 0.12467473, 0.24740396, 0.36627253, 0.47942554,
               0.58509727, 0.68163876, 0.7675435 , 0.84147098])
        >>> numpy.cos(coord)
        array([1.        , 0.99219767, 0.96891242, 0.93050762, 0.87758256,
                0.81096312, 0.73168887, 0.64099686, 0.54030231])
        """        
        return np.linspace(
            start=0.0,
            stop=self.length,
            num=self.grid_size,
            endpoint=not self.is_periodic,
            dtype=param["mytype"],
        )

    def __len__(self):
        """Make the coordinate work with the Python function :obj:`len`.

        Returns
        -------
        int
            Coordinate size (:obj:`grid_size`)
        
        Examples
        --------

        >>> from xcompact3d_toolbox.mesh import Coordinate
        >>> coord = Coordinate(grid_size = 9)
        >>> len(coord)
        9
        """              
        return self.grid_size

    def __repr__(self):
        return f"{self.__class__.__name__}(length = {self.length}, grid_size = {self.grid_size}, is_periodic = {self.is_periodic})"

    def set(self, **kwargs) -> None:
        """Set a new value for any parameter after the initialization.
        
        Parameters
        ----------
        **kwargs
            Keyword arguments for attributes, like :obj:`grid_size`, :obj:`length` and so on.

        Raises
        -------
        KeyError
            Exception is raised when an Keyword arguments is not a valid attribute.

        Examples
        --------

        >>> from xcompact3d_toolbox.mesh import Coordinate
        >>> coord = Coordinate()
        >>> coord.set(length = 1.0, grid_size = 9, is_periodic = False)
        """
        if "is_periodic" in kwargs:
            self.is_periodic = kwargs.get("is_periodic")
            del kwargs["is_periodic"]
        for key, arg in kwargs.items():
            if key not in self.trait_names():
                raise KeyError(f"{key} is not a valid parameter")
            setattr(self, key, arg)

    @traitlets.validate("grid_size")
    def _validate_grid_size(self, proposal):
        if not _validate_grid_size(proposal.get("value"), self.is_periodic):
            raise traitlets.TraitError(
                f'{proposal.get("value")} is an invalid value for grid size'
            )
        return proposal.get("value")

    @traitlets.observe("is_periodic")
    def _observe_is_periodic(self, change):
        if change.get("new"):
            new_grid = self.grid_size - 1
            self._possible_grid_size = _possible_size_periodic
            self.grid_size = new_grid
        else:
            new_grid = self.grid_size + 1
            self._possible_grid_size = _possible_size_not_periodic
            self.grid_size = new_grid

    @traitlets.observe("_sub_grid_size")
    def _observe_sub_grid_size(self, change):
        new_delta = self.length / change.get("new")
        if new_delta != self.delta:
            self.delta = new_delta

    @traitlets.observe("grid_size")
    def _observe_grid_size(self, change):

        new_sgs = change.get("new") if self.is_periodic else change.get("new") - 1
        if new_sgs != self._sub_grid_size:
            self._sub_grid_size = new_sgs

    @traitlets.observe("length")
    def _observe_length(self, change):
        new_delta = change.get("new") / self._sub_grid_size
        if new_delta != self.delta:
            self.delta = new_delta

    @traitlets.observe("delta")
    def _observe_delta(self, change):
        new_length = change.get("new") * self._sub_grid_size
        if new_length != self.length:
            self.length = new_length

    @property
    def vector(self) -> Type(np.ndarray):
        """Construct a vector with :obj:`numpy.linspace` and return it.

        Returns
        -------
        :obj:`numpy.ndarray`
            Numpy array
        """
        return self.__array__()

    @property
    def size(self) -> int:
        """An alias for :obj:`grid_size`.

        Returns
        -------
        int
            Grid size
        """
        return self.grid_size

    @property
    def possible_grid_size(self) -> list:
        """Possible values for grid size.

        Due to restrictions at the FFT library, they must be equal to:

        .. math::
            n = 2^{1+a} \\times 3^b \\times 5^c,

        if the coordinate is periodic, and:

        .. math::
            n = 2^{1+a} \\times 3^b \\times 5^c + 1,

        otherwise, where :math:`a`, :math:`b` and :math:`c` are non negative integers.

        Aditionally, the derivative's stencil imposes that :math:`n \\ge 8` if periodic
        and :math:`n \\ge 9` otherwise.

        Returns
        -------
        list
            Possible values for grid size

        Notes
        -----
        There is no upper limit, as long as the restrictions are satisfied.

        Examples
        --------

        >>> from xcompact3d_toolbox.mesh import Coordinate
        >>> coordinate(is_periodic = True).possible_grid_size
        [8, 10, 12, 16, 18, 20, 24, ..., 7776, 8000, 8100, 8192, 8640, 8748, 9000]
        >>> coordinate(is_periodic = False).possible_grid_size
        [9, 11, 13, 17, 19, 21, 25, ..., 7777, 8001, 8101, 8193, 8641, 8749, 9001]
        """
        return self._possible_grid_size


class StretchedCoordinate(Coordinate):
    """Another coordinate, as a subclass of :obj:`Coordinate`.
    It includes parameters and methods to handle stretched coordinates,
    which is employed by XCompact3d at the vertical dimension ``y``.

    Parameters
    ----------
    length : float
        Length of the coordinate (default is 1.0).
    grid_size : int
        Number of mesh points (default is 17).
    delta : float
        Mesh resolution (default is 0.0625).
    is_periodic : bool
        Specifies if the boundary condition is periodic (True) or not (False) (default is False).
    istret : int
        Type of mesh refinement:

            * 0 - No refinement (default);
            * 1 - Refinement at the center;
            * 2 - Both sides;
            * 3 - Just near the bottom.
    beta : float
        Refinement parameter.

    Notes
    -----
        There is no need to specify both :obj:`length` and :obj:`delta`, because they are
        a function of each other, the missing value is automatically computed from the other.

    Returns
    -------
    :obj:`xcompact3d_toolbox.mesh.StretchedCoordinate`
        Stretched coordinate
    """
    istret = traitlets.Int(
        default_value=0,
        min=0,
        max=3,
        help="type of mesh refinement (0:no, 1:center, 2:both sides, 3:bottom)",
    )
    beta = traitlets.Float(default_value=1.0, min=0.0, help="Refinement parameter")

    def __repr__(self):
        if self.istret == 0:
            return f"{self.__class__.__name__}(length = {self.length}, grid_size = {self.grid_size}, is_periodic = {self.is_periodic})"
        return f"{self.__class__.__name__}(length = {self.length}, grid_size = {self.grid_size}, is_periodic = {self.is_periodic}, istret = {self.istret}, beta = {self.beta})"

    def __array__(self):
        """This method makes the coordinate automatically work as a numpy
        like array in any function from numpy.

        Returns
        -------
        :obj:`numpy.ndarray`
            A numpy array.
        
        Examples
        --------

        >>> from xcompact3d_toolbox.mesh import StretchedCoordinate
        >>> import numpy
        >>> coord = StretchedCoordinate(length = 1.0, grid_size = 9)
        >>> numpy.sin(coord)
        array([0.        , 0.12467473, 0.24740396, 0.36627253, 0.47942554,
               0.58509727, 0.68163876, 0.7675435 , 0.84147098])
        >>> numpy.cos(coord)
        array([1.        , 0.99219767, 0.96891242, 0.93050762, 0.87758256,
                0.81096312, 0.73168887, 0.64099686, 0.54030231])
        """ 
        if self.istret == 0:
            return super().__array__()
        return _stretching(
            istret=self.istret,
            beta=self.beta,
            yly=self.length,
            my=self._sub_grid_size,
            ny=self.grid_size,
            return_auxiliar_variables=False,
        )

    @traitlets.validate("istret")
    def _validate_istret(self, proposal):
        if proposal.get("value") == 3 and self.is_periodic:
            raise traitlets.TraitError(
                f"mesh refinement at the bottom (istret=3) is not possible when periodic"
            )
        return proposal.get("value")

    @traitlets.validate("is_periodic")
    def _validate_is_periodic(self, proposal):
        if proposal.get("value") and self.istret == 3:
            raise traitlets.TraitError(
                f"mesh refinement at the bottom (istret=3) is not possible when periodic"
            )
        return proposal.get("value")


class Mesh3D(traitlets.HasTraits):
    """A three-dimensional coordinate system

    Parameters
    ----------
    x : :obj:`xcompact3d_toolbox.mesh.Coordinate`
        Streamwise coordinate
    y : :obj:`xcompact3d_toolbox.mesh.StretchedCoordinate`
        Vertical coordinate
    z : :obj:`xcompact3d_toolbox.mesh.Coordinate`
        Spanwise coordinate

    Notes
    -----
        :obj:`mesh` is in fact an atribute of :obj:`xcompact3d_toolbox.parameters.Parameters`,
        so there is no need to initialize it manually for most of the common use cases.
        The features of each coordenate are copled by a two-way link with their corresponding
        values at the Parameters class. For instance, the length of each of them is copled to
        :obj:`xlx`, :obj:`yly` and :obj:`zlz`, grid size to :obj:`nx`, :obj:`ny` and :obj:`nz`
        and so on.

    Returns
    -------
    :obj:`xcompact3d_toolbox.mesh.Mesh3D`
        Coordinate system
    """
    x = traitlets.Instance(klass=Coordinate)
    y = traitlets.Instance(klass=StretchedCoordinate)
    z = traitlets.Instance(klass=Coordinate)

    def __init__(self, **kwargs):
        """Initializes the 3DMesh class.

        Parameters
        ----------
        **kwargs
            Keyword arguments for each coordinate (x, y and z), containing a :obj:`dict`
            with the parameters for them, like :obj:`grid_size`, :obj:`length` and so on.

        Raises
        -------
        KeyError
            Exception is raised when an Keyword arguments is not a valid coordinate.

        Examples
        --------

        >>> from xcompact3d_toolbox.mesh import Mesh3D
        >>> mesh = Mesh3D(
        ...     x = dict(length = 4.0, grid_size = 65, is_periodic = False),
        ...     y = dict(length = 1.0, grid_size = 17, is_periodic = False, istret = 0),
        ...     z = dict(length = 1.0, grid_size = 16, is_periodic = True)
        ... )
        """

        self.x = Coordinate()
        self.y = StretchedCoordinate()
        self.z = Coordinate()

        self.set(**kwargs)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(\n"
            f"    x = {self.x},\n"
            f"    y = {self.y},\n"
            f"    z = {self.z},\n"
            ")"
        )

    def __len__(self):
        """Make the coordinate work with the Python function :obj:`len`.

        Returns
        -------
        int
            Mesh size is calculated by multiplying the size of the three coordinates
        """ 
        return self.size

    def set(self, **kwargs) -> None:
        """Set new values for any of the coordinates after the initialization.
        
        Parameters
        ----------
        **kwargs
            Keyword arguments for each coordinate (x, y and z), containing a :obj:`dict`
            with the parameters for them, like :obj:`grid_size`, :obj:`length` and so on.

        Raises
        -------
        KeyError
            Exception is raised when an Keyword arguments is not a valid attribute.

        Examples
        --------

        >>> from xcompact3d_toolbox.mesh import Mesh3D
        >>> mesh = Mesh3D()
        >>> mesh.set(
        ...     x = dict(length = 4.0, grid_size = 65, is_periodic = False),
        ...     y = dict(length = 1.0, grid_size = 17, is_periodic = False, istret = 0),
        ...     z = dict(length = 1.0, grid_size = 16, is_periodic = True)
        ... )
        """
        for key in kwargs.keys():
            if key in self.trait_names():
                getattr(self, key).set(**kwargs.get(key))
            else:
                raise KeyError(f"{key} is not a valid coordinate for Mesh3D")

    def get(self) -> dict:
        """Get the three coordinates in a dictionary, where the keys are their names (x, y and z)
        and the values are their vectors.
        
        Raises
        -------
        KeyError
            Exception is raised when an Keyword arguments is not a valid attribute.

        Returns
        -------
        :obj:`dict` of :obj:`numpy.ndarray`
            A dict containing the coordinates
        
        Notes
        -----

        It is an alias for ``Mesh3D.drop(None)``.
        """
        return self.drop(None)

    def drop(self, *args) -> dict:
        """Get the coordinates in a dictionary, where the keys are their names and the values
        are their vectors. It is possible to drop any of the coordinates in case they are
        needed to process planes. For instance:
        
        * Drop ``x`` if working with ``yz`` planes;
        * Drop ``y`` if working with ``xz`` planes;
        * Drop ``z`` if working with ``xy`` planes.
        
        Parameters
        ----------
        *args : str or list of str
            Name of the coordenate(s) to be dropped

        Raises
        -------
        KeyError
            Exception is raised when an Keyword arguments is not a valid attribute.

        Returns
        -------
        :obj:`dict` of :obj:`numpy.ndarray`
            A dict containing the desired coordinates
        """
        for arg in args:
            if not arg:
                continue
            if arg not in self.trait_names():
                raise KeyError(f"{arg} is not a valid coordinate for Mesh3D")
        return {
            dir: getattr(self, dir).vector
            for dir in self.trait_names()
            if dir not in args
        }

    def copy(self):
        """Return a copy of the Mesh3D object.
        """        
        return Mesh3D(
            **{dim: getattr(self, dim).trait_values() for dim in self.trait_names()}
        )

    @property
    def size(self):
        """Mesh size

        Returns
        -------
        int
            Mesh size is calculated by multiplying the size of the three coordinates
        """ 
        return self.x.size * self.y.size * self.z.size


def _validate_grid_size(grid_size, is_periodic):

    size = grid_size if is_periodic else grid_size - 1

    if size < 8:
        return False

    if size % 2 == 0:
        size //= 2

        for num in [2, 3, 5]:
            while True:
                if size % num == 0:
                    size //= num
                else:
                    break

    if size != 1:
        return False
    return True


def _get_possible_grid_values(
    is_periodic: bool, start: int = 0, end: int = 9002
) -> list:
    return list(
        filter(lambda num: _validate_grid_size(num, is_periodic), range(start, end),)
    )


_possible_size_periodic = _get_possible_grid_values(True)

_possible_size_not_periodic = _get_possible_grid_values(False)


def _stretching(istret, beta, yly, my, ny, return_auxiliar_variables=True):

    yp = np.zeros(ny, dtype=param["mytype"])
    yeta = np.zeros_like(yp)
    ypi = np.zeros_like(yp)
    yetai = np.zeros_like(yp)
    ppy = np.zeros_like(yp)
    pp2y = np.zeros_like(yp)
    pp4y = np.zeros_like(yp)
    ppyi = np.zeros_like(yp)
    pp2yi = np.zeros_like(yp)
    pp4yi = np.zeros_like(yp)
    #
    yinf = -0.5 * yly
    den = 2.0 * beta * yinf
    xnum = -yinf - np.sqrt(np.pi * np.pi * beta * beta + yinf * yinf)
    alpha = np.abs(xnum / den)
    xcx = 1.0 / beta / alpha
    if alpha != 0.0:
        if istret == 1:
            yp[0] = 0.0
        if istret == 2:
            yp[0] = 0.0
        if istret == 1:
            yeta[0] = 0.0
        if istret == 2:
            yeta[0] = -0.5
        if istret == 3:
            yp[0] = 0.0
        if istret == 3:
            yeta[0] = -0.5
        for j in range(1, ny):
            if istret == 1:
                yeta[j] = j / my
            if istret == 2:
                yeta[j] = j / my - 0.5
            if istret == 3:
                yeta[j] = 0.5 * j / my - 0.5
            den1 = np.sqrt(alpha * beta + 1.0)
            xnum = den1 / np.sqrt(alpha / np.pi) / np.sqrt(beta) / np.sqrt(np.pi)
            den = 2.0 * np.sqrt(alpha / np.pi) * np.sqrt(beta) * np.pi * np.sqrt(np.pi)
            den3 = (
                (np.sin(np.pi * yeta[j])) * (np.sin(np.pi * yeta[j])) / beta / np.pi
            ) + alpha / np.pi
            den4 = 2.0 * alpha * beta - np.cos(2.0 * np.pi * yeta[j]) + 1.0
            xnum1 = (
                (np.arctan(xnum * np.tan(np.pi * yeta[j]))) * den4 / den1 / den3 / den
            )
            cst = (
                np.sqrt(beta)
                * np.pi
                / (2.0 * np.sqrt(alpha) * np.sqrt(alpha * beta + 1.0))
            )
            if istret == 1:
                if yeta[j] < 0.5:
                    yp[j] = xnum1 - cst - yinf
                if yeta[j] == 0.5:
                    yp[j] = -yinf
                if yeta[j] > 0.5:
                    yp[j] = xnum1 + cst - yinf
            elif istret == 2:
                if yeta[j] < 0.5:
                    yp[j] = xnum1 - cst + yly
                if yeta[j] == 0.5:
                    yp[j] = yly
                if yeta[j] > 0.5:
                    yp[j] = xnum1 + cst + yly
            elif istret == 3:
                if yeta[j] < 0.5:
                    yp[j] = (xnum1 - cst + yly) * 2.0
                if yeta[j] == 0.5:
                    yp[j] = yly * 2.0
                if yeta[j] > 0.5:
                    yp[j] = (xnum1 + cst + yly) * 2.0
            else:
                raise NotImplementedError("Unsupported: invalid value for istret")
    if alpha == 0.0:
        yp[0] = -1.0e10
        for j in range(1, ny):
            yeta[j] = j / ny
            yp[j] = -beta * np.cos(np.pi * yeta[j]) / np.sin(yeta[j] * np.pi)

    if alpha != 0.0:
        for j in range(ny):
            if istret == 1:
                yetai[j] = (j + 0.5) * (1.0 / my)
            if istret == 2:
                yetai[j] = (j + 0.5) * (1.0 / my) - 0.5
            if istret == 3:
                yetai[j] = (j + 0.5) * (0.5 / my) - 0.5
            den1 = np.sqrt(alpha * beta + 1.0)
            xnum = den1 / np.sqrt(alpha / np.pi) / np.sqrt(beta) / np.sqrt(np.pi)
            den = 2.0 * np.sqrt(alpha / np.pi) * np.sqrt(beta) * np.pi * np.sqrt(np.pi)
            den3 = (
                (np.sin(np.pi * yetai[j])) * (np.sin(np.pi * yetai[j])) / beta / np.pi
            ) + alpha / np.pi
            den4 = 2.0 * alpha * beta - np.cos(2.0 * np.pi * yetai[j]) + 1.0
            xnum1 = (
                (np.arctan(xnum * np.tan(np.pi * yetai[j]))) * den4 / den1 / den3 / den
            )
            cst = (
                np.sqrt(beta)
                * np.pi
                / (2.0 * np.sqrt(alpha) * np.sqrt(alpha * beta + 1.0))
            )
            if istret == 1:
                if yetai[j] < 0.5:
                    ypi[j] = xnum1 - cst - yinf
                elif yetai[j] == 0.5:
                    ypi[j] = 0.0 - yinf
                elif yetai[j] > 0.5:
                    ypi[j] = xnum1 + cst - yinf
            elif istret == 2:
                if yetai[j] < 0.5:
                    ypi[j] = xnum1 - cst + yly
                elif yetai[j] == 0.5:
                    ypi[j] = 0.0 + yly
                elif yetai[j] > 0.5:
                    ypi[j] = xnum1 + cst + yly
            elif istret == 3:
                if yetai[j] < 0.5:
                    ypi[j] = (xnum1 - cst + yly) * 2.0
                elif yetai[j] == 0.5:
                    ypi[j] = (0.0 + yly) * 2.0
                elif yetai[j] > 0.5:
                    ypi[j] = (xnum1 + cst + yly) * 2.0

    if alpha == 0.0:
        ypi[0] = -1e10
        for j in range(1, ny):
            yetai[j] = j * (1.0 / ny)
            ypi[j] = -beta * np.cos(np.pi * yetai[j]) / np.sin(yetai[j] * np.pi)

    # Mapping!!, metric terms
    if istret != 3:
        for j in range(ny):
            ppy[j] = yly * (
                alpha / np.pi
                + (1.0 / np.pi / beta)
                * np.sin(np.pi * yeta[j])
                * np.sin(np.pi * yeta[j])
            )
            pp2y[j] = ppy[j] * ppy[j]
            pp4y[j] = -2.0 / beta * np.cos(np.pi * yeta[j]) * np.sin(np.pi * yeta[j])
        for j in range(ny):
            ppyi[j] = yly * (
                alpha / np.pi
                + (1.0 / np.pi / beta)
                * np.sin(np.pi * yetai[j])
                * np.sin(np.pi * yetai[j])
            )
            pp2yi[j] = ppyi[j] * ppyi[j]
            pp4yi[j] = -2.0 / beta * np.cos(np.pi * yetai[j]) * np.sin(np.pi * yetai[j])

    if istret == 3:
        for j in range(ny):
            ppy[j] = yly * (
                alpha / np.pi
                + (1.0 / np.pi / beta)
                * np.sin(np.pi * yeta[j])
                * np.sin(np.pi * yeta[j])
            )
            pp2y[j] = ppy[j] * ppy[j]
            pp4y[j] = (
                -2.0 / beta * np.cos(np.pi * yeta[j]) * np.sin(np.pi * yeta[j])
            ) / 2.0
        for j in range(ny):
            ppyi[j] = yly * (
                alpha / np.pi
                + (1.0 / np.pi / beta)
                * np.sin(np.pi * yetai[j])
                * np.sin(np.pi * yetai[j])
            )
            pp2yi[j] = ppyi[j] * ppyi[j]
            pp4yi[j] = (
                -2.0 / beta * np.cos(np.pi * yetai[j]) * np.sin(np.pi * yetai[j])
            ) / 2.0
    if return_auxiliar_variables:
        return yp, ppy, pp2y, pp4y
    return yp
