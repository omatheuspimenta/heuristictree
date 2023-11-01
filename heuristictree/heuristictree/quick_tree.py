def partition(arr: list[int], seg: list[int], low: int, high: int) -> int:
    i = low - 1
    pivot = arr[high]

    for j in range(low, high):
        if arr[j] >= pivot:
            i = i + 1
            arr[i], arr[j] = arr[j], arr[i]
            seg[i], seg[j] = seg[j], seg[i]

    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    seg[i + 1], seg[high] = seg[high], seg[i + 1]
    return i + 1


def quickSort(arr: list[int], seg: list[int], low: int, high: int):
    """
    Sorts an array using the QuickSort algorithm.

    This function sorts the input array 'arr' in non-increasing order using the QuickSort algorithm.
    It also reorders the corresponding 'seg' array in the same way as 'arr'.

    Parameters:
        arr (list[int]): The array to be sorted.
        seg (list[int]): The corresponding array to be sorted along with 'arr'.
        low (int): The lower index of the array to be sorted.
        high (int): The upper index of the array to be sorted.

    Example:
    >>> arr = [4, 2, 7, 1, 5]
    >>> seg = [10, 20, 30, 40, 50]
    >>> quickSort(arr, seg, 0, len(arr) - 1)
    >>> arr
    [7, 5, 4, 2, 1]
    >>> seg
    [30, 50, 10, 20, 40]

    Notes:
    - This function sorts the 'arr' and 'seg' arrays using the QuickSort algorithm.
    - The 'arr' array is sorted in non-increasing order.
    """

    if low < high:
        pi = partition(arr, seg, low, high)

        quickSort(arr, seg, low, pi - 1)
        quickSort(arr, seg, pi + 1, high)
