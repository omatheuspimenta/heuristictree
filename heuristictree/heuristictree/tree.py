from heuristictree.quick_tree import quickSort


def tree(
    L: int, l: list[int], d: list[int], smallitem: int = 0
) -> tuple[int, int, int, list[int]]:
    """
    Solve the Cutting Stock Problem using a TREE heuristic algorithm.

    This function takes an available roll length (L), a list of item lengths (l), a list of item demands (d) and the small item length.
    It optimally cuts items of different lengths from rolls to fulfill the demands, minimizing loss.

    Parameters:
        L (int): Available roll length.
        l (list of int): List of item lengths.
        d (list of int): List of item demands corresponding to item lengths.
        smallitem (int): Small item length. If not specified, the smallest item length is used.

    Returns:
        tuple: A tuple containing:
            - leftover (int): Remaining roll length.
            - loss (int): Total loss due to cutting.
            - bar (int): Total rolls used.
            - x_ret (list of list of int): Cutting patterns for each roll used.

    Example:
    >>> L = 100
    >>> l = [20, 30, 40, 50]
    >>> d = [8, 6, 4, 2]
    >>> leftover, loss, bar, x_ret = tree(L, l, d)
    >>> leftover
    0
    >>> loss
    0
    >>> bar
    7
    >>> x_ret
    [[2, 0, 0, 0], [2, 0, 1], [2, 0, 1], [2, 2], [2, 2], [2, 2]]
    >>> L = 1188
    >>> l = [229, 208, 400, 327, 373, 182, 285, 88, 154, 83, 232, 343, 343, 305, 91, 432, 203, 323, 27, 421, 275, 208, 92, 261, 258, 340, 21, 398, 417, 309, 280, 326, 122, 288, 412, 79, 22, 34, 99, 87]
    >>> d = [2, 1, 1, 3, 3, 3, 2, 1, 1, 3, 1, 1, 1, 3, 2, 3, 3, 3, 1, 1, 2, 2, 3, 1, 3, 3, 1, 1, 2, 3, 1, 1, 2, 1, 1, 1, 3, 2, 1, 1]
    >>> leftover, loss, bar, x_ret = tree(L, l, d)
    >>> leftover
    1049
    >>> loss
    17
    >>> bar
    17
    >>> x_ret
    [[0, 0, 0, 0, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1, 1, 3, 1, 1, 0, 0], [2, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 1, 0, 0], [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 2, 2, 1, 1], [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0], [0, 0, 0, 1, 2, 0, 0, 1, 0, 0], [0, 0, 1, 1, 1, 1, 0], [1, 1, 1, 0], [1]]

    Notes:
    - This function optimizes cutting patterns by minimizing roll loss.

    Cite:
    - Soon.

    """
    # Initial Parameters
    n = len(d)
    soma = 0
    leftover = 0
    loss = 0
    L_hat = L
    bar = 1
    x_ret = []

    # Sorting
    quickSort(l, d, 0, n - 1)

    # Put together items of the same size
    i = 0
    while i < (n - 1):
        if l[i] == l[i + 1]:
            d[i] += d[i + 1]
            l.pop(i + 1)
            d.pop(i + 1)
            n -= 1
        else:
            i += 1

    n = len(d)

    # Sum of Demand Items
    soma = sum(d)

    # small item
    small_ = smallitem
    if small_ == 0:
        small_ = l[-1]

    # Begin
    while soma > 0:
        x_ini = [0] * n
        x = [0] * n
        x_aux = [0] * n
        x_fix = [0] * n
        small = l[-1]
        # First branch
        for i in range(n):
            y = min(L_hat // l[i], d[i])
            x_ini[i] = y
            L_hat -= x_ini[i] * l[i]
            if (L_hat < small) or L_hat == 0:
                break
        cont = 1
        L_aux = L
        x_aux[0] = x_ini[0]
        x = x_ini
        while (L_aux != 0) and (cont != n):
            x_fix = [0] * n
            ra = -1
            if x_aux[cont - 1] != 0:
                x_fix[cont - 1] = x_aux[cont - 1] - 1
            else:
                x_fix[cont - 1] = 0
            L_fix = L - (l[cont - 1] * x_fix[cont - 1])
            L_aux = L_fix
            x_aux = x_fix
            for j in range(cont, n):
                if l[j] != -1:
                    y = min(L_aux // l[j], d[j])
                    x_aux[j] = y
                    L_aux -= x_aux[j] * l[j]
                    if L_aux > l[cont]:
                        if L_aux in l[0:cont]:
                            ra = l.index(L_aux)
                            x_aux[ra] = 1
                            L_aux = 0
                        else:
                            for ind in range(cont):
                                if ((L_aux - l[ind]) >= 0) and (
                                    (L_aux - l[ind]) < L_hat
                                ):
                                    L_aux -= l[ind]
                                    x_aux[ind] = 1
                                    break
            if L_aux < L_hat:
                L_hat = L_aux
                x = x_aux
            cont += 1
        x_ret.append(x)

        sum_x = sum(x)
        d = [di - xi for di, xi in zip(d, x)]

        # Remove null demands
        i = 0
        while i <= (n - 1):
            if d[i] == 0:
                l.pop(i)
                d.pop(i)
                n -= 1
            else:
                i += 1

        n = len(d)

        # Add Loss, Leftover and Bar
        if L_hat < small_:
            loss += L_hat
            L_hat = L
        else:
            leftover += L_hat
            L_hat = L

        soma -= sum_x
        bar += 1
    return (leftover, loss, bar, x_ret)
