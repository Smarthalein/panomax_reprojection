#import cv2
import numpy as np
#import glob
import matplotlib.pyplot as plt
#import datetime
import pandas as pd
import rasterio
from rasterio.transform import from_origin
import pyproj
from scipy.interpolate import griddata
#import numba
#from PIL import Image
#import cameratransform as ct
#from scipy import ndimage
from affine import Affine
from rasterio.enums import ColorInterp
#import datetime as dt
#from io import StringIO
#import requests

path = '/albedo/home/mafink001/scripts_python/' #main path to directory
hyd_file = "hydrins_all_s.dat"
angles_df_hyd = pd.read_csv(path + hyd_file, delimiter='\t', skiprows=3, encoding="unicode_escape", names=["datetime", "cog", "heading", "heading rate", "heave", "lat", "lon", "pitch", "pitch rate", "roll", "roll rate", "speed og / kn", "speed x / m/s", "speed y / m/s", "speed z / m/s"])

angles_df_hyd["datetime"] = pd.to_datetime(angles_df_hyd['datetime'])
angles_df_hyd["heading"] = pd.to_numeric(angles_df_hyd.heading, errors='coerce')
angles_df_hyd["heave"] = pd.to_numeric(angles_df_hyd.heave, errors='coerce') #links rechts schwankung
angles_df_hyd["lat"] = pd.to_numeric(angles_df_hyd.lat, errors='coerce') #
angles_df_hyd["lon"] = pd.to_numeric(angles_df_hyd.lon, errors='coerce')
angles_df_hyd["pitch"] = pd.to_numeric(angles_df_hyd.pitch, errors='coerce')
angles_df_hyd["roll"] = pd.to_numeric(angles_df_hyd.roll, errors='coerce')
angles_df_hyd["cog"] = pd.to_numeric(angles_df_hyd.cog, errors='coerce') #links rechts schwankung
angles_df_hyd["heading rate"] = pd.to_numeric(angles_df_hyd["heading rate"], errors='coerce')
angles_df_hyd["pitch rate"] = pd.to_numeric(angles_df_hyd["pitch rate"], errors='coerce')
angles_df_hyd["roll rate"] = pd.to_numeric(angles_df_hyd["roll rate"], errors='coerce')
angles_df_hyd["speed x / m/s"] = pd.to_numeric(angles_df_hyd["speed x / m/s"], errors='coerce')
angles_df_hyd["speed y / m/s"] = pd.to_numeric(angles_df_hyd["speed y / m/s"], errors='coerce')
angles_df_hyd["speed z / m/s"] = pd.to_numeric(angles_df_hyd["speed z / m/s"], errors='coerce')

mask_png = "mask_without_ropes.png" #from jb - crane positions still have to be added
camera_height = 33. #in metres from nicolaus et al
camera_tilt = 90 #degrees, but 0 for yawpitchroll
#roll angle individual for each image
camera_horizontal_angle = 360 #degrees
camera_intervall = 20 #every 20 minutes a picture - but taking image needs approx. 18mins
camera_dimension_x = 15680 #pixels
camera_dimension_y = 2048 #pixels
focal_length = 35. #mm
horizon = 590. #horizon line, pixel from x
sensor_x = 0.014*camera_dimension_x #mm, from pixel amount*ccd size
sensor_y = 29.272 #mm, from pixel*ccd size

# as comparison birdseye
mask_png = "mask_without_ropes.png" #from jb - crane positions still have to be added
camera_height = 33. #in metres from nicolaus et al
camera_tilt = 90 #degrees, but 0 for yawpitchroll
#roll angle individual for each image
camera_horizontal_angle = 360 #degrees
camera_intervall = 20 #every 20 minutes a picture - but taking image needs approx. 18mins
camera_dimension_x = 15680 #pixels
camera_dimension_y = 2048 #pixels
focal_length = 35. #mm
horizon = 590. #horizon line, pixel from x
sensor_x = 0.014*camera_dimension_x #mm, from pixel amount*ccd size
sensor_y = 29.272 #mm, from pixel*ccd size


