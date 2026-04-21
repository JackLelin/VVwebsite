import os
from dash import Dash, html, dcc, Input, Output, State, no_update, callback, clientside_callback, Patch, ctx
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import urllib.parse
import numpy as np

consolidate_dir = "assets/Consolidate_result/" # directory where npy files are stored

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
    xaxis_key = 'xaxis' if col_idx == 1 else f'xaxis{col_idx}'
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
    
    fig.add_trace(go.Scatter(x=fps, y=Z, mode='lines', line=dict(color='darkgreen'), name='spline fp', legend=legend_name), row=1, col=col_idx)
    fig.add_trace(go.Scatter(x=x_vals, y=z, mode='markers', marker=dict(color='green', size=6), name='spline node', legend=legend_name), row=1, col=col_idx)
    fig.add_trace(go.Scatter(x=fvsO, y=vhsO, mode='lines', line=dict(color='red'), name='O-trace hv', legend=legend_name), row=1, col=col_idx)
    fig.add_trace(go.Scatter(x=fvsX, y=vhsX, mode='lines', line=dict(color='blue'), name='X-trace hv', legend=legend_name), row=1, col=col_idx)

    imgO = data['vipir_DNN_imgO']
    imgX = data['vipir_DNN_imgX']
    f_idx_o, f_mu_o, _, _ = filter_out_noise_peaks(imgO, freqs, np.array(data['vipir_thin_freqidx_o']), np.array(data['vipir_thin_mu_o']), np.array(data['vipir_thin_std_o']), np.array(data['vipir_thin_A_o']))
    f_idx_x, f_mu_x, _, _ = filter_out_noise_peaks(imgX, freqs, np.array(data['vipir_thin_freqidx_x']), np.array(data['vipir_thin_mu_x']), np.array(data['vipir_thin_std_x']), np.array(data['vipir_thin_A_x']))
    
    idx_x_ints = np.round(f_idx_x).astype(int)
    mu_x_ints  = np.round(f_mu_x).astype(int)
    fig.add_trace(go.Scatter(x=freqs[idx_x_ints], y=hts[mu_x_ints], mode='markers', marker=dict(symbol='x-thin', size=7, line=dict(width=1.5, color='blue')), name='X-mode peak', legend=legend_name), row=1, col=col_idx)
    
    idx_o_ints = np.round(f_idx_o).astype(int)
    mu_o_ints  = np.round(f_mu_o).astype(int)
    fig.add_trace(go.Scatter(x=freqs[idx_o_ints], y=hts[mu_o_ints], mode='markers', marker=dict(symbol='x-thin', size=7, line=dict(width=1.5, color='red')), name='O-mode peak', legend=legend_name), row=1, col=col_idx)


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
    imgO = data['vipir_DNN_imgO']
    imgX = data['vipir_DNN_imgX']
    f_idx_o, f_mu_o, _, _ = filter_out_noise_peaks(imgO, freqs, np.array(data['vipir_thin_freqidx_o']), np.array(data['vipir_thin_mu_o']), np.array(data['vipir_thin_std_o']), np.array(data['vipir_thin_A_o']))
    f_idx_x, f_mu_x, _, _ = filter_out_noise_peaks(imgX, freqs, np.array(data['vipir_thin_freqidx_x']), np.array(data['vipir_thin_mu_x']), np.array(data['vipir_thin_std_x']), np.array(data['vipir_thin_A_x']))
    
    idx_x_ints = np.round(f_idx_x).astype(int)
    mu_x_ints  = np.round(f_mu_x).astype(int)
    fig.add_trace(go.Scatter(x=freqs[idx_x_ints], y=hts[mu_x_ints], mode='markers', marker=dict(symbol='x', color='blue', size=6), name='X-mode', legend=legend_name), row=1, col=col_idx)
    
    idx_o_ints = np.round(f_idx_o).astype(int)
    mu_o_ints  = np.round(f_mu_o).astype(int)
    fig.add_trace(go.Scatter(x=freqs[idx_o_ints], y=hts[mu_o_ints], mode='markers', marker=dict(symbol='x', color='red', size=6), name='O-mode', legend=legend_name), row=1, col=col_idx)

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
            z=binary_ionogram, x=freqs, y=hts,
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
            colorscale=red_mask_scale, zmin=0, zmax=1, opacity=0.5,
            showscale=False, name='O-mode', showlegend=True, legend=legend_name
        ),
        row=1, col=col_idx
    )
    fig.add_trace(
        go.Heatmap(
            z=maskX, x=freqs, y=hts,
            colorscale=blue_mask_scale, zmin=0, zmax=1, opacity=0.5,
            showscale=False, name='X-mode', showlegend=True, legend=legend_name
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
#   data        : the full .npy dict — access any key like data['my_key']
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
#         go.Scatter(
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
    {'id': 'd', 'label': 'Segmented Mask',      'plot_func': plot_segmented_mask},
    # --- To add a new panel, uncomment and modify: ---
    # {'id': 'd', 'label': '(d) My New Panel',      'plot_func': plot_my_heatmap},
]

def serve_layout():
    return html.Div([
        # LEFT PANE (75%)
        html.Div([
            html.H3("Detailed Plot Dashboard", style={'textAlign': 'center', 'fontFamily': 'sans-serif', 'margin': '5px 0 5px 0'}),
            
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
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'padding': '8px 15px', 'backgroundColor': '#f9f9f9', 'borderRadius': '8px', 'width': 'max-content', 'margin': '0 auto 10px auto'}),
            
            html.Div([
                html.Button('Reset Axes', id='reset-view-btn', n_clicks=0,
                    style={'padding': '6px 16px', 'fontSize': '14px', 'fontFamily': 'sans-serif',
                           'cursor': 'pointer', 'borderRadius': '6px', 'border': '1px solid #aaa',
                           'backgroundColor': '#f0f0f0', 'marginRight': '20px', 'fontWeight': 'bold'}),
                html.Span("Plot Width:", style={'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'sans-serif', 'fontSize': '16px'}),
                html.Div(
                    dcc.Slider(
                        id='plot-size-slider',
                        min=200, max=1000, step=50, value=500,
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
                        min=200, max=1000, step=50, value=600,
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": True},
                        updatemode='mouseup'
                    ),
                    style={'flex': '1', 'minWidth': '200px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'padding': '5px 15px', 'width': 'max-content', 'margin': '0 auto 20px auto'}),
            
            # Container for the synced ABC subplot figure
            html.Div([
                html.Div(
                    dcc.Graph(
                        id='plot-abc-graph', 
                        style={'width': '100%', 'height': '100%'},
                        config={'doubleClick': False, 'scrollZoom': True, 'modeBarButtonsToRemove': ['autoScale2d']}
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
        ], style={'width': '75%', 'paddingRight': '20px', 'borderRight': '3px solid #ccc', 'display': 'flex', 'flexDirection': 'column'}),
        
        # RIGHT PANE (25%)
        html.Div([
            html.H3("Detail of Selected Column", style={'textAlign': 'center', 'fontFamily': 'sans-serif', 'marginTop': '0', 'color': '#333'}),
            dcc.Graph(
                id='cross-section-plot',
                figure=go.Figure().update_layout(title="Click on the (a) Original Ionogram to see cross-section", margin=dict(l=40, r=40, t=50, b=40)),
                style={'width': '100%', 'height': '300px'}, # Fixed height for column stack
                config={'doubleClick': 'reset', 'modeBarButtonsToRemove': ['autoScale2d']}
            ),
            dcc.Graph(
                id='gmm-fit-O',
                figure=go.Figure().update_layout(title="GMM Fit", margin=dict(l=40, r=40, t=50, b=40)),
                style={'width': '100%', 'height': '300px'}, # Fixed height for column stack
                config={'doubleClick': 'reset', 'modeBarButtonsToRemove': ['autoScale2d']}
            ),
            dcc.Graph(
                id='gmm-fit-X',
                figure=go.Figure().update_layout(title="GMM Fit", margin=dict(l=40, r=40, t=50, b=40)),
                style={'width': '100%', 'height': '300px'}, # Fixed height for column stack
                config={'doubleClick': 'reset', 'modeBarButtonsToRemove': ['autoScale2d']}
            )
            # More plots can be added here easily in a column!
        ], style={'width': '25%', 'paddingLeft': '20px', 'display': 'flex', 'flexDirection': 'column', 'gap': '20px'})
        
    ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%', 'padding': '20px', 'boxSizing': 'border-box'})

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
                'width': (width * abcCount) + 'px',
                'height': height + 'px',
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
    Input('url', 'search'),
    Input('plot-toggles', 'value'),
    Input('reset-view-btn', 'n_clicks')
)
def generate_all_plots(search_query, selected_panels, reset_clicks):
    empty_abc = make_subplots(rows=1, cols=1).update_layout(title="No data loaded")
    
    if not search_query:
        return empty_abc
        
    parsed = urllib.parse.parse_qs(search_query.lstrip('?'))
    if 'image' not in parsed:
        return empty_abc
        
    filename = parsed['image'][0]
    npy_filename = filename.replace('.png', '.npy')
    filepath = os.path.join(consolidate_dir, npy_filename)
    
    if not os.path.exists(filepath):
        return empty_abc
        
    # Load data ONCE
    data = np.load(filepath, allow_pickle=True)[()]
    freqs = data['vipir_freqs']
    hts = data['vipir_hts']
    
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
    
    return fig_abc


# Callback 3: Update the Cross-Section Plot when clicking on the ABC subplot
@callback(
    Output('cross-section-plot', 'figure'),
    Output('gmm-fit-O', 'figure'),
    Output('gmm-fit-X', 'figure'),
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
    npy_filename = filename.replace('.png', '.npy')
    filepath = os.path.join(consolidate_dir, npy_filename)
    
    if not os.path.exists(filepath):
        return no_update
        
    data = np.load(filepath, allow_pickle=True)[()]
    hts = data['vipir_hts']
    freqs = data['vipir_freqs']
    org = data['vipir_original']
    # intensity = 10 * np.log10(org + 1)
    
    # In Plotly, the clicked x/y values match the coordinates we provided (freqs and hts)
    click_x = clickData['points'][0]['x'] 
    click_y = clickData['points'][0]['y'] 
    
    # Find the closest frequency index to the clicked x-coordinate (Vertical Cross-Section)
    x_idx = np.argmin(np.abs(freqs - click_x))
    y_idx = np.argmin(np.abs(hts - click_y))
    col_data = org[:, x_idx]
    
    # Plot the 1D vertical cross-section across all heights at that specific frequency
    # We plot Intensity (dB) on the X-axis and Virtual Height (km) on the Y-axis
    updated_cross_section_plot = px.line(
        x=col_data[20:], 
        y=hts[20:],
        title=f"Power Profile at {freqs[x_idx]:.2f} MHz",
        labels={'x': 'Power (linear)', 'y': 'Virtual Height (km)'}
    ).update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.01, bgcolor="rgba(255,255,255,0.7)")
    )

    # Highlight the specific point that was clicked
    updated_cross_section_plot.add_scatter(
        x=[org[y_idx, x_idx]], 
        y=[click_y], 
        mode='markers', 
        marker=dict(color='red', size=12), 
        name='Clicked Point'
    )

    updated_gmm_fit_O = px.line(
        x=np.arange(20, hts.shape[0]),
        y=col_data[20:], 
        title=f"Power Profile at {freqs[x_idx]:.2f} MHz",
        labels={'x': 'Height Index', 'y': 'Power (linear)'}
    ).update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.01, bgcolor="rgba(255,255,255,0.7)")
    )
            # Add a shaded region under the curve between X=10 and X=20
    updated_gmm_fit_O.add_vrect(
        x0=80,                      # Start of the shaded region
        x1=180,                      # End of the shaded region
        fillcolor="LightSkyBlue",   # Color of the shade
        opacity=0.3,                # Make it semi-transparent so you can see gridlines
        layer="below",              # Push the shade *behind* the data line!
        line_width=0                # Remove the border around the shaded box
    )


    updated_gmm_fit_X = px.line(
        x=np.arange(20, hts.shape[0]),
        y=col_data[20:], 
        title=f"Power Profile at {freqs[x_idx]:.2f} MHz",
        labels={'x': 'Height Index', 'y': 'Power (linear)'}
    ).update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.01, bgcolor="rgba(255,255,255,0.7)")
    )
    
    return updated_cross_section_plot, updated_gmm_fit_O, updated_gmm_fit_X
