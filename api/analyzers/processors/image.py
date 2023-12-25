from langchain_core.messages import HumanMessage

from analyzers import utils


def interrogate_image(image_base64: str, questions: list[str]) -> list[tuple[str, str]]:
    """Returns zipped list of (question, response) for the provided image content."""

    chat_model = utils.chat_llm(model="bakllava")

    responses = []
    # Call the chat model with both messages and images
    for question in questions:
        content_parts = []
        image_part = {
            "type": "image_url",
            "image_url": f"data:image/jpeg;base64,{image_base64}",
        }
        text_part = {
            "type": "text",
            "text": question,
        }

        content_parts.append(image_part)
        content_parts.append(text_part)
        prompt = [HumanMessage(content=content_parts)]
        response = chat_model(prompt)  # type: ignore
        responses.append((question, response.content))

    return responses


if __name__ == "__main__":
    import os
    import pathlib
    import base64
    from io import BytesIO
    from PIL import Image

    def _convert_to_base64(pil_image):
        """
        Convert PIL images to Base64 encoded strings

        :param pil_image: PIL image
        :return: Re-sized Base64 string
        """

        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG")  # You can change the format if needed
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str

    file_path = pathlib.Path(os.path.dirname(__file__)) / "test_img.jpeg"
    pil_image = Image.open(file_path)

    image_b64 = _convert_to_base64(pil_image)

    for question, response in interrogate_image(
        image_base64=image_b64,
        questions=[
            "What is the Dollar-based gross retention rate?",
            "What is the Dollar-based net retention rate?",
        ],
    ):
        print(question)
        print("\t" + response)
        print("\n")
