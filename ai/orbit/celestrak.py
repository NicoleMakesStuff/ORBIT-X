import requests


BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"


def get_tle(norad_id):
    params = {
        "CATNR": norad_id,
        "FORMAT": "TLE"
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=15
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"CelesTrak request failed: "
            f"{response.status_code}"
        )

    lines = [
        line.strip()
        for line in response.text.splitlines()
        if line.strip()
    ]

    if len(lines) < 3:
        raise RuntimeError(
            f"Invalid TLE response for NORAD {norad_id}"
        )

    return {
        "name": lines[0],
        "line1": lines[1],
        "line2": lines[2]
    }


if __name__ == "__main__":

    tle = get_tle(25544)

    print("Satellite:", tle["name"])
    print("Line 1:", tle["line1"])
    print("Line 2:", tle["line2"])