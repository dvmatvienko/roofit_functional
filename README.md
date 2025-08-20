# roofit_functional
roofit_functional is a user-friendly python library aiming to simplify work with [RooFit framework](https://root.cern/manual/roofit/) 
which models the expected distribution of events in data analysis based on 
maximum-likelihood (ML) method. The data sample could be multi-dimensional, and has one or more measured (and correlated) observables associated with it.
It was initially created for elementary particle physics but it has universal application for tabular data of arbitrary nature.

roofit_functional is designed to combine multiple RooFit features in one place. RooFit is a complex framework with many hierarchy-structured classes and 
variety of methods and parameters inside each class. The builtin classes provide description for the most popular data distributions, their evaluations and operations 
with them. RooFit has important functionality for processing its models by fitted to data with using 
unbinned or binned ML (or $\chi^2$ fit), projected and plotted along with data, sampled using Monte Carlo technique. 
This functionality is represented by C++ classes. 
roofit_functional gives unified interface to all these operations in python manner. Only a few base classes allow the user to go through the entire 
chain of operations from creating a function, preparing a data set, fitting to data with a function and creating informative plots.  
Ceratinly such unification gives lower flexibility than original RooFit, because several knobs are out of roofit_functional visibility,
but many of these knobs are rarely used and are needed in very specific places. The focus of this tool is on automating widely used features of the RooFit. 

# Installation
```
pip install roofit_functional
```

# Description
RooFit has been initially written in C++. It implements classes that represents variables, probability density functions (PDFs) and operators to compose higher level functions. 
All classes are instrumented to be fully functional: fitting, plotting and toy event generation works the same way for every PDF regardless of its complexity. 
Some important parts of the underlying functionality are delegated to standard [ROOT library](https://root.cern/) and [MINUIT optimization tool](https://root.cern.ch/download/minuit.pdf)

RooFit uses PDF normalization relative to the user-defined range of variables. 

```python
import numpy as np
import roofit_functional as rff
std_gauss = rff.RooFitFunction('Gauss',{'x' : [-3,3]}, 'Gaussian', {'mean' : [0], 'sigma': [1]})
data = rff.RooFitData("test","unbinned",np.linspace(-3,3),std_gauss.get_x())
rff_pdf = rff.digit_function(std_gauss,data)[1]
```

It differs from `scipy.stats` where full space normalization is used. 

```python
import numpy as np 
from scipy import stats
xs = np.linspace(-3,3)
pdf = stats.norm(0, 1).pdf(xs)
```

`rff_pdf - pdf` results to 

```python
array([1.19974776e-05, 1.71937594e-05, 2.42739268e-05, 3.37596182e-05,
       4.62533626e-05, 6.24277081e-05, 8.30041425e-05, 1.08720249e-04,
       1.40284409e-04, 1.78318611e-04, 2.23291521e-04, 2.75445758e-04,
       3.34725070e-04, 4.00708624e-04, 4.72560518e-04, 5.49002692e-04,
       6.28318446e-04, 7.08391664e-04, 7.86783730e-04, 8.60846255e-04,
       9.27863550e-04, 9.85214808e-04, 1.03054282e-03, 1.06191425e-03,
       1.07795630e-03, 1.07795630e-03, 1.06191425e-03, 1.03054282e-03,
       9.85214808e-04, 9.27863550e-04, 8.60846255e-04, 7.86783730e-04,
       7.08391664e-04, 6.28318446e-04, 5.49002692e-04, 4.72560518e-04,
       4.00708624e-04, 3.34725070e-04, 2.75445758e-04, 2.23291521e-04,
       1.78318611e-04, 1.40284409e-04, 1.08720249e-04, 8.30041425e-05,
       6.24277081e-05, 4.62533626e-05, 3.37596182e-05, 2.42739268e-05,
       1.71937594e-05, 1.19974776e-05])

```

The difference of normalizations on a scale of 3 sigma for Gaussian is noticeable despite of the fact that 
99.7% of probability mass lies in this region. 

Here is an example of a model defined in RooFit python interface which allows the creation of bindings between Python and C++ in automatic way.

```python
import ROOT
 
# Declare variables x,mean,sigma with associated name, title, initial
# value and allowed range
x = ROOT.RooRealVar("x", "x", -10, 10)
mean = ROOT.RooRealVar("mean", "mean of gaussian", 1, -10, 10)
sigma = ROOT.RooRealVar("sigma", "width of gaussian", 1, 0.1, 10)
 
# Build gaussian pdf in terms of x,mean and sigma
gauss = ROOT.RooGaussian("gauss", "gaussian PDF", x, mean, sigma)
 
# Generate events
data = gauss.generate({x}, 10000)  # ROOT.RooDataSet
 
# Make a plot frame in x and draw both the
# data and the pdf in the frame
xframe = x.frame(Title="Gaussian pdf with data")  # RooPlot
data.plotOn(xframe)
gauss.plotOn(xframe)

# Fit pdf to data
gauss.fitTo(data, PrintLevel=-1)
 
# Draw all frames on a canvas
c = ROOT.TCanvas("basics", "basics", 800, 400)
ROOT.gPad.SetLeftMargin(0.15)
xframe.GetYaxis().SetTitleOffset(1.6)
xframe.Draw()

# Save plot into the file
c.SaveAs("basics.png")
```

![](./basics.png)

This python interface requires multiline code to create variables, model parameters, PDF and make actions for these objects. 
roofit-functional allows to significantly shorten the code which makes similar actions.  

Let us rewrite the code shown above in the roofit-functional manner. 

```python
import roofit_functional as rff

gauss = rff.RooFitFunction('Gauss', {'x' : [-10,10]}, 'Gaussian', {'mean' : [1,-10,10], 'sigma' : [1,0.1,10]})
data = rff.RooFitData("data","unbinned",(gauss,10000),gauss.get_x())
rff.RooFitMaker(data,gauss,"NLL")
p = rff.RooFitPlot(data,gauss,"x","Gaussian pdf with data")
p.make_plot(filename="basics",pdf_format=False)
```

roofit_functional has class `RooFitData` which converts various tabular data formats (numpy, pandas, ROOT histogram, RDataFrame, ASCII file and etc.) to the 
internal data container (binned or unbinned) and could generate new data obeyed fitted distribution of input data. It also has function `digit_function` which 
converts fitted probability density of data to numpy array and supports rectangular subrange of data sample.

We could easily create the pull plot in addition to the basic plot in one-line code: `p.make_pullplot()`

![](./pull.png)


All PDFs are constructed on the basis of step-to-step procedure in the RooFit framework. 
The first step is associated with elementary PDFs, which are hard-coded. 

The full list of available elementary PDFs in roofit_functional is as follows (to be updated):

- CrystalBall
  
- Uniform
  
- BifurGauss
  
- BreitWigner
  
- Gaussian
  
- Voigtian
  
- Novosibirsk
  
- Johnson

The possibility to include any custom PDF is put in TODO list. 
 
Besides PDF function, an ordinary function (not normalized in the range of its arguments) is also supported. 

```python
import roofit_functional as rff
polynomial_function = rff.RooFitVar({'x' : [-1,1]}, 'p1*x+p0', {'p0' : [0.1,0,1], 'p1' : [0.05,-0.1,0.1]}, "poly")
# The other way to define the same polynomial function
same_polynomial_function = rff.RooFitVar({'x' : [-1,1]}, 'poly', {'p0' : [0.1,0,1], 'p1' : [0.05,-0.1,0.1]}, "poly_same")
```

Structure of the elementary PDFs could be sequentially complicated via four base actions: summation, multiplication, convolution and composition.
(for more description see [RooFit manual](https://root.cern.ch/download/doc/RooFit_Users_Manual_2.91-33.pdf)).

Let us consider actions for PDF functions in a more detail:

1. Summation of two or more PDFs.

   ```python
   sum_of_pdfs = pdf1.get_add(pdf2,{'frac': [0.5,0.,1.]})
   ```

   Fraction of the pdf2 to the pdf1 is important to achieve the normalization of the `sum_of_pdfs` over initially defined region. 

3. Convolution of two PDFs.

   ```python
   conv_of_pdfs = pdf1.get_convolution(pdf2)
   ```

   For now only convolution of functions with the same variables is implemented and
   numeric convolution with Fourier transforms is supported. 
   Normalization of the convolution product is required as it is not generally normalized itself but
   the correct normalization is achieved numerically inside the code. 

5. Composition of PDF and ordinary function by some parameter of the PDF.

   ```python
   comp_of_pdf = pdf.get_composition({'p' : ordinary_function})
   ```

   We need to choose some parameter of the PDF 'p', where the composition is done: $\rm{PDF}(x,f(y)) = \rm{composition}(PDF(x,p), f(y))$.
   Composition replaces the constant PDF parameter with functional dependence of the parameter.
   This is a way to compose a conditional PDF(x|y) which differs from the ordinary PDF(x,y) by normalization.
   Normalization of PDF(x,y) is $\int\rm{PDF}(x,y) dx dy = 1$ whereas for conditional PDF(x|y):
   $\int\rm{PDF}(x|y) dx = 1$  for each value of y. Conditional PDF describes correlated random variables.

7. Multiplication of two or more PDFs.

   ```python
   pdf1 * pdf2
   ```

   Product of the PDFs is automatically normalized for both,
   ordinary and conditional PDFs. Operator `*` works in the same manner for both PDF types.

   Here we demonstrate roofit-functional in the following demo example.

   ```python
    # x-dim PDF as sum of two PDFs
    x_cb =    RooFitFunction('CrystalBall',
                             {'x' : [-.15,.15]},
                             'CrystalBall',
                             {'x0CB' : 0, 'sigmacb' : [0.02,0.01,0.03], 'alphaL' : 0.1, 'nL' : 1, 'alphaR' : 0.1, 'nR' : 1})
    x_Gauss = RooFitFunction('Gauss',
                             {'x' : x_cb},
                             'Gaussian' ,
                             {'mean' : 0, 'sigma': [0.05, 0.03, 0.07]})
    x_pdf = x_cb.get_add(x_Gauss,{'frac': [0.3,0.1,0.9]})

    # y-dim PDF as convolution of two PDFs
    y_bw = RooFitFunction('BreitWigner', {'y': [0.74,0.87]}, 'BreitWigner', {'BWmean' : 0.783, 'BWidth' : 0.0085})
    y_Gauss = RooFitFunction('MGauss', {'all' : y_bw}, 'Gaussian', {'ymean' : 0, 'ysigma': [0.007,0.001,0.015]})
    y_pdf  = y_bw.get_convolution(y_Gauss,"y_pdf")

    # (x-y) uncorr. PDF product
    product = x_pdf * y_pdf

    # Toy data generation
    binned_data = RooFitData("2D-binned-data","binned",(product,300000),product.get_x(),bins=[50,50],seed=1234)

    # PDF product fit to data 
    r = RooFitMaker(binned_data,product,"NLL")
    r.dump_to_file()

    # Plot x-projection for y-slice (0.76-0.80)
    p = RooFitPlot(binned_data,product,"x","1-d x projection in y slice (0.76, 0.80)",Slice={'mom' : (0.76,0.80)})
    p.set_paramOn()
    p.make_pullplot()
    p.make_2d_plot()
   ```

   

   






