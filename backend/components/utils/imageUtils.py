import numpy as np
import cv2


def parse_image(file_bytes):
    '''
    Decodes image from bytes to ndarray

    **Parameters**:
    - `file` (bytes): Raw image bytes.
    
    **Returns**:
    - `ndarray`: Image decoded into ndarray.
    '''
    file_bytes = np.frombuffer(file_bytes, np.uint8)
    image_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    if img is None:
        raise ValueError("Nie udało się przetworzyć pliku jako obrazu.")
    return img


def encode_image(img_array, encode_format=".png"):
    '''
    Encodes image into bytes from ndarray

    **Parameters**:
    - `img_array` (ndarray): Image decoded into ndarray
    - `format` (str): Optional. Encoding format as file extension. Default .png

    **Returns**:
    - `bytes`: Raw image bytes

    **Raises**:
    - `ValueError` - CV2 failed to encode the image to the format.
    '''

    success, buffer = cv2.imencode(encode_format, img_array)
    if not success:
        raise ValueError(f"Image encoding to {encode_format} failed")
    image_bytes = buffer.tobytes()
    return image_bytes