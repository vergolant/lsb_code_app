import cv2
import numpy as np
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox

# Генерируем Code128 штрихкод
def generate_code128_barcode(text, height, width):
    CODE128 = barcode.get_barcode_class('code128')
    code128 = CODE128(text, writer=ImageWriter())
    pil_img = code128.render(writer_options={"module_height": 15.0, "quiet_zone": 1.0})
    barcode_np = np.array(pil_img.convert('L'))
    barcode_np = 255 - barcode_np
    barcode_resized = cv2.resize(barcode_np, (width, height), interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(barcode_resized, cv2.COLOR_GRAY2BGR)

# Преобразуем BGR->RGB->PhotoImage для Tkinter
def cv2_to_photoimage(img_bgr):
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(img_rgb)
    return ImageTk.PhotoImage(pil)

# Добавляем рамки вокруг каждого элемента и по краю изображения
def draw_borders_on_image(img, barcode_img, color=(0,0,255), per_thickness=0, outer_thickness=0):
    # Шкала barcode_img должна совпадать с img
    if img.shape[:2] != barcode_img.shape[:2]:
        bc = cv2.resize(barcode_img, (img.shape[1], img.shape[0]))
    else:
        bc = barcode_img.copy()
    gray = cv2.cvtColor(bc, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    # Рисуем рамки вокруг каждой полосы/символа
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 2 and h > 2:
            cv2.rectangle(img, (x, y), (x + w, y + h), color, thickness=per_thickness)
    # Наружные рамки
    h, w = img.shape[:2]
    cv2.rectangle(img, (0, 0), (w-1, h-1), color, outer_thickness)
    cv2.rectangle(img, (outer_thickness, outer_thickness),
                  (w-1-outer_thickness, h-1-outer_thickness), color, outer_thickness)
    return img


# Конвертация OpenCV->PIL для Tkinter
def cv2_to_photoimage(img_bgr):
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(img_rgb)
    return ImageTk.PhotoImage(pil)

# Рисуем внешние рамки по всему штрихкоду
def draw_outer_borders(img, color=(0,0,0), thickness=0):
    h, w = img.shape[:2]
    cv2.rectangle(img, (0, 0), (w-1, h-1), color, thickness)
    cv2.rectangle(img, (thickness, thickness), (w-1-thickness, h-1-thickness), color, thickness)
    return img

# Рисуем рамки вокруг каждой полосы
def draw_per_bar_borders(img, color=(0,0,0), thickness=0):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 2 and h > 2:
            cv2.rectangle(img, (x, y), (x+w, y+h), color, thickness)
    return img

# Комбинируем границы
def add_borders(barcode_img, outer_color=(0,0,0), per_color=(0,0,0)):
    bc = barcode_img.copy()
    draw_per_bar_borders(bc, color=per_color, thickness=0)
    draw_outer_borders(bc, color=outer_color, thickness=0)
    return bc
# --- Основные встраиватели ---
def embed_alpha_blend(image, barcode_img, alpha=0.3):
    if image.shape != barcode_img.shape:
        barcode_img = cv2.resize(barcode_img, (image.shape[1], image.shape[0]))
    bc = add_borders(barcode_img)
    mask = np.any(bc < [250,250,250], axis=2)
    image_blue = image[:,:,0].astype(float)
    bc_blue = bc[:,:,0].astype(float)
    blended = np.clip((1-alpha)*image_blue + alpha*bc_blue, 0,255).astype(np.uint8)
    image[:,:,0][mask] = blended[mask]
    return image

def embed_lsb(image, barcode_img):
    if image.shape != barcode_img.shape:
        barcode_img = cv2.resize(barcode_img,(image.shape[1], image.shape[0]))
    bc = add_borders(barcode_img)
    gray = cv2.cvtColor(bc, cv2.COLOR_BGR2GRAY)
    _, bin_bc = cv2.threshold(gray, 200, 1, cv2.THRESH_BINARY_INV)
    blue = image[:,:,0]
    image[:,:,0] = (blue & 0b11111110) | bin_bc.astype(np.uint8)
    return image

# --- GUI функции ---
def load_image(entry_field):
    path = filedialog.askopenfilename(
        title="Выберите изображение",
        filetypes=[("Image files","*.jpg;*.jpeg;*.png")]
    )
    if path:
        entry_field.delete(0, tk.END)
        entry_field.insert(0, path)

# Предпросмотр штрихкода с красными рамками
def preview_barcode():
    text = entry_text.get()
    if not text:
        messagebox.showerror("Ошибка","Введите текст для генерации штрихкода.")
        return
    h, w = 100, 300
    bc = generate_code128_barcode(text, h, w)
    preview = draw_borders_on_image(bc.copy(), bc, color=(255,0,0), per_thickness=1, outer_thickness=2)
    photo = cv2_to_photoimage(preview)
    preview_label.config(image=photo)
    preview_label.image = photo

# Основная функция: встраивает и отрисовывает рамки на итоговом изображении
def process_and_embed():
    image_path = entry_image.get()
    text = entry_text.get()
    out = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG","*.png"),("JPEG","*.jpg;*.jpeg")]
    )
    if not image_path or not text or not out:
        messagebox.showerror("Ошибка","Заполните все поля и выберите файл для сохранения.")
        return
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    bc_full = generate_code128_barcode(text, h, w)
    # Встраиваем
    if var_ab.get():
        img = embed_alpha_blend(img, bc_full, float(entry_alpha.get()))
    if var_lsb.get():
        img = embed_lsb(img, bc_full)
    # Отрисовываем рамки после встраивания
    img = draw_borders_on_image(img, bc_full, color=(0,0,0), per_thickness=0, outer_thickness=1) #Поменял второе значение тут
    # Сохраняем
    if cv2.imwrite(out, img):
        messagebox.showinfo("Успех", f"Сохранено как {out}")
    else:
        messagebox.showerror("Ошибка","Не удалось сохранить изображение.")

# Построение GUI
root = tk.Tk()
root.title("Встраивание Code128 штрихкода")

# Выбор изображения
frame_image = tk.Frame(root)
frame_image.pack(pady=5)
tk.Label(frame_image, text="Изображение:").pack(side=tk.LEFT)
entry_image = tk.Entry(frame_image, width=40)
entry_image.pack(side=tk.LEFT, padx=5)
tk.Button(frame_image, text="Загрузить", command=lambda: load_image(entry_image)).pack(side=tk.LEFT)

# Ввод текста и предпросмотр
frame_text = tk.Frame(root)
frame_text.pack(pady=5)
tk.Label(frame_text, text="Текст:").pack(side=tk.LEFT)
entry_text = tk.Entry(frame_text, width=30)
entry_text.pack(side=tk.LEFT, padx=5)
tk.Button(frame_text, text="Предпросмотр", command=preview_barcode).pack(side=tk.LEFT)

# Метка предпросмотра
preview_label = tk.Label(root)
preview_label.pack(pady=5)

# Опции встраивания
frame_opts = tk.LabelFrame(root, text="Опции встраивания")
frame_opts.pack(padx=10, pady=10)
var_ab = tk.BooleanVar(value=True)
var_lsb = tk.BooleanVar(value=False)

tk.Checkbutton(frame_opts, text="Альфа-блендинг", variable=var_ab).grid(row=0, column=0, padx=5, pady=5)
tk.Checkbutton(frame_opts, text="LSB-встраивание", variable=var_lsb).grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame_opts, text="Альфа (0-1):").grid(row=1, column=0, padx=5, pady=5)
entry_alpha = tk.Entry(frame_opts, width=5)
entry_alpha.insert(0, "0.3")
entry_alpha.grid(row=1, column=1, padx=5, pady=5)

# Кнопка встраивания
tk.Button(root, text="Внедрить штрихкод", command=process_and_embed).pack(pady=10)
root.mainloop()
