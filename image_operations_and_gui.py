from PIL import Image, ImageTk
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from image_compressor import ImageCompressor  # Level2
from level3_compressor import Level3Compressor
from level4_compressor import Level4Compressor
from level5_compressor import Level5Compressor
from LZW import LZWCoding

# Declaration and initialization of the global variables used in this program
# -------------------------------------------------------------------------------
# get the current directory where this program is placed
current_directory = os.path.dirname(os.path.realpath(__file__))
image_file_path = current_directory + '/thumbs_up.bmp'   # default image

# Main function where this program starts execution
# -------------------------------------------------------------------------------
def start():
    # Create window
    gui = tk.Tk()
    gui.title('Image Operations')
    gui['bg'] = 'White'
    
    # Create main frame with less padding
    frame = tk.Frame(gui)
    frame.grid(row=0, column=0, padx=10, pady=5)
    frame['bg'] = 'DodgerBlue4'
    
    # Create side-by-side panels frame with fixed size
    images_frame = tk.Frame(frame, bg='DodgerBlue4')
    images_frame.grid(row=0, column=0, columnspan=2, pady=5)
    
    # Left panel - Original image
    left_frame = tk.LabelFrame(images_frame, text="Original Image", 
                             bg='DodgerBlue4', fg='white')
    left_frame.grid(row=0, column=0, padx=5)
    
    gui_img = ImageTk.PhotoImage(file=image_file_path)
    left_panel = tk.Label(left_frame, image=gui_img)
    left_panel.grid(padx=5, pady=5)
    left_panel.photo_ref = gui_img
    
    # Get dimensions from original image
    img_width = gui_img.width()
    img_height = gui_img.height()
    
    # Right panel - Decompressed image (fixed 250x250 size)
    right_frame = tk.LabelFrame(images_frame, text="Decompressed Image", 
                              bg='DodgerBlue4', fg='white')
    right_frame.grid(row=0, column=1, padx=5)
    
    # Create an empty image of 250x250 pixels
    empty_image = Image.new('RGB', (250, 250), 'white')
    empty_photo = ImageTk.PhotoImage(empty_image)
    
    right_panel = tk.Label(right_frame, image=empty_photo, bg='white')
    right_panel.grid(padx=5, pady=5)
    right_panel.photo_ref = empty_photo  # Keep reference to prevent garbage collection
    
    # Image processing buttons in a compact row
    btn_frame = tk.Frame(frame, bg='DodgerBlue4')
    btn_frame.grid(row=1, column=0, columnspan=2, pady=2)
    
    buttons = [
        ('Open Image', lambda: open_image(left_panel, right_panel)),
        ('Grayscale', lambda: display_in_grayscale(left_panel)),
        ('Red', lambda: display_color_channel(left_panel, 'red')),
        ('Green', lambda: display_color_channel(left_panel, 'green')),
        ('Blue', lambda: display_color_channel(left_panel, 'blue'))
    ]
    
    for i, (text, command) in enumerate(buttons):
        btn = tk.Button(btn_frame, text=text, width=8, command=command)
        btn.grid(row=0, column=i, padx=2)
    
    # Create compression buttons with optimized spacing
    create_buttons(gui, left_panel, right_panel)
    
    gui.mainloop()

# Function for opening an image from a file
# -------------------------------------------------------------------------------
def open_image(left_panel, right_panel):
   global image_file_path   # to modify the global variable image_file_path
   # get the path of the image file selected by the user (.bmp is an uncompressed
   # image format that is suitable for this project)
   file_path = filedialog.askopenfilename(initialdir = current_directory, 
                                          title = 'Select an image file', 
                                          filetypes = [('bmp files', '*.bmp')])
   # display an warning message when the user does not select an image file
   if file_path == '':
      messagebox.showinfo('Warning', 'No image file is selected/opened.')
   # otherwise modify the global variable image_file_path and the displayed image
   else:
      image_file_path = file_path
      img = ImageTk.PhotoImage(file = image_file_path) 
      left_panel.config(image = img) 
      left_panel.photo_ref = img

