import ROOT
import numpy as np

from roofit_functional.RooFitFunction import RooFitFunction
from roofit_functional.RooFitData import RooFitData

# https://root-forum.cern.ch/t/rooabsreal-how-to-transform-the-function-or-get-the-value-of-each-points/52738/3
def digit_function(f : RooFitFunction, data : RooFitData, subrange : dict = {}):
    function = f.get_function()
    dataset = data.get_dataset()

    function.attachDataSet(dataset)

    observables = dataset.get()
    digits = []

    for iEvent in range(dataset.numEntries()):
        dataset.get(iEvent)
        digits.append(function.getVal(observables))

    dict_numpy = dataset.to_numpy()
    data_numpy = np.array([dict_numpy[k] for k in dict_numpy.keys()])

    digit_data = np.append(data_numpy,np.expand_dims(digits,axis=0),axis=0)

    for k,v in subrange.items():
        if not k in dict_numpy.keys():
            raise ValueError(f"Only rectangular subrange is allowed! Key of subrange must be one of the function args but '{k}' is assigned")
        if not isinstance(v,list):
            raise TypeError("subrange values must type of list!")
        if not len(v) == 2:
            raise ValueError("subrange value list has two values: min and max of the subrange")
        dict_index = list(dict_numpy.keys()).index(k)
        condition = (digit_data[:,dict_index] > v[0]) & (digit_data[:,dict_index] < v[1])
        digit_data = digit_data[condition]
        
    return digit_data

if __name__ == "__main__":
    from roofit_functional.RooFitFunction import RooFitFunction, RooFitVar, wrapped
    from roofit_functional.RooFitData import RooFitData
    from roofit_functional.RooFitPlot import RooFitPlot
    import numpy as np
    import matplotlib.pyplot as plt

    # Delta E 1-dim RooFit function test
    de_cb = RooFitFunction('CrystalBall',{'dE' : [-.15,.15]}, 'CrystalBall', {'x0CB' : [0,-0.01,0.01], 'sigmacbL': [0.03,0.001,0.05], 'sigmacbR': [0.01,0.001,0.05],
        'alphaL': [0.1,0.005,10], 'nL' : [1,0.1,20.], 'alphaR': [0.1,0.005,10], 'nR' : [1,0.1,20.]})
    de_bfGauss = RooFitFunction('Gauss',{'all' : de_cb}, 'BifurGauss' , {'x0' : [0,-0.01,0.01], 'sigmaL': [0.02,0.01,0.05], 'sigmaR': [0.02,0.01,0.05]})
    de_pdf = de_cb.get_add(de_bfGauss,{'frac': [0.5,0.,1.]})

    data = RooFitData("test","unbinned",(de_pdf,500),de_pdf.get_x())

    dataset = digit_function(de_pdf,data)

    dataset = dataset[dataset[:,0].argsort()]

#    plt.plot(dataset[:,0],dataset[:,1])
#    plt.savefig(f'digit_function.pdf',bbox_inches='tight')

#    p = RooFitPlot(data,de_pdf,"dE","dE plot",Bins=10)
#    p.make_plot()

    sigma = wrapped(RooFitVar({'y' : [-1,1]}, '1/(1+exp(-k*(y-a)))-1/(1+exp(-k*(y-b)))', {'k' : 100, 'a' : -0.5, 'b' : 0.5},'sigma'))
    data_sigma = RooFitData("test","unbinned",(sigma,500),sigma.get_x())

    p_sigma = RooFitPlot(data_sigma,sigma,"y","y plot",Bins=10)
    p_sigma.make_plot()



