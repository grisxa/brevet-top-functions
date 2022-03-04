def unique_integer(integer, l):
    counter = dict()
    unique = set()
    for n in l:
        counter[n] = counter.get(n, 0) + 1
        if counter[n] == 1:
            unique.add(n)
        elif n in unique:
            unique.remove(n)
    if len(unique) > 1:
        return -1
    return unique.pop()


if __name__ == "__main__":
    print(unique_integer(1, [2, 2, 2, 4, 7, 4, 4]))
    print(unique_integer(7, [2, 2, 2, 4, 7, 3, 4]))
