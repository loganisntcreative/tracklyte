import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def upload_photo(file):
    if not file or not file.filename or not allowed_image(file.filename):
        return None
    try:
        result = cloudinary.uploader.upload(
            file,
            resource_type='image',
            folder='tracklyte/profiles',
            transformation=[
                {'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'}
            ]
        )
        return result['secure_url']
    except Exception as e:
        print(f'Photo upload error: {e}')
        return None