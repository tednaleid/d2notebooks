#!/bin/sh

virtualenv=$(cat .python-version)
python_version=$(echo "$virtualenv" | awk -F '-' '{print $NF}')
if command -v pyenv-virtualenv >/dev/null 2>&1; then
  if pyenv versions | grep -q $python_version; then
    echo "Python version $python_version is already installed."
  else
    pyenv install $python_version && "Installed python $python_version"
  fi
  if pyenv virtualenvs | grep -q $virtualenv; then
    echo "Python virtualenv $virtualenv is already installed."
  else
    pyenv virtualenv $python_version $virtualenv && echo "Installed virtualenv $virtualenv"
  fi
else
  echo "Please install https://github.com/pyenv/pyenv-virtualenv first."
fi
pyenv activate $virtualenv
pip install -r requirements.txt
