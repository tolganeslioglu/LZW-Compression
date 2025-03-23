import numpy as np
from PIL import Image
import os
from LZW import LZWCoding

class Level4Compressor:
    def __init__(self, image_path):
        self.image_path = image_path
        # Initialize separate LZW coders for each channel
        self.lzw_r = LZWCoding(os.path.splitext(image_path)[0], 'level4')
        self.lzw_g = LZWCoding(os.path.splitext(image_path)[0], 'level4')
        self.lzw_b = LZWCoding(os.path.splitext(image_path)[0], 'level4')
        self.original_size = os.path.getsize(image_path)
        self.width = None
        self.height = None
        self.compression_ratio = None

    def compress(self):
        print(f"Level 4 - Compressing color image: {self.image_path}")
        try:
            # Read color image
            img = Image.open(self.image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            self.width, self.height = img.size
            print(f"Image dimensions: {self.width}x{self.height}")
            
            # Split into RGB channels
            r, g, b = img.split()
            
            # Convert to numpy arrays
            r_array = np.array(r)
            g_array = np.array(g)
            b_array = np.array(b)
            
            # Convert each channel to string
            r_string = ''.join([chr(x) for x in r_array.flatten()])
            g_string = ''.join([chr(x) for x in g_array.flatten()])
            b_string = ''.join([chr(x) for x in b_array.flatten()])
            
            # Compress each channel separately
            r_encoded = self.lzw_r.encode(r_string)
            g_encoded = self.lzw_g.encode(g_string)
            b_encoded = self.lzw_b.encode(b_string)
            
            # Save compressed file
            output_path = f"{self.image_path}.level4.compressed"
            with open(output_path, 'wb') as f:
                # Write metadata
                f.write(self.width.to_bytes(2, byteorder='big'))
                f.write(self.height.to_bytes(2, byteorder='big'))
                
                # Write lengths of encoded data
                f.write(len(r_encoded).to_bytes(4, byteorder='big'))
                f.write(len(g_encoded).to_bytes(4, byteorder='big'))
                f.write(len(b_encoded).to_bytes(4, byteorder='big'))
                
                # Write encoded data for each channel
                for encoded_data in [r_encoded, g_encoded, b_encoded]:
                    for value in encoded_data:
                        f.write(value.to_bytes(2, byteorder='big'))
            
            # Calculate compression statistics
            compressed_size = os.path.getsize(output_path)
            self.compression_ratio = self.original_size / compressed_size
            
            print(f"\nLevel 4 Compression Statistics:")
            print(f"Original Size: {self.original_size:,} bytes")
            print(f"Compressed Size: {compressed_size:,} bytes")
            print(f"Compression Ratio: {self.compression_ratio:.2f}")
            
            return True
        
        except Exception as e:
            print(f"Error during Level 4 compression: {str(e)}")
            raise e

    def decompress(self, compressed_file_path):
        try:
            print(f"Level 4 - Decompressing file: {compressed_file_path}")
            
            with open(compressed_file_path, 'rb') as f:
                # Read metadata
                self.width = int.from_bytes(f.read(2), byteorder='big')
                self.height = int.from_bytes(f.read(2), byteorder='big')
                
                # Read lengths
                r_length = int.from_bytes(f.read(4), byteorder='big')
                g_length = int.from_bytes(f.read(4), byteorder='big')
                b_length = int.from_bytes(f.read(4), byteorder='big')
                
                # Read encoded values for each channel
                def read_encoded_values(length):
                    values = []
                    for _ in range(length):
                        value = int.from_bytes(f.read(2), byteorder='big')
                        values.append(value)
                    return values
                
                r_encoded = read_encoded_values(r_length)
                g_encoded = read_encoded_values(g_length)
                b_encoded = read_encoded_values(b_length)
            
            # Decode each channel
            r_string = self.lzw_r.decode(r_encoded)
            g_string = self.lzw_g.decode(g_encoded)
            b_string = self.lzw_b.decode(b_encoded)
            
            # Convert to numpy arrays
            r_array = np.array([ord(c) for c in r_string], dtype=np.uint8).reshape((self.height, self.width))
            g_array = np.array([ord(c) for c in g_string], dtype=np.uint8).reshape((self.height, self.width))
            b_array = np.array([ord(c) for c in b_string], dtype=np.uint8).reshape((self.height, self.width))
            
            # Create PIL images for each channel
            r_img = Image.fromarray(r_array, mode='L')
            g_img = Image.fromarray(g_array, mode='L')
            b_img = Image.fromarray(b_array, mode='L')
            
            # Merge channels
            restored_image = Image.merge('RGB', (r_img, g_img, b_img))
            
            # Save restored image
            output_path = compressed_file_path.replace('.level4.compressed', '_level4_restored.bmp')
            restored_image.save(output_path, format='BMP')
            print(f"Restored image saved: {output_path}")
            
            return restored_image
            
        except Exception as e:
            print(f"Error during Level 4 decompression: {str(e)}")
            raise e