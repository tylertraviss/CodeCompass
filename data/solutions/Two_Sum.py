# Optimal

def two_sum(nums, target):
    """
    Finds two numbers in `nums` that add up to `target` and returns their indices.
    
    :param nums: List of integers
    :param target: Target sum
    :return: List containing indices of the two numbers
    """
    num_map = {}  # Dictionary to store numbers and their indices

    for i, num in enumerate(nums):
        complement = target - num  # Calculate the complement
        if complement in num_map:
            return [num_map[complement], i]  # Return indices of the complement and current number
        num_map[num] = i  # Add the current number to the dictionary

    return []  # Return empty list if no solution is found
