# roofit_functional
roofit-functional is a python wrapper (with extended functionality) for [RooFit framework](https://root.cern/manual/roofit/) 
which models the expected distribution of events in data analysis based on 
maximum-likelihood (ML) method. The data sample could be multi-dimensional, and has one or more measured (and correlated) observables associated with it.
It was initially created for elementary particle physics but it has universal application for tabular data of arbitrary nature.

roofit-functional is designed to integrate features from RooFit with C++ interface and python-native packages analyzing tabular data 
(numpy, scipy.stats, pandas, matplotlib, seaborn, iminuit, scikit-learn and etc.) in one place.

roofit-functional has class `RooFitData` which converts various tabular data formats (numpy, pandas, ROOT histogram, RDataFrame, ASCII file and etc.) to the 
internal data container (binned or unbinned) and could generate new data obeyed fitted distribution of input data. It also has function `digit_function` which 
converts fitted probability density of data to numpy array and supports rectangular subrange of data sample. 


# Description
RooFit has been initially written in C++. It implements classes that represents variables, probability density functions (PDFs) and operators to compose higher level functions. 
All classes are instrumented to be fully functional: fitting, plotting and toy event generation works the same way for every PDF regardless of its complexity. 
Some important parts of the underlying functionality are delegated to standard [ROOT library](https://root.cern/) and [MINUIT optimization tool](https://root.cern.ch/download/minuit.pdf)

RooFit uses PDF normalization relative to the user-defined range of variables. 

```
import numpy as np
import roofit_functional as rff
std_gauss = rff.RooFitFunction('Gauss',{'x' : [-3,3]}, 'Gaussian', {'mean' : [0], 'sigma': [1]})
data = rff.RooFitData("test","unbinned",np.linspace(-3,3),std_gauss.get_x())
rff_pdf = rff.digit_function(std_gauss,data)[1]
```

It differs from `scipy.stats` where full space normalization is used. 

```
import numpy as np 
from scipy import stats
xs = np.linspace(-3,3)
pdf = stats.norm(0, 1).pdf(xs)
```

`rff_pdf - pdf` results to 

```
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

```
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
roofit-functional allows to significantly shorten the code which makes similar actions but has flexible structure. 

Let us rewrite the code shown above in the roofit-functional manner. 

```
import roofit_functional as rff

gauss = rff.RooFitFunction('Gauss', {'x' : [-10,10]}, 'Gaussian', {'mean' : [1,-10,10], 'sigma' : [1,0.1,10]})
data = rff.RooFitData("data","unbinned",(gauss,10000),gauss.get_x())
rff.RooFitMaker(data,gauss,"NLL")
p = rff.RooFitPlot(data,gauss,"x","Gaussian pdf with data")
p.make_plot(filename="basics",pdf_format=False)
```

We could easily create the pull plot in addition to the basic plot in one-line code: `p.make_pullplot()`

![](./pull.png)


All PDFs are constructed on the basis of step-to-step procedure in the RooFit framework. 
The first step is associated with elementary PDFs, which are hard-coded. 

The full list of available elementary PDFs in roofit-functional is as follows (to be updated):

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

```
import roofit_functional as rff
polynomial_function = rff.RooFitVar({'x' : [-1,1]}, 'p1*x+p0', {'p0' : [0.1,0,1], 'p1' : [0.05,-0.1,0.1]}, "poly")
# The other way to define the same polynomial function
same_polynomial_function = rff.RooFitVar({'x' : [-1,1]}, 'poly', {'p0' : [0.1,0,1], 'p1' : [0.05,-0.1,0.1]}, "poly_same")
```

Structure of the elementary PDFs could be sequentially complicated via four base actions: summation, multiplication, convolution and composition.
(for more description see [RooFit manual](https://root.cern.ch/download/doc/RooFit_Users_Manual_2.91-33.pdf)).

Let us consider actions for PDF functions in a more detail:

1. Summation of two or more PDFs.

   `sum_of_pdfs = pdf1.get_add(pdf2,{'frac': [0.5,0.,1.]})`

   Fraction of the pdf2 to the pdf1 is important to achieve the normalization of the `sum_of_pdfs` over initially defined region. 

2. Convolution of two PDFs.

   `conv_of_pdfs = pdf1.get_convolution(pdf2)`

   For now only convolution of functions with the same variables is implemented and
   numeric convolution with Fourier transforms is supported. 
   Normalization of the convolution product is required as it is not generally normalized itself but
   the correct normalization is achieved numerically inside the code. 

3. Composition of PDF and ordinary function by some parameter of the PDF.

   `comp_of_pdf = pdf.get_composition({'p' : ordinary_function})`

   We need to choose some parameter of the PDF 'p', where the composition is done: $\rm{PDF}(x,f(y)) = \rm{composition}(PDF(x,p), f(y))$.
   Composition replaces the constant PDF parameter with functional dependence of the parameter.
   This is a way to compose a conditional PDF(x|y) which differs from the ordinary PDF(x,y) by normalization.
   Normalization of PDF(x,y) is $\int\rm{PDF}(x,y) dx dy = 1$ whereas for conditional PDF(x|y):
   $\int\rm{PDF}(x|y) dx = 1$  for each value of y. Conditional PDF describes correlated random variables.

4. Multiplication of two or more PDFs.

   `pdf1 * pdf2`

   It could be done with simple operator `*`. Product of the PDFs is automatically normalized. It is true for both,
   ordinary and conditional PDFs. Operator `*` works in the same manner for both PDF types.

   Here we demonstrate roofit-functional in the following demo example.


   ```
   import roofit_functional as rff

   # 1-dim CrystalBall PDF
   de_cb = rff.RooFitFunction('CrystalBall',{'dE' : [-.15,.15]}, 'CrystalBall', {'x0CB' : [0,-0.01,0.01], 'sigmacbL': [0.03,0.001,0.05], 'sigmacbR': [0.01,0.001,0.05],
                                                                             'alphaL': [0.1,0.005,10], 'nL' : [1,0.1,20.], 'alphaR': [0.1,0.005,10], 'nR' : [1,0.1,20.]})
   de_bfGauss = rff.RooFitFunction('Gauss',{'all' : de_cb}, 'BifurGauss' , {'x0' : [0,-0.01,0.01], 'sigmaL': [0.02,0.01,0.05], 'sigmaR': [0.02,0.01,0.05]})
   de_pdf = de_cb.get_add(de_bfGauss,{'frac': [0.5,0.,1.]})

   # 1-dim convolution of Breit-Wigner and Gaussian PDFs
   mom_bw = rff.RooFitFunction('BreitWigner', {'mom': [0.74,0.87]}, 'BreitWigner', {'mean' : [0.78,0,0], 'width' : [0.0085,0,0]})
   mom_Gauss = rff.RooFitFunction('MGauss', {'all' : mom_bw}, 'Gaussian', {'mmeang' : [0,0,0], 'msigmag': [0.007,0.001,0.01]})
   mom_pdf  = mom_bw.get_convolution(mom_Gauss,"test")

   # Product of CrystalBall and convolution PDFs
   de_mom_uncorr = de_pdf * mom_pdf

   # Toy data generation
   binned_data = rff.RooFitData("test","binned",(de_mom_uncorr,10000),de_mom_uncorr.get_x(),bins=[50,50])

   # PDF product fit to data (unbinned maximum likelihood fit)
   r = rff.RooFitMaker(binned_data,de_mom_uncorr,"NLL")

   # Save fit results to the text file
   r.dump_to_file()

   # Plot 1-d projection to 'dE' variable in the 'mom' user-defined region (slice).
   # Superimpose data and fit results. Show pull plot. 
   p = rff.RooFitPlot(binned_data,de_mom_uncorr,"dE","Test plot",Slice={'mom' : (0.776,0.786)})
   p.set_paramOn()
   p.make_pullplot()
   ```

   

   