# Function for displaying the current image in grayscale
# -------------------------------------------------------------------------------
def display_in_grayscale(image_panel):
   # open the current image as a PIL image
   img_rgb = Image.open(image_file_path)
   # convert the image to grayscale (img_grayscale has only one color channel 
   # whereas img_rgb has 3 color channels as red, green and blue)
   img_grayscale = img_rgb.convert('L')
   print('\nFor the color image')
   print('----------------------------------------------------------------------')
   width, height = img_rgb.size
   print('the width in pixels:', width, 'and the height in pixels:', height)
   img_rgb_array = pil_to_np(img_rgb)
   print('the dimensions of the image array:', img_rgb_array.shape)
   print('\nFor the grayscale image')
   print('----------------------------------------------------------------------')
   width, height = img_grayscale.size
   print('the width in pixels:', width, 'and the height in pixels:', height)
   img_grayscale_array = pil_to_np(img_grayscale)
   print('the dimensions of the image array:', img_grayscale_array.shape)
   # modify the displayed image
   img = ImageTk.PhotoImage(image = img_grayscale) 
   image_panel.config(image = img) 
   image_panel.photo_ref = img

# Function for displaying a given color channel of the current image
# -------------------------------------------------------------------------------
def display_color_channel(image_panel, channel):
   # red channel -> 0, green channel -> 1 and blue channel -> 2
   if channel == 'red':
      channel_index = 0
   elif channel == 'green':
      channel_index = 1
   else:
      channel_index = 2
   # open the current image as a PIL image
   img_rgb = Image.open(image_file_path)
   # convert the current image to a numpy array
   image_array = pil_to_np(img_rgb)
   # traverse all the pixels in the image array
   n_rows = image_array.shape[0]
   n_cols = image_array.shape[1]
   for row in range(n_rows):
      for col in range(n_cols):
         # make all the values 0 for the color channels except the given channel
         for rgb in range(3):
            if (rgb != channel_index):
               image_array[row][col][rgb] = 0
   # convert the modified image array (numpy) to a PIL image
   pil_img = np_to_pil(image_array)
   # modify the displayed image
   img = ImageTk.PhotoImage(image = pil_img) 
   image_panel.config(image = img) 
   image_panel.photo_ref = img

# Function that converts a given PIL image to a numpy array and returns the array
# -------------------------------------------------------------------------------
def pil_to_np(img):
   img_array = np.array(img)
   return img_array

# Function that converts a given numpy array to a PIL image and returns the image
# -------------------------------------------------------------------------------
def np_to_pil(img_array):
   img = Image.fromarray(np.uint8(img_array))
   return img

# Function for compressing the current image using Level 2 compression
# -------------------------------------------------------------------------------
def compress_image(image_panel):
    global image_file_path
    if image_file_path:
        compressor = ImageCompressor(image_file_path)
        compressor.compress()
        messagebox.showinfo("Compression Complete", 
                          f"Image compressed!\nCompression Ratio: {compressor.compression_ratio:.2f}")
    else:
        messagebox.showerror("Error", "Please load an image first!")

# Function for decompressing a Level 2 compressed image file
# -------------------------------------------------------------------------------
def decompress_image(right_panel):
    # Sıkıştırılmış dosyayı seç
    compressed_file = filedialog.askopenfilename(
        title="Select compressed image file",
        filetypes=[("Compressed files", "*.compressed")]
    )
    
    if compressed_file:
        try:
            # Sıkıştırılmış dosya yolunu kullanarak ImageCompressor oluştur
            compressor = ImageCompressor(compressed_file)
            restored_image = compressor.decompress(compressed_file)
            
            # Restore edilmiş görüntüyü göster
            img = ImageTk.PhotoImage(image=restored_image)
            right_panel.config(image=img)
            right_panel.photo_ref = img
            
            messagebox.showinfo("Success", "Image decompressed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to decompress image: {str(e)}")

# Function for compressing the current image using Level 3 compression
# -------------------------------------------------------------------------------
def compress_image_level3(image_panel):
    global image_file_path
    if image_file_path:
        compressor = Level3Compressor(image_file_path)
        compressor.compress()
        messagebox.showinfo("Level 3 Compression Complete", 
                          f"Image compressed using Level 3!\nCompression Ratio: {compressor.compression_ratio:.2f}")
    else:
        messagebox.showerror("Error", "Please load an image first!")

