import requests
from config import API_BASE


def send_otp(phone: str) -> tuple[dict, int]:
    """
    POST /api/v1/auth/send-otp
    Triggers OTP generation for the given phone number.

    Because real SMS is mocked, the backend returns the OTP code directly
    in the response so we can display it to the user during development.

    Returns (response_dict, http_status_code).
    """
    try:
        resp = requests.post(
            f"{API_BASE}/v1/auth/send-otp",
            json={"phone": phone},
            timeout=10,
        )
        return resp.json(), resp.status_code
    except requests.exceptions.ConnectionError:
        return {"detail": "Cannot reach the backend. Is the server running?"}, 503
    except requests.exceptions.Timeout:
        return {"detail": "Request timed out. Please try again."}, 504


def verify_otp(phone: str, otp_code: str) -> tuple[dict, int]:
    """
    POST /api/v1/auth/verify-otp
    Validates the OTP and returns a JWT access token.

    On success the response contains:
      access_token : str  — JWT to include in Authorization header
      is_new_user  : bool — True if this is the first login for this phone
    """
    try:
        resp = requests.post(
            f"{API_BASE}/v1/auth/verify-otp",
            json={"phone": phone, "otp": otp_code},
            timeout=10,
        )
        return resp.json(), resp.status_code
    except requests.exceptions.ConnectionError:
        return {"detail": "Cannot reach the backend. Is the server running?"}, 503
    except requests.exceptions.Timeout:
        return {"detail": "Request timed out. Please try again."}, 504
