import ROOT
import re
import numpy as np
from array import array
from typing import Any, List



class RooFitVar:

    def _setFunction(self):
        x_limits = self._x_limits
        function_type = self._function_type
        param_dict = self._param_dict
        var_name = self._var_name
#        isRooFitVar = False

        x = []
        if not isinstance(x_limits,dict):
            raise TypeError("wrong type of 'x_limits'. It must be dict")

        for k,v in x_limits.items():
            if not isinstance(v,(list,type(self))):
                raise TypeError("wrong type of 'x_limits' dict_value. It must be list or RooFitVar")
            if isinstance(v,list):
                if not len(v) == 2:
                    raise ValueError("length of 'x_limits' dict_value is wrong. It must be equal two")
                x.append(ROOT.RooRealVar(k,k,v[0],v[1]))
            else:
                if not k == 'all' and not k in v.get_x_limits():
                    raise ValueError(f"key {k} does not exist in {v.get_name()}!")
                if k == 'all' and not len(x_limits.items()) == 1:
                    raise ValueError(f"key {k} must be unique in x_limits!")
                if k == 'all':
                    x = v.get_x()
                    self._x_limits = v.get_x_limits()
                    break
                else:
                    for arg in v.get_x():
                        if arg.GetName() == k:
                            x.append(arg)
        
        container = []
        for k,v in param_dict.items():
            if not isinstance(v,(list,type(self),int,float)):
                raise TypeError("wrong type of 'param_dict' dict_value. It must be list / RooFitVar / int / float")
            if not k in function_type and not function_type == 'poly':
                raise ValueError("'function_type' is not correct. There are not used parameters")
            if isinstance(v,(int,float)):
                v = [v]
            if isinstance(v,list):
                if not len(v) in [1,3]:
                    raise ValueError("length of 'param_dict' dict_value is wrong. It must be equal one or three")
                if len(v) == 1 or v[1] == v[2]:
                    container.append(ROOT.RooRealVar(k,k,v[0]))
                else:
                    container.append(ROOT.RooRealVar(k,k,v[0],v[1],v[2]))
            else:
#                isRooFitVar = True
                container.append(v.get_function())

#       if not function_type == 'poly' and not isRooFitVar:
        if not function_type == 'poly':
            container += x

        if function_type == 'poly':
#           If lowestOrder is not zero, then the first element in coefList is interpreted as the 'lowestOrder' coefficient and all subsequent coefficient elements are shifted by a similar amount. 
#           It is useful if we want polynomials with arbitrary powers of x 
            return x, container, ROOT.RooPolyVar(var_name,var_name,*x,container,lowestOrder=self._lowestOrder)
        else:
            return x, container, ROOT.RooFormulaVar(var_name,function_type,container)

    def __init__(self, x_limits: dict, function_type: str, param_dict: dict, var_name: str, lowestOrder : int = 0):
        self._x_limits = x_limits
        self._function_type = function_type
        self._param_dict = param_dict
        self._var_name = var_name
        self._lowestOrder = lowestOrder
        self._x, self._container, self._function = self._setFunction()

    def get_x_limits(self):
        return self._x_limits

    def get_function_type(self):
        return self._function_type

    def get_param_dict(self):
        return self._param_dict

    def get_function(self):
        return self._function

    def get_name(self):
        return self._var_name
    
    def get_lowestOrder(self):
        return self._lowestOrder

    def get_x(self):
        return self._x

    def get_container(self):
        return self._container


