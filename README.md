# Xcompact3d Toolbox

![Build Status](https://github.com/fschuch/xcompact3d_toolbox/workflows/Python%20package/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/xcompact3d-toolbox/badge/?version=latest)](https://xcompact3d-toolbox.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/xcompact3d-toolbox.svg)](https://badge.fury.io/py/xcompact3d-toolbox)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

It is a Python package designed to handle the pre and postprocessing of
the high-order Navier-Stokes solver [XCompact3d](https://github.com/xcompact3d/Incompact3d). It aims to help users and
code developers to build case-specific solutions with a set of tools and
automated processes.

The physical and computational parameters are built on top of [traitlets](https://traitlets.readthedocs.io/en/stable/index.html),
a framework that lets Python classes have attributes with type checking, dynamically calculated default values, and ‘on change’ callbacks.
In addition to [ipywidgets](https://ipywidgets.readthedocs.io/en/latest/) for an user friendly interface.

Data structure is provided by [xarray](http://xarray.pydata.org/en/stable/) (see [Why xarray?](http://xarray.pydata.org/en/stable/why-xarray.html)), that introduces labels in the form of dimensions, coordinates and attributes on top of raw [NumPy](https://numpy.org/)-like arrays, which allows for a more intuitive, more concise, and less error-prone developer experience. It integrates tightly with [dask](https://dask.org/) for parallel computing and [hvplot](https://hvplot.holoviz.org/user_guide/Gridded_Data.html) for interactive data visualization.

Finally, Xcompact3d Toolbox is fully integrated with the new *Sandbox Flow Configuration*.
The idea is to easily provide everything that XCompact3d needs from a [Jupyter Notebook](https://jupyter.org/), like initial conditions, solid geometry, boundary conditions, and the parameters ([see examples](https://xcompact3d-toolbox.readthedocs.io/en/latest/tutorial.html#sandbox-examples)).
It makes life easier for beginners, that can run any new flow configuration without worrying about Fortran and [2decomp](http://www.2decomp.org/).
For developers, it works as a rapid prototyping tool, to test concepts and then compare results to validate any future Fortran implementation.

## Examples

* Importing the package:

   ```python
   import xcompact3d_toolbox as x3d
   ```

* Loading the parameters file (both `.i3d` and `.prm` are supported, see [#7](https://github.com/fschuch/xcompact3d_toolbox/issues/7)) from the disc:

   ```python
   prm = x3d.Parameters(loadfile="input.i3d")
   prm = x3d.Parameters(loadfile="incompact3d.prm")
   ```

* Specifying how the binary fields from your simulations are named, for instance:

   * If the simulated fields are named like `ux-000.bin`:

      ```python
      prm.dataset.filename_properties.set(
         separator = "-",
         file_extension = ".bin",
         number_of_digits = 3
      )
      ```

   * If the simulated fields are named like `ux0000`:

      ```python
      prm.dataset.filename_properties.set(
         separator = "",
         file_extension = "",
         number_of_digits = 4
      )
      ```

* There are many ways to load the arrays produced by your numerical simulation, so you can choose what best suits your post-processing application.
  All arrays are wrapped into [xarray](http://xarray.pydata.org/en/stable/) objects, with many useful methods for indexing, comparisons, reshaping and reorganizing, computations and plotting.
  See the examples:

   * Load one array from the disc:

      ```python
      ux = prm.dataset.load_array("ux-0000.bin")
      ```
   
   * Load the entire time series for a given variable:

      ```python
      ux = prm.dataset["ux"]
      ```
   
   * Load all variables from a given snapshot:

      ```python
      snapshot = prm.dataset[10]
      ```
   
   * Loop through all snapshots, loading them one by one:

      ```python
      for ds in prm.dataset:
         # compute something
         vort = ds.uy.x3d.first_derivative("x") - ds.ux.x3d.first_derivative("y")
         # write the results to the disc
         prm.dataset.write(data = vort, file_prefix = "w3")
      ```
   
   * Or simply load all snapshots at once (if you have enough memory):

      ```python
      ds = prm.dataset[:]
      ```
   
   * It is possible to produce a new xdmf file, so all data can be visualized on any external tool:

      ```python
      prm.dataset.write_xdmf()
      ```


* User interface for the parameters with IPywidgets:

   ```python
   prm = x3d.ParametersGui()
   prm
   ```

   ![An animation showing the graphical user interface in action](https://www.fschuch.com/en/slides/2021-x3d-dev-meeting/Output.gif)



## Installation

It is possible to install using pip:

```bash
pip install xcompact3d-toolbox
```

To install from source, clone de repository:

```bash
git clone https://github.com/fschuch/xcompact3d_toolbox.git
```

And then install it interactively with pip:

```bash
cd xcompact3d_toolbox
pip install -e .
```

Now, any change you make at the source code will be available at your local installation, with no need to reinstall the package every time.

## Useful links

* [Documentation](https://xcompact3d-toolbox.readthedocs.io/);
* [Suggestions for new features and bug report](https://github.com/fschuch/xcompact3d_toolbox/issues);
* [See what is coming next (Project page)](https://github.com/fschuch/xcompact3d_toolbox/projects/1);
* [Xcompact3d's repository](https://github.com/xcompact3d/Incompact3d);
* [My fork from Xcompact3d's repository](https://github.com/fschuch/Xcompact3d/);

## Try it Online

[![badge](https://img.shields.io/badge/launch-Tutorial-579ACA.svg?logo=data:image/png;base64,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)](https://mybinder.org/v2/gh/fschuch/xcompact3d_toolbox/master?urlpath=lab/tree/docs/tutorial)
[![badge](https://img.shields.io/badge/launch-Sandbox%20examples-579ACA.svg?logo=data:image/png;base64,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)](https://mybinder.org/v2/gh/fschuch/xcompact3d_toolbox/master?urlpath=lab/tree/docs/examples)

Click on any link above to launch [Binder](https://mybinder.org/) and interact with our notebooks in a live environment!

## Copyright and License

All content is under [GPL-3.0 License](https://github.com/fschuch/xcompact3d_toolbox/blob/master/LICENSE).
