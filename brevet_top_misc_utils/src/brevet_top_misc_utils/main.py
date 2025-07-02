def get_control_window(distance: float) -> tuple[float, float]:
    """
    Calculate the time window on the control point based on the average speed and distance.
    """
    if distance == 0:
        return 0.0, 1.0
    elif distance <= 60:
        return distance / 34 + 0.008333333333334, distance / 20 + 1.008333333333334
    elif 60 < distance <= 200:
        return (
            distance / 34 + 0.008333333333334,
            (distance - 60) / 15 + 4.008333333333334,
        )
    elif 200 < distance <= 400:
        return (distance - 200) / 32 + 5.890686274509805, (distance - 60) / 15 + 4.008333333333334
    elif 400 < distance <= 600:
        return (distance - 400) / 30 + 12.140333333333333, (distance - 60) / 15 + 4.008333333333334
    elif 600 < distance <= 1000:
        return (distance - 600) / 28 + 18.807, (distance - 600) / 11.428571428571429 + 40.008333333333334
    elif 1000 < distance <= 1200:
        return (distance - 1000) / 26 + 33.09304761904762, (distance - 1000) / 13.333333333333333 + 75.008333333333334
    elif 1200 < distance <= 1400:
        return (distance - 1200) / 25 + 40.78564102564103, (distance - 1200) / 11 + 90.008333333333334
    elif 1400 < distance <= 1800:
        return (distance - 1200) / 25 + 40.78564102564103, (distance - 1400) / 10 + 108.19015151515153
    elif 1800 < distance <= 2000:
        return (distance - 1800) / 24 + 64.78533333333334, (distance - 1800) / 9 + 148.19033333333334
    return 0.0, 0.0  # a fallback


def get_limit_hours(distance: int) -> float:
    """
    Calculate the brevet time limit based on the distance
    """
    if distance == 0:
        return 0.0
    elif distance < 220:
        return (distance - 200) / 15 + 13.5
    # 300 the same as 600
    elif 400 <= distance < 420:
        return (distance - 400) / 15 + 27
    elif distance <= 620:
        return distance / 15
    elif distance <= 1020:
        return (distance - 600) / 11.428571428571429 + 40
    return (distance - 1000) / 13.333333333333333 + 75
