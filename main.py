# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from base64 import b64encode
import datetime
from io import BytesIO, StringIO
import os
import time
from urllib import parse, request
from urllib.request import Request, urlopen
import zipfile
from flask import Flask, Markup, redirect, render_template, request
from generate_creative import detect_objects, generate_html5_parts
from google.appengine.api import wrap_wsgi_app
from google.auth import app_engine
from google.cloud import storage


app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

GCS_BUCKET = f"{os.environ.get('GOOGLE_CLOUD_PROJECT')}.appspot.com"
API_KEY = os.environ.get('API_KEY')
TRANSPARENT_GIF = 'static/images/transparent.gif'
OUTPUT_HTML_FILE_NAME = 'creative.html'
MINUTES_TO_EXPIRE = 60
CSS_FILES = ['gwdgooglead_style.css', 'gwdpage_style.css', 'gwdimage_style.css', 'gwdpagedeck_style.css', 'gwdtaparea_style.css']
JS_FILES = ['Enabler.js', 'gwdtaparea_min.js', 'gwdpage_min.js', 'gwd-events-support.1.0.js', 'gwd_webcomponents_v1_min.js', 'gwdgooglead_min.js', 'gwdpagedeck_min.js', 'gwdimage_min.js']



def _is_local():
  """Checks is the process is running in a localhost

  Returns:
      boolean: True if localhost False otherwise
  """
  print(request.host_url)
  return 'localhost' in request.host_url


def _clean_files(img_url, zip_file_url):
  """Delete the generated files

  Args:
      img_url (str): URL of the image
      zip_file_url (str): URL of the zip file
  """
  img_name = img_url.split('/')[-1]
  zip_name = zip_file_url.split('/')[-1]
  if _is_local():
    _delete_from_local(img_name, zip_name)
  else:
    img_name = img_name.split('?')[0]
    zip_name = zip_name.split('?')[0]
    _delete_from_gcs(img_name, zip_name)


def _delete_from_local(img_name, zip_name):
  """Removes the files from static directory in local drive

  Args:
      img_name (str): name of the image file
      zip_name (str): name of the zip file
  """

  try:
    os.remove(f'static/images/{img_name}')
    os.remove(f'static/{zip_name}')
  except Exception as ex:
    print(ex)


def _delete_from_gcs(img_name, zip_name):
  """Deletes blobs from the bucket

  Args:
      img_name (str): URL of the image file
      zip_name (str): URL of the zip file
  """
  storage_client = storage.Client()
  bucket = storage_client.bucket(GCS_BUCKET)

  try:
    print(f'Trying to delete {img_name}.')
    blob = bucket.get_blob(img_name)
    blob.delete()
    print(f'Blob {img_name} deleted.')
  except Exception as ex:
    print(ex)

  try:
    print(f'Trying to delete {zip_name}.')
    blob = bucket.get_blob(zip_name)
    blob.delete()
    print(f'Blob {zip_name} deleted.')
  except Exception as ex:
    print(ex)


def _read_image(image_url):
  """Reads an image from internet

  Args:
      image_url (str): URL for the image

  Returns:
      bytearray: Bytes for the image
  """

  headers = {
      'User-Agent': (
          'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like'
          ' Gecko) Chrome/23.0.1271.64 Safari/537.11'
      ),
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
      'Accept-Encoding': 'gzip, deflate, br',
      'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
      'Connection': 'keep-alive',
  }

  req = Request(image_url, headers=headers)
  resp = urlopen(req)
  return resp.read()


