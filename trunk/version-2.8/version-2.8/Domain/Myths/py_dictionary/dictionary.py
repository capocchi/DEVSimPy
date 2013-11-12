#------------------------------------------------------------------------------
#           Name: dictionary.py
#         Author: Kevin Harris
#  Last Modified: 02/20/04
#    Description: This Python script demonstrates how to create and use a
#                 dictionary object.
#------------------------------------------------------------------------------

# Initialize a dictionary, which represents office extensions
extensions = {"Jim": 2045, "Carla": 2032, "Tracy": 2052 }

# Add a new key to the dictionary
extensions["Bob"] = 2072

# Dump out the entire dictionary
print extensions

# Dump out just the keys
print extensions.keys()

# Use a key to access its value
print extensions["Carla"]

# Delete a key from the dictionary
del extensions["Bob"]

# Verify whether or not a key exists within the dictionary
print extensions.has_key( "Jim" )

raw_input( '\n\nPress Enter to exit...' )
