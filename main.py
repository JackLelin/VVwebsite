from dash import Dash, html, dcc, Input, Output

# Create the master app instance right here in the main script!
# We split the URL config so Dash knows the browser is asking for /vipir_inversion/
# but internally it routes from the root '/' (because Apache strips the folder name).
vipir_app = Dash(
    __name__, 
    requests_pathname_prefix='/vipir_inversion/',
    routes_pathname_prefix='/'
)

# Expose the underlying Flask server for WSGI (used by dashboard.wsgi)
server = vipir_app.server

# Import the layouts and callbacks from our separate files
import dashboard
import gallery_app

# The Master Router Layout
vipir_app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# The Router Callback
@vipir_app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    # Use .endswith() so it safely catches both '/dashboard' and 
    # '/vipir_inversion/dashboard' regardless of where it is hosted.
    if pathname and pathname.endswith('/dashboard'):
        # Render the detailed plot view
        return dashboard.serve_layout()
    else:
        # Default to the gallery (Main Entrance)
        return gallery_app.serve_layout()

if __name__ == '__main__':
    # Still listen locally if you ever need to run it without Apache
    vipir_app.run(host='127.0.0.1', port=8050, debug=False)