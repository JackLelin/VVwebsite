from dash import Dash, html, dcc, Input, Output

# Create the master app instance right here in the main script!
# vipir_app = Dash(__name__, suppress_callback_exceptions=True)
vipir_app = Dash(__name__, url_base_pathname='/vipir_inversion/')

# Add this line right here to expose the underlying Flask server for WSGI
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
    if pathname == '/dashboard':
        # Render the detailed plot view
        return dashboard.serve_layout()
    else:
        # Default to the gallery (Main Entrance)
        return gallery_app.serve_layout()

# if __name__ == '__main__':
#     print("\n" + "="*50)
#     print("🚀 Starting Multi-Page Dash Application!")
#     print("Main Entrance (Gallery): http://127.0.0.1:8050/")
#     print("Detailed Plot Page:      http://127.0.0.1:8050/dashboard")
#     print("="*50 + "\n")
    
#     vipir_app.run(debug=True, port=8050)
# ... the rest of your layout and callbacks ...

if __name__ == '__main__':
    # Still listen locally
    vipir_app.run(host='127.0.0.1', port=8050, debug=False)
