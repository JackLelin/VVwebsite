import os
from dash import Dash, html, dcc, Input, Output, State, no_update, callback, clientside_callback, Patch, ctx
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import urllib.parse
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

consolidated_dir = os.path.join(BASE_DIR, "assets/Inversion_result_npz/") # directory where npz files are stored

# --- Helper function stub ---
# You used this in matplotlib but did not define it! I provided a fallback so it doesn't crash.
def filter_out_noise_peaks(img, freqs, idx, mu, std, A):
    YY,XX = np.nonzero(img)

    x_filtered = []
    mu_filtered = []
    std_filtered = []
    A_filtered = []
    for irow in range(freqs.shape[0]):
        num_of_peaks = np.sum((idx == irow))
        ii = 0
        if num_of_peaks == 1:
            x_filtered += [irow]
            ii = 0
            # y_median += [(mu[idx == irow])[0]]
        elif num_of_peaks > 1:   
            m = np.median(YY[(XX==irow) | (XX==(irow-1)) | (XX==(irow+1))])
            x_filtered += [irow]
            ii = np.argmin(np.abs(mu[idx == irow] - m))
            # y_median += [(mu[idx == irow])[np.argmin(np.abs(mu[idx == irow] - m))]]
        else:
            continue
        mu_filtered += [(mu[idx == irow])[ii]]
        std_filtered += [(std[idx == irow])[ii]]
        A_filtered += [(A[idx == irow])[ii]]
    return np.array(x_filtered), np.array(mu_filtered), np.array(std_filtered), np.array(A_filtered)

# --- 3. Plot Functions & Config ---
# Each plot function takes (fig, data, col_idx, legend_name)
# and adds its traces to the subplot at the given column.
# Extract freqs, hts, intensity, etc. from `data` inside your function.

def plot_original_ionogram(fig, data, col_idx, legend_name):
    """(a) Original Ionogram — jet colorscale heatmap."""
    freqs = data['vipir_freqs']
    hts = data['vipir_hts']
    intensity = 10 * np.log10(data['vipir_original'] + 1)
    # Position colorbar at the right edge of this subplot's domain
    xaxis_key = f'xaxis{col_idx}'
    domain_end = fig.layout[xaxis_key].domain[1]
    fig.add_trace(
        go.Heatmap(
            z=intensity, x=freqs, y=hts,
            colorscale='Jet', zmin=10, zmax=70,
            colorbar=dict(thickness=10, x=domain_end + 0.01, len=0.9),
            name='Original', showlegend=False
        ),
        row=1, col=col_idx
    )

def plot_inversion_result(fig, data, col_idx, legend_name):
    """(b) Inversion Result — grayscale background + inversion overlay traces."""
    freqs = data['vipir_freqs']
    hts = data['vipir_hts']
    intensity = 10 * np.log10(data['vipir_original'] + 1)
    fig.add_trace(
        go.Heatmap(
            z=intensity, x=freqs, y=hts,
            colorscale='Greys', reversescale=True, zmin=10, zmax=70,
            showscale=False,
            name='Background', showlegend=False
        ),
        row=1, col=col_idx
    )
    fps = data['vipir_inversion_fps']
    Z = data['vipir_inversion_z_hts']
    x_vals = data['vipir_inversion_all_xvals'][-1]
    z = data['vipir_inversion_z_node']
    fvsO = data['vipir_inversion_fvsO']
    vhsO = data['vipir_inversion_vhsO']
    fvsX = data['vipir_inversion_fvsX']
    vhsX = data['vipir_inversion_vhsX']
    
    fig.add_trace(go.Scattergl(x=fps, y=Z, mode='lines', line=dict(color='darkgreen'), name='fp profile', legend=legend_name), row=1, col=col_idx)
    fig.add_trace(go.Scattergl(x=x_vals, y=z, mode='markers', marker=dict(color='green', size=6), name='fp spline node', legend=legend_name), row=1, col=col_idx)
    fig.add_trace(go.Scattergl(x=fvsO, y=vhsO, mode='lines', line=dict(color='red'), name='O-trace hv', legend=legend_name), row=1, col=col_idx)
    fig.add_trace(go.Scattergl(x=fvsX, y=vhsX, mode='lines', line=dict(color='blue'), name='X-trace hv', legend=legend_name), row=1, col=col_idx)

    f_idx_o = data['filtered_idx_o']
    f_idx_x = data['filtered_idx_x']
    f_mu_o = data['filtered_mu_o']
    f_mu_x = data['filtered_mu_x']

    idx_x_ints = np.round(f_idx_x).astype(int)
    mu_x_ints  = np.round(f_mu_x).astype(int)
    fig.add_trace(go.Scattergl(x=freqs[idx_x_ints], y=hts[mu_x_ints], mode='markers', marker=dict(symbol='x-thin', size=7, line=dict(width=1.5, color='blue')), name='X-mode peak', legend=legend_name), row=1, col=col_idx)
    
    idx_o_ints = np.round(f_idx_o).astype(int)
    mu_o_ints  = np.round(f_mu_o).astype(int)
    fig.add_trace(go.Scattergl(x=freqs[idx_o_ints], y=hts[mu_o_ints], mode='markers', marker=dict(symbol='circle-open', color='red', size=7, line=dict(width=1.5, color='red')), name='O-mode peak', legend=legend_name), row=1, col=col_idx)


