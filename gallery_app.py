import os
import glob
import json
from dash import html, dcc, Input, Output, State, callback, ALL, ctx, no_update

# ==========================================
# CONFIGURATION
# ==========================================
# The sub-folder inside 'assets' where the gallery images are stored.
# Set to 'Preview_figures' to scan assets/Preview_figures, or '' for the root assets folder.
TARGET_GALLERY_SUBDIR = 'Preview_figures'

# By setting app.layout to a function, Dash will re-evaluate it every time the page is refreshed!
def serve_layout():
    # 1. Dynamically scan the target folder
    gallery_assets_directory = os.path.join(os.path.dirname(__file__), 'assets', TARGET_GALLERY_SUBDIR)
    
    # Check if the assets folder exists
    if not os.path.exists(gallery_assets_directory):
        return html.Div([
            html.H1("Image Gallery Dashboard", style={'fontFamily': 'sans-serif', 'color': '#333'}),
            html.P("The 'assets' folder does not exist yet.", style={'color': 'red', 'fontSize': '18px'}),
            html.P("Please create an 'assets' folder next to this script and add some PNGs!", style={'color': 'gray'})
        ], style={'textAlign': 'center', 'padding': '50px', 'fontFamily': 'sans-serif'})
        
    # Find all PNG files
    search_pattern = os.path.join(gallery_assets_directory, '*.png')
    gallery_png_filepaths = glob.glob(search_pattern)
    
    # Sort them alphabetically
    gallery_png_filepaths.sort()
    
    if not gallery_png_filepaths:
        return html.Div([
            html.H1("Image Gallery Dashboard", style={'fontFamily': 'sans-serif', 'color': '#333'}),
            html.P("No PNG images found in the 'assets' folder.", style={'color': 'red', 'fontSize': '18px'}),
            html.P("Move your Trace Thinning images into the assets folder and refresh this page!", style={'color': 'gray'})
        ], style={'textAlign': 'center', 'padding': '50px', 'fontFamily': 'sans-serif'})

    # 2. Build the image grid
    gallery_image_cards = []
    for filepath in gallery_png_filepaths:
        filename = os.path.basename(filepath)

        # Create a card for each image
        image_card_container = html.Div([
            html.Div(
                id={'type': 'gallery-image', 'index': filename},
                n_clicks=0,
                style={'cursor': 'pointer'},
                children=[
                    dcc.Markdown(
                        f'<img src="/vipir_inversion/assets/{TARGET_GALLERY_SUBDIR}/{filename}" loading="lazy" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" />',
                        dangerously_allow_html=True
                    )
                ]
            ),
            html.Div([
                html.P(filename, style={
                    'textAlign': 'center', 
                    'margin': '0', 
                    'fontFamily': 'sans-serif',
                    'fontSize': '14px',
                    'fontWeight': 'bold',
                    'color': '#444',
                    'wordBreak': 'break-all'
                }),
                html.A(
                    "Open full dashboard in new tab ↗", 
                    href=f"dashboard?image={filename}", 
                    target="_blank", 
                    style={
                        'fontSize': '12px', 
                        'textDecoration': 'none', 
                        'color': '#3498db', 
                        'marginTop': '8px',
                        'fontWeight': 'bold'
                    }
                )
            ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'marginTop': '15px'})
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
        gallery_image_cards.append(image_card_container)

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
            html.H2("Click on the plot to see the different stages of the inversion.", style={'marginTop': '0', 'color': '#2c3e50'}),
            html.P("The explanations of each sub-panel:"),
            html.Ul([
                html.Li([html.B("(a) Original Ionogram: "), "VIPIR ionogram presented on a dB scale."]),
                html.Li([html.B("(b) Inversion result: "), "Green dots and curve represent the control points for the spline and the inverted electron density (Ne) profile, respectively. The red and blue curves are the predicted O and X traces from the inverted Ne profile."]),
                html.Li([html.B("(c) The virtual height of reflection: "), "The virtual height of reflection is the peak location of the return signal."]),
                html.Li([html.B("(d) Final Inversion: "), "Blue dots: Phase profile from the ISR. Red curve: The predicted phase profile from the Ne profile."])
            ], style={'lineHeight': '1.8', 'fontSize': '16px'}),
            # html.P(html.I("You can edit this text directly in the gallery_app.py file!")),
            html.Div([
                html.Button("Close Window", id="close-modal-btn", style={
                    'marginTop': '20px', 'padding': '10px 20px', 'cursor': 'pointer',
                    'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'borderRadius': '5px',
                    'fontWeight': 'bold', 'fontSize': '16px'
                })
            ], style={'textAlign': 'center'})
        ])
    ])

    # 4. Define the Dashboard Modal Window
    dashboard_modal = html.Div(
        id="dashboard-modal",
        style={
            'display': 'none', 
            'position': 'fixed',
            'zIndex': '1050',
            'left': '0', 'top': '0',
            'width': '100vw', 'height': '100vh',
            'backgroundColor': 'rgba(0,0,0,0.8)',
            'justifyContent': 'center',
            'alignItems': 'center',
            'padding': '10px',
            'boxSizing': 'border-box'
        },
        children=[
            html.Div(
                style={
                    'backgroundColor': 'white',
                    'width': '99%',
                    'height': '99%',
                    'borderRadius': '8px',
                    'boxShadow': '0 4px 20px rgba(0,0,0,0.5)',
                    'overflow': 'hidden',
                    'position': 'relative',
                    'display': 'flex',
                    'flexDirection': 'column'
                },
                children=[
                    html.Button("✖", id="close-dashboard-btn", n_clicks=0, style={
                        'position': 'absolute', 'top': '5px', 'left': '5px', 'zIndex': '1000',
                        'width': '35px', 'height': '35px', 'borderRadius': '50%',
                        'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none',
                        'fontWeight': 'bold', 'fontSize': '16px', 'cursor': 'pointer',
                        'boxShadow': '0 2px 5px rgba(0,0,0,0.3)', 'display': 'flex',
                        'justifyContent': 'center', 'alignItems': 'center', 'padding': '0'
                    }),
                    html.Iframe(
                        id="dashboard-iframe",
                        src="",
                        style={'flex': '1', 'width': '100%', 'border': 'none'}
                    )
                ]
            )
        ]
    )

    # 5. Return the full layout
    return html.Div([
        dashboard_modal, # INJECT THE DASHBOARD MODAL
        caption_modal, # INJECT THE MODAL INTO THE LAYOUT
        
        # Header Area
        html.Div([
            html.H1("Ionogram Inversion Result for Jan 14 2016", style={'textAlign': 'left', 'fontFamily': 'sans-serif', 'color': '#2c3e50', 'margin': '0 0 10px 30px'}),
            html.P(f"Total {len(gallery_png_filepaths)} images.", style={'textAlign': 'left', 'fontFamily': 'sans-serif', 'color': '#7f8c8d', 'margin': '0 0 15px 30px'}),
            # Floating Button Container
            html.Div([
                html.Button("View Panel Explanations", id="open-modal-btn", style={
                    'padding': '15px 25px', 'cursor': 'pointer',
                    'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'borderRadius': '30px',
                    'fontWeight': 'bold', 'fontSize': '16px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.3)',
                    'position': 'fixed', 'bottom': '30px', 'right': '30px', 'zIndex': '999',
                    'transition': 'transform 0.2s'
                })
            ])
        ], style={'padding': '40px 0', 'backgroundColor': '#fff', 'boxShadow': '0 2px 10px rgba(0,0,0,0.05)', 'marginBottom': '30px'}),
        
        # Single Column Layout
        html.Div(gallery_image_cards, style={
            'display': 'flex',
            'flexDirection': 'column', # Stack images vertically
            'gap': '40px', # Generous spacing between the wide plots
            'padding': '0 30px 40px 30px',
            'maxWidth': '1600px', # Allow them to stretch wide
            'margin': '0 auto'
        })
    ], style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh', 'margin': '-8px'}) # -8px margin removes default body margin

# CALLBACK: Toggle the Modal Window Open and Closed
@callback(
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

# CALLBACK: Toggle Dashboard Modal using Iframe
@callback(
    Output("dashboard-modal", "style"),
    Output("dashboard-iframe", "src"),
    Input({'type': 'gallery-image', 'index': ALL}, 'n_clicks'),
    Input("close-dashboard-btn", "n_clicks"),
    State("dashboard-modal", "style"),
    prevent_initial_call=True
)
def toggle_dashboard_modal(n_clicks_list, close_clicks, current_style):
    if not ctx.triggered:
        return no_update, no_update
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if 'close-dashboard-btn' in trigger_id:
        if not current_style:
            current_style = {}
        current_style['display'] = 'none'
        return current_style, ""
        
    if 'gallery-image' in trigger_id:
        if not any(n_clicks_list):
            return no_update, no_update
            
        trigger_dict = json.loads(trigger_id.rsplit('.', 1)[0])
        filename = trigger_dict['index']
        
        style = {
            'display': 'flex', 
            'position': 'fixed',
            'zIndex': '1050',
            'left': '0', 'top': '0',
            'width': '100vw', 'height': '100vh',
            'backgroundColor': 'rgba(0,0,0,0.8)',
            'justifyContent': 'center',
            'alignItems': 'center',
            'padding': '10px',
            'boxSizing': 'border-box'
        }
        return style, f"dashboard?image={filename}"
        
    return no_update, no_update
