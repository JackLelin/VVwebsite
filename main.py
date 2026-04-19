from dash import html, dcc, Input, Output
from app_instance import app

# Import the layouts and callbacks from our separate files
import dashboard
import gallery_app

# The Master Router Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# The Router Callback
@app.callback(
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

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Starting Multi-Page Dash Application!")
    print("Main Entrance (Gallery): http://127.0.0.1:8050/")
    print("Detailed Plot Page:      http://127.0.0.1:8050/dashboard")
    print("="*50 + "\n")
    
    app.run(debug=True, port=8050)
