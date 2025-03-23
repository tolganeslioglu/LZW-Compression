import os  # the os module is used for file and directory operations
import math  # the math module provides access to mathematical functions
from io import StringIO  # using StringIO for efficiency

# A class that implements the LZW compression and decompression algorithms as
# well as the necessary utility methods for text files.
# ------------------------------------------------------------------------------
class LZWCoding:
    def __init__(self, filename, type):
        self.filename = filename
        self.type = type
        if type == 'text' or type == 'level1':
            self.codelength = 12  # 12 bits for text
            self.max_dict_size = 4096  # 2^12
            self.initial_dict_size = 256  # ASCII range
        elif type == 'level5':
            self.codelength = 10  # 10 bits for difference values
            self.max_dict_size = 1024  # 2^10
            self.initial_dict_size = 512  # For difference values [-255, 255]
        elif type == 'level4':
            self.codelength = 12  # 12 bits for better color compression
            self.max_dict_size = 4096  # 2^12
            self.initial_dict_size = 256  # Standard for 8-bit color channels
        elif type == 'level3':
            self.codelength = 10  
            self.max_dict_size = 1024
            self.initial_dict_size = 512
        else:  # level2
            self.codelength = 9
            self.max_dict_size = 512
            self.initial_dict_size = 256

    def encode(self, uncompressed_data):
        if not uncompressed_data:
            raise ValueError("Cannot encode empty data")
            
        # Initialize dictionary based on compression type
        dictionary = {chr(i): i for i in range(self.initial_dict_size)}
        dict_size = self.initial_dict_size
        
        w = uncompressed_data[0]
        result = []
        
        for k in uncompressed_data[1:]:
            wk = w + k
            if wk in dictionary:
                w = wk
            else:
                result.append(dictionary[w])
                if dict_size < self.max_dict_size:
                    dictionary[wk] = dict_size
                    dict_size += 1
                w = k
        
        if w:
            result.append(dictionary[w])
            
        return result

    def compress_text_file(self):
        try:
            input_path = f"{self.filename}.txt"
            
            # Read the text file
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Encode using LZW and get statistics
            encoded_values = self.encode(text)
            
            # Calculate statistics
            stats = {
                'dict_size': self.initial_dict_size,
                'avg_code_length': sum(len(bin(x)[2:]) for x in encoded_values) / len(encoded_values)
            }
            
            # Save compressed file
            output_path = f"{self.filename}.bin"
            with open(output_path, 'wb') as f:
                # Write total length
                f.write(len(encoded_values).to_bytes(4, byteorder='big'))
                
                # Write encoded values
                for value in encoded_values:
                    f.write(value.to_bytes(2, byteorder='big'))
            
            return output_path, stats
            
        except Exception as e:
            print(f"Text compression error: {str(e)}")
            raise

    # A method that converts the integer list returned by the compress method
    # into a binary string and returns the resulting string.
    # ---------------------------------------------------------------------------
    def int_list_to_binary_string(self, int_list):
        # initialize the binary string as an empty string
        bitstring = ''
        # concatenate each integer in the input list to the binary string
        for num in int_list:
            # using codelength bits to compress each value
            for n in range(self.codelength):
                if num & (1 << (self.codelength - 1 - n)):
                    bitstring += '1'
                else:
                    bitstring += '0'
        # return the resulting binary string
        return bitstring

    # A method that adds the code length to the beginning of the binary string
    # that corresponds to the compressed data and returns the resulting string.
    # (the compressed data should contain everything needed to decompress it)
    # ---------------------------------------------------------------------------
    def add_code_length_info(self, bitstring):
        # create a binary string that stores the code length as a byte
        codelength_info = '{0:08b}'.format(self.codelength)
        # add the code length info to the beginning of the given binary string
        bitstring = codelength_info + bitstring
        # return the resulting binary string
        return bitstring

    # A method for adding zeros to the binary string (the compressed data)
    # to make the length of the string a multiple of 8.
    # (This is necessary to be able to write the values to the file as bytes.)
    # ---------------------------------------------------------------------------
    def pad_encoded_data(self, encoded_data):
        # compute the number of the extra bits to add
        if len(encoded_data) % 8 != 0:
            extra_bits = 8 - len(encoded_data) % 8
            # add zeros to the end (padding)
            for i in range(extra_bits):
                encoded_data += '0'
        else:   # no need to add zeros
            extra_bits = 0
        # add a byte that stores the number of added zeros to the beginning of
        # the encoded data
        padding_info = '{0:08b}'.format(extra_bits)
        encoded_data = padding_info + encoded_data
        # return the resulting string after padding
        return encoded_data

    # A method that converts the padded binary string to a byte array and returns 
    # the resulting array. 
    # (This byte array will be written to a file to store the compressed data.)
    # ---------------------------------------------------------------------------
    def get_byte_array(self, padded_encoded_data):
        # the length of the padded binary string must be a multiple of 8
        if (len(padded_encoded_data) % 8 != 0):
            print('The compressed data is not padded properly!')
            exit(0)
        # create a byte array
        b = bytearray()
        # append the padded binary string to byte by byte
        for i in range(0, len(padded_encoded_data), 8):
            byte = padded_encoded_data[i : i + 8]
            b.append(int(byte, 2))
        # return the resulting byte array
        return b

    # A method that reads the contents of a compressed binary file, performs
    # decompression and writes the decompressed output to a text file.
    # ---------------------------------------------------------------------------
    def decompress_text_file(self):
        try:
            input_path = f"{self.filename}.bin"
            print(f"Reading compressed file: {input_path}")
            
            # Read compressed data
            with open(input_path, 'rb') as f:
                # Read total length
                length = int.from_bytes(f.read(4), byteorder='big')
                
                # Read encoded values
                encoded_values = []
                for _ in range(length):
                    value = int.from_bytes(f.read(2), byteorder='big')
                    encoded_values.append(value)
            
            # Decode text
            decoded_text = self.decode(encoded_values)
            
            # Save decompressed file
            output_path = f"{self.filename}_restored.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(decoded_text)
            
            print(f"Decompressed file saved: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Text decompression error: {str(e)}")
            raise

    # A method to remove the padding info and the added zeros from the compressed
    # binary string and return the resulting string.
    def remove_padding(self, padded_encoded_data):
        # extract the padding info (the first 8 bits of the input string)
        padding_info = padded_encoded_data[:8]
        encoded_data = padded_encoded_data[8:]
        # remove the extra zeros (if any) and return the resulting string
        extra_padding = int(padding_info, 2) 
        if extra_padding != 0:
            encoded_data = encoded_data[:-1 * extra_padding]
        return encoded_data

    # A method to extract the code length info from the compressed binary string
    # and return the resulting string.
    # ---------------------------------------------------------------------------
    def extract_code_length_info(self, bitstring):
        # the first 8 bits of the input string contains the code length info
        codelength_info = bitstring[:8]
        self.codelength = int(codelength_info, 2)
        # return the resulting binary string after removing the code length info
        return bitstring[8:]

    # A method that converts the compressed binary string to a list of int codes
    # and returns the resulting list.
    # ---------------------------------------------------------------------------
    def binary_string_to_int_list(self, bitstring):
        # generate the list of integer codes from the binary string
        int_codes = []
        # for each compressed value (a binary string with codelength bits)
        for bits in range(0, len(bitstring), self.codelength):
            # compute the integer code and add it to the list
            int_code = int(bitstring[bits: bits + self.codelength], 2)
            int_codes.append(int_code)
        # return the resulting list
        return int_codes
    
    # A method that decodes a list of encoded integer values into a string (text) 
    # by using the LZW decompression algorithm and returns the resulting output.
    # ---------------------------------------------------------------------------
    def decode(self, encoded_values):
        if not encoded_values:
            return ""
        
        # Initialize dictionary based on compression type
        dictionary = {i: chr(i) for i in range(self.initial_dict_size)}
        dict_size = self.initial_dict_size
        
        # Add debugging information
        print(f"Initial dictionary size: {dict_size}")
        print(f"Maximum dictionary size: {self.max_dict_size}")
        
        result = StringIO()
        
        # First value should be in initial dictionary
        if encoded_values[0] >= dict_size:
            raise ValueError(f"Invalid first value: {encoded_values[0]}")
        
        w = chr(encoded_values[0])
        result.write(w)
        
        for k in encoded_values[1:]:
            if k < dict_size:
                entry = dictionary[k]
            elif k == dict_size and w:
                entry = w + w[0]
            else:
                print(f"Invalid dictionary index: {k}, dict_size: {dict_size}")
                raise ValueError(f'Bad compressed k: {k}')
                
            result.write(entry)
            
            if dict_size < self.max_dict_size and w:
                dictionary[dict_size] = w + entry[0]
                dict_size += 1
                
            w = entry
        
        return result.getvalue()

    def binary_string_from_bytes(self, byte_data):
        """Convert bytes to binary string"""
        bit_string = StringIO()
        for byte in byte_data:
            bits = bin(byte)[2:].rjust(8, '0')
            bit_string.write(bits)
        return bit_string.getvalue()

    def binary_string_to_int_list(self, bit_string):
        """Convert binary string to list of integers using codelength"""
        int_list = []
        for i in range(0, len(bit_string), self.codelength):
            if i + self.codelength <= len(bit_string):
                chunk = bit_string[i:i + self.codelength]
                int_list.append(int(chunk, 2))
        return int_list

    def decompress(self, input_data):
        try:
            # Add error handling
            if not input_data:
                raise ValueError("No input data provided")
            # ...existing decompression code...
        except Exception as e:
            print(f"LZW decompression error: {str(e)}")
            raise
