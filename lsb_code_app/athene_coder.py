import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
import uuid
from PIL import Image, ImageTk

class UUIDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("UUID Image Processor")
        self.processor = UUIDImageProcessor()
        
        self.create_widgets()
    
    def create_widgets(self):
        # Создаем Notebook (вкладки)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(padx=10, pady=10, expand=True, fill='both')

        # Вкладка для кодирования
        self.encode_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.encode_frame, text="Encode UUID")
        self.create_encode_ui()
        
        # Вкладка для декодирования
        self.decode_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.decode_frame, text="Decode UUID")
        self.create_decode_ui()
    
    def create_encode_ui(self):
        # Выбор исходного изображения
        ttk.Label(self.encode_frame, text="Source Image:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.source_path = tk.StringVar()
        ttk.Entry(self.encode_frame, textvariable=self.source_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.encode_frame, text="Browse", command=self.browse_source_image).grid(row=0, column=2, padx=5, pady=5)

        # Поле для ввода UUID
        ttk.Label(self.encode_frame, text="UUID:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.uuid_entry = ttk.Entry(self.encode_frame, width=50)
        self.uuid_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(self.encode_frame, text="Generate UUID", command=self.generate_uuid).grid(row=1, column=2, padx=5, pady=5)

        # Кнопка обработки
        ttk.Button(self.encode_frame, text="Encode UUID", command=self.encode_image).grid(row=2, column=1, pady=10)

        # Превью изображения
        self.preview_label = ttk.Label(self.encode_frame)
        self.preview_label.grid(row=3, column=0, columnspan=3, pady=10)

    def create_decode_ui(self):
        # Выбор закодированного изображения
        ttk.Label(self.decode_frame, text="Encoded Image:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.encoded_path = tk.StringVar()
        ttk.Entry(self.decode_frame, textvariable=self.encoded_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.decode_frame, text="Browse", command=self.browse_encoded_image).grid(row=0, column=2, padx=5, pady=5)

        # Кнопка обработки
        ttk.Button(self.decode_frame, text="Decode UUID", command=self.decode_image).grid(row=1, column=1, pady=10)

        # Отображение результата
        self.result_label = ttk.Label(self.decode_frame, text="Extracted UUID: ", font=('Arial', 10))
        self.result_label.grid(row=2, column=0, columnspan=3, pady=10)

    def browse_source_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if path:
            self.source_path.set(path)
            self.show_preview(path)

    def browse_encoded_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg")])
        if path:
            self.encoded_path.set(path)

    def generate_uuid(self):
        new_uuid = str(uuid.uuid4())
        self.uuid_entry.delete(0, tk.END)
        self.uuid_entry.insert(0, new_uuid)

    def show_preview(self, image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preview: {str(e)}")

    def encode_image(self):
        src_path = self.source_path.get()
        uuid_str = self.uuid_entry.get()
        
        if not src_path:
            messagebox.showerror("Error", "Please select source image")
            return
        
        if not uuid_str or len(uuid_str) != 36:
            messagebox.showerror("Error", "Invalid UUID format")
            return
        
        try:
            modified_image = self.processor.embed_uuid(src_path, uuid_str)
            save_path = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg")])
            
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(modified_image)
                messagebox.showinfo("Success", "UUID successfully encoded!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Encoding failed: {str(e)}")

    def decode_image(self):
        encoded_path = self.encoded_path.get()
        
        if not encoded_path:
            messagebox.showerror("Error", "Please select encoded image")
            return
        
        try:
            with open(encoded_path, "rb") as f:
                image_data = f.read()
            
            extracted_uuid = self.processor.extract_uuid(image_data)
            if extracted_uuid:
                self.result_label.config(text=f"Extracted UUID: {extracted_uuid}")
                messagebox.showinfo("Success", "UUID successfully extracted!")
            else:
                messagebox.showerror("Error", "No UUID found in image")
        
        except Exception as e:
            messagebox.showerror("Error", f"Decoding failed: {str(e)}")

class UUIDImageProcessor:
    def __init__(self):
        self.block_size = 8
        self.uuid_length = 36

    def embed_uuid(self, image_path, uuid_str):
        """Внедряет UUID в изображение"""
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Не удалось загрузить изображение")

        bits = self._uuid_to_bits(uuid_str)
        
        for channel in range(3):
            img[:, :, channel] = self._encode_bits_to_image(
                img[:, :, channel], 
                bits
            )
        
        success, encoded_image = cv2.imencode('.jpg', img)
        if not success:
            raise ValueError("Ошибка сохранения изображения")
        
        return encoded_image.tobytes()

    def _encode_bits_to_image(self, image, bits):
        """Внедрение битов в изображение"""
        height, width = image.shape
        bit_index = 0
        
        for y in range(0, height, self.block_size):
            for x in range(0, width, self.block_size):
                if bit_index >= len(bits):
                    return image
                
                block = image[y:y+self.block_size, x:x+self.block_size]
                M = np.float32([[1, 0.02, 0], [0.02, 1, 0]] if bits[bit_index] == '1' 
                              else [[1, -0.02, 0], [-0.02, 1, 0]])
                
                transformed = cv2.warpAffine(
                    block, M, 
                    (self.block_size, self.block_size),
                    flags=cv2.INTER_LINEAR
                )
                image[y:y+self.block_size, x:x+self.block_size] = transformed
                bit_index += 1
        return image

    def _uuid_to_bits(self, uuid_str):
        return ''.join(format(ord(c), '08b') for c in uuid_str)

    def extract_uuid(self, image_data):
        img = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        extracted_bits = self._decode_bits_from_image(img[:, :, 0])  # Используем только красный канал
        return self._bits_to_uuid(extracted_bits)

    def _decode_bits_from_image(self, image):
        bits = []
        for y in range(0, image.shape[0], self.block_size):
            for x in range(0, image.shape[1], self.block_size):
                block = image[y:y+self.block_size, x:x+self.block_size]
                grad_x = np.mean(block[:, 1:] - block[:, :-1])
                grad_y = np.mean(block[1:, :] - block[:-1, :])
                bits.append('1' if grad_x + grad_y > 0 else '0')
        return bits

    def _bits_to_uuid(self, bits):
        try:
            chars = []
            for i in range(0, len(bits), 8):
                byte = chr(int(''.join(bits[i:i+8]), 2))
                chars.append(byte)
            return ''.join(chars)[:self.uuid_length]
        except:
            return None
    
    def embed_uuid(self, image_path, uuid_str):
        """Внедряет UUID в изображение и сохраняет результат"""
        # Загружаем изображение
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Не удалось загрузить изображение")
        
        # Конвертируем UUID в биты
        bits = self._uuid_to_bits(uuid_str)
        
        # Внедряем биты в каждый канал (для надежности)
        for channel in range(3):
            img[:, :, channel] = self._encode_bits_to_image(img[:, :, channel], bits)
        
        # Конвертируем в JPEG и возвращаем как bytes
        success, encoded_image = cv2.imencode('.jpg', img)
        if not success:
            raise ValueError("Не удалось сохранить изображение")
        
        return encoded_image.tobytes()
    
    def extract_uuid(self, image_data):
        """Извлекает UUID из изображения"""
        # Загружаем изображение из bytes
        img = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Не удалось загрузить изображение")
        
        # Извлекаем биты из каждого канала и выбираем наиболее вероятный UUID
        possible_uuids = []
        for channel in range(3):
            bits = self._decode_bits_from_image(img[:, :, channel])
            uuid_str = self._bits_to_uuid(bits)
            if uuid_str:
                possible_uuids.append(uuid_str)
        
        # Выбираем UUID, который встречается чаще всего
        if not possible_uuids:
            return None
        
        # Возвращаем первый UUID (можно реализовать более сложную логику голосования)
        return possible_uuids[0]

if __name__ == "__main__":
    root = tk.Tk()
    app = UUIDApp(root)
    root.mainloop()