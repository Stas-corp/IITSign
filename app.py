import logging

from src.web.app import StreamlitApp

logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s %(levelname)s [%(module)s:%(funcName)s] %(message)s'
    )     

app = StreamlitApp()
app.run()