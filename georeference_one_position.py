import sys
#enter the path to the directory where panorama_mapping.py is located
sys.path.append('/path/to/your/script_directory/')
#%load_ext autoreload
#%autoreload 2
from panorama_mapping import *


mask_bools_cone = initialiseMask_cone(mask_png=(path + mask_png))
ship_position = '/albedo/work/user/mafink001/images/PS122.4_0_Underway-27/2020/06/30/2020_0630_082342.jpg' #time and date for georeferencing images to one spot
def main():
    if len(sys.argv) < 2:
        print("Error: Please provide an image path!")
        sys.exit(1)

    image_path = sys.argv[1]
    
    print(f"Processing image: {image_path}")
    #change position_ship to image_path to georeference the given image to its "true" position
    inefficient_projection(image_path=image_path, resolution=.5, size=4000, mini_angles=False, position_ship=ship_position, mbc=mask_bools_cone)
    #hier mal eine krasse auflösung gewählt von .5 m/px und ein bild von 4 qkm
    #falls der obere teil spinnt, wieder auf 2 und 1000 setzen :)
    #optimieren kann man das noch mit einem graduellen auflösungsdingen (hohe auflösung in der mitte, niedrig am rand)

if __name__ == "__main__":
    main()