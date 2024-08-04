#!/bin/sh

set -eo pipefail

if ! command -v pyenv-virtualenv >/dev/null 2>&1; then
  echo "Please install https://github.com/pyenv/pyenv-virtualenv first."
  exit 1
fi

virtualenv="$(cat .python-version)"
python_version="$(echo "$virtualenv" | awk -F '-' '{print $NF}')"


if ! pyenv versions | grep "$python_version" >/dev/null; then
  pyenv install $python_version && echo "Installed python $python_version" || exit 1
else
  echo "Python version $python_version is already installed."
fi

if pyenv virtualenvs | grep -q " $virtualenv"; then
  echo "Python virtualenv $virtualenv is already installed."
else
  pyenv virtualenv $python_version $virtualenv && echo "Installed virtualenv $virtualenv" || exit 1
fi

if pyenv virtualenvs | grep -q "* $virtualenv"; then
  echo "Python virtualenv $virtualenv is already activated."
else
  pyenv activate $virtualenv || exit 1
fi

echo "Upgrading requirements in virtualenv $virtualenv:"
pip install -Ur requirements.txt || exit 1

pre-commit install || exit 1

echo ""
echo "Done! Please restart your IDE / notebook to make changes take effect."
