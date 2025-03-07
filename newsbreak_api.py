from helpers.generate_draft import create_draft
from helpers.upload_image import upload_image
from helpers.make_publish import make_publish, PublishError
from helpers.calculate import calculate_nlp
from helpers.put_request import make_put_request
from helpers.config import get_cookies
import json
import sys
import logging
import argparse
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class ArticleConfig:
    # Default values
    title: str = "Draft content..."
    author_name: str = "Temp author"
    author_url: str = "harvard.edu"
    article_credit: str = "Temp byline..."
    image_link: str = "https://i.prt.news/5eb5d392dc405ff764223dd90d0b1ffc.jpg" # doesn't work without this for some reason
    image_credit: str = "testing_credit!"
    content_file: str = "./example_article_content.txt"
    image_file: str = "./example_image.jpg"

def parse_args() -> ArticleConfig:
    parser = argparse.ArgumentParser(description='NewsBreak API Article Publisher')
    parser.add_argument('--title', help='Article title')
    parser.add_argument('--author-name', help='Author name')
    parser.add_argument('--author-url', help='Author URL')
    parser.add_argument('--article-credit', help='Article credit/byline')
    parser.add_argument('--image-link', help='Image link URL')
    parser.add_argument('--image-credit', help='Image credit')
    parser.add_argument('--content-file', help='Path to content file (default: ./fake-content.txt)')
    parser.add_argument('--image-file', help='Path to image file (default: ./crimson.jpg)')
    parser.add_argument('--config', help='Path to JSON config file')
    
    args = parser.parse_args()
    config = ArticleConfig()
    
    # If config file is provided, load it first
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config_data = json.load(f)
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            sys.exit(1)
    
    # Command line arguments override config file
    for key, value in vars(args).items():
        if value is not None and hasattr(config, key.replace('-', '_')):
            setattr(config, key.replace('-', '_'), value)
    
    return config

def process_json_response(response_text: str) -> Optional[Dict[str, Any]]:
    """Parse JSON response and handle errors."""
    try:
        data = json.loads(response_text)
        if isinstance(data, dict):
            if data.get('code') != 0:  # Assuming 0 is success code
                logger.error(f"API Error: {data.get('message', 'No error message')}")
                return None
        return data
    except json.JSONDecodeError:
        logger.error(f"Failed to parse response as JSON. Response type: {type(response_text)}")
        logger.error(f"Response content type check - Contains HTML: {'<html' in response_text.lower()}")
        logger.error(f"First 500 characters: {response_text[:500]}...")
        
        # Try to extract any error messages from HTML
        if '<html' in response_text.lower():
            import re
            error_pattern = re.compile(r'<div[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</div>', re.IGNORECASE)
            matches = error_pattern.findall(response_text)
            if matches:
                logger.error("Found error messages in HTML:")
                for msg in matches:
                    logger.error(f"- {msg.strip()}")
        return None

