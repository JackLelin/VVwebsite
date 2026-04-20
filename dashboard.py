import os
from dash import Dash, html, dcc, Input, Output, State, no_update, callback
import plotly.express as px
import plotly.graph_objects as go
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

# --- 3. Define the Layout ---
def serve_layout():
    return html.Div([
        # LEFT PANE (75%)
        html.Div([
            html.H1("Detailed Plot Dashboard", style={'textAlign': 'center', 'fontFamily': 'sans-serif'}),
            html.P("Select panels to display corresponding to the data.", 
                   style={'textAlign': 'center', 'fontFamily': 'sans-serif', 'color': 'gray'}),
            
            html.Div([
                html.Span("Select Panels to Display:", style={'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'sans-serif', 'fontSize': '16px'}),
                dcc.Checklist(
                    id='plot-toggles',
                    options=[
                        {'label': ' (a) Original Ionogram', 'value': 'a'},
                        {'label': ' (b) Inversion Result', 'value': 'b'},
                        {'label': ' (c) Thinned Traces', 'value': 'c'},
                        {'label': ' (d) ISR Phase Profile', 'value': 'd'}
                    ],
                    value=['a', 'b', 'c', 'd'], # Start with all panels checked
                    inline=True,
                    inputStyle={'cursor': 'pointer', 'marginRight': '5px', 'marginLeft': '10px'},
                    labelStyle={'cursor': 'pointer', 'fontSize': '16px', 'fontFamily': 'sans-serif'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'padding': '8px 15px', 'backgroundColor': '#f9f9f9', 'borderRadius': '8px', 'width': 'max-content', 'margin': '0 auto 10px auto'}),
            
            html.Div([
                html.Span("Plot Width:", style={'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'sans-serif', 'fontSize': '16px'}),
                html.Div(
                    dcc.Slider(
                        id='plot-size-slider',
                        min=200, max=1000, step=50, value=400,
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
                        min=200, max=1000, step=50, value=500,
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": True},
                        updatemode='mouseup'
                    ),
                    style={'flex': '1', 'minWidth': '200px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'padding': '5px 15px', 'width': 'max-content', 'margin': '0 auto 20px auto'}),
            
            # Container for dynamically generated plots
            html.Div([
                html.Div(dcc.Graph(id='plot-a-graph', style={'width': '100%', 'height': '100%'}), id='plot-a-wrapper', style={'display': 'none'}),
                html.Div(dcc.Graph(id='plot-b-graph', style={'width': '100%', 'height': '100%'}), id='plot-b-wrapper', style={'display': 'none'}),
                html.Div(dcc.Graph(id='plot-c-graph', style={'width': '100%', 'height': '100%'}), id='plot-c-wrapper', style={'display': 'none'}),
                html.Div(dcc.Graph(id='plot-d-graph', style={'width': '100%', 'height': '100%'}), id='plot-d-wrapper', style={'display': 'none'}),
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
            html.H2("Detailed Analysis", style={'textAlign': 'center', 'fontFamily': 'sans-serif', 'marginTop': '0', 'color': '#333'}),
            dcc.Graph(
                id='cross-section-plot',
                figure=go.Figure().update_layout(title="Click on the (a) Original Ionogram to see cross-section", margin=dict(l=40, r=40, t=50, b=40)),
                style={'width': '100%', 'height': '400px'} # Fixed height for column stack
            )
            # More plots can be added here easily in a column!
        ], style={'width': '25%', 'paddingLeft': '20px', 'display': 'flex', 'flexDirection': 'column', 'gap': '20px'})
        
    ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%', 'padding': '20px', 'boxSizing': 'border-box'})

# --- 4. Callbacks ---
# --- 4. Callbacks ---

# Callback 1: Toggle Styles (Lightning Fast - Does not reload data or plots)
@callback(
    Output('plot-a-wrapper', 'style'),
    Output('plot-b-wrapper', 'style'),
    Output('plot-c-wrapper', 'style'),
    Output('plot-d-wrapper', 'style'),
    Input('plot-toggles', 'value'),
    Input('plot-size-slider', 'value'),
    Input('plot-height-slider', 'value')
)
def update_styles(selected_panels, width, height):
    styles = []
    for panel in ['a', 'b', 'c', 'd']:
        if panel in selected_panels:
            styles.append({
                'display': 'block',
                'width': f'{width}px',
                'height': f'{height}px',
                'border': '1px dashed #aaa',
                'marginRight': '10px',
                'flexShrink': 0
            })
        else:
            styles.append({'display': 'none'})
    return styles

# Callback 2: Load Data & Generate Plots (Slow - Only runs ONCE on page load)
@callback(
    Output('plot-a-graph', 'figure'),
    Output('plot-b-graph', 'figure'),
    Output('plot-c-graph', 'figure'),
    Output('plot-d-graph', 'figure'),
    Input('url', 'search')
)
def generate_all_plots(search_query):
    empty_fig = go.Figure().update_layout(title="No data loaded")
    
    if not search_query:
        return empty_fig, empty_fig, empty_fig, empty_fig
        
    parsed = urllib.parse.parse_qs(search_query.lstrip('?'))
    if 'image' not in parsed:
        return empty_fig, empty_fig, empty_fig, empty_fig
        
    filename = parsed['image'][0]
    npy_filename = filename.replace('.png', '.npy')
    filepath = os.path.join(consolidate_dir, npy_filename)
    
    if not os.path.exists(filepath):
        return empty_fig, empty_fig, empty_fig, empty_fig
        
    # Load data ONCE
    data = np.load(filepath, allow_pickle=True)[()]
    freqs = data['vipir_freqs']
    hts = data['vipir_hts']
    org = data['vipir_original']
    intensity = 10 * np.log10(org + 1)
    
    # (a) Original Ionogram
    fig_a = px.imshow(intensity, x=freqs, y=hts, color_continuous_scale='jet', origin='lower', aspect='auto')
    fig_a.update_coloraxes(cmin=10, cmax=70, colorbar=dict(thickness=10))
    fig_a.update_layout(title="(a) Original Ionogram (dB)", xaxis_title="Frequency (MHz)", yaxis_title="Virtual Height (km)", margin=dict(l=10, r=10, t=35, b=10))
    
    # (b) Inversion Result
    fig_b = px.imshow(intensity, x=freqs, y=hts, color_continuous_scale='gray_r', origin='lower', aspect='auto')
    fig_b.update_coloraxes(cmin=10, cmax=70, colorbar=dict(thickness=10))
    fps = data['vipir_inversion_fps']
    Z = data['vipir_inversion_z_hts']
    x_vals = data['vipir_inversion_all_xvals'][-1]
    z = data['vipir_inversion_z_node']
    fvsO = data['vipir_inversion_fvsO']
    vhsO = data['vipir_inversion_vhsO']
    fvsX = data['vipir_inversion_fvsX']
    vhsX = data['vipir_inversion_vhsX']
    fig_b.add_scatter(x=fps, y=Z, mode='lines', line=dict(color='darkgreen'), name='spline fp')
    fig_b.add_scatter(x=x_vals, y=z, mode='markers', marker=dict(color='green', size=6), name='spline node')
    fig_b.add_scatter(x=fvsO, y=vhsO, mode='lines', line=dict(color='red'), name='O-trace hv')
    fig_b.add_scatter(x=fvsX, y=vhsX, mode='lines', line=dict(color='blue'), name='X-trace hv')
    fig_b.update_layout(title="(b) Inversion Result", xaxis_title="Frequency (MHz)", yaxis_title="Virtual Height (km)", margin=dict(l=10, r=10, t=35, b=10), legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.7)"))
    
    # (c) Thinned Traces
    fig_c = px.imshow(intensity, x=freqs, y=hts, color_continuous_scale='gray_r', origin='lower', aspect='auto')
    fig_c.update_coloraxes(cmin=10, cmax=70, colorbar=dict(thickness=10))
    imgO = data['vipir_DNN_imgO']
    imgX = data['vipir_DNN_imgX']
    f_idx_o, f_mu_o, _, _ = filter_out_noise_peaks(imgO, freqs, np.array(data['vipir_thin_freqidx_o']), np.array(data['vipir_thin_mu_o']), np.array(data['vipir_thin_std_o']), np.array(data['vipir_thin_A_o']))
    f_idx_x, f_mu_x, _, _ = filter_out_noise_peaks(imgX, freqs, np.array(data['vipir_thin_freqidx_x']), np.array(data['vipir_thin_mu_x']), np.array(data['vipir_thin_std_x']), np.array(data['vipir_thin_A_x']))
    
    scat_idx_x = np.append(np.arange(len(f_idx_x)//5)*5, -2)
    idx_x_ints = np.round(f_idx_x[scat_idx_x]).astype(int)
    mu_x_ints  = np.round(f_mu_x[scat_idx_x]).astype(int)
    fig_c.add_scatter(x=freqs[idx_x_ints], y=hts[mu_x_ints], mode='markers', marker=dict(symbol='x', color='blue', size=6), name='X-mode')
    
    scat_idx_o = np.append(np.arange(len(f_idx_o)//5)*5, -2)
    idx_o_ints = np.round(f_idx_o[scat_idx_o]).astype(int)
    mu_o_ints  = np.round(f_mu_o[scat_idx_o]).astype(int)
    fig_c.add_scatter(x=freqs[idx_o_ints], y=hts[mu_o_ints], mode='markers', marker=dict(symbol='x', color='red', size=6), name='O-mode')
        
    fig_c.update_layout(title="(c) Thinned Traces with GMM", xaxis_title="Frequency (MHz)", yaxis_title="Virtual Height (km)", margin=dict(l=10, r=10, t=35, b=10), legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.7)"))
    
    # (d) Phase Result
    fig_d = go.Figure()
    phase_isr = data['valley_phase']
    phase_unwrapped = data['valley_phase_unwrapped']
    best_channel_idx = data['valley_phase_bestchannel'] 
    p_sim = data['vipir_inversion_phase_sim']
    valleyz = data.get('valley_z', np.linspace(hts.min(), hts.max(), len(p_sim)))
    offset3 = np.mean(phase_unwrapped[best_channel_idx][200:] - p_sim[200:])
    fig_d.add_scatter(x=p_sim + offset3 + 2*np.pi, y=valleyz, mode='lines', line=dict(color='red'), showlegend=False)
    fig_d.add_scatter(x=p_sim + offset3, y=valleyz, mode='lines', line=dict(color='red'), name='Predicted Phase')
    fig_d.add_scatter(x=p_sim + offset3 - 2*np.pi, y=valleyz, mode='lines', line=dict(color='red'), showlegend=False)
    fig_d.add_scatter(x=phase_isr[best_channel_idx], y=valleyz, mode='markers', marker=dict(color='blue', size=4), name='ISR Phase')
    fig_d.add_scatter(x=phase_isr[best_channel_idx]+2*np.pi, y=valleyz, mode='markers', marker=dict(color='blue', size=4), showlegend=False)
    fig_d.add_scatter(x=phase_isr[best_channel_idx]-2*np.pi, y=valleyz, mode='markers', marker=dict(color='blue', size=4), showlegend=False)
    fig_d.add_hrect(y0=valleyz.min(), y1=valleyz.max(), fillcolor="gray", opacity=0.2, line_width=0, name="ISR range")
    fig_d.update_layout(title="(d) ISR Phase Profile", xaxis_title="Phase (rad)", yaxis_title="Virtual Height (km)", 
                      xaxis_range=[-np.pi, np.pi], yaxis_range=[hts.min(), hts.max()], margin=dict(l=10, r=10, t=35, b=10), legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.7)"))

    return fig_a, fig_b, fig_c, fig_d

# Callback 3: Update the Cross-Section Plot when clicking on Plot A
@callback(
    Output('cross-section-plot', 'figure'),
    Input('plot-a-graph', 'clickData'),
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
    intensity = 10 * np.log10(org + 1)
    
    # In Plotly, the clicked x/y values match the coordinates we provided (freqs and hts)
    click_x = clickData['points'][0]['x'] 
    click_y = clickData['points'][0]['y'] 
    
    # Find the closest frequency index to the clicked x-coordinate (Vertical Cross-Section)
    x_idx = np.argmin(np.abs(freqs - click_x))
    col_data = intensity[:, x_idx]
    
    # Plot the 1D vertical cross-section across all heights at that specific frequency
    # We plot Intensity (dB) on the X-axis and Virtual Height (km) on the Y-axis
    updated_cross_section_plot = px.line(
        x=col_data, 
        y=hts,
        title=f"Vertical Profile at {freqs[x_idx]:.2f} MHz",
        labels={'x': 'Intensity (dB)', 'y': 'Virtual Height (km)'}
    ).update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.7)")
    )

    # Highlight the specific point that was clicked
    y_idx = np.argmin(np.abs(hts - click_y))
    updated_cross_section_plot.add_scatter(
        x=[intensity[y_idx, x_idx]], 
        y=[click_y], 
        mode='markers', 
        marker=dict(color='red', size=12), 
        name='Clicked Point'
    )
    
    return updated_cross_section_plot