def initialiseMask_cone(mask_png):
    
    mask = plt.imread(mask_png)
    boat = np.where(mask!=0)
    mask[boat[0], boat[1], boat[2]]=1
    #trash = np.ones(((len(mask), len(mask[0]), 4))) # trash = everything but mosaic floe
    #trash[590:len(mask), 7750:len(mask[0]), :]=0
    #cutoff = np.where(trash!=0)
    mask = np.zeros((len(mask), len(mask[0])), dtype=bool)
    mask[boat[0], boat[1]] = True
    #mask[cutoff[0], cutoff[1]] = True
    
    return mask

def maskImage_cone(image, mask_bools):#, min_x, max_x, min_y, max_y):
    #[]
    im = plt.imread(image)
    #print(im.shape)
    rgba = np.ones((len(im), len(im[0]), 4))    
    if im.shape[2]==3:
        rgba[:, :, :3] = im.astype(np.float32) / 255.0
    else:
        rgba[:, :, :3] = im[:, :, :3].astype(np.float32) / 255.0
    rgba[mask_bools] = [1, 1, 1, 0]

    return rgba


def angles_interp_array(angles_df, image):
    MACSfiles = image[:-4]
    t = pd.to_datetime(MACSfiles, format="%Y_%m%d_%H%M%S")
    print(t)
    x = np.datetime64(t, 'ms')
    if x not in angles_df['datetime'].values:
        print("Error: Given image timestamp not in hydrins data!")
        start_index = angles_df['datetime'].sub(x).abs().idxmin()
        print(start_index)
        print(angles_df['datetime'][start_index])
        print(angles_df.head())
    else:
        start_index = angles_df.loc[angles_df['datetime'] == x].index.astype(int)[0]
    end_index = start_index + 60*18 -1 #1080s for one image
    interpolation_length = 15680
    relevant_angles = angles_df.loc[start_index:end_index].copy()
    timestamp_extra = pd.date_range(start=relevant_angles['datetime'].iloc[0], end=relevant_angles['datetime'].iloc[-1], periods=interpolation_length)
    angles_extra = pd.DataFrame({"datetime": timestamp_extra})

    #print(len(angles_extra))
   
    for col in relevant_angles.columns:
        if col != "datetime":
            angles_extra[col] = np.nan

    merged_angles = pd.concat([relevant_angles, angles_extra], ignore_index=True)
    merged_angles = merged_angles.sort_values(by='datetime').reset_index(drop=True)

    merged_angles.set_index('datetime', inplace=True)
    merged_angles = merged_angles.interpolate(method='time')
    #all_angles = merged_angles.copy()
    cond = merged_angles.index.isin(timestamp_extra)
    merged_angles.drop(merged_angles[~cond].index, inplace = True)
    merged_angles = merged_angles[~merged_angles.index.duplicated(keep='first')]
    return merged_angles, relevant_angles#, lat, lon

def pitch_roll_matrix(image_path):
    matrix = np.zeros((2,15680))
    #print(image_path[-25:-5])
    image_name = '2020_' + image_path[-20:-5]
    merged, _ = angles_interp_array(angles_df=angles_df_hyd, image=image_name)
    pitch = merged['pitch'].to_numpy()
    roll = merged['roll'].to_numpy()
    pixel_nr = np.linspace(0,15680-1, num=15680)
    angle = pixel_nr*2*np.pi/15679
    matrix[0,:] = roll*np.sin(angle)-pitch*np.cos(angle)
    matrix[1,:] = pitch*np.sin(angle)-roll*np.cos(angle)
    return matrix

