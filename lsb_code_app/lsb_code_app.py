from PIL import Image
import numpy as np
import base64
import io

def encode_image(img, data):
    """Кодирует данные в изображение методом LSB"""
    # Преобразуем данные в байты и затем в бинарную строку
    if isinstance(data, str):
        binary_data = ''.join(format(byte, '08b') for byte in data.encode('utf-8'))
    else:
        binary_data = ''.join(format(byte, '08b') for byte in data)
    
    # Добавляем маркер конца (0xFFFE)
    binary_data += '1111111111111110'
    
    data_index = 0
    img_data = np.array(img)
    
    # Проверяем достаточно ли места
    if len(binary_data) > img_data.size * 3:
        raise ValueError("Изображение слишком маленькое для этих данных")
    
    for i in range(img_data.shape[0]):
        for j in range(img_data.shape[1]):
            for k in range(3):  # RGB
                if data_index < len(binary_data):
                    img_data[i,j,k] = (img_data[i,j,k] & 0xFE) | int(binary_data[data_index])
                    data_index += 1
                else:
                    break
    
    return Image.fromarray(img_data)

def decode_image(img):
    """Декодирует данные из изображения"""
    binary_data = []
    img_data = np.array(img)
    
    for i in range(img_data.shape[0]):
        for j in range(img_data.shape[1]):
            for k in range(3):
                binary_data.append(str(img_data[i,j,k] & 1))
                
                # Проверяем маркер конца
                if len(binary_data) >= 16:
                    last_16 = ''.join(binary_data[-16:])
                    if last_16 == '1111111111111110':
                        binary_data = binary_data[:-16]
                        return convert_to_text(binary_data)
    
    return convert_to_text(binary_data)

def convert_to_text(binary_data):
    """Улучшенное преобразование бинарных данных в читаемый формат"""
    if not binary_data:
        return "Нет данных для декодирования"
    
    try:
        # Преобразуем биты в байты
        byte_string = bits_to_bytes(binary_data)
        if not byte_string:
            return "Не удалось преобразовать биты в байты"
        
        # 1. Пробуем декодировать как UTF-8 текст
        try:
            text = byte_string.decode('utf-8')
            if is_printable(text):
                return f"Текст:\n{text}"
        except UnicodeDecodeError:
            pass
        
        # 2. Пробуем декодировать как base64
        try:
            decoded = base64.b64decode(byte_string).decode('utf-8')
            if is_printable(decoded):
                return f"Base64 данные:\n{decoded}"
        except:
            pass
        
        # 3. Возвращаем hex представление
        hex_data = byte_string.hex()
        return f"Двоичные данные (hex):\n{hex_data}"
        
    except Exception as e:
        return f"Ошибка преобразования:\n{str(e)}\nИсходные биты:\n{''.join(binary_data[:200])}..."

def bits_to_bytes(binary_data):
    """Безопасное преобразование битов в байты"""
    byte_array = bytearray()
    for i in range(0, len(binary_data), 8):
        byte_str = ''.join(binary_data[i:i+8])
        if len(byte_str) == 8:
            try:
                byte_array.append(int(byte_str, 2))
            except ValueError:
                continue
    return bytes(byte_array)

def is_printable(text):
    """Проверяет, является ли текст читаемым"""
    printable_chars = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r")
    return all(c in printable_chars for c in text)

def main():
    print("Стеганографический LSB кодер/декодер")
    print("1. Закодировать данные в изображение")
    print("2. Декодировать данные из изображения")
    
    choice = input("Выберите действие (1/2): ")
    
    if choice == '1':
        image_path = input("Путь к исходному изображению: ")
        data_type = input("Тип данных (1 - текст, 2 - файл): ")
        
        try:
            img = Image.open(image_path)
            
            if data_type == '1':
                text = input("Введите текст для кодирования: ")
                encoded_img = encode_image(img, text)
            else:
                file_path = input("Введите путь к файлу: ")
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                encoded_img = encode_image(img, file_data)
            
            output_path = input("Куда сохранить (по умолчанию: encoded.png): ") or "encoded.png"
            encoded_img.save(output_path)
            print(f"Данные успешно закодированы в {output_path}")
            
        except Exception as e:
            print(f"Ошибка: {str(e)}")
    
    elif choice == '2':
        image_path = input("Путь к закодированному изображению: ")
        
        try:
            img = Image.open(image_path)
            result = decode_image(img)
            print("\nРезультат декодирования:")
            print(result)
            
            # Сохраняем в файл при необходимости
            save = input("Сохранить результат в файл? (y/n): ")
            if save.lower() == 'y':
                with open('decoded_result.txt', 'w') as f:
                    f.write(result)
                print("Результат сохранен в decoded_result.txt")
        
        except Exception as e:
            print(f"Ошибка декодирования: {str(e)}")

if __name__ == "__main__":
    main()