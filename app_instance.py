from dash import Dash

# This is the single, shared server instance that all your pages will connect to.
app = Dash(__name__, suppress_callback_exceptions=True)