#put every d_min and every roll angle in this matrix (-> makes projection quite easy?)
def fully_param_matrix(image_path):
    #matrix = np.zeros((2048,15680, 2))
    h_x = np.linspace(0,2047, num=2048) #physical height of the pixel
    angle = np.linspace(-np.pi,np.pi, 15680)
    #height_angle = np.pi/180*np.linspace(80-23,80+23,2048)
    r = 35*1e-3 #bottom radius of the cone
    pitch_roll = pitch_roll_matrix(image_path)
    cam_height = 33
    #hier den horizont noch rausschneiden!
    pv,hv = np.meshgrid(pitch_roll[0], h_x)
    #rv, vh = np.meshgrid(pitch_roll[1], h_x)

    #keks = r + hv*np.cos(pv*np.pi/180) + (cam_height+hv*np.sin(pv*np.pi/180))*np.tan(((103-57)*hv/(1.4*1e-6)/2047-57)*np.pi/180)
    #if eps <= 0 dann nan!
    #if (pv+80)*np.pi/180-((92*hv/2047-46))*np.pi/180
    #old psi tan: 92*hv/2047-46
    keks = r + hv*14*1e-6*np.cos((pv+80)*np.pi/180) + np.tan((pv+80)*np.pi/180-(46*(2047-hv)/2047-23)*np.pi/180)*(cam_height+hv*14*1e-6*np.sin((pv+80)*np.pi/180))
    keks[pv+80-(46*(2047-hv)/2047-23)>89.999]=np.nan 

    milch = np.linspace(-np.pi,np.pi, 15680)+pitch_roll[1]
    np.where(milch < -np.pi, )
    milch[milch < -np.pi]+= 2*np.pi
    milch[milch > +np.pi]-=2*np.pi
    #milch = pitch_roll[1]+angle #roll winkel und actual winkel

    #cookie ist die zylindrische darstellung
    #cookie = r + np.tan((90-(46*(2047-hv)/2047-23)/2)*np.pi/180)*(cam_height+hv*14*1e-6)
    #cookie[(46*(2047-hv)/2047-23)<=0] = np.nan
    
    #plt.imshow(rv)
    #plt.imshow(vh)
    #matrix[:,:,0] = r + h_x*np.cos(pitch_roll[0]*np.pi/180) + (cam_height+h_x*np.sin(pitch_roll[0]*np.pi/180))*np.tan((pitch_roll[0]-23)*np.pi/180)
    #matrix[:,:,1] = pitch_roll[1]+
    #23° = half opening angle of the image / / completion of h_x would be -23 until +23 in 2048 steps
    return keks,milch#,cookie

def fully_param_matrix_one_angle(image_path):
    #matrix = np.zeros((2048,15680, 2))
    h_x = np.linspace(0,2047, num=2048) #physical height of the pixel
    angle = np.linspace(-np.pi,np.pi, 15680)
    #height_angle = np.pi/180*np.linspace(80-23,80+23,2048)
    r = 35*1e-3 #bottom radius of the cone
    pitch_roll = pitch_roll_matrix_one_angle(image_path)
    cam_height = 33
    #hier den horizont noch rausschneiden!
    pv,hv = np.meshgrid(pitch_roll[0], h_x) #das minus ist EXPERIMENTELL
    #rv, vh = np.meshgrid(pitch_roll[1], h_x)

    #keks = r + hv*np.cos(pv*np.pi/180) + (cam_height+hv*np.sin(pv*np.pi/180))*np.tan(((103-57)*hv/(1.4*1e-6)/2047-57)*np.pi/180)
    #if eps <= 0 dann nan!
    #if (pv+80)*np.pi/180-((92*hv/2047-46))*np.pi/180
    #old psi tan: 92*hv/2047-46
    keks = r + hv*14*1e-6*np.cos((pv+80)*np.pi/180) + np.tan((pv+80)*np.pi/180-(46*(2047-hv)/2047-23)*np.pi/180)*(cam_height+hv*14*1e-6*np.sin((pv+80)*np.pi/180))
    keks[pv+80-(46*(2047-hv)/2047-23)>89.999]=np.nan 

    milch = np.linspace(-np.pi,np.pi, 15680)#+pitch_roll[1]
    np.where(milch < -np.pi, )
    milch[milch < -np.pi]+= 2*np.pi
    milch[milch > +np.pi]-=2*np.pi
    #milch = pitch_roll[1]+angle #roll winkel und actual winkel

    #cookie ist die zylindrische darstellung
    #cookie = r + np.tan((90-(46*(2047-hv)/2047-23)/2)*np.pi/180)*(cam_height+hv*14*1e-6)
    #cookie[(46*(2047-hv)/2047-23)<=0] = np.nan
    
    #plt.imshow(rv)
    #plt.imshow(vh)
    #matrix[:,:,0] = r + h_x*np.cos(pitch_roll[0]*np.pi/180) + (cam_height+h_x*np.sin(pitch_roll[0]*np.pi/180))*np.tan((pitch_roll[0]-23)*np.pi/180)
    #matrix[:,:,1] = pitch_roll[1]+
    #23° = half opening angle of the image / / completion of h_x would be -23 until +23 in 2048 steps
    return keks,milch#,cookie

