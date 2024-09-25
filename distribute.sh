#!/bin/sh --

python -m pip install --upgrade build
python -m build
#python -m pip install --upgrade twine
#python -m twine upload --repository testpypi --skip-existing dist/*
#python -m twine upload --skip-existing dist/*
