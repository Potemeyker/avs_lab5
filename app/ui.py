import os
import io
from PIL import Image

import requests
import gradio as gr

from typing import Optional, Tuple, Union


API_URL = os.getenv("API_URL", "http://localhost:5000")
UI_PORT = int(os.getenv("UI_PORT", 7860))


def find_similar(image):
    """
    Отправляет изображение в API /similar и возвращает результаты.
    """
    if image is None:
        return None

    # Открываем файл для отправки
    try:
        with open(image, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_URL}/similar", files=files)

        if response.status_code == 200:
            data = response.json()
            results = data.get("similar", [])

            formatted_results = [
                [item['id'], round(item['distance'], 4)]
                for item in results
            ]
            return formatted_results
        else:
            return f"Error: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Connection Error: {str(e)}"


def upload_cat(image):
    """
    Загружает нового котика в базу через API /upload.
    """
    if image is None:
        return "Please select an image."

    try:
        with open(image, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_URL}/upload", files=files)

        if response.status_code == 200:
            return response.json()
        else:
            return f"Error: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Connection Error: {str(e)}"


if __name__ == "__main__":
    with gr.Blocks(title="Cat Finder Service") as demo:
        gr.Markdown("# Поиск похожих котиков")
        gr.Markdown("Загрузи фото котика, и нейросеть найдет его братьев по разуму.")

        with gr.Tab("Найти похожего"):
            with gr.Row():
                with gr.Column():
                    search_input = gr.Image(type="filepath", label="Загрузите фото котика")
                    search_btn = gr.Button("Найти!", variant="primary")

                with gr.Column():
                    search_output = gr.Dataframe(
                        headers=["ID котика", "Расстояние (чем меньше, тем ближе)"],
                        label="Результаты поиска"
                    )

            search_btn.click(fn=find_similar, inputs=search_input, outputs=search_output)

        with gr.Tab("Добавить котика в базу"):
            with gr.Row():
                with gr.Column():
                    upload_input = gr.Image(type="filepath", label="Новый котик")
                    upload_btn = gr.Button("Загрузить", variant="secondary")

                with gr.Column():
                    upload_output = gr.JSON(label="Статус загрузки")

            upload_btn.click(fn=upload_cat, inputs=upload_input, outputs=upload_output)

    demo.launch(server_name="0.0.0.0", server_port=UI_PORT)
