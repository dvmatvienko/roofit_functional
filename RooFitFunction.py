import ROOT
import re
from array import array
from typing import Any, List


class RooFitVar:

    @classmethod
    def _setBase(cls, x_limits: dict, function_type: str, param_dict: dict):
        isRooFitVar = False
        x = []
        for k,v in x_limits.items():
            if not isinstance(v,list):
                raise TypeError("wrong type of 'x_limits' dict_value. It must be list")
            if not len(v) == 2:
                raise TypeError("length of 'x_limits' dict_value is wrong. It must be equal two")
            x.append(ROOT.RooRealVar(k,k,v[0],v[1]))
        container = []
        for k,v in param_dict.items():
            if not isinstance(v,(list,RooFitVar)):
                raise TypeError("wrong type of 'param_dict' dict_value. It must be list or RooFitVar")
            if isinstance(v,list):
                if not len(v) in [1,3]:
                    raise ValueError("length of 'param_dict' dict_value is wrong. It must be equal one or three")
            if not k in function_type and not function_type == 'poly':
                raise ValueError("'function_type' is not correct. There are not used parameters")
            if isinstance(v,RooFitVar):
                isRooFitVar = True
                container.append(v.get_function())
                continue
            if len(v) == 1 or v[1] == v[2]:
                container.append(ROOT.RooRealVar(k,k,v[0]))
            else:
                container.append(ROOT.RooRealVar(k,k,v[0],v[1],v[2]))
        if not function_type == 'poly' and not isRooFitVar:
            container += x
        return x, container

    def _setFunction(self):
        x, container = self._x, self._container
        var_name, function_type = self._var_name, self._function_type
        if function_type == 'poly':
            return ROOT.RooPolyVar(var_name,var_name,*x,container)
        else:
            return ROOT.RooFormulaVar(var_name,function_type,container)

    def __init__(self, x_limits: dict, function_type: str, param_dict: dict, var_name: str):
        self._x_limits = x_limits
        self._function_type = function_type
        self._param_dict = param_dict
        self._var_name = var_name
        self._x, self._container = self._setBase(x_limits, function_type, param_dict)
        self._function = self._setFunction()

    def get_x_limits(self):
        return self._x_limits

    def get_function_type(self):
        return self._function_type

    def get_param_dict(self):
        return self._param_dict

    def get_function(self):
        return self._function

    def get_var_name(self):
        return self._var_name


