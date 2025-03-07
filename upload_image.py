import uuid
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from config import get_common_headers, get_api_base_url
import os

def upload_image(image_path, data_id, cookies):
    """
    Upload an image to the NewsBreak backend.

    Args:
        image_path (str): Path to the local image file.
        data_id (str): The data ID received from create_draft response.
        cookies (dict): Dictionary containing required cookies for authentication.

    Returns:
        tuple: (status_code, response_text, request_id)
    """
    url = f"{get_api_base_url()}/storage/uploadFile"

    # Generate unique IDs for tracking
    unique_request_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    # Use the static boundary from the cURL example.
    boundary = "----WebKitFormBoundaryNGAmcUQFcSTXnpe4"

    # Build the multipart payload with a custom boundary.
    with open(image_path, "rb") as f:
        multipart_data = MultipartEncoder(
            fields={
                "file": ("blob", f, "image/jpeg")
            },
            boundary=boundary
        )

        # Get common headers from config
        headers = get_common_headers(request_id=unique_request_id, trace_id=trace_id)
        # Override Content-Type for multipart data and update referer
        headers["Content-Type"] = multipart_data.content_type
        headers["Referer"] = f"{os.getenv('REFERER_BASE')}/new-editor/{data_id}"

        # Send the POST request with our custom multipart payload.
        response = requests.post(url, headers=headers, cookies=cookies, data=multipart_data)

    return response.status_code, response.text, unique_request_id