def _create_zip(zip_file_name, html_file, img_url, img_name, base_url):
  """Creates a zip file with the html and images files.

  Args:
      zip_file_name (str): Name for the zip file
      html_file (bytearray): Bytes of the HTML file
      img_url (str): URL for the image
      img_name (str): Name of the image
      base_url (str): Base URL for the server where the app is deployed

  Returns:
      bytes: Bytes for the zip file
  """
  mem_zip = BytesIO()

  transparent_url = f'{base_url}{TRANSPARENT_GIF}'
  
 
  files = []
  files_js = []
  files_css = []
  transparent_file_name = TRANSPARENT_GIF.split('/')[-1]
  files.append((_read_image(img_url), img_name))
  files.append((_read_image(transparent_url), transparent_file_name))
  for file_name in CSS_FILES:
    files_css.append((_read_image(f'{base_url}static/css/{file_name}'), file_name))
  for file_name in JS_FILES:
    files_js.append((_read_image(f'{base_url}static/js/{file_name}'), file_name))
 

  with zipfile.ZipFile(mem_zip, mode='w') as zf:
    for f, name in files:
      zf.writestr(f'{zip_file_name}/images/{name}', f)
    for f, name in files_css:
      zf.writestr(f'{zip_file_name}/css/{name}', f)
    for f, name in files_js:
      zf.writestr(f'{zip_file_name}/js/{name}', f)
    zf.writestr(f'{zip_file_name}/{OUTPUT_HTML_FILE_NAME}', html_file)

  return mem_zip.getvalue()


def _save_zip(file, file_name, base_url):
  """Saves the generate zip file.

  Args:
      file (bytearray): the contents of the zip file in bytes
      file_name (str): the name to give to the saved file
      base_url (str): base URL to use in the resulting URL for the saved file

  Returns:
      str: URL for the saved file
  """

  bucket = None
  if _is_local():
    tmp_dir = 'static'
    return _store_local_file(file, f'{tmp_dir}/{file_name}.zip', base_url)

  else:
    bucket = GCS_BUCKET
    return _store_file_in_gcs(file, f'{file_name}.zip', bucket)


def _store_local_file(file, file_path, base_url):
  """Saves the file into Google Cloud Storage

  Args:
      file (bytearray): file content
      file_name (str): the file to generate the signed URL for
      base_url (str): base URL to use in the resulting URL for the saved file

  Returns:
      str: signed URL to temporary access the GCS files from any client
  """

  f = open(file_path, 'wb')
  f.write(file)

  return f'{base_url}{file_path}'


def _store_file_in_gcs(file, file_name, bucket_name):
  """Saves the file into Google Cloud Storage

  Args:
      file (bytearray): file content
      file_name (str): the file to generate the signed URL for
      bucket_name (str): name of the Google Cloud Storage bucket

  Returns:
      str: signed URL to temporary access the GCS files from any client
  """

  try:
    credentials = app_engine.Credentials()

    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_string(file)
    url = blob.generate_signed_url(
        version='v4',
        expiration=datetime.timedelta(minutes=MINUTES_TO_EXPIRE),
        method='GET',
    )
    return url
  except Exception as ex:
    print(ex)
    return ex


def _get_gcs_signed_url(file_name, bucket_name):
  """Builds the signed URL to temporary access the GCS files from any client

  Args:
      file_name (str): the file to generate the signed URL for
      bucket_name (stre): name of the Google Cloud Storage bucket

  Returns:
      str: signed URL
  """
  credentials = app_engine.Credentials()

  storage_client = storage.Client(credentials=credentials)
  bucket = storage_client.bucket(bucket_name)
  blob = bucket.get_blob(file_name)

  url = blob.generate_signed_url(
      version='v4',
      expiration=datetime.timedelta(minutes=MINUTES_TO_EXPIRE),
      method='GET',
  )
  return url


def _process_image(img_url, threshold, img_dimensions):
  """Detects all the objects in the image, their labels and returns the HTML bits for later

  composition.

  Args:
      img_url (str): URL of the image to analyse
      threshold (float): number between 0 and 1 to use as confidence threshold
        for detection
      img_dimensions (str): image dimensions in widthxheight format. i.e:
        300x600

  Returns:
      (str,
       str,
       int,
       int,
       [str],
       [str],
       [str],
       [str],
       [str]): the generated URL after saving the image in the server, name of
       the image, image width, image height, clip paths HTML5 strings, map areas
       HTML5 strings, cut layer HTML5 strings, object names strings, svg circles
       HTML5 strings
  """

  bucket = None
  local = True
  if _is_local():
    local = True
    tmp_dir = 'static/images'
  else:
    local = False
    tmp_dir = '/tmp'
    bucket = GCS_BUCKET

  desired_width = int(img_dimensions.split('x')[0])
  desired_height = int(img_dimensions.split('x')[1])

  (new_img_url, img_name, width, height, polygons) = detect_objects(
      img_url,
      tmp_dir,
      threshold,
      desired_width,
      desired_height,
      local,
      API_KEY,
      bucket,
  )

  if not _is_local():
    new_img_url = _get_gcs_signed_url(new_img_url, bucket)
    print(f'Replacing the image with the signed GCS URL {new_img_url}')

  new_img_url = parse.unquote(new_img_url)

  (clip_paths, map_areas, tap_areas_hover, tap_areas_active, exit_metrics, cut_layers_hover, cut_layers_active, object_names, circles) = (
      generate_html5_parts(polygons)
  )

  return (
      new_img_url,
      img_name,
      width,
      height,
      clip_paths,
      map_areas,
      tap_areas_hover,
      tap_areas_active,
      exit_metrics,
      cut_layers_hover,
      cut_layers_active,
      object_names,
      circles,
  )