def plot_thinned_traces(fig, data, col_idx, legend_name):
    """(c) Thinned Traces — grayscale background + GMM scatter overlay."""
    freqs = data['vipir_freqs']
    hts = data['vipir_hts']
    intensity = 10 * np.log10(data['vipir_original'] + 1)
    fig.add_trace(
        go.Heatmap(
            z=intensity, x=freqs, y=hts,
            colorscale='Greys', reversescale=True, zmin=10, zmax=70,
            showscale=False,
            name='Background', showlegend=False
        ),
        row=1, col=col_idx
    )
    f_idx_x = data['filtered_idx_x']
    f_mu_x = data['filtered_mu_x']
    f_idx_o = data['filtered_idx_o']
    f_mu_o = data['filtered_mu_o']

    idx_x_ints = np.round(f_idx_x).astype(int)
    mu_x_ints  = np.round(f_mu_x).astype(int)
    fig.add_trace(go.Scattergl(x=freqs[idx_x_ints], y=hts[mu_x_ints], mode='markers', marker=dict(symbol='x', color='blue', size=6), name='X-mode', legend=legend_name), row=1, col=col_idx)
    
    idx_o_ints = np.round(f_idx_o).astype(int)
    mu_o_ints  = np.round(f_mu_o).astype(int)
    fig.add_trace(go.Scattergl(x=freqs[idx_o_ints], y=hts[mu_o_ints], mode='markers', marker=dict(symbol='x', color='red', size=6), name='O-mode', legend=legend_name), row=1, col=col_idx)

def plot_segmented_mask(fig, data, col_idx, legend_name):
    """Plotting segmented mask from T-UNet o-mode and x-mode"""
    freqs = data['vipir_freqs']
    hts   = data['vipir_hts']
    binary_ionogram = data['vipir_binary_ionogram'].astype(np.int_)
    maskO = data['vipir_DNN_imgO']
    maskX = data['vipir_DNN_imgX']
    # 1. Background heatmap
    fig.add_trace(
        go.Heatmap(
            z= binary_ionogram, x=freqs, y=hts,
            colorscale='Greys', reversescale=True, zmin=0, zmax=1,
            showscale=False, name='Background', showlegend=False, legend=legend_name
        ),
        row=1, col=col_idx
    )

    # Define custom colorscales for transparency                               
    # [0, 'rgba(r,g,b,alpha)'] -> 0 is transparent                             
    # [1, 'rgba(r,g,b,alpha)'] -> 1 is opaque                                  
    red_mask_scale = [[0, 'rgba(255,0,0,0)'], [1, 'rgba(255,0,0,1)']]          
    blue_mask_scale = [[0, 'rgba(0,0,255,0)'], [1, 'rgba(0,0,255,1)']]       
    fig.add_trace(
        go.Heatmap(
            z=maskO, x=freqs, y=hts,
            colorscale=red_mask_scale, zmin=0, zmax=1, opacity=0.9,
            showscale=False, name='O-mode', showlegend=True, legend=legend_name
        ),
        row=1, col=col_idx
    )
    fig.add_trace(
        go.Heatmap(
            z=maskX, x=freqs, y=hts,
            colorscale=blue_mask_scale, zmin=0, zmax=1, opacity=0.9,
            showscale=False, name='X-mode', showlegend=True, legend=legend_name
        ),
        row=1, col=col_idx
    )

    # Use a black-to-white colorscale so the background (z=1) is black and signal (z=0) is white
    black_bg_scale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,255,255,1)']]
    fig.add_trace(
        go.Heatmap(
            z=1-binary_ionogram, x=freqs, y=hts, opacity=0.1,
            colorscale=black_bg_scale, reversescale=True, zmin=0, zmax=1,
            showscale=False, name='Background', showlegend=False, legend=legend_name
        ),
        row=1, col=col_idx
    )

def plot_reconstructed_ionogram(fig, data, col_idx, legend_name):
    freqs = data['vipir_freqs']
    hts = data['vipir_hts']


    intensity = 10 * np.log10(data['gauss_reconstruct_o'] + data['gauss_reconstruct_x'] + 1)
    # Position colorbar at the right edge of this subplot's domain
    xaxis_key = f'xaxis{col_idx}'
    domain_end = fig.layout[xaxis_key].domain[1]
    fig.add_trace(
        go.Heatmap(
            z=intensity, x=freqs, y=hts,
            colorscale='Jet', zmin=10, zmax=70,
            colorbar=dict(thickness=10, x=domain_end + 0.01, len=0.9),
            name='Reconstructed Ionogram', showlegend=False
        ),
        row=1, col=col_idx
    )

def plot_reconstructed_X(fig, data, col_idx, legend_name):
    freqs = data['vipir_freqs']
    hts = data['vipir_hts']


    intensity = 10 * np.log10(data['gauss_reconstruct_x'] + 1)
    # Position colorbar at the right edge of this subplot's domain
    xaxis_key = f'xaxis{col_idx}'
    domain_end = fig.layout[xaxis_key].domain[1]
    fig.add_trace(
        go.Heatmap(
            z=intensity, x=freqs, y=hts,
            colorscale='Jet', zmin=10, zmax=70,
            colorbar=dict(thickness=10, x=domain_end + 0.01, len=0.9),
            name='Reconstructed Xtrace', showlegend=False
        ),
        row=1, col=col_idx
    )

