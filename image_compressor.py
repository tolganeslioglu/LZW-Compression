import numpy as np
from PIL import Image
import os
from LZW import LZWCoding  # Doğrudan LZW.py'den import et

class ImageCompressor:
    def __init__(self, image_path):
        self.image_path = image_path
        self.lzw = LZWCoding(os.path.splitext(image_path)[0], 'image')
        self.original_size = os.path.getsize(image_path)
        self.width = None
        self.height = None
        self.compression_ratio = None
        
    def calculate_compression_ratio(self, original_size, compressed_size):
        """Calculate compression statistics"""
        # Calculate compression ratio
        compressed_bits = compressed_size * self.lzw.codelength
        compressed_bytes = compressed_bits / 8
        self.compression_ratio = original_size / compressed_bytes

        # Print statistics
        print(f"\nLevel 2 Compression Statistics:")
        print(f"Original Size: {original_size} bytes")
        print(f"Compressed Size: {int(compressed_bytes)} bytes")
        print(f"Compression Ratio: {self.compression_ratio:.2f}")

    def compress(self):
        print(f"Compressing image: {self.image_path}")
        try:
            # Read and convert image to grayscale
            img = Image.open(self.image_path).convert('L')
            img_array = np.array(img)
            
            self.width, self.height = img.size
            print(f"Image dimensions: {self.width}x{self.height}")
            
            # Convert pixel values to string
            pixel_string = ''.join([chr(pixel) for pixel in img_array.flatten()])
            
            # Compress using LZW
            encoded_values = self.lzw.encode(pixel_string)
            
            # Save compressed file
            output_path = f"{self.image_path}.compressed"
            with open(output_path, 'wb') as f:
                # Write metadata
                f.write(self.width.to_bytes(4, byteorder='big'))
                f.write(self.height.to_bytes(4, byteorder='big'))
                f.write(self.lzw.codelength.to_bytes(2, byteorder='big'))
                
                # Write encoded values with size limit
                for value in encoded_values:
                    # Ensure value doesn't exceed dictionary size limit
                    if value < self.lzw.max_dict_size:
                        f.write(value.to_bytes(2, byteorder='big'))
            
            print(f"Compressed file saved: {output_path}")
            self.calculate_compression_ratio(len(img_array.flatten()), len(encoded_values))
            return encoded_values
            
        except Exception as e:
            print(f"Error during compression: {str(e)}")
            raise e

    def decompress(self, compressed_file_path):
        print(f"Decompressing file: {compressed_file_path}")
        try:
            with open(compressed_file_path, 'rb') as f:
                # Read metadata
                width = int.from_bytes(f.read(4), byteorder='big')
                height = int.from_bytes(f.read(4), byteorder='big')
                print(f"Image dimensions: {width}x{height}")
                
                self.lzw.codelength = int.from_bytes(f.read(2), byteorder='big')
                print(f"Code length: {self.lzw.codelength}")
                
                # Read encoded values
                encoded_values = []
                while True:
                    try:
                        chunk = f.read(2)
                        if not chunk or len(chunk) < 2:
                            break
                        value = int.from_bytes(chunk, byteorder='big')
                        # Only include values within dictionary size limit
                        if value < self.lzw.max_dict_size:
                            encoded_values.append(value)
                    except:
                        break
                
                # Decode using LZW
                decoded_string = self.lzw.decode(encoded_values)
                
                # Convert to pixel values
                pixel_values = [ord(char) for char in decoded_string]
                
                # Ensure correct size
                expected_size = width * height
                if len(pixel_values) != expected_size:
                    if len(pixel_values) < expected_size:
                        pixel_values.extend([0] * (expected_size - len(pixel_values)))
                    else:
                        pixel_values = pixel_values[:expected_size]
                
                # Convert to image
                img_array = np.array(pixel_values, dtype=np.uint8).reshape((height, width))
                restored_image = Image.fromarray(img_array, mode='L')
                
                # Save restored image
                output_path = compressed_file_path.replace('.compressed', '_restored.bmp')
                restored_image.save(output_path, format='BMP')
                print(f"Restored image saved: {output_path}")
                
                return restored_image
                
        except Exception as e:
            print(f"Error during decompression: {str(e)}")
            raise e
        
    def calculate_statistics(self, original_array, encoded_values):
        # Calculate entropy of original image
        pixel_counts = np.bincount(original_array.flatten())
        probabilities = pixel_counts[pixel_counts > 0] / len(original_array.flatten())
        self.entropy = -np.sum(probabilities * np.log2(probabilities))
        
        # Calculate average code length
        self.avg_code_length = len(encoded_values) * self.lzw.codelength / (self.width * self.height)
        
        # Calculate compression ratio
        compressed_size = len(encoded_values) * self.lzw.codelength / 8  # Convert bits to bytes
        self.compression_ratio = self.original_size / compressed_size