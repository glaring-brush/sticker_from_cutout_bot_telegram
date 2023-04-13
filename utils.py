from io import BytesIO
import requests
from PIL import Image

MAX_CANVAS_SIDE_SIZE_PX = 512


def download_image_and_convert_to_webp(image_url, headers={}) -> BytesIO:
    response = requests.get(image_url, headers=headers)
    if not response.ok:
        print(response)
        breakpoint()
        return None

    image = Image.open(BytesIO(response.content))

    image_width, image_height = image.size

    scale_factor = 1
    if image_width > image_height:
        scale_factor = image_width / MAX_CANVAS_SIDE_SIZE_PX
    else:
        scale_factor = image_height / MAX_CANVAS_SIDE_SIZE_PX

    resized_width, resized_height = (
        int(image_width * scale_factor),
        int(image_height * scale_factor),
    )

    image.resize((resized_width, resized_height))

    in_memory_file = BytesIO()
    image.save(in_memory_file, format="webp")

    return in_memory_file.getvalue()


if __name__ == "__main__":
    file_object: BytesIO = download_image_and_convert_to_webp(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/Coat_of_Arms_of_UNR.svg/679px-Coat_of_Arms_of_UNR.svg.png",
        headers={
            "User-Agent": "Sticker from cutout (png/webp) bot/0.1 (https://t.me/sticker_from_cutout_bot/) python-requests/2.28.2"
        },
    )
    with open("sticker.webp", "wb") as sticker_file:
        sticker_file.write(file_object)