def main():
    config = parse_args()
    
    # Validate content file exists
    content_path = Path(config.content_file)
    if not content_path.exists():
        logger.error(f"Content file not found: {config.content_file}")
        sys.exit(1)
    
    # Read article content
    try:
        with open(content_path, 'r') as f:
            article_content = f.read()
    except Exception as e:
        logger.error(f"Error reading content file: {e}")
        sys.exit(1)
    
    # Get cookies from environment variables
    cookies = get_cookies()

    try:
        # 1. Generate a draft request
        print("\n=== Creating Draft ===")
        print("Input Parameters:")
        print(f"  title: {config.title}")
        print(f"  article_credit: {config.article_credit}")
        print(f"  image_link: {config.image_link}")
        print(f"  image_credit: {config.image_credit}")
        print(f"  content_file: {config.content_file}")
        print(f"  content preview: {article_content[:200]}...")
        
        status_code, response_text, request_id = create_draft(
            title=config.title,
            article_credit=config.article_credit,
            image_link=config.image_link,
            image_credit=config.image_credit,
            article_content=article_content,
            cookies=cookies
        )

        print(f"Draft Creation Status: {status_code}")
        print(f"Draft Request ID: {request_id}")

        # Process draft response
        draft_data = process_json_response(response_text)
        if not draft_data:
            print("Failed to create draft")
            sys.exit(1)

        data_id = draft_data.get("data")
        if not data_id:
            print("No data_id in draft response")
            sys.exit(1)

        print(f"Got data_id: {data_id}")

        # 2. Upload image
        print("\n=== Uploading Image ===")
        image_path = config.image_file
        print("Input Parameters:")
        print(f"  image_path: {image_path}")
        print(f"  data_id: {data_id}")
        print(f"  cookies: {json.dumps(cookies, indent=2)}")
        
        image_status, image_response, image_request_id = upload_image(
            image_path=image_path,
            data_id=data_id,
            cookies=cookies
        )

        print(f"Image Upload Status: {image_status}")
        print(f"Image Request ID: {image_request_id}")

        # Process image response
        image_data = process_json_response(image_response)
        if not image_data:
            print("Failed to upload image")
            sys.exit(1)

        image_url = image_data.get("data")
        if not image_url:
            print("No image URL in response")
            sys.exit(1)

        print(f"Uploaded image URL: {image_url}")

        # 3. Update article content with PUT request
        print("\n=== Updating Article Content ===")
        try:
            # First verify we have valid content
            with open(content_path, "r") as f:
                content = f.read()
            if not content.strip():
                logger.error("Content file is empty")
                sys.exit(1)
            
            print("Input Parameters:")
            print(f"  article_id: {data_id}")
            print(f"  title: {config.title}")
            print(f"  content (first 200 chars): {article_content[:200]}...")
            print(f"  cookies: {json.dumps(cookies, indent=2)}")
            
            logger.info(f"Content length: {len(content)} characters")
            logger.info(f"Article ID for PUT request: {data_id}")
            
            put_status, put_response, put_request_id = make_put_request(
                article_id=data_id,
                title=config.title,
                content=article_content,
                cookies=cookies
            )

            print(f"Content Update Status: {put_status}")
            print(f"Content Update Request ID: {put_request_id}")

            # Process PUT response
            if put_status != 200:
                logger.error(f"PUT request failed with status {put_status}")
                logger.error(f"Response: {put_response[:500]}...")
                sys.exit(1)

            # Check for HTML response which indicates session expiration
            if isinstance(put_response, str) and ('<html' in put_response.lower() or put_response.strip().startswith('<!DOCTYPE')):
                logger.error("Session expired - received HTML login page")
                logger.error("Please refresh your session cookies and try again")
                sys.exit(1)

            # Try to parse response as JSON
            try:
                put_data = json.loads(put_response)
                if isinstance(put_data, dict) and put_data.get('code') != 0:
                    logger.error(f"API Error: {put_data.get('message', 'Unknown error')}")
                    sys.exit(1)
            except json.JSONDecodeError:
                logger.error("Failed to parse response as JSON")
                logger.error(f"Response preview: {put_response[:500]}...")
                sys.exit(1)

        except FileNotFoundError:
            logger.error("Could not find fake-content.txt file")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error during PUT request: {str(e)}")
            sys.exit(1)

        # 4. Calculate NLP metrics
        print("\n=== Calculating NLP Metrics ===")
        nlp_status, nlp_response, nlp_request_id = calculate_nlp(
            post_id=int(data_id),
            cookies=cookies
        )

        print(f"NLP Calculation Status: {nlp_status}")
        print(f"NLP Request ID: {nlp_request_id}")

        if nlp_response.get("code") == 0 and nlp_response.get("status") == "success":
            print("NLP calculation completed successfully")
        else:
            print(f"NLP calculation failed: {nlp_response.get('message', 'Unknown error')}")
            sys.exit(1)

        # 5. Publish article
        print("\n=== Publishing Article ===")
        try:
            publish_status, publish_response, publish_request_id = make_publish(
                title=config.title,
                author_name=config.author_name,
                author_url=config.author_url,
                article_credit=config.article_credit,
                image_link=image_url, # NOT image_link
                image_credit=config.image_credit,
                article_content=article_content,
                data_id=data_id,
                cookies=cookies
            )

            print(f"Publish Status: {publish_status}")
            print(f"Publish Request ID: {publish_request_id}")

            # Try to parse and print response nicely
            try:
                response_data = json.loads(publish_response)
                print("Publish Response:", json.dumps(response_data, indent=2))
            except json.JSONDecodeError:
                if '<html' in publish_response.lower():
                    print("Error: Received HTML response - Session may have expired")
                    print("Response preview:", publish_response[:200] + "...")
                else:
                    print("Raw Response:", publish_response[:200] + "..." if len(publish_response) > 200 else publish_response)

        except PublishError as e:
            print(f"Publishing failed: {e.message}")
            if e.status_code:
                print(f"Status code: {e.status_code}")
            if e.response_text:
                print(f"Response preview: {e.response_text[:200]}...")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 