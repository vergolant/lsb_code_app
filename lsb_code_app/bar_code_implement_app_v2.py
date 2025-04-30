import cv2
import numpy as np
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox

def generate_code128_barcode(text, height, width):
    # Генерируем штрихкод Code128 в PIL Image через python-barcode
    CODE128 = barcode.get_barcode_class('code128')
    code128 = CODE128(text, writer=ImageWriter())
    
    # Сохраняем во временный объект PIL Image (в памяти)
    pil_img = code128.render(writer_options={"module_height": 15.0, "quiet_zone": 1.0})
    
    # Конвертируем в numpy array (grayscale)
    barcode_np = np.array(pil_img.convert('L'))
    
    # Инвертируем цвета: у python-barcode белый фон и черные полосы,
    # нам удобнее наоборот (чтобы белый фон был 255)
    barcode_np = 255 - barcode_np
    
    # Масштабируем до нужного размера (width x height)
    barcode_resized = cv2.resize(barcode_np, (width, height), interpolation=cv2.INTER_AREA)
    
    # Конвертируем в BGR (3 канала), чтобы совместить с цветным изображением
    barcode_bgr = cv2.cvtColor(barcode_resized, cv2.COLOR_GRAY2BGR)
    
    return barcode_bgr

def add_gray_borders(barcode_img):
    # Скопируем картинку для рисования
    bordered = barcode_img.copy()
    
    # Переводим в градации серого
    gray = cv2.cvtColor(barcode_img, cv2.COLOR_BGR2GRAY)
    
    # Инвертируем бинаризацию: тёмные полосы станут белыми на чёрном фоне
    _, binary_inv = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    
    # Ищем все контуры (каждая полоса — свой контур)
    contours, _ = cv2.findContours(binary_inv, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    # Проходим по всем контурам
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Фильтрация мелких «шумовых» контуров (по необходимости)
        if w > 2 and h > 2:
            # Рисуем прямоугольник-рамку вокруг каждого элемента
            cv2.rectangle(
                bordered,
                (x, y),
                (x + w, y + h),
                (128, 128, 128),  # или (0,0,0) для чёрного
                thickness=1
            )
    return bordered

def embed_alpha_blend(image, barcode_img, alpha=0.3):
    if image.shape != barcode_img.shape:
        barcode_img = cv2.resize(barcode_img, (image.shape[1], image.shape[0]))
    
    # Добавляем серые рамки перед встраиванием
    barcode_with_borders = add_gray_borders(barcode_img)
    
    # Создаем маску для штрихкода (все, что не белый фон)
    mask = np.any(barcode_with_borders < [250, 250, 250], axis=2)
    
    # Применяем альфа-блендинг только к синему каналу
    image_blue = image[:, :, 0].astype(float)
    bc_blue = barcode_with_borders[:, :, 0].astype(float)
    
    blended = (1 - alpha) * image_blue + alpha * bc_blue
    blended = np.clip(blended, 0, 255).astype(np.uint8)
    
    # Применяем изменения только в области штрихкода
    image[:, :, 0][mask] = blended[mask]
    
    return image

def embed_lsb(image, barcode_img):
    if image.shape != barcode_img.shape:
        barcode_img = cv2.resize(barcode_img, (image.shape[1], image.shape[0]))
    
    # Добавляем серые рамки перед встраиванием
    barcode_with_borders = add_gray_borders(barcode_img)
    
    # Преобразуем в grayscale и бинаризуем
    gray_bc = cv2.cvtColor(barcode_with_borders, cv2.COLOR_BGR2GRAY)
    _, bin_bc = cv2.threshold(gray_bc, 200, 1, cv2.THRESH_BINARY_INV)
    
    # Встраиваем в младший бит синего канала
    blue_channel = image[:, :, 0]
    blue_channel &= 0b11111110
    blue_channel |= bin_bc.astype(np.uint8)
    
    image[:, :, 0] = blue_channel
    
    return image

def embed_barcode(image_path, text_to_encode, output_path,
                 use_alpha_blend=False,
                 use_lsb=False,
                 alpha=0.3):
    
    image = cv2.imread(image_path)
    
    if image is None:
        messagebox.showerror("Ошибка", "Не удалось загрузить изображение.")
        return
    
    h, w, _ = image.shape
    
    if not text_to_encode:
        messagebox.showerror("Ошибка", "Введите текст для генерации штрихкода.")
        return
    
    if not use_alpha_blend and not use_lsb:
        messagebox.showwarning("Внимание", "Выберите хотя бы один способ встраивания.")
        return
    
    # Генерируем штрихкод
    bc_image = generate_code128_barcode(text_to_encode, h, w)
    
    if use_alpha_blend:
        image = embed_alpha_blend(image, bc_image, alpha)
        
    if use_lsb:
        image = embed_lsb(image, bc_image)
        
    success = cv2.imwrite(output_path, image)
    
    if success:
        messagebox.showinfo("Успех", f"Изображение сохранено как {output_path}")
    else:
        messagebox.showerror("Ошибка", "Не удалось сохранить изображение.")
# --- GUI ---

root=tk.Tk()
root.title("Внедрение Code128 штрихкода в изображение")

frame_image=tk.Frame(root)
frame_image.pack(pady=5)

tk.Label(frame_image,text="Изображение:").pack(side=tk.LEFT)
entry_image=tk.Entry(frame_image,width=50)
entry_image.pack(side=tk.LEFT,padx=5)

def load_image():
   file_path=filedialog.askopenfilename(title="Выберите изображение",
                                        filetypes=[("Image files","*.jpg;*.jpeg;*.png")])
   if file_path:
       entry_image.delete(0,tk.END)
       entry_image.insert(0,file_path)

btn_load_img=tk.Button(frame_image,text="Загрузить", command=load_image)
btn_load_img.pack(side=tk.LEFT)

frame_text=tk.Frame(root)
frame_text.pack(pady=5)

tk.Label(frame_text,text="Текст для Code128:").pack(side=tk.LEFT)
entry_text=tk.Entry(frame_text,width=50)
entry_text.pack(side=tk.LEFT,padx=5)

frame_options=tk.LabelFrame(root,text="Опции внедрения")
frame_options.pack(padx=10,pady=10)

var_alpha=tk.BooleanVar(value=True)
var_lsb=tk.BooleanVar(value=False)

chk_alpha=tk.Checkbutton(frame_options,text="Альфа-блендинг (частичное смешивание)", variable=var_alpha)
chk_alpha.grid(row=0,column=0,columnspan=2,padx=5,pady=5)

chk_lsb=tk.Checkbutton(frame_options,text="Встраивание в младший бит синего канала (LSB)", variable=var_lsb)
chk_lsb.grid(row=1,column=0,columnspan=2,padx=5,pady=5)

tk.Label(frame_options,text="Альфа (прозрачность от 0 до 1):").grid(row=2,column=0,padx=5,pady=5)
entry_alpha=tk.Entry(frame_options,width=5)
entry_alpha.insert(0,"0.3")
entry_alpha.grid(row=2,column=1,padx=5,pady=5)

def process_images():
   image_path=entry_image.get()
   text_to_encode=entry_text.get()

   if not image_path or not text_to_encode:
       messagebox.showerror("Ошибка","Пожалуйста выберите изображение и введите текст.")
       return
   
   output_path=filedialog.asksaveasfilename(defaultextension=".jpg",
                                           title="Сохранить как",
                                           filetypes=[("JPEG files","*.jpg"), ("PNG files","*.png")])
   if not output_path:
       return
   
   use_alpha_blend_val=var_alpha.get()
   use_lsb_val       =var_lsb.get()
   
   try:
       alpha_val_float=float(entry_alpha.get())
       if not (0 <= alpha_val_float <=1):
           raise ValueError()
   except ValueError:
       messagebox.showerror("Ошибка","Введите корректное значение альфа (от 0 до 1).")
       return
   
   embed_barcode(image_path,text_to_encode,output_path,use_alpha_blend_val,use_lsb_val,alpha_val_float)

btn_process=tk.Button(root,text="Внедрить штрихкод",command=process_images)
btn_process.pack(pady=10)

root.mainloop()