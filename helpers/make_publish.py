import uuid
import json
import requests
import urllib.parse
import markdown
import re
from typing import Dict, Tuple, Union, Optional
from config import get_common_headers, get_api_base_url
import os

class PublishError(Exception):
    """Custom exception for publish-related errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(self.message)

def is_html_response(text: str) -> bool:
    """Check if the response is HTML instead of JSON."""
    return text.strip().startswith('<!') or '<html' in text.lower()

def validate_response(response: requests.Response) -> Tuple[bool, str]:
    """
    Validate the response from the API.
    Returns (is_valid, error_message)
    """
    if response.status_code != 200:
        return False, f"Request failed with status code: {response.status_code}"
    
    try:
        text = response.text.strip()
        if is_html_response(text):
            return False, "Received HTML response instead of JSON. Session may have expired."
        
        # Try to parse as JSON
        data = json.loads(text)
        
        # Check for API-specific error indicators
        if isinstance(data, dict):
            if data.get('code') != 0:  # Assuming 0 is success code
                return False, f"API returned error code: {data.get('code')} - {data.get('message', 'No message')}"
            
        return True, ""
    except json.JSONDecodeError:
        return False, "Failed to parse response as JSON"

def validate_location(location: str) -> None:
    """Validate the location parameter."""
    allowed_locations = ["Entire U.S", "Cambridge, MA", "Boston, MA", "Massachusetts State"]
    if location not in allowed_locations:
        raise ValueError(f"Invalid location. Must be one of: {', '.join(allowed_locations)}")

def create_image_block(image_url, credit_text):
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
        "imageOriginalWidth": 1500,
        "imageOriginalHeight": 1000
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
        f'data-image-original-width="1500" '
        f'data-image-original-height="1000">'
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

def wrap_paragraphs(html_text):
    """
    Find all <p>...</p> paragraphs in the given HTML text and wrap the inner
    content in a <span> while also adding the desired classes and attributes.
    """
    def repl(match):
        inner = match.group(1)
        return (f'<p class="NBAIEditor_Theme__paragraph" dir="ltr" '
                f'style="text-align: start;"><span>{inner}</span></p>')
    
    wrapped = re.sub(r'<p>(.*?)</p>', repl, html_text, flags=re.DOTALL)
    return wrapped

def make_publish(
    title: str,
    author_name: str,
    author_url: str,
    article_credit: str,
    image_link: str,
    image_credit: str,
    article_content: str,
    data_id: str,
    cookies: Dict[str, str],
    location: str = "Entire U.S",
    is_title_rewrited: bool = False,
    is_ai_assisted: bool = False
) -> Tuple[int, str, str]:
    """
    Publish an article to NewsBreak.
    
    Args:
        title (str): Article title
        author_name (str): Author's name
        author_url (str): URL to author's profile
        article_credit (str): Article credit/byline
        image_link (str): URL of the main image
        image_credit (str): Credit for the main image
        article_content (str): Main article content in Markdown
        data_id (str): The draft ID from create_draft
        cookies (dict): Required cookies for authentication
        location (str): Must be one of: "Entire U.S", "Cambridge, MA", "Boston, MA", "Massachusetts State"
        is_title_rewrited (bool): Whether title was rewritten
        is_ai_assisted (bool): Whether AI assisted in writing
    
    Returns:
        tuple: (status_code, response_text, request_id)
    
    Raises:
        PublishError: If the publish operation fails
        ValueError: If input parameters are invalid
    """
    # Input validation
    if not all([title, author_name, article_content, data_id]):
        raise ValueError("Required fields missing: title, author_name, article_content, or data_id")
    
    validate_location(location)
    
    url = f"{get_api_base_url()}/post/publish/{data_id}"
    
    # Generate unique identifiers
    unique_request_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    try:
        # Process image credit
        try:
            raw_image_credit = markdown.markdown(image_credit).strip()
            if raw_image_credit.startswith("<p>") and raw_image_credit.endswith("</p>"):
                raw_image_credit = raw_image_credit[3:-4]
            
            # Process article content
            html_content = markdown.markdown(article_content)
            html_content = wrap_paragraphs(html_content)
            
            # Process article credit
            raw_article_credit = markdown.markdown(article_credit).strip()
            if raw_article_credit.startswith("<p>") and raw_article_credit.endswith("</p>"):
                raw_article_credit = raw_article_credit[3:-4]
        except Exception as e:
            raise PublishError(f"Error processing markdown content: {str(e)}")
        
        # Build content components
        image_block = create_image_block(image_link, raw_image_credit) if image_link else ""
        
        # Empty paragraph
        empty_paragraph = '<p class="NBAIEditor_Theme__paragraph"><br></p>'
        
        # Style block (kept on one line for simplicity)
        style_block = (
            '<style style="display: none">'
            '.NBAIEditor_Theme__ol1 {padding: 0 0 0 20px !important;margin: 0 0 24px 0 !important;list-style-position: outside !important;}'
            '.NBAIEditor_Theme__ol2 {padding: 0 !important;margin: 0 !important;list-style-type: lower-alpha !important;list-style-position: outside !important;}'
            'html body.post #content-div .content ol li ol {margin: 0 !important;}'
            '.NBAIEditor_Theme__ol3 {padding: 0 !important;margin: 0 !important;list-style-type: lower-roman !important;list-style-position: outside !important;}'
            '.NBAIEditor_Theme__ol4 {padding: 0;margin: 0;list-style-type: upper-roman !important;list-style-position: outside !important;}'
            '.NBAIEditor_Theme__ol5 {padding: 0;margin: 0;list-style-type: lower-roman !important;list-style-position: outside !important;}'
            '.NBAIEditor_Theme__ul {padding: 0 !important;margin: 0 !important;margin-left: 20px !important;list-style-position: outside !important;}'
            '@media all and (max-width: 600px) {.NBAIEditor_Theme__ul {margin-left: 14px !important;}}'
            '.NBAIEditor_Theme__ul li .NBAIEditor_Theme__ul li .NBAIEditor_Theme__ul li::before {display: none !important;}'
            '.NBAIEditor_Theme__ul .NBAIEditor_Theme__ul {list-style-type: circle !important;margin-left: 0 !important;}'
            '.NBAIEditor_Theme__ul .NBAIEditor_Theme__ul .NBAIEditor_Theme__ul {list-style-type: square !important;margin-left: 0 !important;}'
            'html body.post #content-div .content ul li ul li ul {margin-left: 0 !important;}'
            '.ContentEditable__root > ul {margin-bottom: 24px;padding: 0 0 0 20px;}'
            '.NBAIEditor_Theme__listItem {margin: 0 !important;padding: 0 !important;}'
            '.NBAIEditor_Theme__nestedListItem {list-style-type: none !important;padding: 0 0 0 24px !important;}'
            '.NBAIEditor_Theme__nestedListItem:before, .NBAIEditor_Theme__nestedListItem:after {display: none;}'
            '.editor-image-wrap {display: flex;flex-direction: column;position: relative;margin: 24px auto 12px;}'
            '.editor-image-wrap .editor-image {position: relative;z-index: 1;cursor: pointer;margin-top: 0;}'
            '.editor-image-wrap .editor-image img {width: 100%;border-radius: 8px;margin-top: 0;}'
            '.editor-image-wrap .image-introduction-wrap {font-size: 14px;line-height: 20px;color: rgba(0, 0, 0, 0.6);margin-top: 12px;user-select: none;}'
            ':root[class~="dark"] .editor-image-wrap .image-introduction-wrap {color: inherit;}'
            '.editor-image-wrap .image-introduction-wrap .image-caption {margin-right: 3px;}'
            '.editor-image-wrap .image-introduction-wrap .photo-by {color: rgba(0, 0, 0, 0.3);}'
            ':root[class~="dark"] .editor-image-wrap .image-introduction-wrap .photo-by {color: rgba(255, 255, 255, .6);}'
            '.editor-image-wrap .image-introduction-wrap .credit-text {margin-left: 6px;}'
            '.editor-image-wrap .image-introduction-wrap .credit-text a {color: rgba(0, 0, 0, 0.6);position: relative;text-decoration: underline;text-underline-offset: 5px;text-decoration-color: rgba(0, 0, 0, 0.3);}'
            ':root[class~="dark"] .editor-image-wrap .image-introduction-wrap .credit-text a {color: rgb(47, 128, 237);text-decoration: none;}'
            '.editor-image-wrap .image-introduction-wrap .text-on {font-size: 14px;line-height: 20px;color: rgba(0, 0, 0, 0.3);margin-left: 6px;}'
            ':root[class~="dark"] .editor-image-wrap .image-introduction-wrap .text-on {color: rgba(255, 255, 255, .6);}'
            '.editor-image-wrap .image-introduction-wrap .link-unsplash-official {position: relative;margin-left: 6px;color: rgba(0, 0, 0, 0.6);text-decoration: underline;text-underline-offset: 5px;text-decoration-color: rgba(0, 0, 0, 0.3);}'
            ':root[class~="dark"] .editor-image-wrap .image-introduction-wrap .link-unsplash-official {color: rgb(47, 128, 237);text-decoration: none;}'
            '.node-embed-wrap {display: flex;justify-content: center;}'
            '.node-embed-wrap .node-embed {position: relative;width: 100%;box-sizing: content-box;}'
            '.node-embed-wrap .node-embed .mask {position: absolute;left: 0;right: 0;top: 0;bottom: 0;background-color: #fff;opacity: 0.5;z-index: 1;}'
            '.node-embed-wrap .node-embed .btn-edit-delete {position: absolute;top: 38px;right: 32px;cursor: pointer;z-index: 2;}'
            '.node-embed-wrap .node-embed:hover {border: 2px solid rgba(36, 81, 255, 0.3);}'
            '.node-embed-wrap .node-embed.selected {border: 2px solid rgba(36, 81, 255, 0.6);}'
            '#node-article-wrap {display: flex;justify-content: center;align-items: center;border-radius: 11px;border: 1px solid #f2f2f2;padding: 18px 32px;}'
            '#node-article-wrap .node-container {width: 100%;}'
            '#node-article-wrap .node-container .title {margin: 0;font-size: 20px;color: var(--main-color);font-weight: 600;line-height: 28px;overflow: hidden;text-overflow: ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient: vertical;}'
            '#node-article-wrap .node-container .info {margin: 0;display: flex;justify-content: flex-start;align-items: center;font-size: 14px;color: var(--secondary-color);line-height: 20px;}'
            '#node-article-wrap .node-container .info .avatar {margin: 0;width: 20px !important;height: 20px;border-radius: 50%;}'
            '#node-article-wrap .node-container .info .media-name {margin-left: 8px;}'
            '#node-article-wrap .node-container .info .date {margin-left: 2px;}'
            '#node-article-wrap .node-container .thumbnail {margin-top: 16px;width: 100%;border-radius: 8px;}'
            '#node-article-wrap.selected {border: 2px solid rgba(36, 81, 255, 0.6);}'
            '.embedcard-twitter {position: relative;display: flex;justify-content: center;align-items: center;flex-direction: column;width: 100%;height: 100%;margin: 0 !important;}'
            '.embedcard-twitter .loading {position: absolute;left: 50%;top: 50%;transform: translate(-50%, -50%);z-index: 9;}'
            '.embedcard-twitter .embed-holder {position: relative;width: 100%;margin: 0 !important;}'
            '.embedcard-twitter .embed-holder .twitter-tweet {margin: 0 !important;}'
            '.embedcard-youtube {position: relative;display: flex;justify-content: center;align-items: center;flex-direction: column;width: 100%;height: 100%;margin: 0 !important;}'
            '.embedcard-youtube .loading {position: absolute;left: 50%;top: 50%;transform: translate(-50%, -50%);z-index: 9;}'
            '.embedcard-youtube .embed-holder {position: relative;width: 100%;height: 0;padding-bottom: 56.25%;margin: 0 !important;}'
            '.embedcard-youtube .embed-holder .iframe {position: absolute;left: 0;top: 0;width: 100%;height: 100%;}'
            '.embedcard-instagram {position: relative;display: flex;justify-content: center;align-items: center;flex-direction: column;width: 100%;height: 100%;margin: 0 !important;}'
            '.embedcard-instagram .loading {position: absolute;left: 50%;top: 50%;transform: translate(-50%, -50%);z-index: 9;}'
            '.embedcard-instagram .embed-holder {position: relative;width: 100%;margin: 0 !important;}'
            '.embedcard-instagram .embed-holder iframe {margin: 0 !important;}'
            '.embedcard-facebook {position: relative;display: flex;justify-content: center;align-items: center;flex-direction: column;width: 100%;height: 100%;margin: 0 !important;}'
            '.embedcard-facebook .loading {position: absolute;left: 50%;top: 50%;transform: translate(-50%, -50%);z-index: 9;}'
            '.embedcard-facebook .embed-holder {position: relative;width: 100%;margin: 0 !important;}'
            '.embedcard-facebook .embed-holder iframe {margin: 0 !important;}'
            '</style>'
        )
        
        # Combine content
        final_content = (
            image_block +
            html_content +
            empty_paragraph +
            style_block
        )
        
        # Build payload
        payload = {
            "content": final_content,
            "mp_tags_manual": [],
            "location": location,
            "locationPid": location,
            "title": title,
            "is_title_rewrited": is_title_rewrited,
            "is_ai_assisted": is_ai_assisted,
            "editor_version": "1.0",
            "covers": [image_link] if image_link else []
        }
        
        # Get headers from config
        headers = get_common_headers(request_id=unique_request_id, trace_id=trace_id)
        headers["Referer"] = f"{os.getenv('REFERER_BASE')}/new-editor/{data_id}"
        
        # Make the request with timeout and retries
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        session.mount('https://', adapter)
        
        response = session.put(
            url,
            json=payload,
            headers=headers,
            cookies=cookies,
            timeout=30
        )
        
        # Validate response
        is_valid, error_message = validate_response(response)
        if not is_valid:
            raise PublishError(
                error_message,
                status_code=response.status_code,
                response_text=response.text
            )
        
        return response.status_code, response.text, unique_request_id
        
    except requests.RequestException as e:
        raise PublishError(f"Network error occurred: {str(e)}")
    except Exception as e:
        raise PublishError(f"Unexpected error: {str(e)}")