import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox

def embed_alpha_blend(image, qr_code, center_x, center_y, alpha=0.3):
    for i in range(qr_code.shape[0]):
        for j in range(qr_code.shape[1]):
            qr_pixel = qr_code[i, j]
            if not np.array_equal(qr_pixel, [255, 255, 255]):
                orig_blue = image[center_y + i, center_x + j][0]
                new_blue = int((1 - alpha) * orig_blue + alpha * qr_pixel[0])
                image[center_y + i, center_x + j][0] = new_blue
    return image

def embed_lsb(image, qr_bin, center_x, center_y):
    for i in range(qr_bin.shape[0]):
        for j in range(qr_bin.shape[1]):
            bit = qr_bin[i,j]
            blue_val = image[center_y + i, center_x + j][0]
            blue_val = (blue_val & 0b11111110) | bit
            image[center_y + i, center_x + j][0] = blue_val
    return image

def embed_qr_code(image_path, qr_code_path, output_path,
                  use_alpha_blend=False,
                  use_lsb=False,
                  alpha=0.3):
    image = cv2.imread(image_path)
    if image is None:
        messagebox.showerror("Ошибка", "Не удалось загрузить изображение.")
        return

    qr_color = cv2.imread(qr_code_path)
    if qr_color is None:
        messagebox.showerror("Ошибка", "Не удалось загрузить QR-код.")
        return

    # Изменяем размер QR-кода до 1000x1000 пикселей
    qr_color = cv2.resize(qr_color, (1000, 1000))

    img_height, img_width, _ = image.shape
    center_x = img_width // 2 - qr_color.shape[1] // 2
    center_y = img_height // 2 - qr_color.shape[0] // 2

    if not use_alpha_blend and not use_lsb:
        messagebox.showwarning("Внимание", "Выберите хотя бы один способ встраивания.")
        return

    # Если выбран альфа-блендинг — применяем его первым
    if use_alpha_blend:
        image = embed_alpha_blend(image, qr_color, center_x, center_y, alpha)

    # Если выбран LSB — готовим бинарный QR и внедряем
    if use_lsb:
        # Конвертируем QR в ч/б для LSB
        qr_gray = cv2.cvtColor(qr_color, cv2.COLOR_BGR2GRAY)
        _, qr_bin_inv = cv2.threshold(qr_gray, 127, 1, cv2.THRESH_BINARY_INV)
        image = embed_lsb(image, qr_bin_inv, center_x, center_y)

    cv2.imwrite(output_path, image)
    messagebox.showinfo("Успех", f"Изображение сохранено как {output_path}")

def load_image():
    file_path = filedialog.askopenfilename(title="Выберите изображение",
                                           filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
    if file_path:
        entry_image.delete(0, tk.END)
        entry_image.insert(0,file_path)

def load_qr_code():
    file_path = filedialog.askopenfilename(title="Выберите QR-код",
                                           filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
    if file_path:
        entry_qr.delete(0,tk.END)
        entry_qr.insert(0,file_path)

def process_images():
    image_path = entry_image.get()
    qr_code_path = entry_qr.get()

    if not image_path or not qr_code_path:
        messagebox.showerror("Ошибка", "Пожалуйста выберите изображение и QR-код.")
        return

    output_path = filedialog.asksaveasfilename(defaultextension=".jpg",
                                               title="Сохранить как",
                                               filetypes=[("JPEG files","*.jpg"), ("PNG files","*.png")])
    
    if not output_path:
        return

    use_alpha_blend_val = var_alpha.get()
    use_lsb_val       = var_lsb.get()
    
    try:
        alpha_val_float   = float(entry_alpha.get())
        if not (0 <= alpha_val_float <=1):
            raise ValueError()
    except ValueError:
        messagebox.showerror("Ошибка", "Введите корректное значение альфа (от 0 до 1).")
        return
    
    embed_qr_code(image_path,
                  qr_code_path,
                  output_path,
                  use_alpha_blend=use_alpha_blend_val,
                  use_lsb=use_lsb_val,
                  alpha=alpha_val_float)

# --- GUI ---

root = tk.Tk()
root.title("Внедрение QR-кода в изображение")

# Путь к изображению
tk.Label(root,text="Изображение:").pack()
entry_image=tk.Entry(root,width=50)
entry_image.pack()
btn_load_img=tk.Button(root,text="Загрузить изображение", command=load_image)
btn_load_img.pack()

# Путь к QR-коду
tk.Label(root,text="QR-код:").pack()
entry_qr=tk.Entry(root,width=50)
entry_qr.pack()
btn_load_qr=tk.Button(root,text="Загрузить QR-код", command=load_qr_code)
btn_load_qr.pack()

# Опции внедрения
frame_options=tk.Frame(root)
frame_options.pack(pady=10)

var_alpha=tk.BooleanVar(value=True)
var_lsb=tk.BooleanVar(value=False)

chk_alpha=tk.Checkbutton(frame_options,text="Альфа-блендинг (частичное смешивание)", variable=var_alpha)
chk_alpha.grid(row=0,column=0,columnspan=2,padx=5,pady=5)

chk_lsb=tk.Checkbutton(frame_options,text="Встраивание в младший бит синего канала (LSB)", variable=var_lsb)
chk_lsb.grid(row=1,column=0,columnspan=2,padx=5,pady=5)

tk.Label(frame_options,text="Альфа (прозрачность для блендинга от 0 до 1):").grid(row=2,column=0,padx=5,pady=5)
entry_alpha=tk.Entry(frame_options,width=5)
entry_alpha.insert(0,"0.3")
entry_alpha.grid(row=2,column=1,padx=5,pady=5)

# Кнопка запуска обработки
btn_process=tk.Button(root,text="Внедрить QR-код", command=process_images)
btn_process.pack(pady=10)

root.mainloop()