class RooFitFunction:

    @classmethod
    def _setBase(cls, x_limits: dict, param_dict: dict):
        if not isinstance(x_limits,dict):
            raise TypeError("wrong type of 'x_limits'. It must be dict")
        x = []
        for k,v in x_limits.items():
            if not isinstance(v,list):
                raise TypeError("wrong type of 'x_limits' dict_value. It must be list")
            if not len(v) == 2:
                raise ValueError("length of 'x_limits' dict_value is wrong. It must be equal two")
            x.append(ROOT.RooRealVar(k,k,v[0],v[1]))
        container = []
        if not isinstance(param_dict,dict):
            raise TypeError("wrong type of 'param_dict'. It must be dict")
        for k,v in param_dict.items():
            if not isinstance(v,(list,RooFitVar)):
                raise TypeError("wrong type of 'param_dict' dict_value. It must be list or RooFitVar")
            if isinstance(v,list):
                if not len(v) in [1,3]:
                    raise ValueError("length of 'param_dict' dict_value is wrong. It must be equal one or three")
            elif isinstance(v,RooFitVar):
                container.append(v.get_function())
                continue
            if len(v) == 1 or v[1] == v[2]:
                container.append(ROOT.RooRealVar(k,k,v[0],v[0],v[0]))
            else:
                container.append(ROOT.RooRealVar(k,k,v[0],v[1],v[2]))
        return x,container

    def _setFunction(self,functionality=None):
        x, container = self._x, self._container
        function_type = self._function_type
        if "(+)" in function_type:
            if functionality is None:
                raise ValueError("parameter 'functions' must be defined")
            else:
                return ROOT.RooAddPdf(function_type,function_type,functionality,container[-1])
        elif "(X)" in function_type:
            if functionality is None:
                raise ValueError("parameter 'functions' must be defined")
            else:
                for x_val in x: x_val.setBins(1000, "cache")
                return ROOT.RooFFTConvPdf(function_type,function_type,*x,*functionality)
        elif "(*)" in function_type:
            if functionality is None:
                raise ValueError("parameter 'functions' must be defined")
            else:
                return ROOT.RooProdPdf(function_type,function_type,functionality)
        elif "(*|)" in function_type:
            if functionality is None:
                raise ValueError("parameter 'functions' must be defined")
            else:
                one_x_conditonal = [ROOT.RooRealVar(k,k,v[0],v[1]) for k,v in (d.keys(), d.values()) for d in list(functionality[0].values())[0]]
                if type(functionality[1]) is not dict:
                    # two-sided conditional multiplication
                    two_x_conditional = [ROOT.RooRealVar(k,k,v[0],v[1]) for k,v in (d.keys(), d.values()) for d in list(functionality[1].values())[0]]
                    return ROOT.RooProdPdf(function_type,function_type,set(),Conditional=({list(functionality[0].keys())[0],list(functionality[1].keys())[0]},set(one_x_conditonal+two_x_conditional)))
                else:
                    # one-sided conditional multiplication
                    return ROOT.RooProdPdf(function_type,function_type,{functionality[1]},Conditional=({list(functionality[0].keys())[0]},set(one_x_conditonal)))
        function_type = function_type.split('|')[0]
        function_type_dict = {'2sidedCB': 7, 'BFGauss': 3, 'BreitWigner': 2}
        right_param_dict_len = function_type_dict.get(self._function_type, self._param_dict_len)
        if not len(self._param_dict) == right_param_dict_len:
            raise TypeError(f"length of 'param_dict' dict is wrong. It must be equal {right_param_dict_len}")
        if function_type == '2sidedCB':
            return ROOT.RooCrystalBall(function_type,function_type,*x,*container)
        elif function_type == 'BFGauss':
            return ROOT.RooBifurGauss(function_type,function_type,*x,*container)
        elif function_type == 'BreitWigner':
            return ROOT.RooBreitWigner(function_type,function_type,*x,*container)

    def __init__(self, x_limits: dict, function_type: str, param_dict: dict, param_dict_len: int = 0, functionality=None):
        self._x_limits = x_limits
        self._function_type = function_type
        self._param_dict = param_dict
        self._param_dict_len = param_dict_len
        self._functionality = functionality
        self._x, self._container = self._setBase(x_limits, param_dict)
        self._function = self._setFunction(functionality)

    def get_x_limits(self):
        return self._x_limits

    def get_function_type(self):
        return self._function_type

    def get_param_dict(self):
        return self._param_dict

    def get_x(self):
        return self._x

    def get_container(self):
        return self._container

    def get_function(self):
        return self._function

    def get_functionality(self):
        return self._functionality

    def get_add(self,other,frac_parameter: dict):
        if not isinstance(other, type(self)):
            raise TypeError("wrong type of instance. It must be RooFitFunction")
        if not isinstance(frac_parameter,dict):
            raise TypeError("wrong type of 'frac_parameter'. It must be dict")
        if not len(frac_parameter) == 1:
            raise TypeError("length of 'frac_parameter' dict is exceeded. It must be one")
        if not self.get_x_limits() == other.get_x_limits():
            raise TypeError("wrong correspondence of x_limits between instances")
        for k,v in frac_parameter.items():
            if not isinstance(v,list):
                raise TypeError("wrong type of 'frac_parameter' value. It must be list")
            if not len(v) == 3:
                raise TypeError("length of 'frac_parameter' list value is wrong. It must be equal three")
        function_type = "(+)".join([self.get_function_type(),other.get_function_type()])
        param_dict = {**self.get_param_dict(),**other.get_param_dict(),**frac_parameter}
        param_dict_len = len(self._param_dict)
        x_limits = self.get_x_limits()
        functionality = [self.get_function(),other.get_function()]
        return type(self)(x_limits, function_type, param_dict, param_dict_len, functionality)

    def get_extended_add(self,other,frac_parameter: dict):
        pass

# Only convolution, where 'x_limits' of basic and resolution functions are the same, is implemented now!!
# The general case corresponds to the convolution performing only for part of arguments or different resolutions for each argument ..  
    def get_convolution(self,other):
        if not isinstance(other, type(self)):
            raise TypeError("wrong type of instance. It must be RooFitFunction")
        if not self.get_x_limits() == other.get_x_limits():
            raise ValueError("wrong correspondence of x_limits between instances")
        function_type = "(X)".join([self.get_function_type(),other.get_function_type()])
        param_dict = {**self.get_param_dict(),**other.get_param_dict()}
        param_dict_len = len(self._param_dict)
        x_limits = self.get_x_limits()
        functionality = [self.get_function(),other.get_function()]
        return type(self)(x_limits, function_type, param_dict, param_dict_len, functionality)

    def get_composition(self,parameter_other_dict: dict):
        param_dict = self.get_param_dict()
        y_limits = []
        postfix = []
        for k,v in parameter_other_dict.items():
            for x_key in v.get_x_limits().keys():
                for i in range(len(y_limits)):
                    if x_key in y_limits[i].keys() and not v.get_x_limits()[x_key] == y_limits[i][x_key]:
                        raise ValueError("RooFitVar objects have the same x_keys but different x_limits!")
                if not x_key in postfix:
                    postfix.append(x_key)
            if not isinstance(v, RooFitVar):
                raise TypeError(f"wrong type of instance {v}. It must be type of RooFitVar")
            if not k in param_dict.keys():
                raise ValueError(f"wrong parameter {k}. It must be earlier defined in RooFitFunction object")
            param_dict[k] = RooFitVar(v.get_x_limits(),f"{k}*{v.get_var_name()}",{k:param_dict[k], v.get_var_name():v},f"{k}:{v.get_var_name()}")
            y_limits.append(v.get_x_limits())
        print(postfix) 
        function_type = self.get_function_type() + f"|({','.join(map(str,(*postfix,)))})"
        param_dict_len = len(self.get_param_dict())
        x_limits = self.get_x_limits()
       # dict with one key - RooFit function for self, one value - list of dicts of condtional arguments (w/o duplicates)
        for i,d in enumerate(y_limits):
            for d1 in y_limits[:i:-1]:
                if d == d1 :
                    y_limits.remove(d1)
        functionality = {self.get_function() : y_limits}
        return type(self)(x_limits,function_type,param_dict,param_dict_len,functionality)

    def __mul__(self,other):
        if not isinstance(other, type(self)):
            raise TypeError("wrong type of instance. It must be RooFitFunction")

        def str_set(s: List[str]):
            if not isinstance(s,list):
                raise TypeError("wrong type of positional argument provided. It must be 'List[str]'")
            for _ in s:
                if not isinstance(_,str):
                    raise TypeError("wrong type of positional argument provided. It must be 'List[str]'")
            if s == ['']:
                return set()
            else:
                return set(s)

        standard_arguments = [set(obj.get_x_limits().keys()) for obj in (self,other)]
        conditional_arguments = [str_set(','.join(list(map(lambda s: s[2:-1],re.findall(r'\|\([a-z,]+\)',obj.get_function_type())))).split(',')) for obj in (self,other)]
