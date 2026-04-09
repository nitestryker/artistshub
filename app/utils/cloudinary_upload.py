import os
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
    secure=True,
)


def upload_image(file_stream, public_id=None, folder='artapp'):
    kwargs = {'folder': folder}
    if public_id:
        kwargs['public_id'] = public_id
        kwargs['overwrite'] = True
    result = cloudinary.uploader.upload(file_stream, **kwargs)
    return result['secure_url']
