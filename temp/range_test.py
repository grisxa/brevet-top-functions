def extended_range(start=0, stop: float = None, step: float = 1):
    start_, stop_ = (0, start) if stop is None else (start, stop)
    yield start_
    if start_ + step == stop:
        return
    else:
        yield from extended_range(start_ + step, stop_, step)


if __name__ == "__main__":
    print(len(list(extended_range(0, 0.8, 0.1))))
