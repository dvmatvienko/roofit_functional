"""Module to describe probability density functions as well as non-normalized functions."""

import numpy as np
from typing import Self, Union

try:
    import ROOT
except ImportError as e:
    raise ImportError(
        "ROOT is not properly installed. Plase install ROOT support first"
    ) from e


# ========== Utilities ==========
def wrapped(
    obj: Union["RooFitVar", "RooFitFunction"],
    selfNormalized: bool = False,
    x_conditional: list | None = None,
) -> "RooFitFunction":
    """Normalize function provided in obj parameter.

    Args:
        obj: object describing a function to be wrapped
        selfNormalized: (optional) flag controlling normalization of obj function
        x_conditional: (optional) list providing conditional variables for obj function

    """
    if not isinstance(obj, (RooFitVar, RooFitFunction)):
        raise TypeError(
            "Function 'wrapped' can only have arguments of type RooFitFunction or RooFitVar!"
        )
    if not selfNormalized and x_conditional is not None:
        raise ValueError(
            f"selfNormalized is False, but x_conditional is {x_conditional}. It is forbidden."
        )
    if x_conditional is not None and not isinstance(x_conditional, list):
        raise TypeError(
            f"wrong type of x_conditional. It must be list but {type(x_conditional)} is assigned"
        )

    name = "PDF_" + obj.name
    x_limits = (
        obj.x_limits
        if x_conditional is None
        else {
            key: obj.x_limits[key]
            for key in set(obj.x_limits) - set([x.GetName() for x in x_conditional])
        }
    )
    function_type = obj.function_type

    if isinstance(obj, RooFitVar) and ("(+)" in name or "(*)" in name):
        param_dict = {}
        for v in obj.param_dict.values():
            param_dict.update(v.param_dict)
    else:
        param_dict = obj.param_dict
    if x_conditional is not None:
        functionality = {obj: x_conditional}
    else:
        functionality = obj
    setattr(RooFitFunction, "_FUNCTIONALITY", functionality)
    setattr(RooFitFunction, "_MARKER", f"wrapper_{selfNormalized}")
    obj = RooFitFunction(name, x_limits, function_type, param_dict)
    setattr(RooFitFunction, "_FUNCTIONALITY", None)
    setattr(RooFitFunction, "_MARKER", None)
    return obj


