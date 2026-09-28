import os
import glob
import json
from dash import html, dcc, Input, Output, State, callback, ALL, ctx, no_update

# ==========================================
# CONFIGURATION
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
TARGET_GALLERY_SUBDIR = 'Preview_figures'
BASE_URL = '/vipir_inversion/'
DEFALT_START_END_LT = [6,19]

def build_gallery_cards(year, day, start_hour, end_hour):
    """Build list of image cards for a given year and day, optionally filtered by hour range."""
    if not year or not day:
        return [], []
    day_dir = os.path.join(ASSETS_DIR, str(year), str(day), TARGET_GALLERY_SUBDIR)
    gallery_png_filepaths = [
        fp for fp in sorted(glob.glob(os.path.join(day_dir, '*.png')))
        if start_hour <= int(os.path.basename(fp)[13:15]) <= end_hour
    ]

    # Build the image cards
    gallery_image_cards = []
    base_asset_prefix = BASE_URL.rstrip('/')
    for filepath in gallery_png_filepaths:
        filename = os.path.basename(filepath)

        image_card_container = html.Div([
            html.Div(
                id={'type': 'gallery-image', 'index': filename},
                n_clicks=0,
                style={'cursor': 'zoom-in'},
                children=[
                    dcc.Markdown(
                        f'<img src="{base_asset_prefix}/assets/{year}/{day}/{TARGET_GALLERY_SUBDIR}/{filename}" loading="lazy" style="width: 100%; height: auto; min-height: 350px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" />',
                        dangerously_allow_html=True
                    )
                ]
            ),
            html.Div([
                html.A(
                    filename,
                    href=f"{BASE_URL}dashboard?image={filename}&year={year}&day={day}",
                    target="_blank",
                    style={
                        'display': 'block',
                        'textAlign': 'center',
                        'margin': '0',
                        'fontFamily': 'sans-serif',
                        'fontSize': '14px',
                        'fontWeight': 'bold',
                        'color': '#444',
                        'wordBreak': 'break-all',
                        'textDecoration': 'none'
                    }
                )
            ], style={'marginTop': '15px'})
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

    return gallery_png_filepaths, gallery_image_cards


def build_welcome_section():
    example_url = f"{BASE_URL}2016/014"
    return html.Div([
        html.Div([
            html.H2("Inversion Repository for Jicamarca VIPIR Ionograms", style={
                'color': '#2c3e50', 'marginTop': '0', 'fontFamily': 'sans-serif', 'fontSize': '28px'
            }),
            html.P([
                "Welcome to the VIPIR ionogram data portal where we present raw and inverted ionograms recorded at the Jicamarca Radio Observatory. "
                "Electron density profile inversions derived from Vertical Incidence Pulsed Ionospheric Radar (VIPIR) soundings are presented "
                "and compared with complementary measurements obtained with the Jicamarca 50 MHz incoherent scatter radar. "
            ], style={'fontSize': '16px', 'lineHeight': '1.6', 'color': '#4a5568', 'fontFamily': 'sans-serif'}),

            # Instructions Box
            html.Div([
                html.H3("How to Navigate", style={'color': '#2c3e50', 'marginTop': '0', 'fontFamily': 'sans-serif', 'fontSize': '20px'}),
                html.Ol([
                    html.Li([
                        html.B("Select Year & Day: "),
                        "Use the dropdown selectors in the top navigation bar to choose an observation year and day."
                    ], style={'marginBottom': '10px'}),
                    html.Li([
                        html.B("Filter by Time: "),
                        "Use the dual-handle slider above and click ",
                        html.Span("Filter Hours", style={'backgroundColor': '#27ae60', 'color': 'white', 'padding': '2px 8px', 'borderRadius': '4px', 'fontSize': '13px'}),
                        f" to narrow down the observation window. The default range is {DEFALT_START_END_LT[0]}:00-{DEFALT_START_END_LT[1]}:00 LT.",
                    ], style={'marginBottom': '10px'}),
                    html.Li([
                        html.B("Interactive Dashboard: "),
                        "Click on any plot to open the detailed multi-panel view for deep inspection of individual inversion stages, zoom/pan controls, and model traces."
                    ])
                ], style={'fontSize': '15px', 'lineHeight': '1.6', 'fontFamily': 'sans-serif', 'paddingLeft': '20px', 'color': '#2d3748'})
            ], style={
                'backgroundColor': '#f8fafc',
                'border': '1px solid #e2e8f0',
                'borderRadius': '10px',
                'padding': '20px 25px',
                'marginTop': '20px'
            }),

            # Example Link Card
            html.Div([
                html.Div([
                    html.Span("Example Dataset: 2016 Day 014", style={
                        'fontWeight': 'bold', 'fontSize': '18px', 'color': '#1e3a8a'
                    })
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
                html.P([
                    html.B("2016 Day 014 "),
                    " contains both Incoherent Scatter Radar (ISR) phase data and VIPIR ionosonde data.",
                ], style={'fontSize': '15px', 'color': '#1e293b', 'margin': '0 0 16px 0', 'lineHeight': '1.6'}),
                dcc.Link(
                    html.Button([
                        "Open Example: 2016 Day 014 (ISR & VIPIR) ",
                        html.Span("→", style={'fontSize': '18px', 'marginLeft': '6px'})
                    ], style={
                        'backgroundColor': '#2563eb',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 22px',
                        'fontSize': '15px',
                        'fontWeight': 'bold',
                        'borderRadius': '8px',
                        'cursor': 'pointer',
                        'boxShadow': '0 2px 6px rgba(37, 99, 235, 0.3)',
                        'display': 'inline-flex',
                        'alignItems': 'center'
                    }),
                    href=example_url,
                    style={'textDecoration': 'none'}
                )
            ], style={
                'backgroundColor': '#eff6ff',
                'border': '1px solid #bfdbfe',
                'borderRadius': '10px',
                'padding': '20px 25px',
                'marginTop': '25px'
            }),

            # Performance Reminder / Alert Box
            html.Div([
                html.Div([
                    html.Span("⚠️", style={'fontSize': '26px', 'marginRight': '14px', 'lineHeight': '1'}),
                    html.Div([
                        html.Div("Important: Loading Time & Responsiveness Notice", style={
                            'fontWeight': 'bold', 'color': '#92400e', 'fontSize': '16px', 'marginBottom': '5px'
                        }),
                        html.Div(
                            f"Each observation day contains thousands of ionogram figures (~1-2 MB each). "
                            f"Because of the large data volume, the page load time can be relatively long and the website may temporarily feel unresponsive while loading and rendering images. ",
                            style={'fontSize': '14px', 'color': '#78350f', 'lineHeight': '1.6'}
                        )
                    ])
                ], style={'display': 'flex', 'alignItems': 'flex-start'})
            ], style={
                'backgroundColor': '#fef3c7',
                'borderLeft': '5px solid #f59e0b',
                'borderRadius': '6px',
                'padding': '16px 20px',
                'marginTop': '25px'
            })

        ], style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'padding': '35px 40px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
            'maxWidth': '920px',
            'margin': '20px auto'
        })
    ])


# By setting app.layout to a function, Dash re-evaluates it every time the page is refreshed
def serve_layout(selected_year=None, selected_day=None):
    available_years = sorted([os.path.basename(p) for p in glob.glob(os.path.join(ASSETS_DIR, '*')) if os.path.isdir(p) and os.path.basename(p).isdigit()])
    available_days = sorted([os.path.basename(p) for p in glob.glob(os.path.join(ASSETS_DIR, str(selected_year), '*')) if os.path.isdir(p)]) if selected_year else []
    
    if selected_year and selected_day:
        gallery_png_filepaths, initial_content = build_gallery_cards(selected_year, selected_day, start_hour=DEFALT_START_END_LT[0]+5, end_hour=DEFALT_START_END_LT[1]+5)
    else:
        gallery_png_filepaths = []
        initial_content = build_welcome_section()

    # 1. Define the Pop-Up Modal Window
    caption_modal = html.Div(id="caption-modal", style={
        'display': 'none', # Hidden by default
        'position': 'fixed',
        'zIndex': '1000', # Force to the front
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
            html.Div([
                html.Button("Close Window", id="close-modal-btn", style={
                    'marginTop': '20px', 'padding': '10px 20px', 'cursor': 'pointer',
                    'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'borderRadius': '5px',
                    'fontWeight': 'bold', 'fontSize': '16px'
                })
            ], style={'textAlign': 'center'})
        ])
    ])
    # 2. Define the Dashboard Modal Window
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

    # 3. Return the full layout
    out_layout = html.Div([
        dashboard_modal, # INJECT THE DASHBOARD MODAL
        caption_modal,   # INJECT THE MODAL INTO THE LAYOUT

        # Top Bar: Year Selector, Day Selector, and Hour Sliders
        html.Div([
            html.Div([
                html.Span("Select Year:", style={
                    'fontWeight': 'bold',
                    'fontSize': '16px',
                    'color': '#2c3e50',
                    'fontFamily': 'sans-serif',
                    'marginRight': '12px'
                }),
                dcc.Dropdown(
                    id='year-select-dropdown',
                    options=[{'label': str(y), 'value': str(y)} for y in available_years],
                    value=selected_year,
                    placeholder="Select year...",
                    clearable=False,
                    searchable=False,
                    style={
                        'width': '150px',
                        'fontFamily': 'sans-serif',
                        'fontWeight': 'bold'
                    }
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginLeft': '30px'}),
            html.Div([
                html.Span("Select Day:", style={
                    'fontWeight': 'bold',
                    'fontSize': '16px',
                    'color': '#2c3e50',
                    'fontFamily': 'sans-serif',
                    'marginRight': '12px'
                }),
                dcc.Loading(
                    id='day-select-loading',
                    type='dot',
                    color='#3498db',
                    children=dcc.Dropdown(
                        id='day-select-dropdown',
                        options=[{'label': str(d), 'value': str(d)} for d in available_days],
                        value=selected_day,
                        placeholder="Select day...",
                        clearable=False,
                        searchable=False,
                        style={
                            'width': '150px',
                            'fontFamily': 'sans-serif',
                            'fontWeight': 'bold'
                        }
                    )
                ),
                html.Div([
                    html.Div(className='header-spinner'),
                    html.Span("Loading...", className='header-loading-text')
                ], id='header-loading-indicator', style={'display': 'none', 'alignItems': 'center', 'marginLeft': '12px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginLeft': '20px'}),
            html.Div([
                html.Span("Hour Range (UT):", style={
                    'fontWeight': 'bold',
                    'fontSize': '16px',
                    'color': '#2c3e50',
                    'fontFamily': 'sans-serif',
                    'marginRight': '15px'
                }),
                html.Div([
                    dcc.RangeSlider(
                        id='hour-range-slider',
                        min=0,
                        max=24,
                        step=1,
                        value=[DEFALT_START_END_LT[0]+5, DEFALT_START_END_LT[1]+5],
                        updatemode='mouseup',
                        marks={i: str(i - 5 if i >= 5 else i + 19) if i!=0 else f'LT:{i+19}' for i in range(0, 25, 2)}
                    )
                ], style={'width': '550px'}),
                html.Button(
                    "Filter Hours",
                    id='apply-hour-filter-btn',
                    n_clicks=0,
                    style={
                        'marginLeft': '20px',
                        'padding': '6px 16px',
                        'backgroundColor': '#27ae60',
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '6px',
                        'fontWeight': 'bold',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
                    }
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'marginLeft': '30px'}),
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'flexWrap': 'wrap',
            'gap': '10px 0',
            'padding': '14px 0',
            'backgroundColor': '#ffffff',
            'borderBottom': '1px solid #eaeaea',
            'boxShadow': '0 2px 6px rgba(0,0,0,0.03)'
        }),

        # Header Area
        html.Div([
            html.H1(
                f"Jicamarca VIPIR Ionogram Inversion Results for {selected_year} Day {selected_day}"
                if (selected_year and selected_day)
                else"Inversion Repository for Jicamarca VIPIR Ionograms",
                style={'textAlign': 'left', 'fontFamily': 'sans-serif', 'color': '#2c3e50', 'margin': '0 0 10px 30px'}
            ),
            html.P(
                f"Total {len(gallery_png_filepaths)} images."
                if (selected_year and selected_day)
                else "Select a year and day from the top bar to view data, or explore the featured example below.",
                id='gallery-count-text',
                style={'textAlign': 'left', 'fontFamily': 'sans-serif', 'color': '#7f8c8d', 'margin': '0 0 15px 30px'}
            ),
            # Floating Button Container
            html.Div([
                html.Button("README", id="open-modal-btn", style={
                    'padding': '15px 25px', 'cursor': 'pointer',
                    'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'borderRadius': '30px',
                    'fontWeight': 'bold', 'fontSize': '16px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.3)',
                    'position': 'fixed', 'bottom': '30px', 'right': '30px', 'zIndex': '999',
                    'transition': 'transform 0.2s'
                })
            ])
        ], style={'padding': '30px 0', 'backgroundColor': '#fff', 'boxShadow': '0 2px 10px rgba(0,0,0,0.05)', 'marginBottom': '30px'}),

        # Image Grid Container wrapped in dcc.Loading
        dcc.Loading(
            id='gallery-loading',
            type='circle',
            color='#27ae60',
            show_initially=False,
            overlay_style={'visibility': 'hidden', 'filter': 'blur(2px)'},
            children=html.Div(
                id='gallery-grid-container',
                children=initial_content,
                style={
                    'display': 'flex',
                    'flexDirection': 'column', # Stack images vertically
                    'gap': '40px', # Generous spacing between the wide plots
                    'padding': '0 30px 40px 30px',
                    'maxWidth': '1600px', # Allow them to stretch wide
                    'margin': '0 auto'
                }
            )
        )
    ], style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh', 'margin': '-8px'}) # -8px margin removes default body margin
    return out_layout

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


# Task 1 CALLBACK: When Year changes in dropdown, glob to find day folders and update Day selector
@callback(
    Output("day-select-dropdown", "options"),
    Output("day-select-dropdown", "value"),
    Input("year-select-dropdown", "value"),
    prevent_initial_call=True
)
def update_day_selector(selected_year):
    if not selected_year:
        return [], None
    days = sorted([os.path.basename(p) for p in glob.glob(os.path.join(ASSETS_DIR, str(selected_year), '*')) if os.path.isdir(p)])
    return [{'label': str(d), 'value': str(d)} for d in days], None


# CALLBACK: Filter gallery images by hour range when Apply button is clicked
@callback(
    Output('gallery-grid-container', 'children'),
    Output('gallery-count-text', 'children'),
    Input('apply-hour-filter-btn', 'n_clicks'),
    State('hour-range-slider', 'value'),
    State('year-select-dropdown', 'value'),
    State('day-select-dropdown', 'value'),
    prevent_initial_call=True
)
def apply_hour_filter(n_clicks, hour_range, selected_year, selected_day):
    if not selected_year or not selected_day or not hour_range:
        return no_update, no_update
    
    start_hour, end_hour = min(hour_range), max(hour_range)
    gallery_png_filepaths, filtered_cards = build_gallery_cards(
        selected_year, selected_day, start_hour=start_hour, end_hour=end_hour
    )
    count_str = f"Total {len(gallery_png_filepaths)} images."
    return filtered_cards, count_str


# Task 2 CALLBACK: When Day is selected, update the webpage URL path
@callback(
    Output("url", "pathname"),
    Input("day-select-dropdown", "value"),
    State("year-select-dropdown", "value"),
    prevent_initial_call=True
)
def update_webpage_path(selected_day, selected_year):
    if selected_year and selected_day:
        return f"{BASE_URL}{selected_year}/{selected_day}"
    return no_update


# CALLBACK: Toggle Dashboard Modal using Iframe
@callback(
    Output("dashboard-modal", "style"),
    Output("dashboard-iframe", "src"),
    Input({'type': 'gallery-image', 'index': ALL}, 'n_clicks'),
    Input("close-dashboard-btn", "n_clicks"),
    State("dashboard-modal", "style"),
    State("year-select-dropdown", "value"),
    State("day-select-dropdown", "value"),
    prevent_initial_call=True
)
def toggle_dashboard_modal(n_clicks_list, close_clicks, current_style, selected_year, selected_day):
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
        return style, f"{BASE_URL}dashboard?image={filename}&year={selected_year}&day={selected_day}"

    return no_update, no_update
