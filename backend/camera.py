from sign_model import sign_model

def process_frame_for_sign(image_bytes):
    """
    Runs sign detection + prediction for a single captured frame.

    This keeps the public function used by /sign-to-text intact while delegating
    model logic to backend/sign_model.py.
    """
    return sign_model.predict_from_image_bytes(image_bytes)