def plot_reconstructed_O(fig, data, col_idx, legend_name):
    freqs = data['vipir_freqs']
    hts = data['vipir_hts']


    intensity = 10 * np.log10(data['gauss_reconstruct_o'] + 1)
    # Position colorbar at the right edge of this subplot's domain
    xaxis_key = f'xaxis{col_idx}'
    domain_end = fig.layout[xaxis_key].domain[1]
    fig.add_trace(
        go.Heatmap(
            z=intensity, x=freqs, y=hts,
            colorscale='Jet', zmin=10, zmax=70,
            colorbar=dict(thickness=10, x=domain_end + 0.01, len=0.9),
            name='Reconstructed Otrace', showlegend=False
        ),
        row=1, col=col_idx
    )

# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE: How to add a new plot panel
# ═══════════════════════════════════════════════════════════════════════════════
#
# Step 1: Define your plot function below (copy this template and modify).
# Step 2: Add an entry to PLOT_CONFIG at the bottom of this section.
#         That's it — the layout, toggles, legends, and axis sync are automatic.
#
# FUNCTION SIGNATURE:
#   def plot_my_panel(fig, data, col_idx, legend_name):
#
# PARAMETERS (all provided automatically by the main loop):
#   fig         : the make_subplots Figure — call fig.add_trace(..., row=1, col=col_idx)
#   data        : the full .z dict — access any key like data['my_key']
#                 Common keys: data['vipir_freqs'], data['vipir_hts'], data['vipir_original']
#   col_idx     : which subplot column this panel occupies (1-indexed)
#   legend_name : string like 'legend', 'legend2', etc. — pass to scatter traces
#
# RULES:
#   - Extract freqs/hts/intensity from data inside your function
#   - Heatmaps: set showlegend=False (they use colorbars, not legends)
#   - Scatter/Line traces: set legend=legend_name so they appear in this panel's legend
#   - Always use row=1, col=col_idx when adding traces
#
# ─── Example: Heatmap background + scatter overlay (like panels b, c) ────────
#
# def plot_my_overlay(fig, data, col_idx, legend_name):
#     """My custom overlay panel."""
#     freqs = data['vipir_freqs']
#     hts   = data['vipir_hts']
#     intensity = 10 * np.log10(data['vipir_original'] + 1)
#     # 1. Background heatmap
#     fig.add_trace(
#         go.Heatmap(
#             z=intensity, x=freqs, y=hts,
#             colorscale='Greys', reversescale=True, zmin=10, zmax=70,
#             showscale=False, name='Background', showlegend=False
#         ),
#         row=1, col=col_idx
#     )
#     # 2. Overlay scatter/line traces (use legend=legend_name!)
#     x_data = data['my_x_key']
#     y_data = data['my_y_key']
#     fig.add_trace(
#         go.Scattergl(
#             x=x_data, y=y_data,
#             mode='lines+markers',    # or 'lines', 'markers'
#             line=dict(color='red'),
#             marker=dict(size=5),
#             name='My Trace',
#             legend=legend_name       # <-- puts it in this panel's legend
#         ),
#         row=1, col=col_idx
#     )
#
# ═══════════════════════════════════════════════════════════════════════════════

PLOT_CONFIG = [
    {'id': 'a', 'label': 'Original Ionogram',  'plot_func': plot_original_ionogram},
    {'id': 'b', 'label': 'Inversion Result',    'plot_func': plot_inversion_result},
    # {'id': 'c', 'label': 'Thinned Traces',      'plot_func': plot_thinned_traces},
    {'id': 'd', 'label': 'Segmented Mask and Binary Ionogram',      'plot_func': plot_segmented_mask},
    {'id': 'e', 'label': 'Reconstructed Ionogram', 'plot_func': plot_reconstructed_ionogram},
    {'id': 'f', 'label': 'Reconstructed Otrace', 'plot_func': plot_reconstructed_O},
    {'id': 'g', 'label': 'Reconstructed Xtrace', 'plot_func': plot_reconstructed_X},
    # --- To add a new panel, uncomment and modify: ---
    # {'id': 'd', 'label': '(d) My New Panel',      'plot_func': plot_my_heatmap},
]