class RooFitFunction:

    _FUNCTIONALITY = None
    _MARKER = None

    def _setBase(self):
        x_limits = self._x_limits
        param_dict = self._param_dict
        marker = self._marker
        functionality = self._functionality

        if not marker is None and functionality is None:
            raise ValueError("parameter 'functionality' must be defined")

        x = []
        if not isinstance(x_limits,dict):
            raise TypeError("wrong type of 'x_limits'. It must be dict")

        if marker == 'add' or marker == 'convolution':
            x = functionality[0].get_x()
        elif marker == 'ord_mul' or marker == 'cond_mul':
            x = functionality[0].get_x() + functionality[1].get_x()
        elif marker == 'composition':
            obj = next(iter(functionality.keys()))
            x = obj.get_x()            
        else:
            for k,v in x_limits.items():
                if not isinstance(v,(list,RooFitVar,type(self))):
                    raise TypeError("wrong type of 'x_limits' dict_value. It must be list or RooFitVar or RooFitFunction")
                if isinstance(v,list):
                    if not len(v) == 2:
                        raise ValueError("length of 'x_limits' dict_value is wrong. It must be equal two")
                    x.append(ROOT.RooRealVar(k,k,v[0],v[1]))
                else:
                    if not k == 'all' and not k in v.get_x_limits():
                        raise ValueError(f"key {k} does not exist in {v.get_name()}!")
                    if k == 'all' and not len(x_limits.items()) == 1:
                        raise ValueError(f"key {k} must be unique in x_limits!")
                    if k == 'all':
                        x = v.get_x()
                        self._x_limits = v.get_x_limits()
                        break
                    else:
                        for arg in v.get_x():
                            if arg.GetName() == k:
                                x.append(arg)

#        print(f"{self._function_type} : {x}")

        container = []
        if not isinstance(param_dict,dict):
            raise TypeError("wrong type of 'param_dict'. It must be dict")
                
        if marker == 'convolution' or marker == 'ord_mul' or marker == 'cond_mul':
            container = list(np.unique(functionality[0].get_container() + functionality[1].get_container()))
        else:
            indices = []
            for k,v in param_dict.items():
                if not isinstance(v,(list,RooFitVar,type(self),int,float)):
                    raise TypeError("wrong type of 'param_dict' dict_value. It must be list / RooFitVar / RooFitFunction / int / float")
                if isinstance(v,(int,float)):
                    v = [v]
                if isinstance(v,list):
                    if not len(v) in [1,3]:
                        raise ValueError("length of 'param_dict' dict_value is wrong. It must be equal one or three")
                    if len(v) == 1 or v[1] == v[2]:
                        container.append(ROOT.RooRealVar(k,k,v[0]))
                    else:
                        container.append(ROOT.RooRealVar(k,k,v[0],v[1],v[2]))
                elif isinstance(v,RooFitVar):
                    container.append(v.get_function())
                    indices.append(container.index(container[-1]))
                else:
                    if not k in v.get_param_dict():
                        raise ValueError(f"key {k} does not exist in {v.get_param_dict()}!")
                    for arg in v.get_container():
                        if arg.GetName() == k:
                            container.append(arg)
        if marker == 'add':
            container  = list(np.unique(functionality[0].get_container() + functionality[1].get_container())) + container[:-2:-1]
        elif marker == 'composition':
            obj = next(iter(functionality.keys()))
            initial_container = obj.get_container()
            for j in indices:
                initial_container[j] = container[j]
            container = initial_container

        return x,container

    def _setFunction(self):
        function_name = self._function_name
        function_type = self._function_type
        x, container = self._x, self._container
        marker = self._marker
        functionality = self._functionality

        if marker == 'add':
            if functionality is None:
                raise ValueError("parameter 'functionality' must be defined")
            else:
                functionality = [pdf.get_function() for pdf in functionality]
                return ROOT.RooAddPdf(function_name,function_type,functionality,container[-1])
        elif marker == 'convolution':
            if functionality is None:
                raise ValueError("parameter 'functionality' must be defined")
            if not len(x) == 1:
                raise ValueError("wrong number of arguments in convolution. Only one-dimensional convolution is implemented!!")
            else:
                for x_val in x: x_val.setBins(1000, "cache")
                functionality = [pdf.get_function() for pdf in functionality]
                return ROOT.RooFFTConvPdf(function_name,function_type,*x,*functionality)
#                return ROOT.RooNumConvPdf(function_name,function_type,*x,*functionality)
        elif marker == 'ord_mul':
            if functionality is None:
                raise ValueError("parameter 'functions' must be defined")
            else:
                functionality = [pdf.get_function() for pdf in functionality]
                return ROOT.RooProdPdf(function_name,function_type,functionality)
        elif marker == "cond_mul":
            if functionality is None:
                raise ValueError("parameter 'functions' must be defined")
            else:
#                one_x_conditional = [ROOT.RooRealVar(k,k,v[0],v[1]) for l in functionality[0].get_functionality().values() for d in l for k,v in d.items()]
                one_x_conditional = functionality[0].get_conditional_x()
#               The boolean inverts the “conditional”: Conditional(pdf, x, true) = pdf is conditional on x. 
#               That is, don’t integrate it over x to normalise. Conditional(pdf, x, false) = pdf is conditional on all but x (default)
#                one_x_conditonal = [ROOT.RooRealVar(k,k,v[0],v[1]) for k,v in list(functionality[0].keys())[0].get_x_limits().items()]
                if not len(functionality[1].get_conditional_x()) == 0:
                    # two-sided conditional multiplication
#                    two_x_conditional = [ROOT.RooRealVar(k,k,v[0],v[1]) for l in functionality[1].get_functionality().values() for d in l for k,v in d.items()]
                    two_x_conditional = functionality[1].get_conditional_x()
                    return ROOT.RooProdPdf(function_name,
                                           function_type,
                                           set(), 
                                           ROOT.RooFit.Conditional({functionality[0].get_function()},set(one_x_conditional),depsAreCond=True), 
                                           ROOT.RooFit.Conditional({functionality[1].get_function()},set(two_x_conditional),depsAreCond=True))
                else:
                    # one-sided conditional multiplication
                    return ROOT.RooProdPdf(function_name,
                                           function_type,
                                           {functionality[1].get_function()}, 
                                           ROOT.RooFit.Conditional({functionality[0].get_function()},set(one_x_conditional),depsAreCond=True))
        function_type = function_type.split('|')[0]
        function_type_dict = {'2sidedCB': 7, 'BFGauss': 3, 'BreitWigner': 2, 'Gauss': 2, 'Voigt' : 3, 'Novosibirsk' : 3, 'Johnson' : 4}
        right_param_dict_len = function_type_dict.get(self._function_type, self._param_dict_len)
#        if not len(self._param_dict) == right_param_dict_len:
#            raise TypeError(f"length of 'param_dict' dict is wrong. It must be equal {right_param_dict_len}")
        if function_type == '2sidedCB':
            return ROOT.RooCrystalBall(function_name,function_type,*x,*container)
        elif function_type == 'BFGauss':
            return ROOT.RooBifurGauss(function_name,function_type,*x,*container)
        elif function_type == 'BreitWigner':
            return ROOT.RooBreitWigner(function_name,function_type,*x,*container)
        elif function_type == 'Gauss':
            return ROOT.RooGaussian(function_name,function_type,*x,*container)
        elif function_type == 'Voigt':
            return ROOT.RooVoigtian(function_name,function_type,*x,*container)
        elif function_type == 'Novosibirsk':
            return ROOT.RooNovosibirsk(function_name,function_type,*x,*container)
        elif function_type == 'Johnson':
            return ROOT.RooJohnson(function_name,function_type,*x,*container)
        elif function_type == 'Chebychev':
            return ROOT.RooChebychev(function_name,function_type,*x,container)

    def __init__(self, name : str, x_limits: dict, function_type: str, param_dict: dict, param_dict_len: int = 0):
        self._function_name = name
        self._x_limits = x_limits
        self._function_type = function_type
        self._param_dict = param_dict
        self._param_dict_len = param_dict_len
        self._functionality = self._FUNCTIONALITY
        self._marker = self._MARKER
        self._x, self._container = self._setBase()
        self._function = self._setFunction()

    def get_name(self):
        return self._function_name

    def get_x_limits(self):
        return self._x_limits

    def get_function_type(self):
        return self._function_type

    def get_param_dict(self):
        return self._param_dict

    def get_x(self):
        return self._x

    def get_conditional_x(self):
        if isinstance(self._functionality,dict):
            return list(self._functionality.values())[0]
        elif isinstance(self._functionality,list):
            return self._functionality[0].get_conditional_x() + self._functionality[1].get_conditional_x()
        else:
            return []

    def get_container(self):
        return self._container

    def get_function(self):
        return self._function

    def get_functionality(self):
        return self._functionality

    def get_NFitFloated(self):
        return getattr(self,'_NFitFloated',None)

    def get_extended(self):
        return False

    def get_add(self, other, frac_parameter: dict, name: str | None = None):
        if not isinstance(other, type(self)):
            raise TypeError("wrong type of instance. It must be RooFitFunction")
        if not isinstance(frac_parameter,dict):
            raise TypeError("wrong type of 'frac_parameter'. It must be dict")
        if not len(frac_parameter) == 1:
            raise TypeError("length of 'frac_parameter' dict is exceeded. It must be one")
        if not id(self.get_x()) == id(other.get_x()):
            raise TypeError(f"Please use the same objects as arguments for PDF functions to be added!! {self.get_x_limits().keys()} != {other.get_x_limits().keys()}")
