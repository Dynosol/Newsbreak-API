import uuid
import requests
import json
from typing import Dict, Tuple, Optional

def calculate_nlp(post_id: int, cookies: Dict[str, str]) -> Tuple[int, Dict[str, str], str]:
    """
    Calculate NLP metrics for a draft post using the NewsBreak API.
    
    Args:
        post_id (int): The draft post ID to calculate NLP metrics for
        cookies (dict): Dictionary containing required cookies for authentication
    
    Returns:
        tuple: (status_code, response_dict, request_id)
            - status_code (int): HTTP status code
            - response_dict (dict): Parsed JSON response with keys:
                - code (int): 0 for success
                - status (str): "success" for successful calculation
                - message (str): Additional message if any
            - request_id (str): Unique request identifier
    """
    url = "https://creators.newsbreak.com/api/nlp/calculate"
    
    # Generate a unique identifier for x-request-id
    unique_request_id = str(uuid.uuid4())
    
    # Generate trace ID
    trace_id = str(uuid.uuid4())
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://creators.newsbreak.com",
        "Referer": f"https://creators.newsbreak.com/new-editor/{post_id}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/133.0.0.0 Safari/537.36"
        ),
        "baggage": (
            "sentry-environment=production,"
            "sentry-public_key=2a36b78bfa56a1119bb592db18f7f77a,"
            f"sentry-trace_id={trace_id}"
        ),
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sentry-trace": f"{trace_id}-{unique_request_id[:16]}",
        "x-request-id": unique_request_id,
    }
    
    # Build the payload with the post_id
    payload = {
        "post_id": post_id
    }
    
    # Make the API request
    response = requests.post(url, json=payload, headers=headers, cookies=cookies)
    
    # Parse the JSON response
    try:
        response_dict = json.loads(response.text)
    except json.JSONDecodeError:
        response_dict = {"code": -1, "status": "error", "message": "Failed to parse JSON response"}
    
    return response.status_code, response_dict, unique_request_id

def main():
    """Example usage of the calculate_nlp function."""
    cookies = {
        "__nbpix_uid": "1-npo3dbk7-m6v613v5",
        "media_id": "1641912",
        "media_id.sig": "YMvjHElH0nRRCHMxTmXlksoME6o",
        "mp_session": "bd35be32-9efd-45e2-8543-01e1ebf5d8dc",
        "mp_session.sig": "i3h6tciLWD0dcNwqrPQZZPR1ZdY",
    }
    
    # Example post_id
    post_id = 100251263
    
    status_code, response_dict, request_id = calculate_nlp(post_id, cookies)
    print(f"Status Code: {status_code}")
    print(f"Request ID: {request_id}")
    print(f"Response: {json.dumps(response_dict, indent=2)}")
    
    if response_dict.get("code") == 0 and response_dict.get("status") == "success":
        print("NLP calculation completed successfully")
    else:
        print(f"NLP calculation failed: {response_dict.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()