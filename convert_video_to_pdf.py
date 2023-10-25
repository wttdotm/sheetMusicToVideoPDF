
# Import everything needed to edit video clips 
from moviepy.editor import *
from scenedetect import ContentDetector, detect

#this AI thing is probably overkill but I just want an easy way to detect sheet music vs. anything else
from transformers import pipeline
from PIL import Image, ImageDraw, ImageFont

#YT DLP Stuff
from yt_dlp import YoutubeDL
import sys
import subprocess
import shlex

#gets the url you put in the command line
video = sys.argv[1:][0]

# get a low quality video and name the file the title of the video
ydl_opts = {
    'format': "18",
    'outtmpl': '%(title)s.%(ext)s'
}

title = ''
with YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(video, download=False)
    ydl.download(video)
    
    # grab the title for the variable we'll use later
    title = info['title']


video_file = title+".mp4"

# this is to remove any weird contrast cuts
# very hacky way to do this
contrast_command = f'ffmpeg -i "{video_file}" -vf "hue=s=0,eq=contrast=1.4" "2{video_file}" -y'
contrast_args = shlex.split(contrast_command)
subprocess.run(contrast_args)
copy_args = ['cp', str(2)+video_file, video_file]
subprocess.run(copy_args)


clip = VideoFileClip(video_file) 
scene_list = detect(video_file, ContentDetector(threshold=1))
  

# IMAGE_NAME = "beer.png"
LABELS = ["sheet music", "other", 'block'] # these are the things it's looking for!
MODEL = "openai/clip-vit-base-patch32" #600mb

detector = pipeline(model=MODEL, task="zero-shot-image-classification")


i = 0
final_images = []

for shot in scene_list:
  i = i+1
  start_time = shot[0].get_seconds()
  end_time = shot[1].get_seconds()
  print("in for loops at start time", start_time)
  image_name = "./classification_cache/frame"+str(i)+".jpg"
  #hacky solution to not have to deal with weird end screens
  if start_time + 3 > clip.duration:
    continue
  else:
    clip.save_frame(image_name, t=start_time + 2)
  image = Image.open(image_name)
  results = detector(image, candidate_labels=LABELS)
  print(results[0]['label'], results[0]['score'])
  if results[0]['label'] == 'sheet music':
    final_images.append(image)
    print("appending")
  # for r in results:
    print(results[0]["score"], results[0]["label"])
    # final_image_name = "./classification_cache/frame"+str(i)+".jpg"


print("above width height")
width = final_images[0].size[0]
height = final_images[0].size[1] * len(final_images)
print(width, height)

new_im = Image.new('RGB', (width, height), "white")

# Create ImageDraw object
draw = ImageDraw.Draw(new_im)

# Load a TrueType or OpenType font file, and create a font object.
# This font file should be in the same directory as your script or you should provide the full path.
# The second parameter is the size of the font.
font = ImageFont.truetype("Roboto-Medium.ttf", size=20)

#TODO: center text and generally make it look better

# Draw the text on the image
draw.text((10, 10), title, fill="black", font=font)

y_offset = 100
for im in final_images:
  new_im.paste(im, (0, y_offset))
  y_offset += im.size[1]

new_im.save(title + '.jpg')


# y_offset = 100
# for im in final_images:
#   new_im.paste(im, (0, y_offset))
#   y_offset += im.size[1]

# new_im.save('test.jpg')

# for image in final_images:
#   print(image.size[0])