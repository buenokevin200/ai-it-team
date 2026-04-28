terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "~> 1.60"
    }
  }
}

provider "huaweicloud" {
  region      = var.region
  access_key  = var.access_key
  secret_key  = var.secret_key
  project_id  = var.project_id
}

variable "region" {
  type        = string
  description = "Huawei Cloud region (e.g. la-north-2)"
}

variable "access_key" {
  type        = string
  sensitive   = true
  description = "Huawei Cloud Access Key (AK)"
}

variable "secret_key" {
  type        = string
  sensitive   = true
  description = "Huawei Cloud Secret Key (SK)"
}

variable "project_id" {
  type        = string
  description = "Huawei Cloud Project ID"
}
