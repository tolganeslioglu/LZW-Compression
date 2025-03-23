import numpy as np
from PIL import Image
import os
from LZW import LZWCoding

class Level5Compressor:
    def __init__(self, image_path):
        self.image_path = image_path
        # Initialize LZW coders for each channel's differences
        self.lzw_r = LZWCoding(os.path.splitext(image_path)[0] + "_r", 'level5')
        self.lzw_g = LZWCoding(os.path.splitext(image_path)[0] + "_g", 'level5')
        self.lzw_b = LZWCoding(os.path.splitext(image_path)[0] + "_b", 'level5')
        self.original_size = os.path.getsize(image_path)
        self.width = None
        self.height = None
        self.compression_ratio = None
        self.entropy = {"R": 0, "G": 0, "B": 0}
        self.avg_code_length = {"R": 0, "G": 0, "B": 0}

    def calculate_differences(self, img_array):
        """Calculate differences for one channel"""
        height, width = img_array.shape
        diff_image = np.zeros_like(img_array, dtype=np.int16)
        
        # First pixel remains as is
        diff_image[0, 0] = img_array[0, 0]
        
        # Row-wise differences for first row
        for j in range(1, width):
            diff_image[0, j] = int(img_array[0, j]) - int(img_array[0, j-1])
        
        # Column-wise differences for first column
        for i in range(1, height):
            diff_image[i, 0] = int(img_array[i, 0]) - int(img_array[i-1, 0])
        
        # Remaining differences
        for i in range(1, height):
            for j in range(1, width):
                diff_image[i, j] = int(img_array[i, j]) - int(img_array[i, j-1])
        
        return diff_image

    def restore_from_differences(self, diff_image):
        """Restore original channel from differences"""
        height, width = diff_image.shape
        restored = np.zeros_like(diff_image, dtype=np.uint8)
        
        # First pixel
        restored[0, 0] = diff_image[0, 0]
        
        # Restore first row
        for j in range(1, width):
            val = int(restored[0, j-1]) + int(diff_image[0, j])
            restored[0, j] = np.clip(val, 0, 255)
        
        # Restore first column
        for i in range(1, height):
            val = int(restored[i-1, 0]) + int(diff_image[i, 0])
            restored[i, 0] = np.clip(val, 0, 255)
        
        # Restore remaining pixels
        for i in range(1, height):
            for j in range(1, width):
                val = int(restored[i, j-1]) + int(diff_image[i, j])
                restored[i, j] = np.clip(val, 0, 255)
        
        return restored

    def compress(self):
        print(f"Level 5 - Compressing color image: {self.image_path}")
        try:
            # Read color image
            img = Image.open(self.image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            self.width, self.height = img.size
            print(f"Image dimensions: {self.width}x{self.height}")
            
            # Split into RGB channels
            r, g, b = img.split()
            
            # Calculate differences for each channel
            r_diff = self.calculate_differences(np.array(r))
            g_diff = self.calculate_differences(np.array(g))
            b_diff = self.calculate_differences(np.array(b))
            
            # Convert differences to strings (shift range from [-255,255] to [0,511])
            def diff_to_string(diff_array):
                return ''.join([chr((int(x) + 255) & 0x1FF) for x in diff_array.flatten()])
            
            r_string = diff_to_string(r_diff)
            g_string = diff_to_string(g_diff)
            b_string = diff_to_string(b_diff)
            
            # Compress each channel's differences
            r_encoded = self.lzw_r.encode(r_string)
            g_encoded = self.lzw_g.encode(g_string)
            b_encoded = self.lzw_b.encode(b_string)
            
            # Save compressed file
            output_path = f"{self.image_path}.level5.compressed"
            with open(output_path, 'wb') as f:
                # Write metadata
                f.write(self.width.to_bytes(2, byteorder='big'))
                f.write(self.height.to_bytes(2, byteorder='big'))
                
                # Write first pixels
                f.write(int(r_diff[0, 0]).to_bytes(1, byteorder='big'))
                f.write(int(g_diff[0, 0]).to_bytes(1, byteorder='big'))
                f.write(int(b_diff[0, 0]).to_bytes(1, byteorder='big'))
                
                # Write lengths of encoded data
                f.write(len(r_encoded).to_bytes(4, byteorder='big'))
                f.write(len(g_encoded).to_bytes(4, byteorder='big'))
                f.write(len(b_encoded).to_bytes(4, byteorder='big'))
                
                # Write encoded data
                for encoded_data in [r_encoded, g_encoded, b_encoded]:
                    for value in encoded_data:
                        f.write(value.to_bytes(2, byteorder='big'))
            
            # Calculate statistics
            self.calculate_statistics(r_diff, g_diff, b_diff, r_encoded, g_encoded, b_encoded)
            
            return True
            
        except Exception as e:
            print(f"Error during Level 5 compression: {str(e)}")
            raise e

    def decompress(self, compressed_file_path):
        try:
            print(f"Level 5 - Decompressing file: {compressed_file_path}")
            
            with open(compressed_file_path, 'rb') as f:
                # Read metadata
                self.width = int.from_bytes(f.read(2), byteorder='big')
                self.height = int.from_bytes(f.read(2), byteorder='big')
                
                # Read first pixels
                r_first = int.from_bytes(f.read(1), byteorder='big')
                g_first = int.from_bytes(f.read(1), byteorder='big')
                b_first = int.from_bytes(f.read(1), byteorder='big')
                
                # Read lengths
                r_length = int.from_bytes(f.read(4), byteorder='big')
                g_length = int.from_bytes(f.read(4), byteorder='big')
                b_length = int.from_bytes(f.read(4), byteorder='big')
                
                # Read encoded values
                def read_encoded_values(length):
                    return [int.from_bytes(f.read(2), byteorder='big') for _ in range(length)]
                
                r_encoded = read_encoded_values(r_length)
                g_encoded = read_encoded_values(g_length)
                b_encoded = read_encoded_values(b_length)
            
            # Decode differences
            def decode_channel(encoded_values, lzw):
                decoded = lzw.decode(encoded_values)
                diff_values = np.array([(ord(char) - 255) for char in decoded], 
                                     dtype=np.int16)
                return diff_values[:self.width*self.height].reshape((self.height, self.width))
            
            r_diff = decode_channel(r_encoded, self.lzw_r)
            g_diff = decode_channel(g_encoded, self.lzw_g)
            b_diff = decode_channel(b_encoded, self.lzw_b)
            
            # Restore original channels
            r_array = self.restore_from_differences(r_diff)
            g_array = self.restore_from_differences(g_diff)
            b_array = self.restore_from_differences(b_diff)
            
            # Create channel images
            r_img = Image.fromarray(r_array, mode='L')
            g_img = Image.fromarray(g_array, mode='L')
            b_img = Image.fromarray(b_array, mode='L')
            
            # Merge channels
            restored_image = Image.merge('RGB', (r_img, g_img, b_img))
            
            # Save restored image
            output_path = compressed_file_path.replace('.level5.compressed', '_level5_restored.bmp')
            restored_image.save(output_path, format='BMP')
            print(f"Restored image saved: {output_path}")
            
            return restored_image
            
        except Exception as e:
            print(f"Error during Level 5 decompression: {str(e)}")
            raise e

    def calculate_statistics(self, r_diff, g_diff, b_diff, r_encoded, g_encoded, b_encoded):
        # Calculate entropy for each channel
        for channel, arr in [("R", r_diff), ("G", g_diff), ("B", b_diff)]:
            values = arr.flatten() + 255  # Shift to positive range
            counts = np.bincount(values)
            probabilities = counts[counts > 0] / len(values)
            self.entropy[channel] = -np.sum(probabilities * np.log2(probabilities))
        
        # Calculate average code length
        total_pixels = self.width * self.height
        self.avg_code_length["R"] = len(r_encoded) * self.lzw_r.codelength / total_pixels
        self.avg_code_length["G"] = len(g_encoded) * self.lzw_g.codelength / total_pixels
        self.avg_code_length["B"] = len(b_encoded) * self.lzw_b.codelength / total_pixels
        
        # Calculate compression ratio
        total_compressed_bits = sum(len(x) * self.lzw_r.codelength for x in [r_encoded, g_encoded, b_encoded])
        compressed_size = total_compressed_bits / 8
        self.compression_ratio = self.original_size / compressed_size
        
        print(f"\nLevel 5 Compression Statistics:")
        for channel in ["R", "G", "B"]:
            print(f"{channel} Channel:")
            print(f"  Entropy: {self.entropy[channel]:.2f} bits/pixel")
            print(f"  Average Code Length: {self.avg_code_length[channel]:.2f} bits/pixel")
        print(f"Overall Compression Ratio: {self.compression_ratio:.2f}")