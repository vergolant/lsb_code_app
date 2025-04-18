from PIL import Image


enc_path = input("Path? = ")
def encry (path):
 with open(path, mode="rb") as zip_file:
    contents = zip_file.read()
    return contents


print (encry(enc_path))




def show_lsb(image_path):
    img = Image.open(image_path)
    pixels = img.load()
    width, height = img.size
    
    lsb_image = Image.new('RGB', (width, height))
    lsb_pixels = lsb_image.load()
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            # Извлекаем младшие биты и усиливаем их
            lsb_pixels[x, y] = ((r & 1) * 255, (g & 1) * 255, (b & 1) * 255)
    
    lsb_image.show()

show_lsb(enc_path)



