from PIL import Image
import numpy as np
import base64
import io
import concurrent.futures
from multiprocessing import cpu_count

def encode_image(img, data):
    """Кодирует данные в изображение методом LSB с использованием многопоточности"""
    if isinstance(data, str):
        binary_data = ''.join(format(byte, '08b') for byte in data.encode('utf-8'))
    else:
        binary_data = ''.join(format(byte, '08b') for byte in data)
    
    binary_data += '1111111111111110'  # Маркер конца
    
    img_data = np.array(img)
    total_pixels = img_data.shape[0] * img_data.shape[1]
    
    if len(binary_data) > total_pixels * 3:
        raise ValueError("Изображение слишком маленькое для этих данных")

    # Разделяем изображение на части для параллельной обработки
    def process_chunk(start_row, end_row, binary_data):
        chunk_data = img_data[start_row:end_row]
        data_index = start_row * img_data.shape[1] * 3
        
        for i in range(chunk_data.shape[0]):
            for j in range(chunk_data.shape[1]):
                for k in range(3):
                    if data_index < len(binary_data):
                        chunk_data[i,j,k] = (chunk_data[i,j,k] & 0xFE) | int(binary_data[data_index])
                        data_index += 1
        return start_row, end_row, chunk_data

    chunks = []
    num_threads = cpu_count()
    rows_per_chunk = max(1, img_data.shape[0] // num_threads)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(0, img_data.shape[0], rows_per_chunk):
            end_row = min(i + rows_per_chunk, img_data.shape[0])
            futures.append(executor.submit(
                process_chunk, i, end_row, binary_data
            ))
        
        for future in concurrent.futures.as_completed(futures):
            start, end, chunk = future.result()
            img_data[start:end] = chunk

    return Image.fromarray(img_data)

def decode_image(img):
    """Декодирует данные из изображения с использованием многопоточности"""
    img_data = np.array(img)
    binary_data = [None] * (img_data.shape[0] * img_data.shape[1] * 3)
    
    def process_chunk(start_row, end_row):
        chunk_data = img_data[start_row:end_row]
        chunk_bits = []
        base_index = start_row * img_data.shape[1] * 3
        
        for i in range(chunk_data.shape[0]):
            for j in range(chunk_data.shape[1]):
                for k in range(3):
                    chunk_bits.append(str(chunk_data[i,j,k] & 1))
        
        return base_index, chunk_bits

    num_threads = cpu_count()
    rows_per_chunk = max(1, img_data.shape[0] // num_threads)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(0, img_data.shape[0], rows_per_chunk):
            end_row = min(i + rows_per_chunk, img_data.shape[0])
            futures.append(executor.submit(
                process_chunk, i, end_row
            ))
        
        for future in concurrent.futures.as_completed(futures):
            base_idx, bits = future.result()
            for i, bit in enumerate(bits):
                if base_idx + i < len(binary_data):
                    binary_data[base_idx + i] = bit

    binary_str = ''.join(filter(None, binary_data))
    return convert_to_text(binary_str)

def convert_to_text(binary_str):
    """Преобразует бинарную строку в текст"""
    try:
        # Ищем маркер конца
        end_marker = binary_str.find('1111111111111110')
        if end_marker != -1:
            binary_str = binary_str[:end_marker]
        
        # Преобразуем в байты
        byte_array = bytearray()
        for i in range(0, len(binary_str), 8):
            byte = binary_str[i:i+8]
            if len(byte) == 8:
                byte_array.append(int(byte, 2))

        
        # Пробуем декодировать как текст
        try:
            text = byte_array.decode('utf-8')
            if all(ord(c) < 128 for c in text):
                return "Текст: " + text
            return "Текст (UTF-8): " + text
        except UnicodeDecodeError:
            pass
        
        # Пробуем base64
        try:
            decoded = base64.b64decode(byte_array).decode('utf-8')
            return "Base64 данные: " + decoded
        except:
            pass
        
        return "Двоичные данные (hex): " + byte_array.hex()
        
    except Exception as e:
        return f"Ошибка преобразования: {str(e)}"

def main():
    print("Многопоточный LSB кодер/декодер")
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
                print("Кодирование...")
                encoded_img = encode_image(img, text)
            else:
                file_path = input("Введите путь к файлу: ")
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                print("Кодирование...")
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
            print("Декодирование...")
            result = decode_image(img)
            print("\nРезультат декодирования:")
            print(result)
            
            save = input("Сохранить результат в файл? (y/n): ")
            if save.lower() == 'y':
                with open('decoded_result.txt', 'w') as f:
                    f.write(result)
                print("Результат сохранен в decoded_result.txt")
        
        except Exception as e:
            print(f"Ошибка декодирования: {str(e)}")

    else:
        enc_path = input("Путь к закодированному изображению: ")
 
        try:
            print (encry(enc_path))
        except Exception as e:
            print(f"Ошибка декодирования: {str(e)}")








def encry (path):
    open(path,mode="rb")
    print("ter")
    return open(path,mode="rb")


if __name__ == "__main__":
    main()