_LIKELIHOOD = (
    "UNKNOWN",
    "VERY_UNLIKELY",
    "UNLIKELY",
    "POSSIBLE",
    "LIKELY",
    "VERY_LIKELY",
)


def detect_safe_search(filepath: str) -> tuple[bool, str]:
    """Detects unsafe features in the file. Blocking — run via asyncio.to_thread."""
    from google.cloud import vision

    client = vision.ImageAnnotatorClient.from_service_account_file("google_key.json")

    with open(filepath, "rb") as f:
        content = f.read()

    image = vision.Image(content=content)
    response = client.safe_search_detection(image=image)  # type: ignore

    if response.error.message:
        raise Exception(response.error.message)

    safe = response.safe_search_annotation

    passed = all(1 <= val <= 2 for val in [safe.adult, safe.medical, safe.spoof, safe.violence, safe.racy])

    details = (
        f"adult: {_LIKELIHOOD[safe.adult]}\n"
        f"medical: {_LIKELIHOOD[safe.medical]}\n"
        f"spoof: {_LIKELIHOOD[safe.spoof]}\n"
        f"violence: {_LIKELIHOOD[safe.violence]}\n"
        f"racy: {_LIKELIHOOD[safe.racy]}"
    )

    return passed, details