def serve_layout():
    return html.Div([
        
        # LEFT PANE (75%)
        html.Div([
            html.H2("Detailed Plots", id="dashboard-title", style={'textAlign': 'left', 'fontFamily': 'sans-serif', 'margin': '5px 0 5px 0'}),
            html.H3("This page plots the different stages of inverion.", style={'textAlign': 'left', 'fontFamily': 'sans-serif', 'color': '#333', 'margin': '0 0 15px 0'}),
            
            html.Div([
                html.Span("Select Panels to Display:", style={'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'sans-serif', 'fontSize': '16px'}),
                dcc.Checklist(
                    id='plot-toggles',
                    options=[{'label': f" {p['label']}", 'value': p['id']} for p in PLOT_CONFIG],
                    value=[p['id'] for p in PLOT_CONFIG], # Start with all panels checked
                    inline=True,
                    inputStyle={'cursor': 'pointer', 'marginRight': '5px', 'marginLeft': '10px'},
                    labelStyle={'cursor': 'pointer', 'fontSize': '16px', 'fontFamily': 'sans-serif'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'padding': '8px 15px', 'backgroundColor': '#f9f9f9', 'borderRadius': '8px', 'maxWidth': '100%', 'flexWrap': 'wrap', 'margin': '0 auto 10px auto'}),
            
            html.Div([
                html.Button('Reset Axes', id='reset-view-btn', n_clicks=0,
                    style={'padding': '6px 16px', 'fontSize': '14px', 'fontFamily': 'sans-serif',
                           'cursor': 'pointer', 'borderRadius': '6px', 'border': '1px solid #aaa',
                           'backgroundColor': '#f0f0f0', 'marginRight': '10px', 'fontWeight': 'bold'}),
                html.Button('Zoom Out', id='zoom-out-btn', n_clicks=0,
                    style={'padding': '6px 16px', 'fontSize': '14px', 'fontFamily': 'sans-serif',
                           'cursor': 'pointer', 'borderRadius': '6px', 'border': '1px solid #aaa',
                           'backgroundColor': '#e8f4f8', 'marginRight': '20px', 'fontWeight': 'bold'}),
                html.Button('Box Zoom', id='box-zoom-btn', n_clicks=0,
                    style={'padding': '6px 16px', 'fontSize': '14px', 'fontFamily': 'sans-serif',
                           'cursor': 'pointer', 'borderRadius': '6px', 'border': '2px solid #3498db',
                           'backgroundColor': '#b3e0ff', 'marginRight': '10px', 'fontWeight': 'bold'}),
                html.Button('Pan', id='pan-btn', n_clicks=0,
                    style={'padding': '6px 16px', 'fontSize': '14px', 'fontFamily': 'sans-serif',
                           'cursor': 'pointer', 'borderRadius': '6px', 'border': '1px solid #aaa',
                           'backgroundColor': '#e8f4f8', 'marginRight': '10px', 'fontWeight': 'bold'}),
                html.Span("Plot Width:", style={'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'sans-serif', 'fontSize': '16px'}),
                html.Div(
                    dcc.Slider(
                        id='plot-size-slider',
                        min=10, max=100, step=1, value=25,
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": True},
                        updatemode='mouseup'
                    ),
                    style={'flex': '1', 'minWidth': '200px'}
                ),
                html.Span("Plot Height:", style={'fontWeight': 'bold', 'marginLeft': '30px', 'marginRight': '10px', 'fontFamily': 'sans-serif', 'fontSize': '16px'}),
                html.Div(
                    dcc.Slider(
                        id='plot-height-slider',
                        min=10, max=100, step=1, value=30,
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": True},
                        updatemode='mouseup'
                    ),
                    style={'flex': '1', 'minWidth': '200px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'padding': '5px 15px', 'maxWidth': '100%', 'flexWrap': 'wrap', 'margin': '0 auto 20px auto'}),
            
            # Container for the synced ABC subplot figure
            html.Div([
                html.Div(
                    dcc.Graph(
                        id='plot-abc-graph', 
                        style={'width': '100%', 'height': '100%'},
                        config={'doubleClick': False, 'scrollZoom': False, 'modeBarButtonsToRemove': ['autoScale2d', 'lasso2d', 'select2d'], 'displayModeBar': True}
                    ), 
                    id='plot-abc-wrapper', 
                    style={'display': 'block', 'flexShrink': 0}
                ),
                ],
                id='left-plots-container',
                style={
                    'width': '100%', 
                    'display': 'flex',
                    'flexDirection': 'row', # Stack horizontally
                    'overflowX': 'auto', # Allow horizontal scrolling
                    'overflowY': 'hidden',
                    'paddingBottom': '20px'
                }
            ),
            html.Div([
                html.H4("Plot usage: Select tools at the top left corner. Click on any pixel in any plot to show the GMM fitting for the corresponding column.", style={'fontFamily': 'sans-serif', 'marginTop': '10px', 'color': '#2c3e50'}),
                html.H4("Panel Captions", style={'fontFamily': 'sans-serif', 'marginTop': '10px', 'color': '#2c3e50'}),
                html.Ul([
                html.Li([html.B("Original Ionogram: "), "VIPIR ionogram presented on a dB scale."]),
                html.Li([html.B("Inversion result: "), "Green dots and curve represent the control points for the spline and the inverted electron density (Ne) profile, respectively. The red and blue curves are the predicted O and X traces from the inverted Ne profile. The red and blue crosses are the virtual heights of reflection. The inversion process minimizes the Euclidean distance between the predicted trace and its nearest cross."]),
                html.Li([html.B("Segmented Mask: "), "The segmented masks are shown in red and blue, which are overlaid on top of the binary ionogram shown in black and white pixels. The T-UNet takes the binary ionogram and outputs the O and X masks."]),
                html.Li([html.B("Reconstructed Otrace and Xtrace: "), "The ionograms are reconstructed by fitting a Gaussian function to the returned power for each frequency and plotting the Gaussian functions."]),
            ], style={'lineHeight': '1.8', 'fontSize': '16px'})
            ], style={'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px', 'borderLeft': '4px solid #3498db', 'marginTop': '10px'})
            
        ], className="dashboard-left-pane", style={'width': '75%', 'paddingRight': '20px', 'borderRight': '3px solid #ccc', 'display': 'flex', 'flexDirection': 'column'}),
        
        # RIGHT PANE (25%)
        html.Div([
            html.H3("Detail of Selected Column", style={'textAlign': 'center', 'fontFamily': 'sans-serif', 'marginTop': '0', 'color': '#333'}),
            dcc.Graph(
                id='cross-section-plot',
                className='no-hover-legend',
                figure=make_subplots(
                    rows=3, cols=1,
                    shared_xaxes=True, shared_yaxes=False,
                    subplot_titles=["Click on the plots to see details of a column", "", ""],
                    vertical_spacing=0.1
                ),
                style={'width': '100%', 'height': '85vh'}, # Increased height
                config={'doubleClick': 'reset', 'scrollZoom': False, 'modeBarButtonsToRemove': ['autoScale2d', 'lasso2d', 'select2d'], 'displayModeBar': True}
            ),
            
            # Explanations block matching fig_abc style
            html.Div([
                html.H4("Cross-Section Plot Explanations", style={'fontFamily': 'sans-serif', 'marginTop': '10px', 'color': '#2c3e50'}),
                html.P("Plot usage: Drag the mouse horizontally to zoom in on a section of the x-axis. Zoom in, Zoom out, and Reset tools are located at the top left corner.", style={'fontFamily': 'sans-serif', 'fontSize': '14px'}),
                html.Ul([
                    html.Li([html.B("Power Profile: "), "Description of the power profile."]),
                    html.Li([html.B("O-mode GMM fit: "), "Description of the O-mode Gaussian Mixture Model fit."]),
                    html.Li([html.B("X-mode GMM fit: "), "Description of the X-mode Gaussian Mixture Model fit."])
                ], style={'lineHeight': '1.8', 'fontSize': '14px'})
            ], style={'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px', 'borderLeft': '4px solid #3498db', 'marginTop': '10px'})

        ], className="dashboard-right-pane", style={'width': '25%', 'paddingLeft': '20px', 'display': 'flex', 'flexDirection': 'column', 'gap': '20px'})
        
    ], className="dashboard-main-container", style={'display': 'flex', 'flexDirection': 'row', 'width': '100%', 'padding': '20px', 'boxSizing': 'border-box'})

# --- 4. Callbacks ---

# Callback 1: Toggle visibility & resize (Client-Side Javascript - No server roundtrip)
clientside_callback(
    '''
    function(selected_panels, width, height) {
        var abcPanels =  '''+f"{[p['id'] for p in PLOT_CONFIG]}"+''';
        var anyABC = abcPanels.some(function(p) { return selected_panels.includes(p); });
        var abcCount = abcPanels.filter(function(p) { return selected_panels.includes(p); }).length;
        
        if (anyABC) {
            return {
                'display': 'block',
                'width': (width * abcCount) + 'vw',
                'height': height + 'vw',
                'flexShrink': 0
            };
        } else {
            return {'display': 'none'};
        }
    }
    ''',
    Output('plot-abc-wrapper', 'style'),
    Input('plot-toggles', 'value'),
    Input('plot-size-slider', 'value'),
    Input('plot-height-slider', 'value')
)


# Callback 2: Load Data & Generate Plots (runs on page load, toggle change, or reset)
@callback(
    Output('plot-abc-graph', 'figure'),
    Output('dashboard-title', 'children'),
    Input('url', 'search'),
    Input('plot-toggles', 'value'),
    Input('reset-view-btn', 'n_clicks'),
    State('box-zoom-btn', 'style')
)
def generate_all_plots(search_query, selected_panels, reset_clicks, box_zoom_style):
    empty_abc = make_subplots(rows=1, cols=1).update_layout(title="No data loaded")
    
    if not search_query:
        return empty_abc, "Detailed Plots"
        
    parsed = urllib.parse.parse_qs(search_query.lstrip('?'))
    if 'image' not in parsed:
        return empty_abc, "Detailed Plots"
    
    filename = parsed['image'][0]
    np_filename = filename.replace('.png', '.npz')
    filepath = os.path.join(consolidated_dir, np_filename)

    if not os.path.exists(filepath):
        return empty_abc, f"Detailed Plots: {filename} (Data not found)"
        
    # Load data ONCE
    data = dict(np.load(filepath, allow_pickle=True))
    
    timestruct = data['vipir_vipirTimeSct']
    temp_hour = timestruct['start_hour'][0]
    temp_day = timestruct['start_day'][0]
    if temp_hour < 5:
        temp_hour = temp_hour + 24 - 5
        temp_day = temp_day - 1
    localtime = f"LT: {timestruct['start_year'][0]:4d}.{timestruct['start_month'][0]:02d}.{temp_day:02d} {temp_hour:02d}:{timestruct['start_minute'][0]:02d}:{timestruct['start_second'][0]:02d}"

    freqs = data['vipir_freqs']
    hts = data['vipir_hts']
    
    imgO = data['vipir_DNN_imgO']
    imgX = data['vipir_DNN_imgX']
    original = data['vipir_original']

    f_idx_o, f_mu_o, f_std_o, f_A_o = filter_out_noise_peaks(imgO, freqs, data['vipir_thin_freqidx_o'], data['vipir_thin_mu_o'], data['vipir_thin_std_o'], data['vipir_thin_A_o'])
    f_idx_x, f_mu_x, f_std_x, f_A_x = filter_out_noise_peaks(imgX, freqs, data['vipir_thin_freqidx_x'], data['vipir_thin_mu_x'], data['vipir_thin_std_x'], data['vipir_thin_A_x'])
    
    data['filtered_idx_o'] = f_idx_o
    data['filtered_mu_o'] = f_mu_o
    data['filtered_std_o'] = f_std_o
    data['filtered_A_o'] = f_A_o
    data['filtered_idx_x'] = f_idx_x
    data['filtered_mu_x'] = f_mu_x
    data['filtered_std_x'] = f_std_x
    data['filtered_A_x'] = f_A_x

    gauss_reconstruct_o = np.zeros_like(original)
    gauss_reconstruct_x = np.zeros_like(original)
    for i in range(len(f_idx_o)):
        gauss_reconstruct_o[:, f_idx_o[i]] += gaussian(np.arange(original.shape[0]), f_A_o[i], f_mu_o[i], f_std_o[i])
    for i in range(len(f_idx_x)):
        gauss_reconstruct_x[:, f_idx_x[i]] += gaussian(np.arange(original.shape[0]), f_A_x[i], f_mu_x[i], f_std_x[i])

    data['gauss_reconstruct_o'] = gauss_reconstruct_o
    data['gauss_reconstruct_x'] = gauss_reconstruct_x

    # --- Determine which panels are visible ---
    abc_panels = [p['id'] for p in PLOT_CONFIG if p['id'] in selected_panels]
    n_cols = len(abc_panels) if abc_panels else 1
    
    # Build column titles based on which panels are active
    label_map = {p['id']: p['label'] for p in PLOT_CONFIG}
    col_titles = [label_map[p] for p in abc_panels]
    
    if not abc_panels:
        col_titles = ["No panels selected"]
    
    # Create subplot figure with shared axes — this is the Plotly equivalent of 
    # Bokeh's shared Range1d: zoom/pan on any subplot automatically syncs all others
    fig_abc = make_subplots(
        rows=1, cols=n_cols,
        shared_xaxes=True, shared_yaxes=True,
        subplot_titles=col_titles,
        horizontal_spacing=0.03
    )
    
    # Build each panel by calling its registered plot function
    config_map = {p['id']: p for p in PLOT_CONFIG}
    legend_style = dict(yanchor="top", y=0.99, bgcolor="rgba(255,255,255,0.7)", font=dict(size=10))
    layout_update = dict(margin=dict(l=10, r=10, t=60, b=10))
    
    for col_idx, panel_id in enumerate(abc_panels, start=1):
        # Each column gets its own legend: legend, legend2, legend3, ...
        legend_name = f'legend{col_idx}'
        config_map[panel_id]['plot_func'](fig_abc, data, col_idx, legend_name)
        
        # Position this column's legend over its subplot domain
        xaxis_key = f'xaxis{col_idx}'
        domain = fig_abc.layout[xaxis_key].domain
        layout_update[legend_name] = dict(**legend_style, xanchor="left", x=domain[0] + 0.01)
    
    current_dragmode = 'zoom'
    if box_zoom_style and box_zoom_style.get('backgroundColor') != '#b3e0ff':
        current_dragmode = 'pan'
    layout_update['dragmode'] = current_dragmode

    fig_abc.update_layout(**layout_update)
    # Label axes - only first column gets y-axis label
    fig_abc.update_yaxes(title_text="Virtual Height (km)", row=1, col=1)
    for i in range(1, n_cols + 1):
        fig_abc.update_xaxes(title_text="Frequency (MHz)", row=1, col=i)
    # Link all x-axes to the first column's x-axis so zoom/pan syncs horizontally
    # (shared_xaxes only works across rows, not columns in a single-row layout)
    for i in range(2, n_cols + 1):
        fig_abc.update_xaxes(matches='x', row=1, col=i)
    # Set explicit axis limits (propagates to all subplots via shared/matched axes)
    fig_abc.update_xaxes(range=[freqs.min(), freqs.max()], autorange=False, row=1, col=1)
    fig_abc.update_yaxes(range=[hts.min(), hts.max()], autorange=False, row=1, col=1)
    return fig_abc, f"Detailed Plots: {np_filename}  |  {localtime}"

def gaussian(x, A, mu, sigma):
    return A * np.exp(-(x - mu)**2 / (2 * sigma**2))
def get_mask_intervals(col_mask):                                                                                                                                                                                              
    # Find where the value changes                                                      
    diff = np.diff(col_mask.astype(int), prepend=0, append=0)                               
    starts = (np.where(diff == 1)[0]).reshape(-1,1)                                         
    ends = (np.where(diff == -1)[0]).reshape(-1,1) - 1                                                  
    return np.hstack([starts, ends])

# Callback 3: Update the Cross-Section Plot when clicking on the ABC subplot
@callback(
    Output('cross-section-plot', 'figure'),
    Input('plot-abc-graph', 'clickData'),
    State('url', 'search'),
    prevent_initial_call=True
)
def update_cross_section(clickData, search_query):
    if not clickData or not search_query:
        return no_update
        
    parsed = urllib.parse.parse_qs(search_query.lstrip('?'))
    if 'image' not in parsed:
        return no_update
        
    filename = parsed['image'][0]
    np_filename = filename.replace('.png', '.npz')
    filepath = os.path.join(consolidated_dir, np_filename)
    
    if not os.path.exists(filepath):
        return no_update
        
    data = np.load(filepath, allow_pickle=True)
    hts = data['vipir_hts']
    freqs = data['vipir_freqs']
    org = data['vipir_original']
    maskO = data['vipir_DNN_imgO']
    maskX = data['vipir_DNN_imgX']
    # intensity = 10 * np.log10(org + 1)
    
    # In Plotly, the clicked x/y values match the coordinates we provided (freqs and hts)
    click_x = clickData['points'][0]['x'] 
    click_y = clickData['points'][0]['y'] 
    
    # Find the closest frequency index to the clicked x-coordinate (Vertical Cross-Section)
    x_idx = np.argmin(np.abs(freqs - click_x))
    y_idx = np.argmin(np.abs(hts - click_y))
    col_data = org[:, x_idx]
    
    
    row_titles = [f'Power Profile at {freqs[x_idx]:.2f} MHz', 'O-mode GMM fit', 'X-mode GMM fit']
    updated_plot= make_subplots(
        rows=3, cols=1,
        shared_xaxes=True, shared_yaxes=False,
        subplot_titles=row_titles,
        vertical_spacing=0.1
    )

    updated_plot.add_trace(
        go.Scattergl(x=np.arange(20, hts.shape[0]), y=col_data[20:], mode='lines', line=dict(color='black'), name='Power (linear)', legend='legend1'),
        row=1, col=1
    )
    updated_plot.add_trace(
        go.Scattergl(x=[y_idx], y=[org[y_idx, x_idx]], mode='markers', marker=dict(color='red', size=8), name='Clicked Point', legend='legend1'),
        row=1, col=1
    )

    updated_plot.add_trace(
        go.Scattergl(x=np.arange(20, hts.shape[0]), y=col_data[20:], mode='lines', line=dict(color='grey'), name='Power', legend='legend2'),
        row=2, col=1
    )
    updated_plot.add_trace(
        go.Bar(x=np.arange(20, hts.shape[0]), y=col_data[20:] * maskO[20:, x_idx], marker_color='grey', opacity=0.6, name='O masked power', legend='legend2'),
        row=2, col=1
    )

    updated_plot.add_trace(
        go.Scattergl(x=np.arange(20, hts.shape[0]), y=col_data[20:], mode='lines', line=dict(color='grey'), name='Power', legend='legend3'),
        row=3, col=1
    )
    updated_plot.add_trace(
        go.Bar(x=np.arange(20, hts.shape[0]), y=col_data[20:] * maskX[20:, x_idx], marker_color='grey', opacity=0.6, name='X masked power', legend='legend3'),
        row=3, col=1
    )

    idx_o = data['vipir_thin_freqidx_o']
    mu_o = data['vipir_thin_mu_o'][idx_o == x_idx]
    std_o = data['vipir_thin_std_o'][idx_o == x_idx]
    A_o = data['vipir_thin_A_o'][idx_o == x_idx]
    idx_x = data['vipir_thin_freqidx_x']
    mu_x = data['vipir_thin_mu_x'][idx_x == x_idx]
    std_x = data['vipir_thin_std_x'][idx_x == x_idx]
    A_x = data['vipir_thin_A_x'][idx_x == x_idx]

    # Find the median index (center) of the active O-mask at this frequency
    mask_indices_o = np.where(maskO[:, x_idx])[0]
    if len(mask_indices_o) > 0 and len(mu_o) > 0:
        mask_center_o = np.median(mask_indices_o)
        # Identify the component whose mu is closest to the mask center
        major_idx_o = np.argmin(np.abs(mu_o - mask_center_o))
    else:
        major_idx_o = 0 # Default fallback

    if len(mu_o) > 0:
        x_axis_o = np.linspace(mu_o.min()-10, mu_o.max()+10, 1000)
        gmm_sum_o = np.zeros_like(x_axis_o)
        
        for i in range(len(mu_o)):
            pdf = gaussian(x_axis_o, A_o[i], mu_o[i], std_o[i])
            
            # Apply styling based on whether this is the major component
            is_major = (i == major_idx_o)
            comp_color = 'red' if is_major else 'black'
            comp_width = 2 if is_major else 1
            comp_name = 'Major Component' if is_major else f'Minor Component'
            
            updated_plot.add_trace(
                go.Scattergl(x=x_axis_o, y=pdf, mode='lines', line=dict(color=comp_color, width=comp_width), name=comp_name, legend='legend2'),
                row=2, col=1
            ) 
            gmm_sum_o += pdf

        # Changed the sum trace to a dotted black line so it contrasts nicely against the grey minor components!
        updated_plot.add_trace(
            go.Scattergl(x=x_axis_o, y=gmm_sum_o, mode='lines', line=dict(color='black', width=2, dash='dot'), name=f'Sum of Components', legend='legend2'), 
            row=2, col=1
        )

    # Find the median index (center) of the active X-mask at this frequency
    mask_indices_x = np.where(maskX[:, x_idx])[0]
    if len(mask_indices_x) > 0 and len(mu_x) > 0:
        mask_center_x = np.median(mask_indices_x)
        # Identify the component whose mu is closest to the mask center
        major_idx_x = np.argmin(np.abs(mu_x - mask_center_x))
    else:
        major_idx_x = 0 # Default fallback

    # Find the median index (center) of the active O-mask at this frequency
    mask_indices_o = np.where(maskO[:, x_idx])[0]
    if len(mask_indices_o) > 0 and len(mu_o) > 0:
        mask_center_o = np.median(mask_indices_o)
        # Identify the component whose mu is closest to the mask center
        major_idx_o = np.argmin(np.abs(mu_o - mask_center_o))
    else:
        major_idx_o = 0 # Default fallback

    if len(mu_x) > 0:
        x_axis_x = np.linspace(mu_x.min()-10, mu_x.max()+10, 1000)
        gmm_sum_x = np.zeros_like(x_axis_x)
        
        for i in range(len(mu_x)):
            pdf = gaussian(x_axis_x, A_x[i], mu_x[i], std_x[i])
            
            # Apply styling based on whether this is the major component
            is_major = (i == major_idx_x)
            comp_color = 'red' if is_major else 'black'
            comp_width = 2 if is_major else 1
            comp_name = 'Major Component' if is_major else f'Minor Component'
            
            updated_plot.add_trace(
                go.Scattergl(x=x_axis_x, y=pdf, mode='lines', line=dict(color=comp_color, width=comp_width), name=comp_name, legend='legend3'),
                row=3, col=1
            ) 
            gmm_sum_x += pdf

        # Changed the sum trace to a dotted black line so it contrasts nicely against the grey minor components!
        updated_plot.add_trace(
            go.Scattergl(x=x_axis_x, y=gmm_sum_x, mode='lines', line=dict(color='black', width=2, dash='dot'), name=f'Sum of Components', legend='legend3'), 
            row=3, col=1
        )


    intervals = get_mask_intervals(maskO[:, x_idx])                                                    
    for i_interv in range(intervals.shape[0]):
        updated_plot.add_vrect(
            x0=intervals[i_interv,0], x1=intervals[i_interv,1], 
            fillcolor="LightPink", opacity=0.5, 
            layer="below", line_width=0, 
            row=1, col=1)
        
        updated_plot.add_vrect(
            x0=intervals[i_interv,0], x1=intervals[i_interv,1], 
            fillcolor="LightPink", opacity=0.5, 
            layer="below", line_width=0, 
            row=2, col=1)
    # Dummy trace to generate the legend entry for the O-mask shaded regions
    updated_plot.add_trace(
        go.Scattergl(x=[None], y=[None], mode='markers', marker=dict(color='LightPink', size=12, symbol='square'), name='O-mask', legend='legend1'),
        row=1, col=1
    )

    intervals = get_mask_intervals(maskX[:, x_idx])                                                    
    for i_interv in range(intervals.shape[0]):
        updated_plot.add_vrect(
            x0=intervals[i_interv,0], x1=intervals[i_interv,1], 
            fillcolor="LightSkyBlue", opacity=0.5, 
            layer="below", line_width=0, 
            row=1, col=1)
                
        updated_plot.add_vrect(
            x0=intervals[i_interv,0], x1=intervals[i_interv,1], 
            fillcolor="LightSkyBlue", opacity=0.5, 
            layer="below", line_width=0, 
            row=3, col=1)
        
    # Dummy trace to generate the legend entry for the X-mask shaded regions
    updated_plot.add_trace(
        go.Scattergl(x=[None], y=[None], mode='markers', marker=dict(color='LightSkyBlue', size=12, symbol='square'), name='X-mask', legend='legend1'),
        row=1, col=1
    )

    # Use horizontal orientation, smaller font, and semi-transparent background
    legend_style = dict(yanchor="top", xanchor="left", x=0.01, orientation="h", bgcolor="rgba(255,255,255,0.5)", font=dict(size=9), itemclick=False, itemdoubleclick=False)
    layout_update = dict(margin=dict(l=10, r=10, t=60, b=10), showlegend=True, 
        plot_bgcolor='white',
        paper_bgcolor='white')

    for i_row in range(1, 4):
        axis_key = 'yaxis' if i_row == 1 else f'yaxis{i_row}'
        b_domain = updated_plot.layout[axis_key].domain
        layout_update[f'legend{i_row}'] = dict(**legend_style, y=b_domain[1])
    
    updated_plot.update_layout(**layout_update)

    for i_row in range(1, 4):
        # updated_plot.update_xaxes(title_text="Height Index", row=i_row, col=1, gridcolor='lightgrey')
        updated_plot.update_yaxes(title_text="Power (linear)", row=i_row, col=1, gridcolor='lightgrey')
    updated_plot.update_xaxes(title_text="Height Index", row=1, col=1, gridcolor='lightgrey')
    return updated_plot

# Callback 4: Change Dragmode (Client-Side Javascript)
clientside_callback(
    '''
    function(zoom_clicks, pan_clicks, out_clicks, zoom_style, pan_style) {
        var triggered = dash_clientside.callback_context.triggered;
        if (!triggered || triggered.length === 0) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }
        var prop_id = triggered[0].prop_id;
        
        var new_zoom_style = Object.assign({}, zoom_style);
        var new_pan_style = Object.assign({}, pan_style);
        
        var graphWrapper = document.getElementById('plot-abc-graph');
        if (graphWrapper) {
            var plotlyDiv = graphWrapper.querySelector('.js-plotly-plot');
            if (plotlyDiv) {
                if (prop_id === 'pan-btn.n_clicks') {
                    Plotly.relayout(plotlyDiv, {dragmode: 'pan'});
                    new_pan_style['backgroundColor'] = '#b3e0ff';
                    new_pan_style['border'] = '2px solid #3498db';
                    new_zoom_style['backgroundColor'] = '#e8f4f8';
                    new_zoom_style['border'] = '1px solid #aaa';
                } else if (prop_id === 'box-zoom-btn.n_clicks') {
                    Plotly.relayout(plotlyDiv, {dragmode: 'zoom'});
                    new_zoom_style['backgroundColor'] = '#b3e0ff';
                    new_zoom_style['border'] = '2px solid #3498db';
                    new_pan_style['backgroundColor'] = '#e8f4f8';
                    new_pan_style['border'] = '1px solid #aaa';
                } else if (prop_id === 'zoom-out-btn.n_clicks') {
                    var outBtn = plotlyDiv.querySelector('[data-title="Zoom out"]');
                    if (outBtn) {
                        outBtn.click();
                    }
                }
            }
        }
        return [new_zoom_style, new_pan_style];
    }
    ''',
    [Output('box-zoom-btn', 'style'), Output('pan-btn', 'style')],
    Input('box-zoom-btn', 'n_clicks'),
    Input('pan-btn', 'n_clicks'),
    Input('zoom-out-btn', 'n_clicks'),
    State('box-zoom-btn', 'style'),
    State('pan-btn', 'style'),
    prevent_initial_call=True
)
