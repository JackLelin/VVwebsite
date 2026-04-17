from dash import Dash, html, dcc, Input, Output, Patch
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- 1. Generate an example 2D matrix using numpy ---
np.random.seed(42)
# Create a 50x50 matrix with some pattern (e.g., a 2D sine wave + noise)
x = np.linspace(-5, 5, 50)
y = np.linspace(-5, 5, 50)
X, Y = np.meshgrid(x, y)
Z = np.sin(X**2 + Y**2) + np.random.normal(0, 0.1, (50, 50))

# --- 2. Initialize the Dash App ---
app = Dash(__name__)

# --- 3. Define the Layout ---
# Define a base figure with empty traces so we only have to update data later
base_fig = go.Figure()
base_fig.add_trace(go.Scatter(x=[], y=[], mode='lines', name='Cross-Section'))
base_fig.add_trace(go.Scatter(x=[], y=[], mode='markers', marker=dict(color='red', size=12), name='Clicked Point'))
base_fig.update_layout(
    title="Awaiting Click... Select a point on the matrix above.",
    xaxis_title="X Index", yaxis_title="Value"
)

app.layout = html.Div([
    html.H1("2D Matrix as Image", style={'textAlign': 'center', 'fontFamily': 'sans-serif'}),
    html.P("Click anywhere on the image below to see a 1D cross-section of that row.", 
           style={'textAlign': 'center', 'fontFamily': 'sans-serif', 'color': 'gray'}),
    
    # Create a flex container to hold both graphs side-by-side
    html.Div([
        # Plot the 2D matrix as an image (heatmap)
        dcc.Graph(
            id='matrix-image',
            figure=px.imshow(
                Z, 
                labels=dict(x="X Index", y="Y Index", color="Value"),
                title="Interactive 2D Numpy Array (imshow)",
                color_continuous_scale="Viridis"
            ),
            style={'width': '50%'}
        ),
        
        # A secondary plot to show interactivity
        dcc.Graph(
            id='cross-section-plot',
            figure=base_fig,
            style={'width': '50%'}
        )
    ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%'})
])

# --- 4. Define Interactivity ---
@app.callback(
    Output('cross-section-plot', 'figure'),
    Input('matrix-image', 'clickData')
)
def update_cross_section(clickData):
    if clickData is None:
        return Patch()
    
    # Extract the x and y indices of the clicked point
    click_x = clickData['points'][0]['x']
    click_y = clickData['points'][0]['y']
    # Get the cross-section (the specific row) from the numpy matrix
    row_data = Z[click_y, :]
    
    # Use Patch to ONLY update the data, rather than rebuilding the figure
    patched_fig = Patch()
    patched_fig['layout']['title']['text'] = f"Horizontal Cross-Section at Y-index: {click_y}"
    
    # Update the line trace (index 0)
    patched_fig['data'][0]['x'] = np.arange(len(row_data))
    patched_fig['data'][0]['y'] = row_data
    
    # Update the dot trace (index 1)
    patched_fig['data'][1]['x'] = [click_x]
    patched_fig['data'][1]['y'] = [Z[click_y, click_x]]
    
    return patched_fig

# --- 5. Run the Server ---
if __name__ == '__main__':
    app.run(debug=True, port=8050)
