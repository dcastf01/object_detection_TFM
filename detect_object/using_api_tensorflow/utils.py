import os
import tensorflow as tf

def create_folder(numclass,train=True,test=False,basepath="/data",debug=False):
  if train:
    folder="train"
  elif test:
    folder="test"

  for idclass in numclass:
    data_path = os.path.join(basepath, folder,str(idclass) )

    try:
        os.makedirs(data_path)
    except OSError:
      if debug:
        print ("Creation of the directory %s failed" % data_path)
    else:
      if debug:
        print ("Successfully created the directory %s" % data_path)
# @tf.function(experimental_relax_shapes=True)
def copy_image_to_next_dataset(image,filename,label="",dst_base="/content/data/train",extension="jpg"):

  dst_path=dst_base + os.sep + str(label)+os.sep+filename+"."+extension
  try:
    image=tf.io.encode_jpeg(image, quality=100)
    tf.io.write_file(dst_path, image)
    # img.save(dst_path)
  except Exception as e:
    print("error en crear imagen")
    print(e)
def crop_image(image,bbox):
   #las cajas siguen esta convención ymin, xmin, ymax, xmax
    width=image.shape[0]
    height=image.shape[1]

    # ymin, xmin, ymax, xmax=bbox
    ymin=tf.cast(tf.multiply(bbox[0],height),tf.int32)
    ymax=tf.cast(tf.multiply(bbox[2],height),tf.int32)
    xmin=tf.cast(tf.multiply(bbox[1],width),tf.int32)
    xmax=tf.cast(tf.multiply(bbox[3],width),tf.int32)
    result= tf.image.crop_to_bounding_box(image, xmin, ymin, 
                                        xmax-xmin, ymax-ymin)
    return result
    # plt.imshow(result.numpy())
    # plt.show()
def crop_image_and_copy_next_dataset(image,bbox,filename,label,dst_base="/content/data/train",extension="jpg"):

  image_to_save=crop_image(image,bbox)
  copy_image_to_next_dataset(image_to_save,filename,label)