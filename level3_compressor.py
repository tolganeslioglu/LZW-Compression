import numpy as np
from PIL import Image
import os
from LZW import LZWCoding

class Level3Compressor:
    def __init__(self, image_path):
        self.image_path = image_path
        self.lzw = LZWCoding(os.path.splitext(image_path)[0], 'level3')  # Specify level3 type
        self.original_size = os.path.getsize(image_path)
        self.width = None
        self.height = None
        self.compression_ratio = None

    def calculate_differences(self, img_array):
        """Calculate row-wise and column-wise differences"""
        height, width = img_array.shape
        diff_image = np.zeros_like(img_array, dtype=np.int16)
        
        # First pixel remains as is
        diff_image[0, 0] = img_array[0, 0]
        
        # Calculate row-wise differences
        for j in range(1, width):
            diff_image[0, j] = int(img_array[0, j]) - int(img_array[0, j-1])
        
        # Calculate column-wise differences for first column
        for i in range(1, height):
            diff_image[i, 0] = int(img_array[i, 0]) - int(img_array[i-1, 0])
        
        # Calculate remaining differences
        for i in range(1, height):
            for j in range(1, width):
                diff_image[i, j] = int(img_array[i, j]) - int(img_array[i, j-1])
        
        return diff_image

    def restore_from_differences(self, diff_image, first_pixel):
        height, width = diff_image.shape
        restored = np.zeros_like(diff_image, dtype=np.uint8)
        
        # Set first pixel
        restored[0, 0] = first_pixel
        
        # Restore first row
        for j in range(1, width):
            val = int(restored[0, j-1]) + int(diff_image[0, j])
            restored[0, j] = np.clip(val, 0, 255)
        
        # Restore first column
        for i in range(1, height):
            val = int(restored[i-1, 0]) + int(diff_image[i, 0])
            restored[i, 0] = np.clip(val, 0, 255)
        
        # Restore rest of the image
        for i in range(1, height):
            for j in range(1, width):
                val = int(restored[i, j-1]) + int(diff_image[i, j])
                restored[i, j] = np.clip(val, 0, 255)
        
        return restored

    def compress(self):
        print(f"Level 3 - Compressing image: {self.image_path}")
        try:
            # Read and convert image
            img = Image.open(self.image_path).convert('L')
            img_array = np.array(img)
            
            self.width, self.height = img.size
            print(f"Image dimensions: {self.width}x{self.height}")
            
            # Calculate differences
            diff_image = self.calculate_differences(img_array)
            first_pixel = int(img_array[0, 0])
            
            # Convert differences to string (shift range from [-255,255] to [0,511])
            diff_chars = []
            for x in diff_image.flatten():
                shifted_val = (int(x) + 255) & 0x1FF  # Ensure value is in [0,511]
                if shifted_val < 0 or shifted_val > 511:
                    print(f"Warning: Value {shifted_val} out of range")
                diff_chars.append(chr(shifted_val))
            
            diff_string = ''.join(diff_chars)
            if not diff_string:
                raise ValueError("Empty difference string generated")
            
            # Compress using LZW
            encoded_values = self.lzw.encode(diff_string)
            
            # Save compressed file
            output_path = f"{self.image_path}.level3.compressed"
            with open(output_path, 'wb') as f:
                f.write(int(self.width).to_bytes(4, byteorder='big'))
                f.write(int(self.height).to_bytes(4, byteorder='big'))
                f.write(int(self.lzw.codelength).to_bytes(2, byteorder='big'))
                f.write(int(first_pixel).to_bytes(1, byteorder='big'))
                
                for value in encoded_values:
                    f.write(int(value).to_bytes(2, byteorder='big'))
            
            print(f"Compressed file saved: {output_path}")
            self.calculate_statistics(img_array, encoded_values)
            return encoded_values
            
        except Exception as e:
            print(f"Error during Level 3 compression: {str(e)}")
            raise e

    def decompress(self, compressed_file_path):
        try:
            print(f"Level 3 - Decompressing file: {compressed_file_path}")
            
            with open(compressed_file_path, 'rb') as f:
                # Read metadata
                width = int.from_bytes(f.read(4), byteorder='big')
                height = int.from_bytes(f.read(4), byteorder='big')
                self.lzw.codelength = int.from_bytes(f.read(2), byteorder='big')
                first_pixel = int.from_bytes(f.read(1), byteorder='big')
                
                print(f"Image dimensions: {width}x{height}")
                print(f"Code length: {self.lzw.codelength}")
                
                # Read encoded values
                encoded_values = []
                while True:
                    chunk = f.read(2)
                    if not chunk or len(chunk) < 2:
                        break
                    value = int.from_bytes(chunk, byteorder='big')
                    encoded_values.append(value)
            
            # Decode data and shift back from [0,511] to [-255,255]
            decoded_string = self.lzw.decode(encoded_values)
            diff_values = np.array([(ord(char) - 255) for char in decoded_string], 
                                 dtype=np.int16)
            diff_values = diff_values[:width*height].reshape(height, width)
            
            # Restore image
            restored_array = self.restore_from_differences(diff_values, first_pixel)
            restored_image = Image.fromarray(restored_array, mode='L')
            
            # Save restored image
            output_path = compressed_file_path.replace('.level3.compressed', '_level3_restored.bmp')
            restored_image.save(output_path, format='BMP')
            print(f"Restored image saved: {output_path}")
            
            return restored_image
            
        except Exception as e:
            print(f"Error during Level 3 decompression: {str(e)}")
            raise e

    def calculate_statistics(self, original_array, encoded_values):
        # Calculate entropy
        pixel_counts = np.bincount(original_array.flatten())
        probabilities = pixel_counts[pixel_counts > 0] / len(original_array.flatten())
        self.entropy = -np.sum(probabilities * np.log2(probabilities))
        
        # Calculate average code length
        self.avg_code_length = len(encoded_values) * self.lzw.codelength / (self.width * self.height)
        
        # Calculate compression ratio
        compressed_size = len(encoded_values) * self.lzw.codelength / 8
        self.compression_ratio = self.original_size / compressed_size
        
        print(f"\nLevel 3 Compression Statistics:")
        print(f"Entropy: {self.entropy:.2f} bits/pixel")
        print(f"Average Code Length: {self.avg_code_length:.2f} bits/pixel")
        print(f"Compression Ratio: {self.compression_ratio:.2f}")