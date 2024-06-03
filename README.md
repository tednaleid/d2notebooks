# Setup/Installation

I'm using VSCode's python and jupyter plugins to run the notebook: 

* https://marketplace.visualstudio.com/items?itemName=ms-python.python
* https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter


## Install pyenv-virtualenv

I use [pyenv](https://github.com/pyenv/pyenv) and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) for managing python and installing virtual environments.  On the Mac, they can be installed with homebrew using:

```
brew update
brew install pyenv pyenv-virtualenv
```

and you can add this to your `.zshrc` to get it to automatically load the shims in your terminal with:

```
if command -v pyenv >/dev/null 2>&1; then
  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init -)"
  eval "$(pyenv virtualenv-init -)"
else
  echo "missing pyenv, install with:"
  echo "brew install pyenv"
  echo "pyenv install 3.12.2"
fi
```

## Create a Python Envirnoment and Install Dependencies

Then run `./mkenv.sh` from the command-line to install the version of Python
defined in .python-version, create the virtual environment named in that file,
and install the Python dependencies needed by this project using pip.

Alternatively, you'll learn a bit more about how pyenv works if you follow the
alternative instructions below:

### Alternative (manual) Instructions

Install python and create a new virtual environment for this notebook with:

```
pyenv install 3.12.2

# make it the global python if desired:
pyenv global 3.12.2

# create the virtual environment used in .python-version:
pyenv virtualenv 3.12.2 d2notebooks-3.12.2
```

Now, when you're in this directory in your shell, you should see this as the active virtualenv:

```
which python
/Users/<your user>/.pyenv/shims/python

python -V
Python 3.12.2

pyenv versions
  system
  3.12.2
  3.12.2/envs/d2notebooks-3.12.2
* d2notebooks-3.12.2 --> /Users/<your user>/.pyenv/versions/3.12.2/envs/d2notebooks-3.12.2 (set by /Users/<your user>/<path to>/d2notebooks/.python-version)
```

Python (pip) typically stores dependencies in `requirements.txt` (or other modern replacements), install them with:

```
pip install -r requirements.txt
```

## Choose the Python kernel in VSCode

When you run the first python cell, VSCode will prompt you for the kernel to use.  You should be able to pick the `d2notebooks-3.12.2` kernel.

## Notebooks

- d2profile.ipynb - this downloads your account profile from bungie.net.  This should be run first to download files to the `data` directory.
- d2armor.ipynb - this is the armor analysis notebook.  It assumes that d2profile.ipynb has been run successfully first.
- d2utils.ipynb - an optional notebook that can download manifest files from bungie.net for grep/browse capability.