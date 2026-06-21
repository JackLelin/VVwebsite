# VVwebsite: Ionogram Inversion Dashboard

This is a web application built with Plotly Dash to visualize the different stages of VIPIR ionogram inversion.

## Features

- **Gallery View:** A main entrance showcasing inversion result.
- **Detailed Dashboard View:** Interactive plots showing original ionograms, segmented masks, GMM fits, reconstructed O/X traces, and inversion results.

## Data Setup

The `assets` folder currently contains all inversion for Jan 14 2016. To use the dashboard with the data of other days downloaded from the databank, place the actual `.npz` files into the `assets/Inversion_result_npz/` directory.

## Requirements

The application requires the packages listed in `requirements.txt`. Install them using:
```bash
pip install -r requirements.txt
```

## How to Run Locally

To test the application locally without an Apache WSGI server, run the main application file:
```bash
python main.py
```

Then, open your web browser and navigate to:
[`http://127.0.0.1:8050/vipir_inversion/`](http://127.0.0.1:8050/vipir_inversion/)

To view the detailed plots, simply click on the plot you are interested in from the gallery view.

## Deployment on Server

The application can be deployed on a server via Apache WSGI using `dashboard.wsgi`.
