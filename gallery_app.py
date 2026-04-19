import os
import glob
from dash import Dash, html, dcc, Input, Output, State

# suppress_callback_exceptions=True is required because the modal and buttons
# are generated dynamically by the serve_layout function!
app = Dash(__name__, suppress_callback_exceptions=True)

# By setting app.layout to a function, Dash will re-evaluate it every time the page is refreshed!
def serve_layout():
    # 1. Dynamically scan the assets folder
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    
    # Check if the assets folder exists
    if not os.path.exists(assets_dir):
        return html.Div([
            html.H1("Image Gallery Dashboard", style={'fontFamily': 'sans-serif', 'color': '#333'}),
            html.P("The 'assets' folder does not exist yet.", style={'color': 'red', 'fontSize': '18px'}),
            html.P("Please create an 'assets' folder next to this script and add some PNGs!", style={'color': 'gray'})
        ], style={'textAlign': 'center', 'padding': '50px', 'fontFamily': 'sans-serif'})
        
    # Find all PNG files
    search_pattern = os.path.join(assets_dir, '*.png')
    png_files = glob.glob(search_pattern)
    
    # Sort them alphabetically
    png_files.sort()
    
    if not png_files:
        return html.Div([
            html.H1("Image Gallery Dashboard", style={'fontFamily': 'sans-serif', 'color': '#333'}),
            html.P("No PNG images found in the 'assets' folder.", style={'color': 'red', 'fontSize': '18px'}),
            html.P("Move your Trace Thinning images into the assets folder and refresh this page!", style={'color': 'gray'})
        ], style={'textAlign': 'center', 'padding': '50px', 'fontFamily': 'sans-serif'})

    # 2. Build the image grid
    image_components = []
    for filepath in png_files:
        filename = os.path.basename(filepath)
        
        # Create a card for each image
        card = html.Div([
            dcc.Markdown(
                f'<img src="{app.get_asset_url(filename)}" loading="lazy" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" />',
                dangerously_allow_html=True
            ),
            html.P(filename, style={
                'textAlign': 'center', 
                'marginTop': '15px', 
                'fontFamily': 'sans-serif',
                'fontSize': '14px',
                'fontWeight': 'bold',
                'color': '#444',
                'wordBreak': 'break-all'
            })
        ], style={
            'backgroundColor': 'white',
            'padding': '15px',
            'borderRadius': '12px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.05)',
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center',
            'transition': 'transform 0.2s ease-in-out'
        })
        image_components.append(card)

    # 3. Define the Pop-Up Modal Window
    caption_modal = html.Div(id="caption-modal", style={
        'display': 'none', # Hidden by default!
        'position': 'fixed',
        'zIndex': '1000', # Force it to the front
        'left': '0', 'top': '0',
        'width': '100%', 'height': '100%',
        'backgroundColor': 'rgba(0,0,0,0.6)', # Darkened background
        'justifyContent': 'center',
        'alignItems': 'center'
    }, children=[
        html.Div(style={
            'backgroundColor': 'white',
            'padding': '40px',
            'borderRadius': '12px',
            'maxWidth': '800px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
            'fontFamily': 'sans-serif'
        }, children=[
            html.H2("Plot Panel Explanations", style={'marginTop': '0', 'color': '#2c3e50'}),
            html.P("This plot consists of multiple sub-panels showing different stages of the inversion:"),
            html.Ul([
                html.Li([html.B("(a) Original Trace: "), "Description of the first panel."]),
                html.Li([html.B("(b) First Pass: "), "Description of the second panel."]),
                html.Li([html.B("(c) Second Pass: "), "Description of the third panel."]),
                html.Li([html.B("(d) Final Inversion: "), "Description of the fourth panel."])
            ], style={'lineHeight': '1.8', 'fontSize': '16px'}),
            html.P(html.I("You can edit this text directly in the gallery_app.py file!")),
            html.Div([
                html.Button("Close Window", id="close-modal-btn", style={
                    'marginTop': '20px', 'padding': '10px 20px', 'cursor': 'pointer',
                    'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'borderRadius': '5px',
                    'fontWeight': 'bold', 'fontSize': '16px'
                })
            ], style={'textAlign': 'center'})
        ])
    ])

    # 4. Return the full layout
    return html.Div([
        caption_modal, # INJECT THE MODAL INTO THE LAYOUT
        
        # Header Area
        html.Div([
            html.H1("Trace Thinning Image Gallery", style={'textAlign': 'center', 'fontFamily': 'sans-serif', 'color': '#2c3e50', 'margin': '0 0 10px 0'}),
            html.P(f"Found {len(png_files)} images in the assets folder.", style={'textAlign': 'center', 'fontFamily': 'sans-serif', 'color': '#7f8c8d', 'margin': '0 0 15px 0'}),
            # Floating Button Container
            html.Div([
                html.Button("📖 View Panel Explanations", id="open-modal-btn", style={
                    'padding': '15px 25px', 'cursor': 'pointer',
                    'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'borderRadius': '30px',
                    'fontWeight': 'bold', 'fontSize': '16px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.3)',
                    'position': 'fixed', 'bottom': '30px', 'right': '30px', 'zIndex': '999',
                    'transition': 'transform 0.2s'
                })
            ])
        ], style={'padding': '40px 0', 'backgroundColor': '#fff', 'boxShadow': '0 2px 10px rgba(0,0,0,0.05)', 'marginBottom': '30px'}),
        
        # Single Column Layout
        html.Div(image_components, style={
            'display': 'flex',
            'flexDirection': 'column', # Stack images vertically
            'gap': '40px', # Generous spacing between the wide plots
            'padding': '0 30px 40px 30px',
            'maxWidth': '1600px', # Allow them to stretch wide
            'margin': '0 auto'
        })
    ], style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh', 'margin': '-8px'}) # -8px margin removes default body margin

# Assign the function to app.layout
app.layout = serve_layout

# CALLBACK: Toggle the Modal Window Open and Closed
@app.callback(
    Output("caption-modal", "style"),
    Input("open-modal-btn", "n_clicks"),
    Input("close-modal-btn", "n_clicks"),
    State("caption-modal", "style"),
    prevent_initial_call=True
)
def toggle_modal(open_clicks, close_clicks, current_style):
    if current_style['display'] == 'none':
        current_style['display'] = 'flex' # 'flex' centers the box on screen
    else:
        current_style['display'] = 'none' # Hide it
    return current_style

if __name__ == '__main__':
    # Using port 8051 so you can leave your original app running on 8050!
    app.run(debug=True, port=8051)
