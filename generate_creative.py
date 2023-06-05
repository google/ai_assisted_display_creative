# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from types import Dict
from urllib.request import Request
from urllib.request import urlopen
import cv2
from google.cloud import storage
import numpy as np


OBJECT_FILTERS = ['Person']
SCORE_THRESHOLD = 0.85


def localize_objects(img_url, api_key):
  """Detect objects in the image using Google Vision API.

  Args:
      img_url (str): the URL to get the image from
      api_key (str): API key for Google Vision API

  Returns:
      Dict[str,Dict]: JSON object with the Vision API response
  """

  endpoint = f'https://vision.googleapis.com/v1/images:annotate?key={api_key}'
  data = {
      'requests': [{
          'image': {'source': {'imageUri': f'{img_url}'}},
          'features': [{'type': 'OBJECT_LOCALIZATION'}],
      }]
  }

  req = Request(endpoint)
  req.add_header('Content-Type', 'application/json')
  print(json.dumps(data))
  response = urlopen(req, json.dumps(data).encode('utf-8'))
  return json.load(response)


def _vertices_to_np_array(vertices):
  """Translates the vertices format in the Vision AI response to Numpy array.

  Args:
      vertices (Dict[str, str]): Dictionary of containing the x, y coordinates
        for each vertex

  Returns:
      ndarray: numpy array
  """
  temp_array = []
  for vertex in vertices:
    temp_array.append((vertex['x'], vertex['y']))
  return np.array(temp_array)


def _get_polygons(objects_response, width, height, threshold):
  """Filters & Calculates the vertices according to image dimesions so they
  could be printed.

  Args:
      objects_response (Dict[str, str]): the response from Google Vision API
      width (int): width of the image in pixels
      height (int): height of the image in pixels
      threshold (float): threshold to use for object detection confidence level

  Returns:
      Dict[str, Dict]: JSON object containing the polygon information
  """
  polygons = {}
  for localized_object in objects_response['responses'][0][
      'localizedObjectAnnotations'
  ]:
    normalized_vertices = localized_object['boundingPoly']['normalizedVertices']
    name = localized_object['name']
    score = localized_object['score']
    if not name in OBJECT_FILTERS and score >= threshold:
      name = f"{localized_object['name']}_1"
      if name in polygons:
        name = f"{localized_object['name']}_2"
      polygons[name] = {
          'score': localized_object['score'],
          'vertices': _vertices_to_np_array(normalized_vertices),
      }
      vertices_array = np.array(
          [
              (int(vertex[0] * width), int(vertex[1] * height))
              for vertex in polygons[name]['vertices']
          ]
      )
      polygons[name]['printable_vertices'] = vertices_array

  return polygons


def _generate_rounded_clip_path(polygon, vertices):
  """Creates the HTML for the rounded clip path corresponding to a polygon.

  Args:
      polygon (str): label corresponding to the polygon
      vertices ([(int, int)]): array with the x,y coordintes or the vertices

  Returns:
      str: HTML with the clip path
  """

  width = vertices[1][0] - vertices[0][0]
  height = vertices[2][1] - vertices[0][1]

  return (
      f'<clipPath id="{polygon}"><rect x="{vertices[0][0]}"'
      f' y="{vertices[0][1]}"         rx="10" ry="10" width="{width}"'
      f' height="{height}"/></clipPath>'
  )


def _generate_rounded_cut_layer(polygon, vertices):
  """Creates the HTML for the cut layer corresponding to a polygon.

  Args:
      polygon (str): label corresponding to the polygon
      vertices ([(int, int)]): array with the x,y coordintes or the vertices

  Returns:
      str: HTML with the cut layer
  """

  count = 0
  points = ''
  cut_layer_prefix = (
      f'#figura #area-{polygon}:hover ~ #capaRecorte {{ -webkit-clip-path:'
      ' inset('
  )
  cut_layer_suffix = f'round 10px);clip-path: url(#{polygon});}}'

  for vertex in vertices:
    if count == 0:
      point = f'{vertex[1]}px'
    if count == 1:
      point = f'{vertex[0]}px'
    if count == 2:
      point = f'{vertex[1]}px'
    if count == 3:
      point = f'{vertex[0]}px'

    points = f'{points}{point} '
    count = count + 1

  return f'{cut_layer_prefix}{points}{cut_layer_suffix}'


def _generate_circles(polygon, vertices):
  """Creates the HTML for the cut svg circles corresponding to a polygon

  Args:
      polygon (str): label corresponding to the polygon
      vertices ([(int, int)]): array with the x,y coordintes or the vertices

  Returns:
      str: HTML with the svg circles
  """

  outer_circle = (
      f'<circle id="outer-circle-{polygon}" class="outer-circle"'
      f' cx="{vertices[1][0] - 10}" cy="{vertices[1][1] + 10}" r="10"'
      ' stroke="white"  stroke-width="1" fill=none />'
  )
  inner_circle = (
      f'<circle id="inner-circle-{polygon}" class="inner-circle"'
      f' cx="{vertices[1][0] - 10}" cy="{vertices[1][1] + 10}" r="5"'
      ' stroke="white" stroke-width="1" fill="white" />'
  )

  return f'{outer_circle}{inner_circle}'


