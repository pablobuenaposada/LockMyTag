# variables for our terraform configuration files

variable "image" {
  type        = string
  description = "the image to use for our linux server"
}

variable "droplet_name" {
  type        = string
  description = "name for our droplet"
}

variable "droplet_region" {
  type        = string
  description = "region for our droplet"
}

variable "image_size" {
  type        = string
  description = "size for our image"
}