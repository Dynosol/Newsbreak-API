import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

def get_cookies():
    """Get cookies from environment variables."""
    return {
        "__nbpix_uid": os.getenv("NBPIX_UID"),
        "media_id": os.getenv("MEDIA_ID"),
        "media_id.sig": os.getenv("MEDIA_ID_SIG"),
        "mp_session": os.getenv("MP_SESSION"),
        "mp_session.sig": os.getenv("MP_SESSION_SIG"),
    }

def get_common_headers(request_id=None, trace_id=None):
    """
    Get common headers from environment variables.
    
    Args:
        request_id (str, optional): Custom request ID. If None, one will be generated.
        trace_id (str, optional): Custom trace ID. If None, one will be generated.
    """
    if not request_id:
        request_id = str(uuid.uuid4())
    if not trace_id:
        trace_id = str(uuid.uuid4()).replace('-', '')[:32]
    span_id = str(uuid.uuid4()).replace('-', '')[:16]
    
    return {
        "Accept": os.getenv("ACCEPT"),
        "Accept-Language": os.getenv("ACCEPT_LANGUAGE"),
        "Connection": "keep-alive",
        "Content-Type": os.getenv("CONTENT_TYPE"),
        "Origin": os.getenv("ORIGIN"),
        "Referer": f"{os.getenv('REFERER_BASE')}/new-editor",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": os.getenv("USER_AGENT"),
        "baggage": (
            f"sentry-environment={os.getenv('SENTRY_ENVIRONMENT')},"
            f"sentry-public_key={os.getenv('SENTRY_PUBLIC_KEY')},"
            f"sentry-trace_id={trace_id}"
        ),
        "sec-ch-ua": os.getenv("SEC_CH_UA"),
        "sec-ch-ua-mobile": os.getenv("SEC_CH_UA_MOBILE"),
        "sec-ch-ua-platform": os.getenv("SEC_CH_UA_PLATFORM"),
        "sentry-trace": f"{trace_id}-{span_id}",
        "x-request-id": request_id,
    }

def get_api_base_url():
    """Get base API URL."""
    return f"{os.getenv('ORIGIN')}/api" 