#        if not isinstance(list(frac_parameter.values())[0],list):
#            raise TypeError("wrong type of 'frac_parameter' value. It must be list")
#        if not len(list(frac_parameter.values())[0]) == 3:
#            raise TypeError("length of 'frac_parameter' list value is wrong. It must be equal three")

        name = self.get_name() + ' + ' + other.get_name() if name is None else name
        function_type = "(+)".join([self.get_function_type(),other.get_function_type()])
        param_dict = {**self.get_param_dict(),**other.get_param_dict(),**frac_parameter}
        param_dict_len = len(self._param_dict) + len(other._param_dict) + 1        
        x_limits = self.get_x_limits()
        functionality = [self,other]
        setattr(type(self),'_FUNCTIONALITY',functionality)
        setattr(type(self),'_MARKER',"add")
        obj = type(self)(name, x_limits, function_type, param_dict, param_dict_len)
        setattr(type(self),'_FUNCTIONALITY',None)
        setattr(type(self),'_MARKER',None)
        return obj

    def get_extended_add(self,other,frac_parameter: dict):
        pass

# Only convolution, where arguments of basic and resolution functions are the same, is implemented now!!
# The general case corresponds to the convolution performing only for part of arguments or different resolutions for each argument ..  
    def get_convolution(self, other, name : str | None = None):
        if not isinstance(other, type(self)):
            raise TypeError("wrong type of instance. It must be RooFitFunction")
        if not id(self.get_x()) == id(other.get_x()):
            raise TypeError("Please use the same objects as arguments for PDF functions to be convolved!")

        name = self.get_name() + ' X ' + other.get_name() if name is None else name
        function_type = "(X)".join([self.get_function_type(),other.get_function_type()])
        param_dict = {**self.get_param_dict(),**other.get_param_dict()}
        param_dict_len = len(self._param_dict) + len(other._param_dict)
        x_limits = self.get_x_limits()
        functionality = [self,other]
        setattr(type(self),'_FUNCTIONALITY',functionality)
        setattr(type(self),'_MARKER',"convolution")
        obj = type(self)(name, x_limits, function_type, param_dict, param_dict_len)
        setattr(type(self),'_FUNCTIONALITY',None)
        setattr(type(self),'_MARKER',None)
        return obj

    def get_composition(self, parameter_other_dict: dict, normalized: bool = False):
        name = self.get_name()

        param_dict = self.get_param_dict()
        y_limits = []
        postfix = []
        for k,v in parameter_other_dict.items():
            if not isinstance(v, RooFitVar):
                raise TypeError(f"wrong type of instance {v}. It must be type of RooFitVar")
            if not k in param_dict:
                raise ValueError(f"wrong parameter {k}. It must be earlier defined in RooFitFunction object")

            for x in v.get_x():
                for y in y_limits:
                    if x.GetName() == y.GetName() and not id(x) == id(y):
                        raise ValueError("RooFitVar objects have the same x_keys but different arguments (argument objects must be the same)!")
                if not x.GetName() in postfix:
                    postfix.append(x.GetName())
                y_limits.append(x)
            if not normalized:
                param_dict[k] = v
            else:
                param_dict[k] = RooFitVar(v.get_x_limits(),f"{k}*({v.get_name()})",{k:param_dict[k], v.get_name():v},f"{k}:{v.get_name()}")

        function_type = self.get_function_type() + f"|({','.join(map(str,(*postfix,)))})"
        param_dict_len = len(self.get_param_dict())
        x_limits = self.get_x_limits()
       # list of condtional arguments (w/o duplicates)
        for i,y in enumerate(y_limits):
            for y1 in y_limits[:i:-1]:
                if id(y) == id(y1) :
                    y_limits.remove(y1)
