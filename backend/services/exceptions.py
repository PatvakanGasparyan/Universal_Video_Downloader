"""Structured domain exceptions and yt-dlp error classification.

The whole point of this module is that **raw yt-dlp exceptions never reach the
user**. Every failure is translated into a :class:`DownloaderError` carrying a
stable machine-readable ``error`` code, a human ``message`` and an actionable
``solution``. API handlers turn these into a consistent JSON envelope:

    {
      "success": false,
      "error": "youtube_auth_required",
      "message": "Authentication required.",
      "solution": "Upload cookies.txt or sign in to YouTube."
    }
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class DownloaderError(Exception):
    """Base class for all user-facing downloader errors.

    Attributes:
        error: Stable machine-readable code (snake_case).
        message: Short human-readable description (safe to show to users).
        solution: Actionable hint on how to resolve the problem.
        http_status: Suggested HTTP status code for API responses.
        debug: Optional raw detail kept for logs only (never sent to clients).
    """

    error: str = "download_failed"
    message: str = "The download could not be completed."
    solution: str = "Please try again later."
    http_status: int = 422
    debug: str = ""

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def to_dict(self) -> dict[str, object]:
        """Return the public JSON envelope (never includes ``debug``)."""
        return {
            "success": False,
            "error": self.error,
            "message": self.message,
            "solution": self.solution,
        }


class AuthRequiredError(DownloaderError):
    """Site requires authentication / cookies (e.g. YouTube bot check)."""

    def __init__(self, debug: str = "", site: str = "YouTube") -> None:
        super().__init__(
            error="youtube_auth_required" if site.lower() == "youtube" else "auth_required",
            message="Authentication required.",
            solution=(
                "Upload cookies.txt in Settings (or sign in to the site in your "
                "browser and export fresh cookies), then try again."
            ),
            http_status=401,
            debug=debug,
        )


class VideoUnavailableError(DownloaderError):
    def __init__(self, debug: str = "") -> None:
        super().__init__(
            error="video_unavailable",
            message="This video is unavailable.",
            solution=(
                "The video may be private, deleted, or region-locked. "
                "Check the URL in a browser."
            ),
            http_status=404,
            debug=debug,
        )


class GeoRestrictedError(DownloaderError):
    def __init__(self, debug: str = "") -> None:
        super().__init__(
            error="geo_restricted",
            message="This content is not available in the server's region.",
            solution="Provide cookies from an allowed region or use a different source.",
            http_status=451,
            debug=debug,
        )


class RateLimitedError(DownloaderError):
    def __init__(self, debug: str = "") -> None:
        super().__init__(
            error="rate_limited",
            message="The source is rate-limiting requests.",
            solution="Wait a minute and try again. Providing cookies often helps.",
            http_status=429,
            debug=debug,
        )


class UnsupportedURLError(DownloaderError):
    def __init__(self, debug: str = "") -> None:
        super().__init__(
            error="unsupported_url",
            message="This URL is not supported.",
            solution="Make sure it is a direct link to a video on a supported site.",
            http_status=400,
            debug=debug,
        )


class NetworkError(DownloaderError):
    def __init__(self, debug: str = "") -> None:
        super().__init__(
            error="network_error",
            message="A network error occurred while contacting the source.",
            solution="Check the server's internet connection and try again.",
            http_status=502,
            debug=debug,
        )


class InvalidURLError(DownloaderError):
    def __init__(self, message: str = "Invalid URL.", debug: str = "") -> None:
        super().__init__(
            error="invalid_url",
            message=message,
            solution="Paste a valid http(s) video URL.",
            http_status=400,
            debug=debug,
        )


class DownloadCancelledError(DownloaderError):
    def __init__(self, debug: str = "") -> None:
        super().__init__(
            error="cancelled",
            message="The download was cancelled.",
            solution="Start the download again if this was not intentional.",
            http_status=409,
            debug=debug,
        )


# --- Classification -------------------------------------------------------

_AUTH_PATTERNS = (
    "sign in to confirm you're not a bot",
    "sign in to confirm youre not a bot",
    "confirm you're not a bot",
    "confirm youre not a bot",
    "sign in to confirm your age",
    "use --cookies",
    "cookies-from-browser",
    "login required",
    "requested format is not available",  # often a symptom of anonymous throttling
    "please sign in",
    "account associated with this",
)
_UNAVAILABLE_PATTERNS = (
    "video unavailable",
    "this video is not available",
    "video is private",
    "private video",
    "has been removed",
    "no longer available",
    "http error 404",
    "not found",
    "unable to download options json",
)
_GEO_PATTERNS = (
    "not available in your country",
    "geo restricted",
    "geo-restricted",
    "blocked it in your country",
)
_RATE_PATTERNS = (
    "http error 429",
    "too many requests",
    "rate-limit",
    "rate limit",
)
_UNSUPPORTED_PATTERNS = (
    "unsupported url",
    "is not a valid url",
    "no suitable extractor",
    "no video formats found",
)
_NETWORK_PATTERNS = (
    "timed out",
    "timeout",
    "connection reset",
    "connection aborted",
    "temporary failure in name resolution",
    "failed to resolve",
    "http error 5",
    "network is unreachable",
    "urlopen error",
    "read operation timed out",
)


def _contains(haystack: str, needles: tuple[str, ...]) -> bool:
    return any(n in haystack for n in needles)


def is_auth_error(message: str) -> bool:
    """Return True when the failure looks solvable by providing cookies."""
    low = (message or "").lower()
    return _contains(low, _AUTH_PATTERNS) or _contains(low, _RATE_PATTERNS)


def classify_ytdlp_error(exc: Exception, *, url: str = "") -> DownloaderError:
    """Translate an arbitrary yt-dlp / network exception into a DownloaderError.

    Never returns the raw message to the user; the original text is preserved
    only in ``debug`` for server-side logs.
    """
    if isinstance(exc, DownloaderError):
        return exc

    raw = str(exc)
    low = raw.lower()
    site = "YouTube" if "youtube" in low or "youtu.be" in (url or "").lower() else "the site"

    if _contains(low, _AUTH_PATTERNS):
        return AuthRequiredError(debug=raw, site="youtube" if site == "YouTube" else site)
    if _contains(low, _GEO_PATTERNS):
        return GeoRestrictedError(debug=raw)
    if _contains(low, _RATE_PATTERNS):
        return RateLimitedError(debug=raw)
    if _contains(low, _UNSUPPORTED_PATTERNS):
        return UnsupportedURLError(debug=raw)
    if _contains(low, _NETWORK_PATTERNS):
        return NetworkError(debug=raw)
    if _contains(low, _UNAVAILABLE_PATTERNS):
        return VideoUnavailableError(debug=raw)

    return DownloaderError(
        error="download_failed",
        message="The video could not be processed.",
        solution="Verify the URL and try again. Some sites need cookies to work.",
        http_status=422,
        debug=raw,
    )


def is_transient(error: DownloaderError) -> bool:
    """Whether an outer retry could plausibly help."""
    return error.error in {"network_error", "rate_limited"}


_SCHEME_RE = re.compile(r"^https?://", re.IGNORECASE)


def looks_like_url(value: str) -> bool:
    return bool(_SCHEME_RE.match((value or "").strip()))
