def modify_array(my_array, my_dict):
	# Modify the array within this function
	my_array.append(42)
	my_dict['d'] = 42

def main():
	# Create an array
	my_array = [1, 2, 3]
	my_dict = {"a": 1, "b": 2, "c": 3}
	# Pass the array to the function for modification
	modify_array(my_array, my_dict)

	# The changes made in the function are reflected outside
	print(my_array)  # Output: [1, 2, 3, 42]
	print(my_dict)  # Output: {'a': 1, 'b': 2, 'c': 3, 'd': 42}

if __name__ == "__main__":
	main()