def pitch_roll_matrix_one_angle(image_path):
    matrix = np.zeros((2,15680))
    #print(image_path[-25:-5])
    image_name = '2020_' + image_path[-20:-5]
    merged, _ = angles_interp_array(angles_df=angles_df_hyd, image=image_name)
    pitch_matrix = merged['pitch'].to_numpy()
    roll_matrix = merged['roll'].to_numpy()
    pitch, roll = np.average(pitch_matrix), np.average(roll_matrix)
    pixel_nr = np.linspace(0,15680-1, num=15680)
    angle = pixel_nr*2*np.pi/15679
    matrix[0,:] = roll*np.sin(angle)-pitch*np.cos(angle)
    matrix[1,:] = pitch*np.sin(angle)-roll*np.cos(angle)
    return matrix

def position(image_path):
    MACSfiles = '2020_' + image_path[-20:-9]
    t = pd.to_datetime(MACSfiles, format="%Y_%m%d_%H%M%S")
    index = angles_df_hyd.loc[angles_df_hyd['datetime'] == t].index
    lat = angles_df_hyd['lat'][index].item()
    lon = angles_df_hyd['lon'][index].item()
    heading = angles_df_hyd['heading'][index].item()
    cog = angles_df_hyd['cog'][index].item()
    return lat, lon, heading, cog
#print(position(image_path))


def position_by_lars(image_path): #extract lat, lon, heading and cog from hydrins data with awi
    MACSfiles = '2020_' + image_path[-20:-9]
    t = pd.to_datetime(MACSfiles, format="%Y_%m%d_%H%M%S")
    index = angles_df_hyd.loc[angles_df_hyd['datetime'] == t].index
    lat = angles_df_hyd['lat'][index].item()
    lon = angles_df_hyd['lon'][index].item()
    heading = angles_df_hyd['heading'][index].item()
    cog = angles_df_hyd['cog'][index].item()
    return lat, lon, heading, cog
#print(position(image_path))

def find_nearest(array, value):
    array = np.asarray(array)
    if len(array[np.where(np.isnan(array))])!=0:
        array[np.where(np.isnan(array))] = -np.nanmax(array)*2
    if len(array)==0:
        print("empty array")
        print(len(array), value)
        return np.nan
    elif value>=(np.nanmax(array)+10):
        print("value too high")
        print(len(array), value)
        return np.nan
    idx = (np.abs(array - value)).argmin()
    
    if len(array)>=idx:
        print(len(array), idx)
        print('irgendwas ist hier auch kaputt')
        return np.nan
    return array[idx]

