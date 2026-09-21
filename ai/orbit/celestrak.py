import requests


BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"


def get_tle(norad_id):
    """
    Fetch the latest TLE for a satellite from CelesTrak.

    Parameters
    ----------
    norad_id : int
        NORAD catalog number.

    Returns
    -------
    dict
        Satellite name and TLE lines.
    """

    params = {
        "CATNR": norad_id,
        "FORMAT": "TLE"
    }

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=60
        )

    except requests.RequestException as error:
        raise RuntimeError(
            f"CelesTrak request failed for NORAD {norad_id}: {error}"
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"CelesTrak returned HTTP {response.status_code} "
            f"for NORAD {norad_id}"
        )

    lines = [
        line.strip()
        for line in response.text.splitlines()
        if line.strip()
    ]

    if len(lines) < 3:
        raise RuntimeError(
            f"Invalid CelesTrak response for NORAD {norad_id}: "
            f"expected at least 3 lines"
        )

    return {
        "name": lines[0],
        "line1": lines[1],
        "line2": lines[2]
    }