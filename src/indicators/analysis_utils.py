def quick_select(arr, k):
    if len(arr) == 0:  # Ensure that the array isn't empty
        raise ValueError("The array is empty.")
        
    if len(arr) == 1:
        return arr[0]
    
    pivot = arr[len(arr) // 2]  # Choose a pivot
    left = [x for x in arr if x < pivot]
    right = [x for x in arr if x > pivot]
    
    if k < len(left):
        return quick_select(left, k)
    elif k < len(left) + 1:  # Ensure pivot is handled properly
        return pivot
    else:
        return quick_select(right, k - len(left) - 1)  # Adjust for the pivot
    

# I consider a wick of 0.05% as no wick
def no_wick(edge1: float, edge2: float) -> bool:

    max_edge  = max(edge1, edge2)
    min_edge  = min(edge1, edge2)

    return (max_edge - min_edge) / max_edge < 0.002

def is_marubuzo(candle):

    if candle['Open'] > candle['Close']:
        return no_wick(candle['Open'], candle['Low']) and no_wick(candle['Close'], candle['High'])
    
    return False

def is_doji(candle):
        
    change_percentage = abs(candle['Close'] - candle['Open']) / candle['Open']
    return change_percentage <= 0.0015 # it's a doji candle