# ========== Module for ordinary function ==========
class RooFitVar:
    """Description of ordinary non-normalized functions.

    It gives an object with parameters of arbitrary non-normalized functon.

    **Examples**

    >>> my_function = RooFitVar({'y' : [-1,1]}, 'p1*y', {'p1' : [1,1,1]},'my_function')
    >>> polynomial_function = RooFitVar({'x' : [-1,1]}, 'poly', {'p0' : [0.1,0,1], 'p1' : [0.05,-0.1,0.1]}, "poly")

    """

    def _arithmetic(self, other, sign: str) -> Self:
        """Do arithmetic operations with non-normalized functions."""
        if not isinstance(other, (type(self), RooFitFunction)):
            raise ArithmeticError(
                "Wrong type of instance. It must be RooFitVar or RooFitFunction"
            )
        x_limits = {**self.x_limits, **other.x_limits}
        name = self.name + sign + other.name
        param_dict = {self.name: self, other.name: other}
        function_type = f"({sign})".join([self.name, other.name])
        name, function_type = function_type, name
        return type(self)(x_limits, function_type, param_dict, name)

    def _setFunction(self) -> tuple:
        """Fill in containers of variables and parameters of non-normalized function."""
        x_limits = self._x_limits
        function_type = self._function_type
        param_dict = self._param_dict
        var_name = self._var_name
        # isRooFitVar = False

        x = []
        if not isinstance(x_limits, dict):
            raise TypeError("wrong type of 'x_limits'. It must be dict")

        for k, v in x_limits.items():
            if not isinstance(v, (list, type(self))):
                raise TypeError(
                    f"wrong type of 'x_limits' dict_value. It must be list or RooFitVar. {type(v)}"
                )
            if isinstance(v, list):
                if not len(v) == 2:
                    raise ValueError(
                        "length of 'x_limits' dict_value is wrong. It must be equal two"
                    )
                x.append(ROOT.RooRealVar(k, k, v[0], v[1]))
            else:
                if not k == "all" and k not in v.x_limits:
                    raise ValueError(f"key {k} does not exist in {v.name}!")
                if k == "all" and not len(x_limits.items()) == 1:
                    raise ValueError(f"key {k} must be unique in x_limits!")
                if k == "all":
                    x = v.x
                    self._x_limits = v.x_limits
                    break
                else:
                    for arg in v.x:
                        if arg.GetName() == k:
                            x.append(arg)

        container = []
        for k, v in param_dict.items():
            if not isinstance(v, (list, type(self), RooFitFunction, int, float)):
                raise TypeError(
                    f"wrong type of 'param_dict' dict_value. It must be list / RooFitVar / RooFitFunction / int / float but {type(v)} is assigned"
                )
            if (
                k not in function_type
                and not function_type == "poly"
                and not function_type == "step"
            ):
                raise ValueError(
                    "'function_type' is not correct. There are not used parameters"
                )
            if isinstance(v, (int, float)):
                v = [v]
            if isinstance(v, list):
                if not function_type == "step":
                    if len(v) not in [1, 3]:
                        raise ValueError(
                            "length of 'param_dict' dict_value is wrong. It must be equal one or three"
                        )
                    elif len(v) == 1 or v[1] == v[2]:
                        parameter = ROOT.RooRealVar(
                            k, k, v[0], v[0] - abs(v[0] * 1e-3), v[0] + abs(v[0] * 1e-3)
                        )
                        parameter.setVal(v[0])
                        parameter.setConstant(True)
                        container.append(parameter)
                    else:
                        container.append(ROOT.RooRealVar(k, k, v[0], v[1], v[2]))
                else:
                    container += v
            else:
                # isRooFitVar = True
                container.append(v.function)

        if not function_type == "poly" and not function_type == "step":
            container += x
        else:
            if not len(x) == 1:
                raise AttributeError(
                    "wrong number of arguments in the polynomial. Only one-dimensional polynomial primitives is allowed!! "
                )

        if function_type == "poly":
            # If lowestOrder is not zero, then the first element in coefList is interpreted as the 'lowestOrder' coefficient and all subsequent coefficient elements are shifted by a similar amount.
            # It is useful if we want polynomials with arbitrary powers of x
            return (
                x,
                container,
                ROOT.RooPolyVar(
                    var_name, var_name, *x, container, lowestOrder=self._lowestOrder
                ),
            )
        elif function_type == "step":
            if len(container) % 2 == 0:
                raise ValueError("length of 'param_dict' for step function must be odd")
            number_of_bins = int((len(container) - 1) / 2)
            if (
                not (len(container[number_of_bins:]) - len(container[:number_of_bins]))
                == 1
            ):
                raise ValueError(
                    "list of bin bounds must be one more than list of weghts in the 'param_dict'"
                )
            return (
                x,
                container,
                ROOT.RooStepFunction(
                    var_name,
                    var_name,
                    *x,
                    container[:number_of_bins],
                    container[number_of_bins:],
                ),
            )
        else:
            return x, container, ROOT.RooFormulaVar(var_name, function_type, container)

    def __init__(
        self,
        x_limits: dict,
        function_type: str,
        param_dict: dict,
        var_name: str,
        lowestOrder: int = 0,
    ) -> None:
        """Initialize RooFitVar object.

        Args:
            x_limits: python dict initializing function variables
            function_type: string describing the function formula or predefined behaviour: poly / step
            param_dict: python dict initializing function parameters
            var_name: string defining function name
            lowestOrder: int configuring polynomials with arbitrary powers

        """
        self._x_limits = x_limits
        self._function_type = function_type
        self._param_dict = param_dict
        self._var_name = var_name
        self._lowestOrder = lowestOrder
        self._x, self._container, self._function = self._setFunction()

    def __add__(self, other):
        """Add two non-normalized functions."""
        return self._arithmetic(other, "+")

    def __radd__(self, other):
        """Reverse add two non-normalized functions."""
        return self + other

    def __sub__(self, other):
        """Sub two non-normalized functions."""
        return self._arithmetic(other, "-")

    def __rsub__(self, other):
        """Reverese sub two non-normalized functions."""
        return self - other

    def __mul__(self, other):
        """Mul two non-normalized functions."""
        return self._arithmetic(other, "*")

    @property
    def x_limits(self):
        """Getter for x_limits."""
        return self._x_limits

    @property
    def function_type(self):
        """Getter for function_type."""
        return self._function_type

    @property
    def param_dict(self):
        """Getter for param_dict."""
        return self._param_dict

    @property
    def name(self):
        """Getter for name."""
        return self._var_name

    @property
    def lowestOrder(self):
        """Getter for lowestOrder."""
        return self._lowestOrder

    @property
    def function(self):
        """Getter for function."""
        return self._function

    @property
    def x(self):
        """Getter for x."""
        return self._x

    @property
    def container(self):
        """Getter for container."""
        return self._container


