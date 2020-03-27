from picamera import PiCamera
import boto3
import os
import uuid

# pip3 install picamera
# pip3 install requests
# pip3 install boto3
# pip3 install envbash

S3_BUCKET_NAME = "inovation-project-01"
S3_BASE_URL = "https://" + S3_BUCKET_NAME + ".s3.amazonaws.com/"
LOCAL_IMG_DIR = os.path.abspath('.') + "/Images/"
S3_BUCKET_FOLDER_UNKNOW = "unknow"
camera = PiCamera()
camera.resolution = (640, 480)

def set_credential(service):
	client = boto3.client(service, 
		region_name='us-east-1',
		aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
		aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
	)
	return client	

def take_pick(camera):
	camera.start_preview()
	img_name = "img-" + uuid.uuid4().hex + ".jpg"
	camera.capture(LOCAL_IMG_DIR + img_name)
	camera.stop_preview()
	return img_name

def analyze_img(img_name):
	params = {
	'S3Object': {
		'Bucket': S3_BUCKET_NAME,
		'Name': img_name
		}
	}
	client = set_credential("rekognition")
	resp = client.detect_labels(Image=params, MaxLabels=3, MinConfidence=90)
	return resp

def send_image(server_dir, img_name):
	client = set_credential("s3")
	resp = client.upload_file(LOCAL_IMG_DIR + img_name, S3_BUCKET_NAME, server_dir + img_name)
	return resp

def find_bucket_dir(label):
	client = set_credential("s3")
	resp = client.list_objects(Bucket=S3_BUCKET_NAME)
	img_dir = S3_BUCKET_FOLDER_UNKNOW + "/" + label
	for h in resp["Contents"]:
		object_full_path = h["Key"].split("/")
		object_full_path.pop()
		directory_full_path = object_full_path
		for sub_dir in directory_full_path:
			if label == sub_dir:
				img_dir = "/".join(directory_full_path)
	return img_dir + "/"

def delete_obj(img_source):
	client = set_credential("s3")
	resp = client.delete_object(
		Bucket=S3_BUCKET_NAME,
	    	Key=img_source
	)
	return resp

def classify_in_folder(label, img_name):
	server_dir = find_bucket_dir(label)
	client = set_credential("s3")
	client.copy_object(
		Bucket=S3_BUCKET_NAME,
    		CopySource={
		    'Bucket': S3_BUCKET_NAME, 
		    'Key': img_name
	    },
	    Key=server_dir+img_name
	)

def main():
	while True:
		txt = input("Take picture? (Yes/No)")
		if txt == "Yes":
			print("Taking Picture ...")
			img_name = take_pick(camera)
			print("Sending Picture S3 ...")
			resp = send_image("", img_name)
			print("Rekognition analysing ...")
			resp = analyze_img(img_name)
			print("Printing Response ...")
			print(resp)
			for label in resp['Labels']:
				print("================")
				print(label)
				print("Classify in S3 folder ...")
				classify_in_folder(label["Name"], img_name)
				print("Finished")
			delete_obj(img_name)

if __name__ == "__main__":
    main()
