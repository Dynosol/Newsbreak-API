import uuid
import requests
import json
import urllib.parse
import logging
from config import get_common_headers

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_image_block(image_url, credit_text, width=1500, height=993):
    """
    Create the HTML block for the image using a data-editornodeinfo attribute
    that contains URL-encoded JSON metadata.
    """
    info_dict = {
        "type": "editor-image-node",
        "imageUrl": image_url,
        "imageCaption": "",
        "creditText": credit_text,
        "creditUrl": "",
        "imagePlatform": "SELF_UPLOAD",
        "imageOriginalWidth": width,
        "imageOriginalHeight": height
    }
    info_str = urllib.parse.quote(json.dumps(info_dict))
    
    image_block = (
        f'<figure>'
        f'<div data-editornodeinfo="{info_str}">'
        f'<div class="editor-image-wrap">'
        f'<div class="editor-image">'
        f'<img class="" src="{image_url}" '
        f'data-image-caption="" '
        f'data-credit-text="{credit_text}" '
        f'data-credit-url="" '
        f'data-image-platform="SELF_UPLOAD" '
        f'data-image-original-width="{width}" '
        f'data-image-original-height="{height}">'
        f'</div>'
        f'<span class="image-introduction-wrap">'
        f'<span class="photo-by">Photo by</span>'
        f'<span class="credit-text">{credit_text}</span>'
        f'</span>'
        f'</div>'
        f'</div>'
        f'</figure>'
    )
    return image_block

def wrap_paragraph(text, align="start"):
    """Wrap text in a properly formatted paragraph block."""
    return (
        f'<p class="NBAIEditor_Theme__paragraph" dir="ltr" style="text-align: {align};">'
        f'<span>{text}</span></p>'
    )

def make_put_request(article_id: str, title: str, content: str, cookies: dict):
    """
    Make a PUT request to update an article.
    
    Args:
        article_id (str): The ID of the article to update
        title (str): The article title
        content (str): The article content in HTML format
        cookies (dict): Dictionary containing required cookies for authentication
    
    Returns:
        tuple: (status_code, response_text, request_id)
    """
    url = f"https://creators.newsbreak.com/api/post/draft/{article_id}"
    
    # Generate a unique request ID and trace ID
    unique_request_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4()).replace('-', '')[:32]
    
    # Get headers from config
    headers = get_common_headers(request_id=unique_request_id, trace_id=trace_id)
    headers["Referer"] = f"https://creators.newsbreak.com/new-editor/{article_id}"
    
    payload = {
        "title": title,
        "content": content
    }
    
    # Log request details
    logger.debug(f"Making PUT request to URL: {url}")
    logger.debug(f"Request ID: {unique_request_id}")
    logger.debug(f"Headers: {json.dumps(headers, indent=2)}")
    logger.debug(f"Cookies: {json.dumps(cookies, indent=2)}")
    logger.debug(f"Payload length: {len(json.dumps(payload))} bytes")
    logger.debug(f"Content length: {len(content)} characters")
    
    try:
        # Make the PUT request
        response = requests.put(url, json=payload, headers=headers, cookies=cookies)
        
        # Log response details
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
        logger.debug(f"Response content type: {response.headers.get('content-type', 'unknown')}")
        logger.debug(f"Response length: {len(response.text)} bytes")
        
        if response.status_code != 200:
            logger.error(f"Request failed with status {response.status_code}")
            logger.error(f"Response preview: {response.text[:500]}...")
        
        return response.status_code, response.text, unique_request_id
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed with error: {str(e)}")
        raise 