from dash import Dash, html, dcc, Input, Output

# Define your universal base URL
BASE_URL = '/vipir_inversion/'

# Create the master app instance right here in the main script!
# We make it smart: Detect if we are running locally or via Apache WSGI
if __name__ == '__main__':
    # Local Testing Mode: Forces local testing to use the exact same subfolder URL
    vipir_app = Dash(__name__, url_base_pathname=BASE_URL, suppress_callback_exceptions=True)
else:
    # Apache WSGI Mode: Apache strips the folder name, so we split the routing
    vipir_app = Dash(
        __name__, 
        requests_pathname_prefix=BASE_URL,
        routes_pathname_prefix='/',
        suppress_callback_exceptions=True
    )

# Expose the underlying Flask server for WSGI (used by dashboard.wsgi)
server = vipir_app.server

# Import the layouts and callbacks from our separate files
import dashboard
import gallery_app

# ==========================================
# THE FIX: Wrap layout in a function!
# This stops Dash from crashing when it looks for callback IDs that 
# haven't been rendered yet.
# ==========================================
def serve_master_layout():
    return html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content')
    ])

vipir_app.layout = serve_master_layout

# The Router Callback
@vipir_app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    Input('url', 'search')
)
def display_page(pathname, search):
    # Use .endswith() so it safely catches both '/dashboard' and 
    # '/vipir_inversion/dashboard' regardless of where it is hosted.
    if pathname and pathname.endswith('/dashboard'):
        # Render the detailed plot view
        return dashboard.serve_layout()
    elif search and 'image=' in search:
        # User went directly to /?image=...
        return dashboard.serve_layout()
    else:
        # Default to the gallery (Main Entrance)
        return gallery_app.serve_layout()

if __name__ == '__main__':
    # Still listen locally if you ever need to run it without Apache
    # debug=True is okay here since we are only using it locally
    vipir_app.run(host='127.0.0.1', port=8050, debug=True)