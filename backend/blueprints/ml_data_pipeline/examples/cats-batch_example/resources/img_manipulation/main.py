import boto3
from io import BytesIO
from PIL import Image
import os

import argparse


def from_s3(s3, bucket, key):
    file_byte_string = s3.get_object(Bucket=bucket, Key=key)['Body'].read()
    return Image.open(BytesIO(file_byte_string))
    
def get_safe_ext(key):
        ext = os.path.splitext(key)[-1].strip('.').upper()
        if ext in ['JPG', 'JPEG']:
            return 'JPEG' 
        elif ext in ['PNG']:
            return 'PNG' 
        else:
            raise S3ImagesInvalidExtension('Extension is invalid') 

def to_s3(s3, img, bucket, key):
        buffer = BytesIO()
        img.save(buffer, get_safe_ext(key))
        buffer.seek(0)
        sent_data = s3.put_object(Bucket=bucket, Key=key, Body=buffer)
        if sent_data['ResponseMetadata']['HTTPStatusCode'] != 200:
            raise Exception('Failed to upload image {} to bucket {}'.format(key, bucket))


def modify(img, width, height):
    """ Rasizes image and then flip and rotate 
    :param img the image to be manipulated
    :param width the target width
    :param height the target height
    :return [resized_image, flipped_image,  resized_rotated_1, resized_rotated_2, flipped_rotated_1, flipped_rotated_2]
    """
    resized_img = img.resize((width, height))
    flipped = resized_img.transpose(Image.FLIP_LEFT_RIGHT)
    rotated_img_1 = resized_img.rotate(10)
    rotated_img_2 = resized_img.rotate(-10)
    flipped_rotated_1 = flipped.rotate(10)
    flipped_rotated_2 = flipped.rotate(-10)

    return resized_img, flipped, rotated_img_1, rotated_img_2, flipped_rotated_1, flipped_rotated_2


def modify_and_upload(img, width, height, s3, bucket, prefix, name):
    """ Modifies and uploads the modified images to an s3 bucket"""
   
    resized_img, flipped, rotated_img_1, rotated_img_2, flipped_rotated_1, flipped_rotated_2 = modify(img, width, height)
    to_s3(s3, resized_img, bucket, prefix + name)
    print("{} uploaded".format(prefix + name))

    to_s3(s3, flipped, bucket, prefix + "flipped_" + name)
    print("{} uploaded".format(prefix + "flipped_" + name))

    to_s3(s3, rotated_img_1, bucket, prefix + "rotated10_"  + name)
    print("{} uploaded".format(prefix + "rotated10_"  + name))

    to_s3(s3, rotated_img_2, bucket, prefix + "rotatedmin10_" + name)
    print("{} uploaded".format(prefix + "rotatedmin10_" + name))

    to_s3(s3, flipped_rotated_1, bucket, prefix + "flipped_rotated10_" + name)
    print("{} uploaded".format(prefix + "flipped_rotated10_" + name))

    to_s3(s3, flipped_rotated_2, bucket, prefix + "flipprotatedmin10_" + name)
    print("{} uploaded".format(prefix + "flipped_rotatedmin10_" + name))


def modify_and_upload_prefix(s3, bucket, origin, destination, width, height):
    response = s3.list_objects_v2(Bucket=bucket, Prefix=origin)
    contents = [c.get("Key") for c in response.get("Contents")]
    while response.get("NextContinuationToken"):
        response = s3.list_objects_v2(Bucket=bucket, Prefix=origin, ContinuationToken=response["NextContinuationToken"])
        contents = contents + [c.get("Key") for c in response.get("Contents")]
    
    for c in contents:
        if c.split("/")[-1].split(".")[-1]:
            im = from_s3(s3, bucket, c)
            modify_and_upload(im, width, height, s3, bucket, destination, c.split("/")[-1])

ap = argparse.ArgumentParser() 
ap.add_argument("-b", "--bucket", required=True, help="Origin bucket")
ap.add_argument("-o", "--origin", required=True, help="Origin prefix")
ap.add_argument("-d", "--dest", required=True, help="Destination prefix")
ap.add_argument("--height", required=True, help="Height", type=int)
ap.add_argument("--width", required=True, help="Width", type=int)

args = vars(ap.parse_args())
print("Starting the processing with arguments {}".format(str(vars)))

s3 = boto3.client('s3')
modify_and_upload_prefix(s3 = s3, 
    width=args["width"], 
    height=args["height"], 
    bucket=args["bucket"],
    origin=args["origin"] + "/",
    destination=args["dest"] + "/")
