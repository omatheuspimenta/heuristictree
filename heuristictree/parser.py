def load_file(path: str) -> tuple[int, list[int], list[int]]:
    """
    Load a file and return the parameters of the heuristic tree.
    """

    with open(path, "r") as file:
        L = int(file.readline())
        l, d = [], []
        for line in file:
            split = line.split()
            l.append(int(split[0]))
            d.append(int(split[1]))
    return L, l, d
