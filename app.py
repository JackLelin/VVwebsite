from dash import Dash, html, dcc, Input, Output, State, Patch, no_update, ALL, callback_context
import plotly.express as px
import numpy as np

# --- 1. Helper function to generate dummy 2D data ---
def generate_matrix(seed):
    np.random.seed(seed)
    x = np.linspace(-5, 5, 50)
    y = np.linspace(-5, 5, 50)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(X**2 + (Y * (seed/10 + 1))**2) + np.random.normal(0, 0.1, (50, 50))
    return Z

# Global reference matrix for the base plot
Z_ref = generate_matrix(42)

# --- 2. Initialize the Dash App ---
app = Dash(__name__)

# --- 3. Define the Layout ---
# Initial default cross-section plot
initial_y_index = 25
initial_row = Z_ref[initial_y_index, :]
initial_fig = px.line(
    x=np.arange(len(initial_row)), 
    y=initial_row,
    title=f"Cross-Section of Original Plot at Y-index: {initial_y_index}",
    labels={'x': 'X Index', 'y': 'Value'}
)
initial_fig.add_scatter(x=[25], y=[Z_ref[initial_y_index, 25]], mode='markers', 
                        marker=dict(color='red', size=12), name='Clicked Point')

app.layout = html.Div([
    html.H1("Dynamic 2D Matrix Dashboard", style={'textAlign': 'center', 'fontFamily': 'sans-serif'}),
    html.P("Toggle plots using the checkboxes. Click anywhere on any image below to see its 1D cross-section on the right.", 
           style={'textAlign': 'center', 'fontFamily': 'sans-serif', 'color': 'gray'}),
    
    html.Div([
        html.H3("Select Plots to Display:", style={'display': 'inline-block', 'marginRight': '20px', 'fontFamily': 'sans-serif'}),
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
            inputStyle={'cursor': 'pointer', 'marginRight': '5px', 'marginLeft': '15px'},
            labelStyle={'cursor': 'pointer', 'fontSize': '16px', 'fontFamily': 'sans-serif'}
        )
    ], style={'textAlign': 'center', 'marginBottom': '20px', 'padding': '15px', 'backgroundColor': '#f9f9f9', 'borderRadius': '8px', 'width': 'max-content', 'margin': '0 auto 20px auto'}),
    
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
                'borderRight': '3px solid #666', # Visually looks like a separator
                'paddingRight': '10px'
            }
        ),
        
        # Right Pane: A secondary plot to show interactivity
        html.Div([
            dcc.Graph(
                id='cross-section-plot',
                figure=initial_fig,
                style={'width': '100%', 'height': '100%'}
            )
        ], style={'flex': '1', 'minWidth': '10%', 'paddingLeft': '10px'})
        
    ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%'})
])

# --- 4. Callbacks ---

# A. Generate the selected plots
@app.callback(
    Output('left-plots-container', 'children'),
    Input('plot-toggles', 'value')
)
def update_plots(selected_values):
    children = []
    
    # Sort so they appear in a consistent order (Original, +10, +20, +30)
    for offset in sorted(selected_values):
        
        # ADD the offset to the base matrix!
        Z_new = Z_ref + offset
        
        plot_title = "Original 2D Plot" if offset == 0 else f"2D Plot (+{offset} Offset)"
        
        # Create the figure
        new_fig = px.imshow(
            Z_new, 
            labels=dict(x="X-Axis Label", y="Y-Axis Label", color="Intensity"),
            title=plot_title,
            color_continuous_scale="Viridis",
            height=600,
            aspect="auto" 
        ).update_layout(
            xaxis_title="X-Axis Label", 
            yaxis_title="Y-Axis Label",
            coloraxis_colorbar=dict(
                title="Color Bar",
                thickness=15,
                len=0.75
            ),
            # Unified hovermode goes well with crosshairs
            hovermode="x unified"
        )
        
        # ADD CROSSHAIRS!
        new_fig.update_xaxes(showspikes=True, spikemode="across", spikedash="solid", spikecolor="gray", spikethickness=1)
        new_fig.update_yaxes(showspikes=True, spikemode="across", spikedash="solid", spikecolor="gray", spikethickness=1)

        # Wrap the new figure in a resizable div
        new_plot_component = html.Div([
            dcc.Graph(
                # Using Pattern-Matching IDs! The index is the offset value.
                id={'type': 'matrix-image', 'index': offset},
                figure=new_fig,
                style={
                    'resize': 'both', 
                    'overflow': 'hidden',
                    'minWidth': '400px', # Give each plot a decent minimum width
                    'minHeight': '300px',
                    'maxWidth': '95%',  
                    'maxHeight': '95%',
                    'width': '100%', 
                    'border': '1px dashed #aaa',
                    'marginRight': '20px' # Space between stacked plots
                }
            )
        ], style={'minWidth': '500px', 'flexShrink': 0}) # flexShrink=0 ensures it doesn't get squished if too many plots are added
        
        children.append(new_plot_component)
        
    return children


# B. Update the cross-section plot when ANY matrix is clicked
@app.callback(
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
    Z_clicked = Z_ref + plot_offset
    
    row_data = Z_clicked[click_y, :]
    
    # Plot the 1D cross-section
    plot_title = f"Cross-Section of Original Plot at Y: {click_y}" if plot_offset == 0 else f"Cross-Section of +{plot_offset} Plot at Y: {click_y}"
    
    fig = px.line(
        x=np.arange(len(row_data)), 
        y=row_data,
        title=plot_title,
        labels={'x': 'X Index', 'y': 'Value'}
    )
    
    fig.add_scatter(x=[click_x], y=[Z_clicked[click_y, click_x]], mode='markers', 
                    marker=dict(color='red', size=12), name='Clicked Point')
    
    return fig

# --- 5. Run the Server ---
if __name__ == '__main__':
    app.run(debug=True, port=8050)
