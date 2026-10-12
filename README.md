# VVwebsite: Jicamarca VIPIR Ionogram Inversion Repository & Dashboard

A web application built with [Plotly Dash](https://dash.plotly.com/) to visualize, explore, and analyze the different stages of Vertical Incidence Pulsed Ionospheric Radar (VIPIR) ionogram inversion and electron density profile reconstruction, compared against Jicamarca Radio Observatory Incoherent Scatter Radar (ISR) measurements.

## Features

- **Gallery View:** A main entrance showcasing inversion result.
  - **Multi-Year & Day Browsing:** Dropdown selectors dynamically populate available years and days (Day of Year / DOY) directly from the `assets/` directory.
  - **UT / Local Time Range Filtering:** Dual-handle slider to filter ionograms by observation hour (default range: 06:00–19:00 LT / 11:00–24:00 UT) to quickly isolate time windows of interest.
- **Detailed Dashboard View:** Interactive plots showing original ionograms, segmented masks, GMM fits, reconstructed O/X traces, and inversion results.
  - **Interactive Subplot Toggles:** Dropdown selector to show or hide panels on demand.
  - **Zoom, Pan & Axis Controls:** Coordinated pan/zoom across all subplots, one-click reset, and dynamic plot width/height sliders.
  - **Cross-Section Analysis (Column Inspector):** Click any pixel coordinate in the 2D ionograms to inspect the 1D power profile and O/X GMM Gaussian curve fits for that specific sounding frequency.

## Data Setup & Directory Structure
The application dynamically scans and detects folders matching `assets/<YEAR>/<DOY>/`. Inside each day folder, two subdirectories are required:

1. `Preview_figures/`: Contains the preview `.png` image files used for gallery display.
2. `Inversion_result_npz/`: Contains the corresponding `.npz` numerical inversion results used by the detailed dashboard.

```text
VVwebsite/
├── assets/
│   ├── responsive.css
│   ├── toolbartopleft.css
│   └── <YEAR>/                          # e.g., 2016 (4-digit year)
│       ├── <DOY>/                      # e.g., 014 (3-digit Day of Year)
│       │   ├── Preview_figures/        # Preview images for the gallery
│       │   │   ├── JM91J_2016014131404.png
│       │   │   ├── JM91J_2016014131423.png
│       │   │   └── ...
│       │   └── Inversion_result_npz/   # Inversion data for the dashboard
│       │       ├── JM91J_2016014131404.npz
│       │       ├── JM91J_2016014131423.npz
│       │       └── ...
│       ├── 015/
│       │   ├── Preview_figures/
│       │   └── Inversion_result_npz/
│       └── ...
...
```

### Adding Data for Other Days or Years

Follow these steps when adding data downloaded from the databank or inversion pipeline:

1. **Download Daily Archives from Databank:**
   Download the day archive (e.g., `015.zip`) or individual processed files for the desired observation date.

2. **Extract into the Year and Day Directory:**
   Ensure the destination directory follows the `assets/<YEAR>/<DOY>/` naming convention (4-digit year, 3-digit DOY). Extract the archive so that `Preview_figures/` and `Inversion_result_npz/` sit directly inside the day folder:
   ```text
   assets/2016/015/
   ├── Preview_figures/
   │   ├── JM91J_2016015110000.png
   │   └── ...
   └── Inversion_result_npz/
       ├── JM91J_2016015110000.npz
       └── ...
   ```

## Requirements & Installation

The application requires the packages listed in `requirements.txt`. Install them using:
```bash
pip install -r requirements.txt
```

Core dependencies:
- `dash`
- `plotly`
- `numpy`

## How to Run Locally

To test the application locally without an Apache WSGI server, run the main application file:
```bash
python main.py
```

Then open your web browser and navigate to:
[`http://127.0.0.1:8050/vipir_inversion/`](http://127.0.0.1:8050/vipir_inversion/)
To view the detailed plots from the gallery view, simply click on any plot card to open the fullscreen modal, or click the filename link below the plot to open the dashboard in a new tab.

## Deployment on Server

The application is configured for deployment on an Apache server via `mod_wsgi` using `dashboard.wsgi`:

1. In `dashboard.wsgi`, ensure `sys.path.insert(0, ...)` points to the absolute directory where `main.py` is hosted.
2. In Apache configuration, map the WSGI script alias:
   ```apache
   WSGIScriptAlias /vipir_inversion /path/to/VVwebsite/dashboard.wsgi
   ```

