**Disclaimer: This is not an official Google product.**

# AI Assisted Display Creative

This solution assists to create multi product display creatives ready for activation in
Google Ads and DV360.
Using Google Vision AI, different products are identified within the image for click to product landing
page

## Prerequisites

Google cloud user with privileges over App Engine and Vision API (ideally Owner role)

- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed
- Latest version of Terraform installed
- Python version >= 3.8.1 installed
- Python Virtualenv installed
- [Obtain the Google Cloud Vision API key](https://cloud.google.com/docs/authentication/api-keys?hl=en&visit_id=638212395469740489-1395798417&rd=1)

## How to deploy

- Clone this repository onto your local machine
by running ```git clone http://github.com/google/ai_assisted_display_creative.git```
- Navigate to the project folder ```cd ai_assisted_display_creative/```
- Make sure you edit the ```variables.tf``` file with all the relevant values.
- Run in the shell: ```gcloud auth application-default login``` [more details here](https://cloud.google.com/vision/docs/setup) and follow the steps to copy the code.
- Set the environment variable ```GOOGLE_APPLICATION_CREDENTIALS``` to the generated user key file after running the command above. It says something similar to ```Credentials saved to file: [/usr/local/xxx/home/xxxx/.config/gcloud/application_default_credentials.json]```. An example of the export command would be: ```export GOOGLE_APPLICATION_CREDENTIALS=/usr/local/xxx/home/xxxx/.config/gcloud/application_default_credentials.json```
- Run in the shell: terraform init
- Run in the shell: terraform apply
- Type `yes` and hit return
- When deployment is complete, the URL must be displayed in the shell. Somtehing like:
Deployed service [default] to [https://<my-project>.<region>.r.appspot.com]
- Open a browser and go to https://<my-project>.<region>.r.appspot.com

## How to run it in your local computer

- Clone this repository onto your local machine
by running ```git clone http://github.com/google/ai_assisted_display_creative```
- Navigate to the project folder ```cd ai_assisted_display_creative/```
- Run in the shell: ```gcloud auth application-default login``` [more details here](https://cloud.google.com/vision/docs/setup) and follow the steps to copy the code.
- Set the environment variable ```GOOGLE_APPLICATION_CREDENTIALS``` to the generated user key file after running the command above. It says something similar to ```Credentials saved to file: [/usr/local/xxx/home/xxxx/.config/gcloud/application_default_credentials.json]```. An example of the export command would be: ```export GOOGLE_APPLICATION_CREDENTIALS=/usr/local/xxx/home/xxxx/.config/gcloud/application_default_credentials.json```
- Make sure you replace the ```vision_api_key``` value in  the ```variables.tf```. No other values are required
- Run in the shell: sh run_local.sh
- Open a browser and go to [localhost:8000](http://localhost:8000)

## Generated Cloud Artefacts

- Google App Engine


## Ouput

The output is a zip file containing all the required files:
- html file
- images/ folder with all the referenced files

## Author

- Jaime Martinez (jaimemm@)