# ========== Module for probability density function ==========
class RooFitFunction:
    """Description of probability density functions (PDFs).

    It gives an object with parameters of pre-defined PDFs.

    **Examples**
    >>>gauss = RooFitFunction('Gauss', {'x' : [-6,6]}, 'Gaussian', {'mu' : [0,-1,1], 'sigma' : [1,0.5,1.5]})
    >>>bw = RooFitFunction('BreitWigner', {'x' : [-6,6]}, 'BreitWigner', {'mean' : [0.78265,0.77,0.79], 'width' : [0.0085,0,0]})
    """

    _FUNCTIONALITY = None
    _MARKER = None

    def _setBase(self) -> tuple:
        """Fill in containers of variables and parameters of PDFs."""
        x_limits = self._x_limits
        param_dict = self._param_dict
        marker = self._marker
        functionality = self._functionality

        if marker is not None and functionality is None:
            raise ValueError("parameter 'functionality' must be defined")

        x = []
        if not isinstance(x_limits, dict):
            raise TypeError("wrong type of 'x_limits'. It must be dict")

        if marker == "add" or marker == "convolution":
            x = functionality[0].x
        elif marker == "ord_mul" or marker == "cond_mul":
            x = functionality[0].x + functionality[1].x
        elif marker == "composition":
            obj = next(iter(functionality.keys()))
            x = obj.x
        # elif not marker is None and 'wrapper' in marker:
        #   if not isinstance(functionality,dict):
        #       x = functionality.get_x()
        #       x = list(functionality.keys())[0].get_x()
        #    else:
        #       x = functionality.get_x()
        else:
            for k, v in x_limits.items():
                if not isinstance(v, (list, RooFitVar, type(self))):
                    raise TypeError(
                        "wrong type of 'x_limits' dict_value. It must be list or RooFitVar or RooFitFunction"
                    )
                if isinstance(v, list):
                    if not len(v) == 2:
                        raise ValueError(
                            "length of 'x_limits' dict_value is wrong. It must be equal two"
                        )
                    x.append(ROOT.RooRealVar(k, k, v[0], v[1]))
                else:
                    if not k == "all" and k not in v.x_limits:
                        raise ValueError(f"key {k} does not exist in {v.name}!")
                    if k == "all" and not len(x_limits.items()) == 1:
                        raise ValueError(f"key {k} must be unique in x_limits!")
                    if k == "all":
                        x = v.x
                        self._x_limits = v.x_limits
                        break
                    else:
                        for arg in v.x:
                            if arg.GetName() == k:
                                x.append(arg)

        container = []
        if not isinstance(param_dict, dict):
            raise TypeError("wrong type of 'param_dict'. It must be dict")

        if marker is not None and "wrapper" in marker:
            if isinstance(functionality, dict):
                container = list(functionality.keys())[0].container
            else:
                container = functionality.container
        elif marker == "convolution" or marker == "ord_mul" or marker == "cond_mul":
            # container = list(np.unique(functionality[0].get_container() + functionality[1].get_container()))
            container = list(
                set(functionality[0].container + functionality[1].container)
            )
        else:
            indices = []
            for k, v in param_dict.items():
                if not isinstance(v, (list, RooFitVar, type(self), int, float)):
                    raise TypeError(
                        "wrong type of 'param_dict' dict_value. It must be list / RooFitVar / RooFitFunction / int / float"
                    )
                if isinstance(v, (int, float)):
                    v = [v]
                if isinstance(v, list):
                    if len(v) not in [1, 3]:
                        raise ValueError(
                            "length of 'param_dict' dict_value is wrong. It must be equal one or three"
                        )
                    elif len(v) == 1 or v[1] == v[2]:
                        parameter = ROOT.RooRealVar(
                            k, k, v[0], abs(v[0] - 1e-3), abs(v[0] + 1e-3)
                        )
                        parameter.setVal(v[0])
                        parameter.setConstant(True)
                        container.append(parameter)
                    else:
                        container.append(ROOT.RooRealVar(k, k, v[0], v[1], v[2]))
                elif isinstance(v, RooFitVar):
                    container.append(v.function)
                    indices.append(container.index(container[-1]))
                else:
                    if k not in v.param_dict:
                        raise ValueError(f"key {k} does not exist in {v.param_dict}!")
                    for arg in v.container:
                        if arg.GetName() == k:
                            container.append(arg)
        if marker == "add":
            container = (
                list(np.unique(functionality[0].container + functionality[1].container))
                + container[:-2:-1]
            )
            # container = list(set(functionality[0].get_container() + functionality[1].get_container()))
        elif marker == "composition":
            obj = next(iter(functionality.keys()))
            initial_container = obj.container
            for j in indices:
                initial_container[j] = container[j]
            container = initial_container

        return x, container

    def _setFunction(self) -> ROOT:
        """Define PDF as an attribute of RooFitFunction object."""
        function_name = self._function_name
        function_type = self._function_type
        x, container = self._x, self._container
        marker = self._marker
        functionality = self._functionality

        if marker is not None and "wrapper" in marker:
            selfNormalized = True if marker.split("_")[1] == "True" else False
            if functionality is None:
                raise ValueError("parameter 'functionality' must be defined")
            elif isinstance(functionality, dict):
                return ROOT.RooWrapperPdf(
                    function_name,
                    function_type,
                    list(functionality.keys())[0].function,
                    selfNormalized=selfNormalized,
                )
            else:
                return ROOT.RooWrapperPdf(
                    function_name,
                    function_type,
                    functionality.function,
                    selfNormalized=selfNormalized,
                )
        elif marker == "add":
            if functionality is None:
                raise ValueError("parameter 'functionality' must be defined")
            else:
                functionality = [pdf.function for pdf in functionality]
                return ROOT.RooAddPdf(
                    function_name, function_type, functionality, container[-1]
                )
        elif marker == "convolution":
            if functionality is None:
                raise ValueError("parameter 'functionality' must be defined")
            if not len(x) == 1:
                raise ValueError(
                    "wrong number of arguments in convolution. Only one-dimensional convolution is implemented!!"
                )
            else:
                for x_val in x:
                    x_val.setBins(1000, "cache")
                functionality = [pdf.function for pdf in functionality]
                return ROOT.RooFFTConvPdf(
                    function_name, function_type, *x, *functionality
                )
                # return ROOT.RooNumConvPdf(function_name,function_type,*x,*functionality)
        elif marker == "ord_mul":
            if functionality is None:
                raise ValueError("parameter 'functionality' must be defined")
            else:
                functionality = [pdf.function for pdf in functionality]
                return ROOT.RooProdPdf(function_name, function_type, functionality)
        elif marker == "cond_mul":
            if functionality is None:
                raise ValueError("parameter 'functionality' must be defined")
            else:
                # one_x_conditional = [ROOT.RooRealVar(k,k,v[0],v[1]) for l in functionality[0].get_functionality().values() for d in l for k,v in d.items()]
                one_x_conditional = functionality[0].conditional_x
                # The boolean inverts the “conditional”: Conditional(pdf, x, true) = pdf is conditional on x.
                # That is, don’t integrate it over x to normalise. Conditional(pdf, x, false) = pdf is conditional on all but x (default)
                # one_x_conditonal = [ROOT.RooRealVar(k,k,v[0],v[1]) for k,v in list(functionality[0].keys())[0].get_x_limits().items()]
                if not len(functionality[1].conditional_x) == 0:
                    # two-sided conditional multiplication
                    # two_x_conditional = [ROOT.RooRealVar(k,k,v[0],v[1]) for l in functionality[1].get_functionality().values() for d in l for k,v in d.items()]
                    two_x_conditional = functionality[1].conditional_x
                    return ROOT.RooProdPdf(
                        function_name,
                        function_type,
                        set(),
                        ROOT.RooFit.Conditional(
                            {functionality[0].function},
                            set(one_x_conditional),
                            depsAreCond=True,
                        ),
                        ROOT.RooFit.Conditional(
                            {functionality[1].function},
                            set(two_x_conditional),
                            depsAreCond=True,
                        ),
                    )
                else:
                    # one-sided conditional multiplication
                    return ROOT.RooProdPdf(
                        function_name,
                        function_type,
                        {functionality[1].function},
                        ROOT.RooFit.Conditional(
                            {functionality[0].function},
                            set(one_x_conditional),
                            depsAreCond=True,
                        ),
                    )
        # To provide function name for composed functions (w/ conditional variables)
        function_type = function_type.split("|")[0]
        # Dict to check correct number of parameters provided in the constructor
        function_type_dict = {
            "CrystalBall": [6, 7],
            "Uniform": [0],
            "BifurGauss": [3],
            "BreitWigner": [2],
            "Gaussian": [2],
            "Voigtian": [3],
            "Novosibirsk": [3],
            "Johnson": [4],
        }
        right_param_dict_len = function_type_dict.get(
            function_type, [len(self._param_dict)]
        )
        if len(self._param_dict) not in right_param_dict_len:
            raise TypeError(
                f"length of 'param_dict' dict is wrong. It must be equal one in {right_param_dict_len}"
            )
        # This behaviour could be enhanced with NN classification of function_type provided...
        if function_type not in function_type_dict.keys():
            raise AttributeError(
                f"param 'function_type' is not implemented. It must be one in {list[function_type_dict.keys()]}"
            )
        if not len(x) == 1:
            raise AttributeError(
                "wrong number of arguments in the function. Only one-dimensional functional primitive is allowed!!"
            )
        return eval("ROOT.Roo" + function_type)(
            function_name, function_type, *x, *container
        )

    def __init__(
        self, name: str, x_limits: dict, function_type: str, param_dict: dict
    ) -> None:
        """Initialize RooFitFunction object.

        Args:
            name: string defining the PDF name
            x_limits: python dict initializing PDF variables
            function_type: string defining the RooFit class to createPDF
            param_dict: python dict initializing PDF  parameters

        """
        self._function_name = name
        self._x_limits = x_limits
        self._function_type = function_type
        self._param_dict = param_dict
        self._functionality = self._FUNCTIONALITY
        self._marker = self._MARKER
        self._x, self._container = self._setBase()
        self._function = self._setFunction()

    def get_add(self, other, frac_parameter: dict[str,list[int|float]], name: str | None = None) -> Self:
        """Create normalized sum of two PDFs.

        Args:
            other: RooFitFucntion object
            frac_parameter: python dict initializing relative fraction of two PDFs
            name: (optional) string defining name of the sum

        """
        if not isinstance(other, type(self)):
            raise TypeError("wrong type of instance. It must be RooFitFunction")
        if not isinstance(frac_parameter, dict):
            raise TypeError("wrong type of 'frac_parameter'. It must be dict")
        if not len(frac_parameter) == 1:
            raise ValueError(
                "length of 'frac_parameter' dict is exceeded. It must be one"
            )
        if not len(self.x) == len(other.x) == 1:
            raise ValueError("Only 1-dim PDFs could be added!")
        if not id(*(self.x)) == id(*(other.x)):
            raise ValueError(
                f"Please use the same objects as arguments for PDF functions to be added!! id(x_1): {id * (self.x)} != id(x2) : {id(*(other.x))}"
            )

        name = self.name + " + " + other.name if name is None else name
        function_type = "(+)".join([self.function_type, other.function_type])
        param_dict = {**self.param_dict, **other.param_dict, **frac_parameter}
        x_limits = self.x_limits
        functionality = [self, other]
        setattr(type(self), "_FUNCTIONALITY", functionality)
        setattr(type(self), "_MARKER", "add")
        obj = type(self)(name, x_limits, function_type, param_dict)
        setattr(type(self), "_FUNCTIONALITY", None)
        setattr(type(self), "_MARKER", None)
        return obj

    def get_extended_add(
        self, other, frac_parameter: dict[str,list[int|float]], name: str | None = None
    ) -> None:
        """Create extended normalized sum of two PDFs.

        Args:
            other: RooFitFunction object
            frac_parameter: python dict initializing relative fraction of two PDFs
            name: (optional) string defining name of the sum

        """
        pass

    # Only convolution, where arguments of basic and resolution functions are the same, is implemented now!!
    # The general case corresponds to the convolution performing only for part of arguments or different resolutions for each argument ..
    def get_convolution(self, other, name: str | None = None) -> Self:
        """Create convolution of two 1-dim PDFs.

        Args:
            other: RooFitFunction object
            name: (optional) string defining name of the convolution

        """
        if not isinstance(other, type(self)):
            raise TypeError("wrong type of instance. It must be RooFitFunction")
        if not id(self.x) == id(other.x):
            raise TypeError(
                "Please use the same objects as arguments for PDF functions to be convolved!"
            )

        name = self.name + " X " + other.name if name is None else name
        function_type = "(X)".join([self.function_type, other.function_type])
        param_dict = {**self.param_dict, **other.param_dict}
        x_limits = self.x_limits
        functionality = [self, other]
        setattr(type(self), "_FUNCTIONALITY", functionality)
        setattr(type(self), "_MARKER", "convolution")
        obj = type(self)(name, x_limits, function_type, param_dict)
        setattr(type(self), "_FUNCTIONALITY", None)
        setattr(type(self), "_MARKER", None)
        return obj

    def get_composition(
        self, parameter_other_dict: dict, normalized: bool = False
    ) -> Self:
        """Create composition of two base (not sum, product, etc.) PDFs.

        Args:
            parameter_other_dict: python dict initializing functional behaviour of the PDF parameter
            normalized: (optional) bool defining whether or not multiply function with the parameter

        """
        name = self.name

        param_dict = self.param_dict
        y_limits = []
        postfix = []
        for k, v in parameter_other_dict.items():
            if not isinstance(v, RooFitVar):
                raise TypeError(
                    f"wrong type of instance {v}. It must be type of RooFitVar"
                )
            if k not in param_dict:
                raise ValueError(
                    f"wrong parameter {k}. It must be earlier defined in RooFitFunction object"
                )

            for x in v.x:
                for y in y_limits:
                    if x.GetName() == y.GetName() and not id(x) == id(y):
                        raise ValueError(
                            "RooFitVar objects have the same x_keys but different arguments (argument objects must be the same)!"
                        )
                if x.GetName() not in postfix:
                    postfix.append(x.GetName())
                y_limits.append(x)
            if not normalized:
                param_dict[k] = v
            else:
                param_dict[k] = RooFitVar(
                    v.x_limits,
                    f"{k}*({v.name})",
                    {k: param_dict[k], v.name: v},
                    f"{k}:{v.name}",
                )

        function_type = self.function_type + f"|({','.join(map(str, (*postfix,)))})"
        x_limits = self.x_limits
        # list of condtional arguments (w/o duplicates)
        for i, y in enumerate(y_limits):
            for y1 in y_limits[:i:-1]:
                if id(y) == id(y1):
                    y_limits.remove(y1)
        functionality = {self: y_limits}
        if self.functionality is not None:
            raise ValueError(
                "Please make composition only with simple RooFitFunction objects (not added, convolved, multiplied)!!!"
            )
        setattr(type(self), "_FUNCTIONALITY", functionality)
        setattr(type(self), "_MARKER", "composition")
        obj = type(self)(name, x_limits, function_type, param_dict)
        setattr(type(self), "_FUNCTIONALITY", None)
        setattr(type(self), "_MARKER", None)
        return obj

    def __mul__(self, other) -> Self:
        """Create product of two PDFs (conditional or not)."""
        if not isinstance(other, (type(self), RooFitVar)):
            raise ArithmeticError(
                "Wrong type of instance. It must be RooFitFunction or RooFitVar"
            )

        if isinstance(other, RooFitVar):
            return other._arithmetic(self, "*")

        for x1 in self.x:
            for x2 in other.x:
                if x2.GetName() == x1.GetName() and not id(x2) == id(x1):
                    raise ValueError(
                        "RooFitFunction objects have the same x_keys but different arguments (argument objects must be the same)!"
                    )

        standard_arguments = [set(obj.x) for obj in (self, other)]
        conditional_arguments = [set(obj.conditional_x) for obj in (self, other)]

        if standard_arguments[0] & standard_arguments[1]:
            raise ValueError(
                f"PDF multiplication is allowed only for functions w/ different arguments. But PDF1 has {standard_arguments[0]} and PDF2 - {standard_arguments[1]}"
            )

        # common multiplication (no conditional arguments)
        # functionality  - list of self and other
        list_of_conditions = [
            conditional_arguments[_] < standard_arguments[_] for _ in range(2)
        ]
        if all(list_of_conditions):
            function_type = "(*)".join([self.function_type, other.function_type])
            functionality = [self, other]
            setattr(type(self), "_MARKER", "ord_mul")
        # two-sided conditional multiplication (conditional arguments for self and other)
        # functionality - list of dicts with key / item = RooFitFunction object  / list of dicts (key = x_limits key), item (range of limits))
        # with conditional arguments (formed by 'get_composition' method)
        elif not any(list_of_conditions):
            function_type = "(*|)".join([self.function_type, other.function_type])
            functionality = [self, other]
            setattr(type(self), "_MARKER", "cond_mul")
        # one-sided conditional multiplication (conditional arguments for either self or other)
        # functionality - list of dict for conditional PDF and RooFitFunction object for ordinary PDF
        else:
            o1, o2 = (self, other) if list_of_conditions[1] else (other, self)
            # o1 - conditional PDF , o2 - ordinary PDF
            function_type = "(*|)".join([o1.function_type, o2.function_type])
            functionality = [o1, o2]
            setattr(type(self), "_MARKER", "cond_mul")
        name = self.name + " * " + other.name
        param_dict = {**self.param_dict, **other.param_dict}
        x_limits = {**self.x_limits, **other.x_limits}
        setattr(type(self), "_FUNCTIONALITY", functionality)
        obj = type(self)(name, x_limits, function_type, param_dict)
        setattr(type(self), "_FUNCTIONALITY", None)
        setattr(type(self), "_MARKER", None)
        return obj

    def __rmul__(self, other) -> Self:
        """Reverse mul of two PDFs (conditional or not)."""
        return self * other

    def get_extended(self) -> bool:
        """Transform a PDF to the extended one."""
        return False

    def set_fixed(self, fixed_parameters: dict[str, int | float]) -> None:
        """Fix user-defined parameters of the PDF.

        Args:
            fixed_parameters: python dict fixing the PDF parameter.

        """
        if not isinstance(fixed_parameters, dict):
            raise TypeError("wrong type of 'fixed_parameters'. It must be dict")
        keys = self.param_dict
        for k, v in fixed_parameters.items():
            if not isinstance(v, (float, int)):
                raise TypeError(f"wrong type of parameter {v}. It must be float / int")
            if k in keys:
                icontainer = list(keys).index(k)
                parameter = ROOT.RooRealVar(k, k, v, v - 1e03, v + 1e-3)
                parameter.setVal(v)
                parameter.setConstant(True)
                self._container[icontainer] = parameter
                self._param_dict[k] = v
        self._function = self._setFunction()

    def set_floated(self, floated_parameters: dict[str, list[int | float]]) -> None:
        """Fix user-defined parameters of the PDF.

        Args:
            floated_parameters: python dict relaxing the PDF parameter.

        """
        if not isinstance(floated_parameters, dict):
            raise TypeError("wrong type of 'floated_parameters'. It must be dict")
        keys = self.param_dict
        for k, v in floated_parameters.items():
            if not isinstance(v, list):
                raise TypeError(f"wrong type of parameter {v}. It must be list")
            if k in keys:
                icontainer = list(keys).index(k)
                self._container[icontainer] = ROOT.RooRealVar(k, k, v[0], v[1], v[2])
                self._param_dict[k] = v
            self._function = self._setFunction()

    def set_limits(
        self, x_limits: dict[str, list[int | float]] | list[int | float]
    ) -> None:
        """Change the limits of the PDF variables.

        Args:
            x_limits: python dict or list with the range of the PDF variable.
                      If list - all the vatiables are within the range.

        """
        if not isinstance(x_limits, (dict, list)):
            raise TypeError("wrong type of 'x_limits'. It must be dict / list")
        keys = self.x_limits
        if isinstance(x_limits, list):
            for v in x_limits:
                if not isinstance(v, (float, int)):
                    raise TypeError(
                        f"wrong type of parameter {v}. It must be float / int"
                    )
            for k in keys:
                ix = list(keys).index(k)
                self._x[ix] = ROOT.RooRealVar(k, k, x_limits[0], x_limits[1])
                self._x_limits[k] = x_limits
        elif isinstance(x_limits, dict):
            for k, v in x_limits.items():
                if not isinstance(v, list):
                    raise TypeError(f"wrong type of parameter {v}. It must be list")
                if k in keys:
                    ix = list(keys).index(k)
                    self._x[ix] = ROOT.RooRealVar(k, k, x_limits[k][0], x_limits[k][1])
                    self._x_limits[k] = x_limits[k]
        self._function = self._setFunction()

    def get_NFitFloated(self) -> int:
        """Calculate number of free parameters during the fit."""
        counts = 0
        for arg in self.x:
            if not arg.isConstant():
                counts += 1
        return counts

    @property
    def name(self):
        """Getter for name."""
        return self._function_name

    @property
    def x_limits(self):
        """Getter for x_limits."""
        return self._x_limits

    @property
    def function_type(self):
        """Getter for function_type."""
        return self._function_type

    @property
    def param_dict(self):
        """Getter for param_dict."""
        return self._param_dict

    @property
    def x(self):
        """Getter for x."""
        return self._x

    @property
    def conditional_x(self):
        """Getter for conditional_x."""
        if isinstance(self._functionality, dict):
            return list(self._functionality.values())[0]
        elif isinstance(self._functionality, list):
            conditional_x = set(
                self._functionality[0].conditional_x
                + self._functionality[1].conditional_x
            )
            x = set(self._functionality[0].x + self._functionality[1].x)
            return list(conditional_x - x)
        else:
            return []

    @property
    def container(self):
        """Getter for container."""
        return self._container

    @property
    def function(self):
        """Getter for function."""
        return self._function

    @property
    def functionality(self):
        """Getter for functionality."""
        return self._functionality

