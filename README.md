# Example script for working with cardioDI data export

## Getting Started

We recommend that you use `poetry` to manage your dependencies for this project. You can find instructions for installing `poetry` [here](https://python-poetry.org/docs/). Once you have installed `poetry`, you can install all dependencies by running `poetry install` from within this directory.

## Using the conversion script

This script is an example of how to work with the cardioDI data export to create a wide data format (one row per encounter, all variables expanded as columns). To run the script, run

```
poetry run python convert.py --input_file=<path to your data export> --output_file=<name of the csv you want exported>
```

or

```
poetry shell
python convert.py --input_file=<path to your data export> --output_file=<name of the csv you want exported>
deactivate
```