#        print("y-limits = ", y_limits)
        functionality = {self : y_limits}
        if not self.get_functionality() is None:
            raise ValueError("Please make composition only with simple RooFitFunction objects (not added, convolved, multiplied)!!!")
        setattr(type(self),'_FUNCTIONALITY',functionality)
        setattr(type(self),'_MARKER',"composition")
        obj = type(self)(name, x_limits, function_type, param_dict, param_dict_len)
        setattr(type(self),'_FUNCTIONALITY',None)
        setattr(type(self),'_MARKER',None)
        return obj

    def __mul__(self,other):
#        def str_set(s: List[str]):
#            if not isinstance(s,list):
#                raise TypeError("wrong type of positional argument provided. It must be 'List[str]'")
#            for _ in s:
#                if not isinstance(_,str):
#                    raise TypeError("wrong type of positional argument provided. It must be 'List[str]'")
#            if s == ['']:
#                return set()
#            else:
#                return set(s)

#        if not isinstance(other, type(self)):
#            raise TypeError("wrong type of instance. It must be RooFitFunction")

        for x1 in self.get_x():
            for x2 in other.get_x():
                if x2.GetName() == x1.GetName() and not id(x2) == id(x1):
                    raise ValueError("RooFitFunction objects have the same x_keys but different arguments (argument objects must be the same)!")

#        standard_arguments = [set(obj.get_x_limits().keys()) for obj in (self,other)]
        standard_arguments = [set(obj.get_x()) for obj in (self,other)]
#        conditional_arguments = [str_set(','.join(list(map(lambda s: s[2:-1],re.findall(r'\|\([a-z,]+\)',obj.get_function_type())))).split(',')) for obj in (self,other)]
        conditional_arguments = [set(obj.get_conditional_x()) for obj in (self,other)]

#       common multiplication (no conditional arguments)
#       functionality  - list of self and other
        list_of_conditions = [conditional_arguments[_] < standard_arguments[_] for _ in range(2)]
        if all(list_of_conditions):
            function_type = "(*)".join([self.get_function_type(),other.get_function_type()])
            functionality = [self,other]
            setattr(type(self),'_MARKER',"ord_mul")
#       two-sided conditional multiplication (conditional arguments for self and other)
#       functionality - list of dicts with key / item = RooFitFunction object  / list of dicts (key = x_limits key), item (range of limits)) 
#       with conditional arguments (formed by 'get_composition' method)
        elif not any(list_of_conditions):
            function_type = "(*|)".join([self.get_function_type(),other.get_function_type()])
#            functionality = [self.get_functionality(),other.get_functionality()]
            functionality = [self,other]
            setattr(type(self),'_MARKER',"cond_mul")
#       one-sided conditional multiplication (conditional arguments for either self or other)
#       functionality - list of dict for conditional PDF and RooFitFunction object for ordinary PDF
        else:
            o1, o2 = (self, other) if list_of_conditions[1] else (other, self)
#           o1 - conditional PDF , o2 - ordinary PDF            
            function_type = "(*|)".join([o1.get_function_type(),o2.get_function_type()])
#            print("function_type = ", function_type)
#            functionality = [o1.get_functionality(),o2]
            functionality = [o1,o2]
            setattr(type(self),'_MARKER',"cond_mul")