# Function for decompressing a Level 3 compressed image file
# -------------------------------------------------------------------------------
def decompress_image_level3(right_panel):
    try:
        # Use wildcard pattern for macOS
        compressed_file = filedialog.askopenfilename(
            title="Select Level 3 compressed image file",
            initialdir=current_directory,
            filetypes=[("Compressed files", "*.compressed")]
        )
        
        if compressed_file:
            # Check file extension manually
            if not compressed_file.endswith('.level3.compressed'):
                messagebox.showerror("Error", "Please select a .level3.compressed file")
                return
                
            base_name = os.path.splitext(os.path.splitext(compressed_file)[0])[0]
            compressor = Level3Compressor(base_name)
            restored_image = compressor.decompress(compressed_file)
            
            img = ImageTk.PhotoImage(image=restored_image)
            right_panel.config(image=img)
            right_panel.photo_ref = img
            
            messagebox.showinfo("Success", "Image decompressed successfully using Level 3!")
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to decompress Level 3 image: {str(e)}")

# Function for compressing the current image using Level 4 compression
# -------------------------------------------------------------------------------
def compress_image_level4(image_panel):
    global image_file_path
    if image_file_path:
        compressor = Level4Compressor(image_file_path)
        compressor.compress()
        messagebox.showinfo("Level 4 Compression Complete", 
                          f"Color image compressed using Level 4!\nCompression Ratio: {compressor.compression_ratio:.2f}")
    else:
        messagebox.showerror("Error", "Please load an image first!")

# Function for decompressing a Level 4 compressed image file
# -------------------------------------------------------------------------------
def decompress_image_level4(right_panel):
    try:
        # Use wildcard pattern for macOS
        compressed_file = filedialog.askopenfilename(
            title="Select Level 4 compressed image file",
            initialdir=current_directory,
            filetypes=[("Compressed files", "*.compressed")]
        )
        
        if compressed_file:
            # Check file extension manually
            if not compressed_file.endswith('.level4.compressed'):
                messagebox.showerror("Error", "Please select a .level4.compressed file")
                return
                
            compressor = Level4Compressor(compressed_file)
            restored_image = compressor.decompress(compressed_file)
            
            img = ImageTk.PhotoImage(image=restored_image)
            right_panel.config(image=img)
            right_panel.photo_ref = img
            
            messagebox.showinfo("Success", "Image decompressed successfully using Level 4!")
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to decompress Level 4 image: {str(e)}")

# Function for compressing the current image using Level 5 compression
# -------------------------------------------------------------------------------
def compress_image_level5(image_panel):
    global image_file_path
    if image_file_path:
        compressor = Level5Compressor(image_file_path)
        compressor.compress()
        messagebox.showinfo("Level 5 Compression Complete", 
                          f"Color image compressed using Level 5!\nCompression Ratio: {compressor.compression_ratio:.2f}")
    else:
        messagebox.showerror("Error", "Please load an image first!")

# Function for decompressing a Level 5 compressed image file
# -------------------------------------------------------------------------------
def decompress_image_level5(right_panel):
    compressed_file = filedialog.askopenfilename(
        title="Select Level 5 compressed image file",
        initialdir=current_directory,
        filetypes=[("Compressed files", "*.compressed")]
    )
    
    if compressed_file:
        if not compressed_file.endswith('.level5.compressed'):
            messagebox.showerror("Error", "Please select a .level5.compressed file")
            return
            
        try:
            compressor = Level5Compressor(compressed_file)
            restored_image = compressor.decompress(compressed_file)
            
            img = ImageTk.PhotoImage(image=restored_image)
            right_panel.config(image=img)
            right_panel.photo_ref = img
            
            messagebox.showinfo("Success", "Image decompressed successfully using Level 5!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to decompress Level 5 image: {str(e)}")