def find_nearest(array, value):
    array = np.asarray(array)
    array[np.where(np.isnan(array))] = -np.nanmax(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

#das hier optimieren

def safe_geotiff(lat, lon, heading, output_tif_path, cartesian_map, resolution):
    camera_gps_lat = lat
    camera_gps_lon = lon
    output_size_pixels = len(cartesian_map)
    meters_per_pixel = resolution
    
    print("Save GeoTIFF...")
  
    utm_zone = int((camera_gps_lon + 180) / 6) + 1
    crs_utm_str = f"EPSG:326{utm_zone:02d}" # Nordhalbkugel
    if camera_gps_lat < 0:
        crs_utm_str = f"EPSG:327{utm_zone:02d}" # Südhalbkugel
        
    transformer = pyproj.Transformer.from_crs("EPSG:4326", crs_utm_str, always_xy=True)
    cam_x_utm, cam_y_utm = transformer.transform(camera_gps_lon, camera_gps_lat)
    
    #cog hier noch rein?
    #cog0 = 184.5
    #cog = cog0 #hier schrauben

    if cam_x_utm >= 0:
        heading_tot = heading - np.atan2(cam_y_utm, cam_x_utm)  # Annahme: Bild zeigt nach Norden (y-Richtung)
    else:
        heading_tot = heading + np.atan2(cam_y_utm, cam_x_utm)

    transform = (Affine.translation(cam_x_utm, cam_y_utm)
                 * Affine.rotation(heading_tot)
                 * Affine.scale(meters_per_pixel, -meters_per_pixel)
                 * Affine.translation(-output_size_pixels / 2, -output_size_pixels / 2))
    
    #top_left_x = cam_x_utm - (output_size_pixels / 2) * meters_per_pixel
    #top_left_y = cam_y_utm + (output_size_pixels / 2) * meters_per_pixel # Y geht nach SÜDEN

    #transform = from_origin(top_left_x, top_left_y, meters_per_pixel, meters_per_pixel)

    cartesian_map_rasterio = np.moveaxis(cartesian_map, 2, 0)
    num_channels = cartesian_map_rasterio.shape[0]
    #cartesian_map[3,:,:] = (cartesian_map[3,:,:]+1)*255
    #print(cartesian_map_rasterio.shape)
    with rasterio.open(
        output_tif_path, 'w', driver='GTiff',
        height=output_size_pixels, width=output_size_pixels,
        count=num_channels, dtype=cartesian_map_rasterio.dtype,
        crs=crs_utm_str, transform=transform,
    ) as dst:
        #print(dst.colorinterp[0], dst.colorinterp[1], dst.colorinterp[2], dst.colorinterp[3])
        dst.write(cartesian_map_rasterio)
        if num_channels == 4:
            print("Alpha range: " + str(np.min(cartesian_map[3,:,:])), str(np.max(cartesian_map[3,:,:])))
            
            dst.colorinterp = [
                ColorInterp.red, 
                ColorInterp.green, 
                ColorInterp.blue, 
                ColorInterp.alpha
            ]
    #print(num_channels)
    print(f"Done! Saved under {output_tif_path}")


def inefficient_projection(image_path, resolution, size, mini_angles, position_ship, mbc):
    mask_bools_cone = mbc
    #img_src = cv2.imread(image_path)
    image_src_path = image_path
    if image_path[-6]!='_':
        image_path = image_path[:-20] + image_path[-15:-4] + 'l_0_1.png'
    if mini_angles==True:
        dist_matrix_src, angle_vector = fully_param_matrix(image_path=image_path)
    else:
        dist_matrix_src, angle_vector = fully_param_matrix_one_angle(image_path=image_path)
    dist_matrix_src, angle_vector = fully_param_matrix(image_path=image_path)
    lat, lon, heading, c2 = position(image_path=image_path)
    print(lat,lon, heading, c2)
    #print(dist_matrix.shape, angle_vector.shape)
    #make grid for projection
    distance = size/2*resolution
    mesh_cart_x, mesh_cart_y = np.meshgrid(np.linspace(-distance,+distance,size), np.linspace(-distance,+distance,size))
    dist_matrix = np.flipud(dist_matrix_src)
    img_masked = maskImage_cone(image_src_path, mask_bools_cone)
    #plt.imshow(img_masked)
    r_polar_grid = np.sqrt(mesh_cart_x**2+mesh_cart_y**2)
    theta_polar_grid = np.arctan2(mesh_cart_y,mesh_cart_x)
    img_mapped = np.zeros((size, size,4))
    if mini_angles==True:
        dist_matrix_src, angle_vector = fully_param_matrix(image_path=image_path)
    else:
        dist_matrix_src, angle_vector = fully_param_matrix_one_angle(image_path=image_path)
    #print(np.min(angle_vector), np.max(angle_vector))
    #print(np.min(dist_matrix), np.max(dist_matrix))
    for i in range(size):
        for j in range(size):
            single_angle = theta_polar_grid[i,j]
            single_radius = r_polar_grid[i,j]
            #find nearest anstelle von where
            #print(np.where(angle_vector==single_angle))
            #print(single_angle, single_radius)
            #wir brauchen hier noch n radius ab wann das nans sind
            #print('values: ',  single_angle, single_radius)
            k = find_nearest(angle_vector,single_angle)
            k_num = np.where(angle_vector==k)[0]
            #print(np.nanmin(dist_matrix[:,k_num]))
            
            distance_vector = dist_matrix[:,k_num]
            #print(np.nanmax(distance_vector), single_radius, k, k_num)
            l = find_nearest(distance_vector, single_radius)
            
            if single_radius>=(np.nanmin(dist_matrix[:,k_num])):
                #print(k, k_num)
                #l = find_nearest(dist_matrix[:,k_num], single_radius)
                #plt.plot(dist_matrix[:,k_num])
                #plt.plot(0,single_radius,2048,single_radius)
                #plt.xlim(0,2048)
                #plt.ylim(0)
                #print(l, single_radius)
                #if abs((l-single_radius))>1:
                #    img_mapped[i,j] = 0
                #    break
                #else:
                l_num = np.where(dist_matrix[:,k_num]==l)[0]
                #print(l, l_num)
                img_mapped[i,j,:] = img_masked[l_num,k_num]
            elif l==np.nan:
                img_mapped[i,j,:] = 0
            else:
                img_mapped[i,j,:] = 0
    #one_pos = False

    image_path_fixed = position_ship#'/albedo/work/user/mafink001/images/PS122.4_0_Underway-27/2020/06/30/2020_0630_082342.jpg' #only for the fixed time
    c1=c2
    heading1=heading
    print(image_path_fixed, image_src_path)
    print(heading1, c1)
    if image_path_fixed!=image_src_path:
        #beim folgenden hab ich heading1 rausgenommen, da wir das alte nur nehmen wollen
        lat, lon, _, c1 = position(image_path=(image_path_fixed[:-20] + image_path_fixed[-15:-4] + 'l_0_1.png'))        
    matr_norm = img_mapped.astype(np.float64) # normalize the data to 0 - 1
    matr_norm = 255 * matr_norm # Now scale by 255
    matr_norm = matr_norm.astype(np.uint8)
    #safe_geotiff(lat, lon, heading1 + (c1-c2), "/albedo/work/projects/p_sip_ponds/panomax_mosaic/projected_images/image_position/real_pos_" + image_path[-20:-9] + ".tif" , matr_norm, resolution)
    #pfadfinder = "/albedo/home/mafink001/scripts_python/test_images_rot"
    # obiger pfad ist für testzwecke
    pfadfinder = "/albedo/work/projects/p_sip_ponds/panomax_mosaic/projected_images/mosaic_position/heading_fixed_"
    safe_geotiff(lat, lon, heading1, pfadfinder + image_path[-20:-9] + ".tif" , matr_norm, resolution)
    #print(heading, heading1)
    return img_mapped
