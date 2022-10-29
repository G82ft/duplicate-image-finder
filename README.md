# duplicate-image-finder
This is simple duplicate image finder.

## How to use?
Enter where to scan and where to export better images.

## How it works?
It just shrinks all images to the minimum size found in the folder and then group all same images.

## Requirements
On Windows you just need to install Pillow:
```
pip install pillow
pip install --upgrade pip
pip install --upgrade Pillow
```
or:
```
pip install -r requirements.txt
```

If you are using Linux, you **also** need to install tkinter:
```
sudo apt-get install python3-tk
```