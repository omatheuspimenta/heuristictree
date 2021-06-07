def partition(arr,seg,low,high): 
    i = ( low-1 )   
    pivot = arr[high]
  
    for j in range(low , high): 
        if  arr[j] >= pivot: 
            i = i+1 
            arr[i],arr[j] = arr[j],arr[i] 
            seg[i],seg[j] = seg[j],seg[i]
  
    arr[i+1],arr[high] = arr[high],arr[i+1]
    seg[i+1],seg[high] = seg[high],seg[i+1]
    return ( i+1 ) 

def quickSort(arr,seg,low,high): 
    if low < high: 
        pi = partition(arr, seg,low,high) 
        
        quickSort(arr, seg, low, pi-1) 
        quickSort(arr, seg, pi+1, high) 