def _generate_map_area(img_url, polygon, vertices):
  """Creates the HTML for the map area corresponding to a polygon

  Args:
      img_url (str): the URL to get the image from
      polygon (str): label corresponding to the polygon
      vertices ([(int, int)]): array with the x,y coordintes or the vertices

  Returns:
      str: HTML with the map area
  """
  map_area_prefix = (
      f'<area id="area-{polygon}" shape="poly" title="{polygon}" coords="'
  )
  map_area_suffix = f'" target="_blank" href="{img_url}">'
  count = 0
  points = ''

  for vertex in vertices:
    point = f'{vertex[0]},{vertex[1]}'
    if count < vertices.shape[0] - 1:
      points = f'{points}{point},'
    else:
      points = f'{points}{point}'
    count = count + 1

  return f'{map_area_prefix}{points}{map_area_suffix}'


def image_resize(image, width=None, height=None, inter=cv2.INTER_AREA):
  """Modifies the image according to the given width and height.

  Args:
      image (bytearray): image content
      width (int, optional): width in pixels. Defaults to None
      height (int, optional): height in pixels. Defaults to None
      inter (int, optional): cv2 interpolation method

  Returns:
      bytearray: transformed image content
  """
  # initialize the dimensions of the image to be resized and
  # grab the image size

  print(width)
  print(height)
  dim = None
  (h, w) = image.shape[:2]

  # if both the width and height are None, then return the
  # original image
  if width is None and height is None:
    return image

  # check to see if the width is None
  if width is None:
    # calculate the ratio of the height and construct the
    # dimensions
    r = height / float(h)
    dim = (int(w * r), height)

  # otherwise, the height is None
  else:
    # calculate the ratio of the width and construct the
    # dimensions
    r = width / float(w)
    dim = (width, int(h * r))

  # resize the image
  resized = cv2.resize(image, dim, fx=1, fy=1, interpolation=inter)

  # return the resized image
  return resized


def generate_html5_parts(polygons, img_url):
  """Builds all the HTML5 parts according to the detected polygons in the image

  Args:
      polygons (Dict[str, Dict]): polygons detected by Google Vision API
      img_url (str): UTR to read the image from

  Returns:
      ([str], [str], [str], [str], [str]): arrays with the HTML5 strings for
      clip paths cut layers, map areas, object names and circles
  """
  clip_paths = []
  map_areas = []
  cut_layers = []
  object_names = []
  circles = []

  for polygon in polygons:
    print(polygon)
    object_names.append(f'"{str(polygon)}"')
    clip_paths.append(
        _generate_rounded_clip_path(
            polygon, polygons[polygon]['printable_vertices']
        )
    )
    map_areas.append(
        _generate_map_area(
            img_url, polygon, polygons[polygon]['printable_vertices']
        )
    )
    cut_layers.append(
        _generate_rounded_cut_layer(
            polygon, polygons[polygon]['printable_vertices']
        )
    )
    circles.append(
        _generate_circles(polygon, polygons[polygon]['printable_vertices'])
    )

  return (clip_paths, map_areas, cut_layers, object_names, circles)


def _upload_file_to_gcs(file_url, file_name, bucket_name):
  """Uploads the file to Google Cloud Storage.

  Args:
      file_url (str): URL to get the file from
      file_name (str): name of the file to use in Google Cloud Storage
      bucket_name (str): name of the Google Cloud Storage bucket

  Returns:
      str: the URL for the resulting Google Cloud Storage blob
  """
  storage_client = storage.Client()
  bucket = storage_client.bucket(bucket_name)
  blob = bucket.blob(file_name)
  blob.upload_from_filename(file_url)

  return f'https://storage.cloud.google.com/{bucket_name}/{file_name}'


def detect_objects(
    img_url,
    tmp_dir,
    threshold,
    desired_width,
    desired_height,
    local,
    api_key,
    bucket=None,
):
  """Detects all the objects in the image.

  Args:
      img_url (str): URL to get the image from
      tmp_dir (str): temporary directory to store the image
      threshold (float): confidence level for object detection
      desired_width (int): desired image width in pixels
      desired_height (int): desired image height in pixels
      local (boolean): describes if the server is running on localhost
      api_key (str): key for the Google Vision API
      bucket (str, optional): Name of the Google Cloud Storage. Defaults to None

  Returns:
      (str,
       str,
       int,
       int,
       Dict[str,Dict]): the generated URL after saving the image in the server,
       name of the image, image width, image height and the polygons found in
       the image
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
  del desired_height
  objects = localize_objects(img_url, api_key)
  req = Request(img_url, headers=headers)
  resp = urlopen(req)
  arr = np.asarray(bytearray(resp.read()), dtype=np.uint8)
  img = cv2.imdecode(arr, -1)

  if desired_width:
    img = image_resize(img, width=desired_width)
  img_name = img_url.split('/')[-1]
  new_img_url = f'{tmp_dir}/{img_name}'
  cv2.imwrite(new_img_url, img)
  height, width = img.shape[:2]
  polygons = _get_polygons(objects, width, height, float(threshold))

  if not local:
    _upload_file_to_gcs(new_img_url, img_name, bucket)
    new_img_url = img_name
  else:
    new_img_url = f'/{new_img_url}'

  return (new_img_url, img_name, width, height, polygons)
