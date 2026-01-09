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