def compress_text_level1():
    text_file = filedialog.askopenfilename(
        title="Select text file to compress",
        initialdir=current_directory,
        filetypes=[("Text files", "*.txt")]
    )
    
    if text_file:
        try:
            # Get original file size
            original_size = os.path.getsize(text_file)
            
            # Create LZW instance with full path
            lzw = LZWCoding(os.path.splitext(text_file)[0], 'level1')
            
            # Compress the file and get statistics
            output_path, stats = lzw.compress_text_file()
            
            # Calculate compression ratio
            compressed_size = os.path.getsize(output_path)
            compression_ratio = original_size / compressed_size
            
            # Show statistics
            stats_message = (
                f"Text Compression Statistics:\n"
                f"------------------------\n"
                f"Original Size: {original_size:,} bytes\n"
                f"Compressed Size: {compressed_size:,} bytes\n"
                f"Compression Ratio: {compression_ratio:.2f}\n"
                f"Dictionary Size: {stats['dict_size']} entries\n"
                f"Average Code Length: {stats['avg_code_length']:.2f} bits\n"
                f"\nCompressed file saved as:\n{output_path}"
            )
            
            messagebox.showinfo("Compression Complete", stats_message)
            
        except Exception as e:
            print(f"Compression error: {str(e)}")
            messagebox.showerror("Error", f"Failed to compress text file: {str(e)}")

def decompress_text_level1():
    compressed_file = filedialog.askopenfilename(
        title="Select compressed text file",
        initialdir=current_directory,
        filetypes=[("Binary files", "*.bin")]
    )
    
    if compressed_file:
        try:
            # Create LZW instance with full path
            lzw = LZWCoding(os.path.splitext(compressed_file)[0], 'level1')
            
            # Decompress the file
            output_path = lzw.decompress_text_file()
            
            # Verify file integrity
            original_file = f"{os.path.splitext(compressed_file)[0]}.txt"
            if os.path.exists(original_file):
                with open(original_file, 'r', encoding='utf-8') as f1, \
                     open(output_path, 'r', encoding='utf-8') as f2:
                    original_content = f1.read()
                    decompressed_content = f2.read()
                
                if original_content == decompressed_content:
                    integrity_msg = "\nFile integrity check: PASSED ✓\nDecompressed file is identical to original."
                else:
                    integrity_msg = "\nFile integrity check: FAILED ✗\nDecompressed file differs from original."
            else:
                integrity_msg = "\nFile integrity check: SKIPPED\nOriginal file not found for comparison."
            
            messagebox.showinfo("Decompression Complete", 
                              f"Text file decompressed successfully!\n"
                              f"Saved as: {output_path}\n{integrity_msg}")
            
        except Exception as e:
            print(f"Decompression error: {str(e)}")
            messagebox.showerror("Error", f"Failed to decompress text file: {str(e)}")

# Function for creating buttons
# ----------------------------------------------------------------------------------
def create_buttons(window, image_panel, right_panel):
    frame = window.winfo_children()[0]
    
    # Create more compact compression buttons frame
    comp_frame = tk.Frame(frame, bg='DodgerBlue4')
    comp_frame.grid(row=2, column=0, columnspan=2, pady=2)
    
    # Text compression (Level 1)
    text_frame = tk.LabelFrame(comp_frame, text="Level 1 - Text", 
                             bg='DodgerBlue4', fg='white')
    text_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=2, sticky='ew')
    
    tk.Button(text_frame, text="Compress", width=12,
             command=compress_text_level1).grid(row=0, column=0, padx=2, pady=2)
    tk.Button(text_frame, text="Decompress", width=12,
             command=decompress_text_level1).grid(row=0, column=1, padx=2, pady=2)
    
    # Image compression (Levels 2-5)
    img_frame = tk.LabelFrame(comp_frame, text="Image Compression", 
                            bg='DodgerBlue4', fg='white')
    img_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=2, sticky='ew')
    
    # Compression level buttons in a grid with correct parameter handling
    compression_buttons = [
        ("L2", compress_image, decompress_image),  # L2 only needs one parameter
        ("L3", compress_image_level3, decompress_image_level3),
        ("L4", compress_image_level4, decompress_image_level4),
        ("L5", compress_image_level5, decompress_image_level5)
    ]
    
    for i, (level, comp_func, decomp_func) in enumerate(compression_buttons):
        comp_btn = tk.Button(
            img_frame, 
            text=f"Compress {level}", 
            width=12,
            command=lambda f=comp_func, p=image_panel: f(p)
        )
        comp_btn.grid(row=i, column=0, padx=2, pady=2)
        
        decomp_btn = tk.Button(
            img_frame, 
            text=f"Decompress {level}", 
            width=12,
            command=lambda f=decomp_func, p=right_panel: f(p)  # image_panel yerine right_panel kullanın
        )
        decomp_btn.grid(row=i, column=1, padx=2, pady=2)

if __name__== '__main__':
    start()