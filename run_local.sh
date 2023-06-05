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

# Create virtual environment with python3
VIRTUALENV_PATH=$HOME/"ai-assisted-display-creative"
echo $VIRTUALENV_PATH
if [[ ! -d "${VIRTUALENV_PATH}" ]]; then
  virtualenv -p python3 "${VIRTUALENV_PATH}"
fi

# Activate virtual environment.
source ${VIRTUALENV_PATH}"/bin/activate"

find_config_value()
{

  
  NAME=$1

  FILE="./variables.tf"
  LINE_NO=$(grep -n "$NAME" "$FILE" | sed "s/:.*//")

  #echo "$LINE_NO"

  I=0
  LINE=""
  NOT_FOUND=1

  while [ "$NOT_FOUND" -eq 1 ]
  do
    read -r LINE
    I=$(( I + 1 ))
    if [[ ("$LINE" == *"default"*)  && ($I -gt $LINE_NO) ]]; then
      RESULT=$(echo "$LINE" | cut -d '=' -f2 | sed -e 's/^[[:space:]]*//' | sed -e 's/"//g')
      NOT_FOUND=0
    fi;

  done < "$FILE"

  echo "$RESULT"
}

export API_KEY=$(find_config_value "variable \"vision_api_key\"")
pip install -r requirements.txt
pip install gunicorn
cp third_party/jscolor.js static/js/
gunicorn -w 4 main:app