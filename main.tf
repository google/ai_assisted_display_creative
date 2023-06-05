provider "google" {
  project = var.gcp_project
  region  = var.gcp_project_location
}

data "template_file" "data" {
  template = file("app_template.yaml")
  vars = {
    gcp_project  = var.gcp_project
    vision_api_key = var.vision_api_key
  }
}

resource "local_file" "yaml" {
  content  = data.template_file.data.rendered
  filename = "${path.module}/app.yaml"
}

resource "null_resource" "copy_third_party" {
 depends_on = [google_app_engine_application.app]
 triggers = {
        build_number = "${timestamp()}"
 }
 provisioner "local-exec" {
    command = "cp ./third_party/jscolor.js ./static/js/"
  }
}

resource "google_project_service" "appengine_api" {
  depends_on = [local_file.yaml]
  project = var.gcp_project
  service = "appengine.googleapis.com"
  disable_dependent_services = true
}

resource "google_app_engine_application" "app" {
  depends_on = [google_project_service.appengine_api]
  project     =  var.gcp_project
  location_id = var.gcp_project_location
}

resource "null_resource" "run_cloud_deploy" {
 depends_on = [google_app_engine_application.app]
 triggers = {
        build_number = "${timestamp()}"
 }
 provisioner "local-exec" {
    command = "gcloud app deploy"
  }
}