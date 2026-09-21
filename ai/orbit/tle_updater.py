from datetime import datetime, timezone


def normalize_datetime(dt):
    """
    Convert a datetime into a timezone-aware UTC datetime.

    MongoDB/PyMongo can sometimes return timezone-naive datetimes,
    while newly generated Python datetimes may be timezone-aware.

    This function makes both formats comparable.
    """

    if dt is None:
        return None

    # If datetime has no timezone information,
    # assume it represents UTC.
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    # Convert timezone-aware datetime to UTC.
    return dt.astimezone(timezone.utc)


def compare_tle_epochs(current_epoch, new_epoch):
    """
    Compare the current database TLE epoch with
    the newly fetched TLE epoch.

    Returns:

        "NEW"    -> new TLE is newer
        "SAME"   -> epochs are identical
        "OLDER"  -> new TLE is older
    """

    current_epoch = normalize_datetime(current_epoch)
    new_epoch = normalize_datetime(new_epoch)

    if new_epoch is None:
        return "OLDER"

    if current_epoch is None:
        return "NEW"

    if new_epoch > current_epoch:
        return "NEW"

    if new_epoch == current_epoch:
        return "SAME"

    return "OLDER"


def save_tle_history(history_collection, satellite):
    """
    Save the satellite's current TLE into tle_history
    before replacing it with a newer TLE.

    A TLE is archived only once for a given
    NORAD ID + epoch combination.
    """

    tle = satellite.get("tle")

    if not tle:
        return False

    history_document = {
        "norad_id": satellite["norad_id"],
        "satellite_name": satellite.get("name"),
        "line1": tle.get("line1"),
        "line2": tle.get("line2"),
        "epoch": normalize_datetime(tle.get("epoch")),
        "source": tle.get("source"),
        "retrieved_at": normalize_datetime(
            tle.get("retrieved_at")
        ),
        "archived_at": datetime.now(timezone.utc)
    }

    result = history_collection.update_one(
        {
            "norad_id": history_document["norad_id"],
            "epoch": history_document["epoch"]
        },
        {
            "$setOnInsert": history_document
        },
        upsert=True
    )

    if result.upserted_id:
        print(
            f"[INFO] TLE history archived for "
            f"NORAD {history_document['norad_id']}"
        )
        return True

    print(
        f"[INFO] TLE history already exists for "
        f"NORAD {history_document['norad_id']} "
        f"epoch {history_document['epoch']}"
    )

    return False