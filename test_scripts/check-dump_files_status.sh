echo check projects:
sudo docker inspect -f '{{.State.Status}}' dump_projects
echo check screens:
sudo docker inspect -f '{{.State.Status}}' dump_screens
