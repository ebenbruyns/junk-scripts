import os
import sys
import json

# Define the directory path where the fragment files are located
import os
import sys
import json

# Define the directory path where the fragment files are located
directory_path = "/home/eben/homebrew/data/Junk-Store/static-json/"

# Initialize the dictionary to store the fragments
json_fragments = {}

# Iterate over the files in the directory
for filename in os.listdir(directory_path):
    file_path = os.path.join(directory_path, filename)
    if os.path.isfile(file_path):
        with open(file_path, "r") as file:
            # Read the file and extract the argument and JSON fragment
            argument = filename.split(".")[0]
            json_fragment = json.load(file)

            # Store the argument and JSON fragment in the dictionary
            json_fragments[argument] = json_fragment

# Generate the code by combining the code template with the extracted fragments
generated_code = """
import sys
import json


json_fragments = # JSON_FRAGMENT_PLACEHOLDER

# Check if an argument is provided
if len(sys.argv) < 2:
    print("Please provide an argument.")
    sys.exit(1)

# Get the argument from the command line
argument = sys.argv[1]

# Look up the JSON fragment based on the argument
if argument in json_fragments:
    json_fragment = json_fragments[argument]
else:
    print("Invalid argument.")
    sys.exit(1)
"""
# Replace the placeholder with the JSON fragment
json_string = json.dumps(json_fragments)
generated_code = generated_code.replace(
    "# JSON_FRAGMENT_PLACEHOLDER", json_string)

# Print the generated code
print(generated_code)
