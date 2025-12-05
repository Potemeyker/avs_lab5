from typing import Optional, Tuple, Union
import gradio
from PIL import Image
import io
import os

API_URL = os.getenv("API_URL", "http://localhost:5000")
UI_PORT = os.getenv("UI_PORT", 7860)

if __name__ == "__main__":
    with gradio.Blocks() as demo:
        raise NotImplementedError
        # TODO рeaлизoвaть интepфeйс

    demo.launch(server_name="0.0.0.0", server_port=UI_PORT)
