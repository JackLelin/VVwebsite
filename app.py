from dash import Dash, html, dcc, Input, Output, Patch, no_update
import plotly.express as px
import numpy as np

# --- 1. Generate an example 2D matrix using numpy ---
np.random.seed(42)
x = np.linspace(-5, 5, 50)
y = np.linspace(-5, 5, 50)
X, Y = np.meshgrid(x, y)
Z = np.sin(X**2 + Y**2) + np.random.normal(0, 0.1, (50, 50))

# --- 2. Initialize the Dash App ---
app = Dash(__name__)

# --- 3. Define the Layout ---
# Create the initial cross-section figure so we have a base structure to update
initial_y_index = 25
initial_row = Z[initial_y_index, :]
initial_fig = px.line(
    x=np.arange(len(initial_row)), 
    y=initial_row,
    title=f"Horizontal Cross-Section at Y-index: {initial_y_index}",
    labels={'x': 'X Index', 'y': 'Value'}
)
initial_fig.add_scatter(x=[25], y=[Z[initial_y_index, 25]], mode='markers', 
                        marker=dict(color='red', size=12), name='Clicked Point')

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
                labels=dict(x="X-Axis Label", y="Y-Axis Label", color="Intensity"),
                title="Large Interactive 2D Plot",
                color_continuous_scale="Viridis",
                height=750 # Make the plot larger
            ).update_layout(
                xaxis_title="X-Axis Label", 
                yaxis_title="Y-Axis Label",
                coloraxis_colorbar=dict(
                    title="Color Bar", # Give the color bar a clear title
                    thickness=20,
                    len=0.75
                )
            ),
            style={'width': '50%'}
        ),
        
        # A secondary plot to show interactivity
        dcc.Graph(
            id='cross-section-plot',
            figure=initial_fig,
            style={'width': '50%'}
        )
    ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%'})
])

# --- 4. Define Interactivity ---
# By using Patch, we only send the changed data to the browser instead of redrawing the plot
@app.callback(
    Output('cross-section-plot', 'figure'),
    Input('matrix-image', 'clickData'),
    prevent_initial_call=True
)
def update_cross_section(clickData):
    if clickData is None:
        return no_update
    
    # Extract the x and y indices of the clicked point
    click_x = clickData['points'][0]['x']
    click_y = clickData['points'][0]['y']
    
    # Get the cross-section (the specific row) from the numpy matrix
    row_data = Z[click_y, :]
    
    # Plot the 1D cross-section
    fig = px.line(
        x=np.arange(len(row_data)), 
        y=row_data,
        title=f"Horizontal Cross-Section at Y-index: {click_y}",
        labels={'x': 'X Index', 'y': 'Value'}
    )
    
    # Add a red dot to show exactly where they clicked on that cross-section
    fig.add_scatter(x=[click_x], y=[Z[click_y, click_x]], mode='markers', 
                    marker=dict(color='red', size=12), name='Clicked Point')
    
    return fig

# --- 5. Run the Server ---
if __name__ == '__main__':
    app.run(debug=True, port=8050)
