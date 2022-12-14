#!/bin/bash
read -p "Do you want to stop all the containers? (y/n) " resp
if [ "$resp" = "y" ]; then
  sudo docker stop $(sudo docker ps -q)
  sudo docker rm  $(sudo docker ps -a  -q)
else
  echo "Exit" ;
fi
