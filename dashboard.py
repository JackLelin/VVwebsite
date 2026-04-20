from dash import Dash, html, dcc, Input, Output, State, Patch, no_update, ALL, callback_context, callback
import plotly.express as px
import urllib.parse
import numpy as np

consolidate_dir = "assets/Consolidated/" # directory where npy files are stored

# --- 1. Helper function to generate dummy 2D data ---
def generate_matrix(seed):
    np.random.seed(seed)
    x = np.linspace(-5, 5, 50)
    y = np.linspace(-5, 5, 50)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(X**2 + (Y * (seed/10 + 1))**2) + np.random.normal(0, 0.1, (50, 50))
    return Z

# Global reference matrix for the base plot
base_reference_matrix = generate_matrix(42)

# --- 3. Define the Layout ---
def serve_layout():
    # Initial default cross-section plot
    default_y_index = 25
    default_row_data = base_reference_matrix[default_y_index, :]
    default_cross_section_figure = px.line(
        x=np.arange(len(default_row_data)), 
        y=default_row_data,
        title=f"Cross-Section of Original Plot at Y-index: {default_y_index}",
        labels={'x': 'X Index', 'y': 'Value'}
    ).update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(yanchor="top", y=0.95, xanchor="right", x=0.99) # Move legend inside plot
    )
    default_cross_section_figure.add_scatter(x=[25], y=[base_reference_matrix[default_y_index, 25]], mode='markers', 
                            marker=dict(color='red', size=12), name='Clicked Point')

    return html.Div([
        html.H1("Dynamic 2D Matrix Dashboard", style={'textAlign': 'center', 'fontFamily': 'sans-serif'}),
        html.P("Toggle plots using the checkboxes. Click anywhere on any image below to see its 1D cross-section on the right.", 
               style={'textAlign': 'center', 'fontFamily': 'sans-serif', 'color': 'gray'}),
        
        html.Div([
            html.Span("Select Plots to Display:", style={'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'sans-serif', 'fontSize': '16px'}),
            dcc.Checklist(
                id='plot-toggles',
                options=[
                    {'label': ' Original (Base)', 'value': 0},
                    {'label': ' +10 Offset', 'value': 10},
                    {'label': ' +20 Offset', 'value': 20},
                    {'label': ' +30 Offset', 'value': 30}
                ],
                value=[0], # Start with just the original plot checked
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
        
        # Create a flex container to hold both the left panes and the right pane
        html.Div([
            # Left Pane: Container for dynamically generated plots
            html.Div(
                id='left-plots-container',
                children=[], # Starts empty, filled by callback
                style={
                    'width': '66.6%', 
                    'display': 'flex',
                    'flexDirection': 'row', # Stack horizontally!
                    'overflowX': 'auto', # Allow horizontal scrolling if multiple plots are added
                    'overflowY': 'auto',
                    'maxHeight': '70vh', # Cap the maximum height of the left pane
                    'borderRight': '3px solid #666', # Visually looks like a separator
                    'paddingRight': '10px'
                }
            ),
            
            # Right Pane: A secondary plot to show interactivity
            html.Div([
                dcc.Graph(
                    id='cross-section-plot',
                    figure=default_cross_section_figure,
                    style={'width': '100%', 'height': '100%'}
                )
            ], style={'flex': '1', 'minWidth': '10%', 'paddingLeft': '10px'})
            
        ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%'})
    ])

# --- 4. Callbacks ---

# A. Generate the selected plots
@callback(
    Output('left-plots-container', 'children'),
    Input('plot-toggles', 'value'),
    Input('plot-size-slider', 'value'),
    Input('plot-height-slider', 'value')
)
def update_plots(selected_values, plot_size, plot_height):
    heatmap_components_list = []
    
    # Sort so they appear in a consistent order (Original, +10, +20, +30)
    for offset in sorted(selected_values):
        
        # ADD the offset to the base matrix!
        offset_matrix = base_reference_matrix + offset
        
        plot_title = "Original 2D Plot" if offset == 0 else f"2D Plot (+{offset} Offset)"
        
        # Create the figure
        heatmap_figure = px.imshow(
            offset_matrix, 
            labels=dict(x="X-Axis Label", y="Y-Axis Label", color="Intensity"),
            title=plot_title,
            color_continuous_scale="Viridis",
            height=plot_height, # Driven by slider
            aspect="auto",
            origin="lower" # Set origin to bottom-left corner
        ).update_layout(
            xaxis_title="X-Axis Label", 
            yaxis_title="Y-Axis Label",
            coloraxis_colorbar=dict(
                title=" ",
                thickness=15,
                len=0.75,
                x=1.00, # Move flush to the edge of the plot
                xpad=5  # Remove colorbar padding
            ),
            # Use 'closest' instead of 'x unified' to strictly obey the hovertemplate
            hovermode="closest",
            margin=dict(l=10, r=10, t=35, b=10) # Minimum internal whitespace!
        )
        
        # ADD CROSSHAIRS!
        heatmap_figure.update_xaxes(showspikes=True, spikemode="across", spikedash="solid", spikecolor="gray", spikethickness=1)
        heatmap_figure.update_yaxes(showspikes=True, spikemode="across", spikedash="solid", spikecolor="gray", spikethickness=1)

        # CUSTOMIZE THE HOVER TOOLTIP!
        heatmap_figure.update_traces(
            hovertemplate=(
                "<b>X-Coordinate:</b> %{x}<br>"
                "<b>Y-Coordinate:</b> %{y}<br>"
                "<b>Intensity Value:</b> %{z:.2f}" 
                "<extra></extra>" 
            )
        )

       # ADD A LINE OR SCATTER PLOT ON TOP OF THE 2D HEATMAP!
        heatmap_figure.add_scatter(
            x=[10, 20, 30, 40],        # Array of X coordinates
            y=[10, 35, 15, 45],        # Array of Y coordinates
            mode='lines+markers',      # Choose 'lines', 'markers', or 'lines+markers'
            line=dict(color='white', width=2, dash='dash'), 
            marker=dict(color='red', size=10, symbol='star'),
            name='My Overlay',
            hoverinfo='skip'           # Prevents the overlay from hijacking the crosshairs!
        )

        # Wrap the new figure in a fixed-size div, no longer individually resizable
        heatmap_wrapper_div = html.Div([
            dcc.Graph(
                # Using Pattern-Matching IDs! The index is the offset value.
                id={'type': 'matrix-image', 'index': offset},
                figure=heatmap_figure,
                responsive=True, # This tells Plotly to instantly fill its container
                style={
                    'width': '100%', 
                    'height': '100%'
                }
            )
        ], style={
            'width': f'{plot_size}px', # Explicitly drive width from the wrapper
            'height': f'{plot_height}px', # Drive height from the wrapper
            'border': '1px dashed #aaa',
            'marginRight': '5px',
            'flexShrink': 0
        })
        
        heatmap_components_list.append(heatmap_wrapper_div)
        
    return heatmap_components_list


# B. Update the cross-section plot when ANY matrix is clicked
@callback(
    Output('cross-section-plot', 'figure'),
    Input({'type': 'matrix-image', 'index': ALL}, 'clickData'),
    prevent_initial_call=True
)
def update_cross_section(clickData_list):
    # Figure out which input triggered the callback
    ctx = callback_context
    if not ctx.triggered:
        return no_update
    
    # The property ID of the component that triggered the event
    triggered_id = ctx.triggered[0]['prop_id']
    
    # Extract the index (the offset value) of the specific plot that was clicked
    import json
    try:
        dict_id = json.loads(triggered_id.split('.')[0])
        plot_offset = dict_id['index']
    except:
        return no_update

    # Grab the exact value of the click that fired the event
    clickData = ctx.triggered[0]['value']
    
    if clickData is None:
        return no_update
        
    click_x = clickData['points'][0]['x']
    click_y = clickData['points'][0]['y']
    
    # Re-generate the exact Z matrix for the plot that was clicked
    clicked_matrix = base_reference_matrix + plot_offset
    
    selected_row_data = clicked_matrix[click_y, :]
    
    # Plot the 1D cross-section
    plot_title = f"Cross-Section of Original Plot at Y: {click_y}" if plot_offset == 0 else f"Cross-Section of +{plot_offset} Plot at Y: {click_y}"
    
    updated_cross_section_plot = px.line(
        x=np.arange(len(selected_row_data)), 
        y=selected_row_data,
        title=plot_title,
        labels={'x': 'X Index', 'y': 'Value'}
    ).update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(yanchor="top", y=0.95, xanchor="right", x=0.99) # Move legend inside plot
    )
    # Add a shaded region under the curve between X=10 and X=20
    updated_cross_section_plot.add_vrect(
        x0=10,                      # Start of the shaded region
        x1=20,                      # End of the shaded region
        fillcolor="LightSkyBlue",   # Color of the shade
        opacity=0.3,                # Make it semi-transparent so you can see gridlines
        layer="below",              # Push the shade *behind* the data line!
        line_width=0                # Remove the border around the shaded box
    )

    updated_cross_section_plot.add_scatter(x=[click_x], y=[clicked_matrix[click_y, click_x]], mode='markers', 
                    marker=dict(color='red', size=12), name='Clicked Point')
    
    return updated_cross_section_plot

# C. Read URL to get the target image from the Gallery
@callback(
    Output('url', 'pathname'), # Dummy output
    Input('url', 'search'),
    prevent_initial_call=False
)
def handle_gallery_redirect(search_query):
    if search_query:
        parsed = urllib.parse.parse_qs(search_query.lstrip('?'))
        if 'image' in parsed:
            filename = parsed['image'][0]
            print(f"\n{'='*60}\nSUCCESS! Received filename from gallery: {filename}\n{'='*60}\n")

            data = np.load(consolidate_dir + filename, allow_pickle=True)[()]
            freqs = data['vipir_freqs']
            hts = data['vipir_hts']
            img = data['vipir_binary_ionogram']
            org = data['vipir_original']
            fvsO = data['vipir_inversion_fvsO']
            vhsO = data['vipir_inversion_vhsO']
            fvsX = data['vipir_inversion_fvsX']
            vhsX = data['vipir_inversion_vhsX']
            losses = data['vipir_inversion_all_losses']
            x_vals = data['vipir_inversion_all_xvals'][-1]
            z = data['vipir_inversion_z_node']
            Z = data['vipir_inversion_z_hts']
            fps = data['vipir_inversion_fps']
            
            fig, axes = plt.subplots(1, 4, figsize=(20, 6), gridspec_kw={'wspace': 0.07})
            --- (a) original ionogram ---
            ax1 = axes[0]
            im1 = ax1.pcolormesh(freqs,hts,10*np.log10(org+1),shading='auto',cmap='jet')
            im1.set_clim([10, 70])
            ax1.set_xlim(freqs.min(),freqs.max())
            ax1.set_ylim(hts.min() ,hts.max())
            ax1.set_title("(a) Original Ionogram (dB)")
            ax1.set_xlabel("Frequency (MHz)")
            ax1.set_ylabel("Virtual Height (km)")

            # --- (b) Inversion result ---
            ax2 = axes[1]
            im2 = ax2.pcolormesh(freqs,hts,10*np.log10(org+1),shading='auto',cmap='binary')
            im2.set_clim([10, 70])
            m, = ax2.plot (fps, Z, '-',color='darkgreen', label='spline fp')
            l, = ax2.plot (x_vals,z,color='g',linestyle='none',marker='o',markersize=6, label='spline node')
            mO, = ax2.plot(fvsO, vhsO, 'r-', label='O-trace hv')
            mX, = ax2.plot(fvsX, vhsX, 'b-', label='X-trace hv')
            ax2.legend(loc='best')
            ax2.set_xlim(freqs.min(),freqs.max())
            ax2.set_ylim(hts.min() ,hts.max())
            ax2.set_title("(b) Inversion Result")
            ax2.set_xlabel("Frequency (MHz)")
            ax2.set_yticks([])

            # --- (c) Thinned Traces ---
            imgO = data['vipir_DNN_imgO']
            imgX = data['vipir_DNN_imgX']
            idx_o = data['vipir_thin_freqidx_o']
            mu_o = data['vipir_thin_mu_o']
            std_o = data['vipir_thin_std_o']
            A_o = data['vipir_thin_A_o']
            idx_x = data['vipir_thin_freqidx_x']
            mu_x = data['vipir_thin_mu_x']
            std_x = data['vipir_thin_std_x']
            A_x = data['vipir_thin_A_x']

            filtered_idx_o, filtered_mu_o, filtered_std_o, filtered_A_o = filter_out_noise_peaks(imgO, np.array(idx_o), np.array(mu_o), np.array(std_o), np.array(A_o))
            filtered_idx_x, filtered_mu_x, filtered_std_x, filtered_A_x = filter_out_noise_peaks(imgX, np.array(idx_x), np.array(mu_x), np.array(std_x), np.array(A_x))

            ax3 = axes[2]
            im4 = ax3.pcolormesh(freqs, hts, 10*np.log10(org+1), shading='auto', cmap='binary', alpha=1)
            im4.set_clim([10, 70])
            # X-mode Thinned
            scat_idx_x = np.append(np.arange(filtered_idx_x.shape[0]//5)*5, -2)
            idx_x_ints = np.round(filtered_idx_x[scat_idx_x]).astype(int)
            mu_x_ints  = np.round(filtered_mu_x[scat_idx_x]).astype(int)
            ax3.scatter(freqs[idx_x_ints], hts[mu_x_ints], marker='x', s=35, linewidths=0.9, color='b', label='X-mode')

            # O-mode Thinned
            scat_idx_o = np.append(np.arange(filtered_idx_o.shape[0]//5)*5, -2)
            idx_o_ints = np.round(filtered_idx_o[scat_idx_o]).astype(int)
            mu_o_ints  = np.round(filtered_mu_o[scat_idx_o]).astype(int)
            ax3.scatter(freqs[idx_o_ints], hts[mu_o_ints], marker='x', s=35, linewidths=0.9, color='r', label='O-mode')

            ax3.set_xlabel("Frequency (MHz)")
            ax3.set_yticks([])
            ax3.set_title("(c) Thinned Traces with GMM")
            ax3.legend(loc='best')

            # --- (d) phase result ---
            phase_isr = data['valley_phase']
            phase_unwrapped = data['valley_phase_unwrapped']
            best_channel_idx = data['valley_phase_bestchannel'] 
            p_sim = data['vipir_inversion_phase_sim']

            ax4 = axes[3]
            offset3 = np.mean(phase_unwrapped[best_channel_idx][200:] - p_sim[200:])
            ax4.plot(p_sim + offset3 + 2*np.pi, valleyz, c='r')
            ax4.plot(p_sim + offset3, valleyz, c='r', label='Predicted Phase')
            ax4.plot(p_sim + offset3 - 2*np.pi, valleyz, c='r')

            ax4.scatter(phase_isr[best_channel_idx], valleyz, marker='.', color='b', label='ISR Phase')
            ax4.scatter(phase_isr[best_channel_idx]+2*np.pi, valleyz, marker='.', color='b')
            ax4.scatter(phase_isr[best_channel_idx]-2*np.pi, valleyz, marker='.', color='b')
            ax4.set_ylim(hts.min(), hts.max())
            ax4.set_xlim(-np.pi, np.pi)
            ax4.set_xlabel("Phase (rad)")
            ax4.set_yticks([])
            ax4.set_title("(d) ISR Phase Profile")
            ax4.axhspan(valleyz.min(), valleyz.max(), color='gray', alpha=0.2, label='ISR range')
            ax4.legend(loc='best')
    return no_update

# --- 5. Run the Server ---
# Server execution moved to main.py