#       common multiplication (no conditional arguments)
#       functionality  - list of RooFit function objects
        list_of_conditions = [conditional_arguments[_] < standard_arguments[_] for _ in range(2)]
        if all(list_of_conditions):
            function_type = "(*)".join([self.get_function_type(),other.get_function_type()])
            functionality = [self.get_function(),other.get_function()]
#       two-sided conditional multiplication (conditional arguments for self and other)
#       functionality - list of dicts with key / item = RooFit function object  / list of dicts (key = x_limits key), item (range of limits)) 
#       with conditional arguments (formed by 'get_composition' method)
        elif not any(list_of_conditions):
            function_type = "(*|)".join([self.get_function_type(),other.get_function_type()])
            functionality = [self.get_functionality(),other.get_functionality()]
#       one-sided conditional multiplication (conditional arguments for either self or other)
#       functionality - list of dict for conditional PDF and RooFit function object for ordinary PDF
        else:
            o1, o2 = (self, other) if list_of_conditions[1] else (other, self)
#           o1 - conditional PDF , o2 - ordinary PDF            
            function_type = "(*|)".join([o1.get_function_type(),o2.get_function_type()])
            functionality = [o1.get_functionality(),o2.get_function()]
        param_dict = {**self.get_param_dict(),**other.get_param_dict()}
        param_dict_len = len(self._param_dict)
        x_limits = {**self.get_x_limits(), **other.get_x_limits()}
        return type(self)(x_limits,function_type,param_dict,param_dict_len,functionality)

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


if __name__ == "__main__":
    # Delta E 1-dim RooFit function test
    de_cb = RooFitFunction({'dE' : [-.15,.15]}, '2sidedCB', {'x0CB' : [0,-0.01,0.01], 'sigmacbL': [0.02,0.005,0.05], 'sigmacbR': [0.02,0.005,0.05], 
        'alphaL': [0.1,0.005,2], 'alphaR': [0.1,0.005,2], 'nL' : [1,0.1,20.], 'nR' : [1,0.1,20.]})
    de_bfGauss = RooFitFunction({'dE' : [-.15,.15]}, 'BFGauss' , {'x0' : [0,-0.01,0.01], 'sigmaL': [0.01,0.001,0.05], 'sigmaR': [0.1,0.001,0.05]})
    de_pdf = de_cb.get_add(de_bfGauss,{'frac': [0.5,0.,1.]})

    # Omega 1-dim RooFit function test
    mom_bw = RooFitFunction({'mom': [0.74,.855]}, 'BreitWigner', {'mean' : [0.78265,0,0], 'width' : [0.0085,0,0]})
    mom_cb = RooFitFunction({'mom': [0.74,.855]}, '2sidedCB', {'x0CB' : [0,0,0], 'sigcbL' : [0.005,0.001,0.05], 'sigcbR' : [0.005,0.001,0.05], 
        'alphaL' : [1,0,2], 'alphaR' : [1,0,2], 'nL' : [1,0.01,50.], 'nR' : [1,0.01,50.]})
    mom_pdf  = mom_bw.get_convolution(mom_cb)

    # Example of composition
    de_poly = RooFitVar({'dE' : [-.15,.15]}, 'poly', {"p0" : [5.,5.,5.], "p1" : [-2.,-2.,-2.], "p2" : [3.,3.,3.]}, "poly3")
    mom_de_poly_pdf = mom_bw.get_convolution(mom_cb.get_composition({'sigcbL' : de_poly}))

    # (Delta E - Omega) RooFit uncorr. product 
    de_mom_uncorr_pdf = de_pdf * mom_pdf

    # (Delta E - Omega) RooFit one-sided conditional product
    de_mom_1cond_pdf = mom_de_poly_pdf * de_pdf



