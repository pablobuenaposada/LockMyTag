resource "digitalocean_project" "my_project" {
  name = "LockMyTag"
}

resource "digitalocean_droplet" "droplet_name" {
  image     = var.image
  name      = var.droplet_name
  region    = var.droplet_region
  size      = var.image_size
  user_data = templatefile("${path.module}/init.sh", {})
}

resource "digitalocean_project_resources" "droplet_in_project" {
  project   = digitalocean_project.my_project.id
  resources = [digitalocean_droplet.droplet_name.urn]
}

output "droplet_ip" {
  value       = digitalocean_droplet.droplet_name.ipv4_address
  description = "The public IPv4 address of the droplet"
}