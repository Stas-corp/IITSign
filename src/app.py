import logging
from dotenv import load_dotenv, find_dotenv

from src.web.app import StreamlitApp

load_dotenv(find_dotenv(), override=True)

logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s %(levelname)s [%(module)s:%(funcName)s] %(message)s'
    )     

app = StreamlitApp()
app.run()