import cv2
import numpy as np
import uuid

def uuid_to_bits(u):
    # Преобразуем UUID в строку из 32 hex символов без дефисов
    hex_str = u.hex  # 32 символа hex
    bits = ''.join(bin(int(c, 16))[2:].zfill(4) for c in hex_str)
    return bits  # строка из '0' и '1', длина 128 бит

def bits_to_uuid(bits):
    # bits - строка из '0' и '1', длина 128
    hex_str = ''
    for i in range(0, len(bits), 4):
        nibble = bits[i:i+4]
        hex_digit = hex(int(nibble, 2))[2:]
        hex_str += hex_digit
    return uuid.UUID(hex=hex_str)

def detect_keypoints(image_gray, max_points=50):
    # Используем ORB (бесплатный аналог SIFT)
    orb = cv2.ORB_create(nfeatures=max_points)
    keypoints = orb.detect(image_gray, None)
    keypoints = sorted(keypoints, key=lambda k: -k.response)
    return keypoints[:max_points]

def embed_bits_in_patch(patch, bits):
    # Встраиваем биты в LSB яркости каждого пикселя патча (grayscale)
    flat = patch.flatten()
    for i in range(min(len(bits), len(flat))):
        val = flat[i]
        val = (val & ~1) | int(bits[i])
        flat[i] = val
    return flat.reshape(patch.shape)

def extract_bits_from_patch(patch, n_bits):
    flat = patch.flatten()
    bits = ''
    for i in range(min(n_bits, len(flat))):
        bits += str(flat[i] & 1)
    return bits

def embed_uuid(image_path, u: uuid.UUID, output_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Не удалось загрузить изображение")
    
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    keypoints = detect_keypoints(image_gray)
    
    bits = uuid_to_bits(u)  # 128 бит
    
    # Размер патча вокруг ключевой точки для встраивания (например 8x8)
    patch_size = 8
    
    # Количество бит на патч — ограничено размером патча
    max_bits_per_patch = patch_size * patch_size
    
    # Дублируем данные по нескольким патчам для устойчивости
    n_patches_needed = int(np.ceil(len(bits) / max_bits_per_patch))
    
    if n_patches_needed > len(keypoints):
        raise ValueError(f"Недостаточно ключевых точек ({len(keypoints)}), нужно {n_patches_needed}")
    
    image_mod = image.copy()
    
    for i in range(n_patches_needed):
        kp = keypoints[i]
        x, y = int(kp.pt[0]), int(kp.pt[1])
        
        half_size = patch_size // 2
        
        x_start = max(x - half_size, 0)
        y_start = max(y - half_size, 0)
        
        x_end = min(x_start + patch_size, image.shape[1])
        y_end = min(y_start + patch_size, image.shape[0])
        
        patch_bgr = image_mod[y_start:y_end, x_start:x_end]
        
        if patch_bgr.shape[0] != patch_size or patch_bgr.shape[1] != patch_size:
            # Если патч на краю изображения меньше нужного размера — пропускаем или обрезаем биты
            continue
        
        # Конвертируем патч в YCrCb для изменения яркости (Y канал)
        patch_ycrcb = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2YCrCb)
        
        y_channel = patch_ycrcb[:, :, 0]
        
        start_bit_idx = i * max_bits_per_patch
        end_bit_idx = min(start_bit_idx + max_bits_per_patch, len(bits))
        
        bits_to_embed = bits[start_bit_idx:end_bit_idx]
        
        y_channel_mod = embed_bits_in_patch(y_channel, bits_to_embed)
        
        patch_ycrcb[:, :, 0] = y_channel_mod
        
        patch_bgr_mod = cv2.cvtColor(patch_ycrcb, cv2.COLOR_YCrCb2BGR)
        
        image_mod[y_start:y_end, x_start:x_end] = patch_bgr_mod
    
    cv2.imwrite(output_path, image_mod)
    
def decode_uuid(image_path):
    image = cv2.imread(image_path)
    
    if image is None:
        raise ValueError("Не удалось загрузить изображение")
    
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    keypoints = detect_keypoints(image_gray)
    
    patch_size=8
    max_bits_per_patch=patch_size*patch_size
    
    n_patches_needed=16   # Для UUID длиной 128 бит при таком размере патча
    
    extracted_bits_list=[]
    
    for i in range(min(n_patches_needed,len(keypoints))):
        kp=keypoints[i]
        
        x,y=int(kp.pt[0]),int(kp.pt[1])
        
        half_size=patch_size//2
        
        x_start=max(x-half_size,0)
        y_start=max(y-half_size,0)
        
        x_end=min(x_start+patch_size,image.shape[1])
        y_end=min(y_start+patch_size,image.shape[0])
        
        patch_bgr=image[y_start:y_end,x_start:x_end]
        
        if patch_bgr.shape[0]!=patch_size or patch_bgr.shape[1]!=patch_size:
            continue
        
        patch_ycrcb=cv2.cvtColor(patch_bgr,cv2.COLOR_BGR2YCrCb)
        
        y_channel=patch_ycrcb[:,:,0]
        
        bits=extract_bits_from_patch(y_channel,max_bits_per_patch)
        
        extracted_bits_list.append(bits)

    
    if not extracted_bits_list:
      raise ValueError("Не удалось извлечь данные")
      
      
      # Объединяем все биты и выбираем наиболее частый бит по позиции (голосование) для повышения устойчивости
    
  
      
      
      
      
      
      
      
      
      
      
      
      
      
      
      
      
    
    
    
    
    
    

if __name__=="__main__":
  
  