# ========== Simple examples for the module ==========
if __name__ == "__main__":

    def make_examples(num: int = 1) -> None:
        """Make simple examples with objects of classes provided in the modeule."""
        # Main functionality No.1
        if num == 1:
            de_cb = RooFitFunction(
                "CrystalBall",
                {"dE": [-0.15, 0.15]},
                "CrystalBall",
                {
                    "x0CB": [0, -0.01, 0.01],
                    "sigmacbL": [0.02, 0.005, 0.05],
                    "sigmacbR": [0.02, 0.005, 0.05],
                    "alphaL": [0.1, 0.005, 2],
                    "alphaR": [0.1, 0.005, 2],
                    "nL": [1, 0.1, 20.0],
                    "nR": [1, 0.1, 20.0],
                },
            )

            de_bfGauss = RooFitFunction(
                "Gauss",
                {"all": de_cb},
                "BifurGauss",
                {
                    "x0": [0, -0.01, 0.01],
                    "sigmaL": [0.01, 0.001, 0.05],
                    "sigmaR": [0.1, 0.001, 0.05],
                },
            )

            x0cb_function = RooFitVar(
                {"mom": [0.74, 0.85]},
                "p1*(mom-0.7826)+p0",
                {"p1": [0.1, 0.0, 1.0], "p0": [0, -0.1, 0.1]},
                "x0CB_func",
            )

            de_cb = de_cb.get_composition({"x0CB": x0cb_function})
            de_pdf = de_cb.get_add(de_bfGauss, {"frac": [0.5, 0.0, 1.0]})

            mom_bw = RooFitFunction(
                "BreitWigner",
                {"mom": [0.74, 0.85]},
                "BreitWigner",
                {"mean": [0.78265, 0.77, 0.79], "width": 0.0085},
            )

            mom_cb = RooFitFunction(
                "CrystalBall",
                {"all": mom_bw},
                "CrystalBall",
                {
                    "x0CB": 0,
                    "sigcbL": [0.005, 0.001, 0.05],
                    "sigcbR": [0.005, 0.001, 0.05],
                    "alphaL": [1, 0.005, 2],
                    "alphaR": [1, 0.005, 2],
                    "nL": [1, 0.01, 50.0],
                    "nR": [1, 0.01, 50.0],
                },
            )

            # Example of nested convolution and composition
            de_poly = RooFitVar(
                {"dE": [-0.15, 0.15]},
                "p0+p1*dE+p2*dE**2",
                {"p0": 0.1, "p1": 0.1, "p2": 1},
                "poly3",
            )

            mom_de_poly_pdf = mom_bw.get_convolution(
                mom_cb.get_composition({"sigcbL": de_poly})
            )

            # (Delta E - Omega) RooFit one-sided conditional product
            de_mom_1cond_pdf = mom_de_poly_pdf * de_pdf

            print("Main functionality No.1 :", de_mom_1cond_pdf.function_type)

        # Main functionality No.2
        elif num == 2:
            mu = RooFitVar({"y": [-1, 1]}, "p1*y", {"p1": [1, 1, 1]}, "mu_function")
            sigma = RooFitVar(
                {"all": mu},
                "p0+p1*y",
                {"p0": [0.5, 0.5, 0.5], "p1": [1, 1, 1]},
                "sigma_function",
            )

            gauss_xy = RooFitFunction(
                "Gauss_xy",
                {"x": [-6, 6]},
                "Gaussian",
                {"mu": [0, -1, 1], "sigma": [1, 0.5, 1.5]},
            )

            gauss_xy = gauss_xy.get_composition({"mu": mu, "sigma": sigma})
            uniform_y = RooFitFunction("Uniform_y", {"all": mu}, "Uniform", {})
            f_xy = gauss_xy * uniform_y

            print("Main functionality No.2 :", f_xy.function_type)
            print("Main functionality No.2 :", uniform_y.x_limits)

        # Main funcitonality No.3
        elif num == 3:
            x0cb = RooFitVar(
                {"mom": [0.74, 0.855]},
                "p1*(mom-0.7826)+p0",
                {"p1": [0.1, 0.0, 1.0], "p0": [0, -0.1, 0.1]},
                "x0CB",
            )

            x1cb = RooFitVar(
                {"all": x0cb},
                "p12*(mom-0.7826)**2+p11*(mom-0.7826)+p10",
                {"p10": [-1, -2, 0], "p11": [0.5, 0.0, 1.0], "p12": [0, -0.1, 0.1]},
                "x1CB",
            )

            bw = RooFitFunction(
                "BreitWigner",
                {"all": x0cb},
                "BreitWigner",
                {"mean": [0.78265, 0.77, 0.79], "width": [0.0085, 0, 0]},
            )

            bw_x0cb = bw * x0cb
            x0cb_bw = x0cb * bw
            x0cb_x1cb = x0cb * x1cb
            x0cb_p_bw = x0cb + bw
            bw_p_x0cb = bw + x0cb
            pdf = wrapped(bw * x0cb)

            print(
                "Main functionality No.3 :",
                bw_x0cb.name,
                x0cb_bw.name,
                x0cb_x1cb.name,
                x0cb_p_bw.name,
                bw_p_x0cb.name,
            )
            print("Main functionality No.3 :", pdf.name)

            mu = RooFitVar({"y": [-1, 1]}, "p1*y", {"p1": [1, 1, 1]}, "mu_function")

            null_func = RooFitVar({"all": mu}, "0", {}, "0")
            print("null_func_name is ", null_func.name)

    make_examples(1)
    make_examples(2)
    make_examples(3)