#        functionality = [self,other]
        name = self.get_name() + ' * ' + other.get_name()
        param_dict = {**self.get_param_dict(),**other.get_param_dict()}
        param_dict_len = len(self._param_dict)
        x_limits = {**self.get_x_limits(), **other.get_x_limits()}
        setattr(type(self),'_FUNCTIONALITY',functionality)
        obj = type(self)(name,x_limits,function_type,param_dict,param_dict_len)
        setattr(type(self),'_FUNCTIONALITY',None)
        setattr(type(self),'_MARKER',None)
        return obj

    def set_fixed(self,fixed_parameters: dict):
        keys = list(self._param_dict.keys())
        for k, v in fixed_parameters.items():
            if not isinstance (v,(float,int)):
                raise TypeError("type of 'fixed_parameters' dict_values is not '(float,int)'")
            if k in keys:
                icontainer = keys.index(k)
                self._container[icontainer] = ROOT.RooRealVar(k,k,v,v,v) 
        self._function = self._setFunction()

    def set_floated(self,floated_parameters: dict):
        keys = list(self._param_dict.keys())
        for k,v in floated_parameters.items():
            if not isinstance(v,list):
                raise TypeError("type of 'floated_parameters' dict_values is not 'list'")
            if k in keys:
                icontainer = keys.index(k)
                self._container[icontainer] = ROOT.RooRealVar(k,k,v[0],v[1],v[2])
            self._function = self._setFunction()

    def set_limits(self,x_limits_values: List):
        for k in self._x_limits.keys():
            self._x = ROOT.RooRealVar(k,k,x_limits_values[0],x_limits_values[1])
        self._function = self._setFunction()

    def set_NFitFloated(self,number):
        setattr(self,'_NFitFloated',number)


if __name__ == "__main__":
    # Delta E 1-dim RooFit function test
    de_cb = RooFitFunction('CrystalBall',{'dE' : [-.15,.15]}, '2sidedCB', {'x0CB' : [0,-0.01,0.01], 'sigmacbL': [0.02,0.005,0.05], 'sigmacbR': [0.02,0.005,0.05], 
        'alphaL': [0.1,0.005,2], 'alphaR': [0.1,0.005,2], 'nL' : [1,0.1,20.], 'nR' : [1,0.1,20.]})
    de_bfGauss = RooFitFunction('Gauss',{'all' : de_cb}, 'BFGauss' , {'x0' : [0,-0.01,0.01], 'sigmaL': [0.01,0.001,0.05], 'sigmaR': [0.1,0.001,0.05]})

    x0cb_function = RooFitVar({'mom': [0.74,.855]}, 'p1*(mom-0.7826)+p0', {'p1' : [0.1,0.,1.], 'p0' : [0,-0.1,0.1]},"x0CB_func")
    de_cb = de_cb.get_composition({'x0CB' : x0cb_function})
    de_pdf = de_cb.get_add(de_bfGauss,{'frac': [0.5,0.,1.]})

    # Omega 1-dim RooFit function test
    mom_bw = RooFitFunction('BreitWigner', {'mom': [0.74,.855]}, 'BreitWigner', {'mean' : [0.78265,0.77,0.79], 'width' : [0.0085,0,0]})
    mom_cb = RooFitFunction('CrystalBall', {'all': mom_bw}, '2sidedCB', {'x0CB' : [0,0,0], 'sigcbL' : [0.005,0.001,0.05], 'sigcbR' : [0.005,0.001,0.05], 
        'alphaL' : [1,0.005,2], 'alphaR' : [1,0.005,2], 'nL' : [1,0.01,50.], 'nR' : [1,0.01,50.]})
    mom_pdf  = mom_bw.get_convolution(mom_cb)

    # Example of nested compositions and shared parameters
    de_poly = RooFitVar({'dE' : [-.15,.15]}, 'p0+p1*dE+p2*dE**2', {"p0" : [5.,5.,5.], "p1" : [-2.,-2.,-2.], "p2" : [3.,3.,3.]}, "poly3")
    mom_de_poly_pdf = mom_bw.get_convolution(mom_cb.get_composition({'sigcbL' : de_poly}))

    # (Delta E - Omega) RooFit uncorr. product 
    de_mom_uncorr_pdf = de_pdf * mom_pdf

    # (Delta E - Omega) RooFit one-sided conditional product
    de_mom_1cond_pdf = mom_de_poly_pdf * de_pdf

    print(de_mom_1cond_pdf.get_function_type())



