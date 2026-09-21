import math


EARTH_RADIUS_KM = 6378.137

EARTH_EQUATORIAL_RADIUS = 6378.137
EARTH_POLAR_RADIUS = 6356.7523142


def gmst(jd):

    T = (jd - 2451545.0) / 36525.0

    gmst_deg = (
        280.46061837
        + 360.98564736629 * (jd - 2451545.0)
        + 0.000387933 * T * T
        - (T ** 3) / 38710000.0
    )

    return math.radians(
        gmst_deg % 360
    )


def teme_to_ecef(
    x,
    y,
    z,
    jd
):

    theta = gmst(jd)

    x_ecef = (
        x * math.cos(theta)
        + y * math.sin(theta)
    )

    y_ecef = (
        -x * math.sin(theta)
        + y * math.cos(theta)
    )

    z_ecef = z

    return (
        x_ecef,
        y_ecef,
        z_ecef
    )


def ecef_to_geodetic(
    x,
    y,
    z
):

    a = EARTH_EQUATORIAL_RADIUS
    b = EARTH_POLAR_RADIUS

    e2 = (
        a * a - b * b
    ) / (a * a)

    longitude = math.atan2(
        y,
        x
    )

    p = math.sqrt(
        x * x + y * y
    )

    latitude = math.atan2(
        z,
        p * (1 - e2)
    )

    for _ in range(10):

        N = a / math.sqrt(
            1
            - e2
            * math.sin(latitude) ** 2
        )

        altitude = (
            p / math.cos(latitude)
        ) - N

        latitude = math.atan2(
            z,
            p * (
                1
                - e2 * N
                / (N + altitude)
            )
        )

    N = a / math.sqrt(
        1
        - e2 * math.sin(latitude) ** 2
    )

    altitude = (
        p / math.cos(latitude)
    ) - N

    return (
        math.degrees(latitude),
        math.degrees(longitude),
        altitude
    )