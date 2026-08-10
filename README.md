# panomax_reprojection
Reprojection of the panomax images from the mosaic expedition.


### Setup
Download the files, unpack in a suitable location.
Open `georeference_one_position.py`, put the path to the directory where `panorama_mapping.py` is located in `sys.path.append('/path/to/your/script_directory/')`.
If a different mask is needed for the panoramas, exchange the path for `mask_bools_cone`.
`ship_position` is not a real file and can stay like this. It is to georeference all images to the time and date of the hypothetical image mentioned there. In this case it is referring to the central time of the helicopter flight on the 30th June 2020.
The main command is

```
inefficient_projection(image_path=image_path, resolution=.5, size=4000, mini_angles=False, position_ship=ship_position, mbc=mask_bools_cone)
```
The resolution is about how many meters are displayed per pixel, the size is the size of the projected image in pixels, `mini_angles` should stay on `False`, hence it is still under developement to improve the projection.
For first tries it is recommended to use a resolution of 2m/px and a size of 1000x1000px.
This reduces the calculation power and size of output by 3/4. To maintain the final radius of the output image, make sure that the sum of resolution and size stays at 2000 with positive values, whereas size needs to be an integer.
If the images are supposed to be georeferenced onto their inital position, `position_ship` needs to be adapted to `position_ship = image_path`. Herefore it is important that the image paths are in the same format as the one for `ship_position`, they need to have the format of `yyyy_mmdd_hhmmss.jpg`.

The slurm script is just for explanatory reasons.
Change Account, job name, resources, etc. according to your computing.
For the environment panomax_mosaic_env the following packages are necessary:
 - `numpy`
 - `matplotlib`
 - `pandas`
 - `rastrio`
 - `pyproj`
 - `scipy`
 - `affine`

Install these in a suitable environment and add the environment instead of "conda activate panomax_mosaic_env".
Add the paths to the panorama images you want to reproject from a .txt file (see l4_complete.txt as an example).

Now adjust `panorama_mapping.py`.
The hydrins file is specific for mosaic. If other panoramas should be processed, attention has to be paid to the format of the file.
`path` needs to be updated according to the path the script is stored in.
The following lines ensure that the hydrins file is loaded and initialise parameters for the panomax camera that was used during mosaic.

At the bottom of `panorama_mapping.py` the `pfadfinder` needs to be adjusted to the desired output file path.


The hydrins data can not be put on gitlab, but it is available upon request.
