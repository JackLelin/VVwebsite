import sys
import logging

# Log errors to the Apache error log
logging.basicConfig(stream=sys.stderr)

# Add your project directory to the Python path so it can find your modules
# (Make sure this matches the actual path where main.py lives)
sys.path.insert(0, '/rd0/home/linle2/vvwebsite/')

# 1. Import your master Dash app instance from main.py
from main import vipir_app

# 2. Extract the underlying Flask server and name it 'application'
# (mod_wsgi strictly requires the variable to be named 'application')
application = vipir_app.server