@app.route('/')
def index():
  """Main page.

  Returns:
      str: HTML rendered text for the main page
  """
  return render_template('/index.html')


@app.route('/build_creative', methods=(['POST']))
def build_creative():
  """Detects all the objects in the image, their labels and presents it in HTML.

  Returns:
      str: rendered HTML with the image & detect objects or the error
      description
  """

  try:
    img_url = request.form['img_url']
    threshold = request.form['threshold']
    img_dimensions = request.form['img_dimensions']

    (
        img_url,
        img_name,
        width,
        height,
        clip_paths,
        map_areas,
        tap_areas_hover,
        tap_areas_active,
        exit_metrics,
        cut_layers_hover,
        cut_layers_active,
        object_names,
        circles,
    ) = _process_image(img_url, threshold, img_dimensions)

    return render_template(
        '/build_creative.html',
        img_url=img_url,
        img_name=img_name,
        width=width,
        height=height,
        object_names=','.join(object_names),
        cut_layers_hover=Markup('\n'.join(cut_layers_hover)).unescape(),
        cut_layers_active=Markup('\n'.join(cut_layers_active)).unescape(),
        clip_paths=Markup('\n'.join(clip_paths)).unescape(),
        map_areas=Markup('\n'.join(map_areas)).unescape(),
        tap_areas_hover=Markup('\n'.join(tap_areas_hover)).unescape(),
        tap_areas_active=Markup('\n'.join(tap_areas_active)).unescape(),
        exit_metrics=Markup('\n'.join(exit_metrics)).unescape(),
        circles=Markup('\n'.join(circles)).unescape(),
    )
  except Exception as ex:
    return render_template(
        'error.html', message=f'Error while processing the image:{str(ex)}'
    )


@app.route('/generate_zip', methods=(['POST']))
def generate_zip():
  """Generates and save the zip file.

  Returns:
      str: rendered text with generated zip file URL or error description
  """

  try:
    img_url = parse.unquote(request.form['img_url'])
    img_name = parse.unquote(request.form['img_name'])
    html_file = request.files.get('html_file')
    local_base_url = request.url_root
    zip_file_name = f'creative_{str(time.time()).replace(".","")}'
    zip_file = _create_zip(
        zip_file_name, html_file.read(), img_url, img_name, local_base_url
    )
    zip_file_url = _save_zip(zip_file, zip_file_name, local_base_url)
    print(f'Results generated at {zip_file_url}')

    return zip_file_url
  except Exception as ex:
    return render_template(
        'error.html', message=f'Error while creating the zip file:{str(ex)}'
    )


@app.route('/clean', methods=(['GET']))
def clean():
  """Deletes the generated artefacast: zip file and image.

  Returns:
      None: it redirects to the root page
  """

  try:
    img_url = request.args.get('img_url')
    zip_file_url = request.args.get('zip_file_url')
    print(img_url)
    print(zip_file_url)
    _clean_files(img_url, zip_file_url)
  except Exception as ex:
    None

  return redirect('/')


if __name__ == '__main__':
  # This is used when running locally only. When deploying to Google App
  # Engine, a webserver process such as Gunicorn will serve the app. This
  # can be configured by adding an `entrypoint` to app.yaml.

  # Flask's development server will automatically serve static files in
  # the "static" directory. See:
  # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
  # App Engine itself will serve those files as configured in app.yaml.
  app.run(host='127.0.0.1', port=8080, debug=True)