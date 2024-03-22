#!/bin/sh --

python3 -m pip install --upgrade build
python3 -m build
#python3 -m pip install --upgrade twine
#python3 -m twine upload --repository testpypi --skip-existing dist/*
#python3 -m twine upload --skip-existing dist/*
