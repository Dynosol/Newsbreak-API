import uuid
import time
import random
import requests
import json
import markdown
import re
import urllib.parse
from config import get_common_headers, get_api_base_url

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

def build_article_json(title, article_credit, image_link, image_credit, article_content):
    """
    Build the final JSON string. The article_content is assumed to be in Markdown
    so that formatting like italics, bold, and links is supported.
    This version places the article credit before the article content.
    """
    # Process image credit with Markdown and strip wrapping <p> tags if present
    raw_image_credit = markdown.markdown(image_credit).strip()
    if raw_image_credit.startswith("<p>") and raw_image_credit.endswith("</p>"):
        raw_image_credit = raw_image_credit[3:-4]
    # Create the image block with the image credit embedded
    image_block = create_image_block(image_link, raw_image_credit)
    
    # Process the article content (Markdown to HTML)
    html_content = markdown.markdown(article_content)
    # Wrap paragraphs to the desired <p><span>...</span></p> structure
    html_content = wrap_paragraphs(html_content)
    
    # Process the article credit with Markdown and strip wrapping <p> tags if present
    raw_article_credit = markdown.markdown(article_credit).strip()
    if raw_article_credit.startswith("<p>") and raw_article_credit.endswith("</p>"):
        raw_article_credit = raw_article_credit[3:-4]
    # Build the article credit paragraph and place it before the article content
    article_credit_html = (
        f'<p class="NBAIEditor_Theme__paragraph" dir="ltr" style="text-align: start;">'
        f'<span>{raw_article_credit}</span></p>'
    )
    
    # Combine the article credit and content so that the credit appears first
    combined_content = article_credit_html + html_content
    
    # Define the CSS style block (all on one line to simplify embedding)
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
    
    final_content = image_block + combined_content + style_block
    
    # Build the final article dictionary
    article_dict = {
        "title": title,
        "content": final_content,
        "covers": [image_link] if image_link else [],
        "isEvergreen": False,
        "location": "",
        "locationPid": "",
        "mp_tags_manual": [],
        "editor_version": "1.0"
    }
    
    return article_dict

def create_draft(title, article_credit, image_link, image_credit, article_content, cookies):
    """
    Create a new draft article using the NewsBreak API.
    
    Args:
        title (str): The article title
        article_credit (str): The article credit/byline
        image_link (str): URL of the main image
        image_credit (str): Credit for the main image
        article_content (str): The main article content in Markdown format
        cookies (dict): Dictionary containing required cookies for authentication
    
    Returns:
        tuple: (status_code, response_text, request_id)
    """
    url = f"{get_api_base_url()}/post/draft"
    
    # Generate a unique identifier for x-request-id
    unique_request_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    # Add uniqueness to title and content
    timestamp = int(time.time())
    unique_suffix = f"{timestamp}-{random.randint(1000, 9999)}"
    unique_title = f"{title} [{unique_suffix}]"
    unique_content = f"{article_content}\n\n[Draft ID: {str(uuid.uuid4())}]"
    
    # Get headers from config
    headers = get_common_headers(request_id=unique_request_id, trace_id=trace_id)
    
    # Build the article JSON
    article_dict = build_article_json(
        title=unique_title,
        article_credit=article_credit,
        image_link=image_link,
        image_credit=image_credit,
        article_content=unique_content
    )
    
    # Make the API request
    response = requests.post(url, json=article_dict, headers=headers, cookies=cookies)
    
    return response.status_code, response.text, unique_request_id