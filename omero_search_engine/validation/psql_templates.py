#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2022 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This file contains SQLstatment templates which are used to test the app
It will compare the results from the PostgreSQL and the searchengine and
report it to the user.
It will use direct PostgreSQL statement templates to allow the tester to
compare the results through a method inside manage.py
It will support complex queries as well as single queries.
"""

from string import Template


class SqlSearchEngineTemplate(Template):
    def __init__(self, template):
        self.operator = "="
        super(SqlSearchEngineTemplate, self).__init__(template)

    def substitute(self, **kwargs):
        if "operator" not in kwargs:
            kwargs["operator"] = self.operator

        return super(SqlSearchEngineTemplate, self).substitute(kwargs)


# get available values for an image key
query_images_available_values_for_key = Template(
    """
Select DISTINCT lower(annotation_mapvalue.value) from image
inner join imageannotationlink on image.id =imageannotationlink.parent
inner join annotation_mapvalue on
annotation_mapvalue.annotation_id=imageannotationlink.child
where lower(annotation_mapvalue.name)='$name' """
)

# get any values for an image keys
query_images_any_value = Template(
    """
Select DISTINCT lower(annotation_mapvalue.name),
lower(annotation_mapvalue.value) from image
inner join imageannotationlink on image.id =imageannotationlink.parent
inner join annotation_mapvalue on
annotation_mapvalue.annotation_id=imageannotationlink.child
where lower(annotation_mapvalue.value) like '%$val_part%' """
)

# get any values for an image keys
query_images_contains_not_contains = Template(
    """
Select DISTINCT image.id from image
inner join imageannotationlink on image.id =imageannotationlink.parent
inner join annotation_mapvalue on
annotation_mapvalue.annotation_id=imageannotationlink.child
where lower(annotation_mapvalue.name)='$name'
and lower(annotation_mapvalue.value) $operator ('%$value%') """
)


# get images satisfy image key-value query
query_images_key_value = Template(
    """
Select DISTINCT image.id from image
inner join imageannotationlink on image.id =imageannotationlink.parent
inner join annotation_mapvalue on
annotation_mapvalue.annotation_id=imageannotationlink.child
where lower(annotation_mapvalue.name)='$name' and
lower(annotation_mapvalue.value)$operator lower('$value')"""
)

# get images satisfy image key-value query
query_images_value_only = Template(
    """
Select DISTINCT image.id from image
inner join imageannotationlink on image.id =imageannotationlink.parent
inner join annotation_mapvalue on
annotation_mapvalue.annotation_id=imageannotationlink.child
where lower(annotation_mapvalue.value) like '%$value%'"""
)


# Get number of images which satisfy project key-value query
query_image_project_meta_data = Template(
    """
Select image.id from image inner join datasetimagelink
on datasetimagelink.child=image.id
inner join dataset on datasetimagelink.parent=dataset.id
inner join projectdatasetlink on dataset.id=projectdatasetlink.child
inner join project on project.id=projectdatasetlink.parent
inner join projectannotationlink
on project.id =projectannotationlink.parent
inner join annotation_mapvalue
on annotation_mapvalue.annotation_id=projectannotationlink.child
where lower(annotation_mapvalue.name)=lower('$name')
and lower(annotation_mapvalue.value) $operator lower('$value')"""
)

# Get the  number of images using "in"
query_image_in = Template(
    """
Select DISTINCT image.id from image
inner join imageannotationlink
on image.id =imageannotationlink.parent
inner join annotation_mapvalue
on annotation_mapvalue.annotation_id=imageannotationlink.child
where lower(annotation_mapvalue.name) in ($names)
and lower(annotation_mapvalue.value) $operator ($values)"""
)

# Get the images which satisfy screen key-value query
query_images_screen_key_value = Template(
    """
Select DISTINCT image.id from image
inner join wellsample on wellsample.image=image.id
inner join well on wellsample.well= well.id
inner join  plate  on well.plate=plate.id
inner join screenplatelink on plate.id=screenplatelink.child
inner join screen on screen.id=screenplatelink.parent
inner join screenannotationlink
on screen.id =screenannotationlink.parent
inner join annotation_mapvalue
on annotation_mapvalue.annotation_id=screenannotationlink.child
where lower(annotation_mapvalue.name)= lower('$name')
and lower(annotation_mapvalue.value)$operator lower('$value')"""
)


# Get the images in a project using the project id
query_images_in_project_id = Template(
    """
Select DISTINCT image.id  from image
inner join datasetimagelink on datasetimagelink.child=image.id
inner join dataset on datasetimagelink.parent=dataset.id
inner join projectdatasetlink on dataset.id=projectdatasetlink.child
inner join  project on project.id=projectdatasetlink.parent
where project.id=$project_id"""
)

# get images in a project using project name
query_images_in_project_name = Template(
    """
Select DISTINCT  image.id from image
inner join datasetimagelink on datasetimagelink.child=image.id
inner join dataset on datasetimagelink.parent=dataset.id
inner join projectdatasetlink on dataset.id=projectdatasetlink.child
inner join project on project.id=projectdatasetlink.parent
where lower (project.name) $operator lower ('$name')"""
)

# get images in a screen using id
query_images_in_screen_id = Template(
    """
Select DISTINCT image.id from image
inner join wellsample on wellsample.image=image.id
inner join well on wellsample.well= well.id
inner join  plate  on well.plate=plate.id
inner join screenplatelink on plate.id=screenplatelink.child
inner join screen on screen.id=screenplatelink.parent
where screen.id=$screen_id"""
)

# Get the images in a screen using name
query_images_screen_name = Template(
    """
Select DISTINCT image.id from image
inner join wellsample on wellsample.image=image.id
inner join well on wellsample.well= well.id
inner join plate on well.plate=plate.id
inner join screenplatelink on plate.id=screenplatelink.child
inner join screen on screen.id=screenplatelink.parent
where lower(screen.name)$operator lower('$name')"""
)

# get resource id using its name
res_by_name = Template("""select id from $resource where name $name""")

# idr0015-colin-taraoceans/screenA

projects_count = Template(
    """
select DISTINCT project.name from image
inner join imageannotationlink on image.id=imageannotationlink.parent
inner join annotation_mapvalue on
annotation_mapvalue.annotation_id=imageannotationlink.child
inner join datasetimagelink on datasetimagelink.child=image.id
inner join dataset on datasetimagelink.parent=dataset.id
inner join projectdatasetlink on dataset.id=projectdatasetlink.child
inner join project on project.id=projectdatasetlink.parent
where lower(annotation_mapvalue.name)=lower('$key')
and lower(annotation_mapvalue.value) =lower('$value')
"""
)

screens_count = Template(
    """
select DISTINCT screen.name from image
inner join imageannotationlink on image.id = imageannotationlink.parent
inner join annotation_mapvalue on
annotation_mapvalue.annotation_id=imageannotationlink.child
inner join wellsample on wellsample.image=image.id
inner join well on wellsample.well= well.id
inner join plate on well.plate=plate.id
inner join screenplatelink on plate.id=screenplatelink.child
inner join screen on screen.id=screenplatelink.parent
where lower(annotation_mapvalue.name)=lower('$key')
and  lower(annotation_mapvalue.value) =lower('$value')"""
)

head_space_query = Template(
    """
select image.id as image_id, screen.name as screen_name, project.name as project_name,
 annotation_mapvalue.name, annotation_mapvalue.value  from image
 inner join imageannotationlink on image.id =imageannotationlink.parent
 inner join annotation_mapvalue on
 annotation_mapvalue.annotation_id=imageannotationlink.child
 left join datasetimagelink on datasetimagelink.child=image.id
 left join dataset on datasetimagelink.parent=dataset.id
 left join projectdatasetlink on dataset.id=projectdatasetlink.child
 left join project on project.id=projectdatasetlink.parent
 left join wellsample on wellsample.image=image.id
 left join well on wellsample.well= well.id  left join plate on well.plate=plate.id
 left join screenplatelink on plate.id=screenplatelink.child
 left join screen on screen.id=screenplatelink.parent
 where annotation_mapvalue.value  like ' %' $condition
 group by  project_name, screen_name,image.id,
 annotation_mapvalue.name, annotation_mapvalue.value
"""
)

trail_space_query = Template(
    """
select image.id as image_id, screen.name as screen_name, project.name as project_name,
 annotation_mapvalue.name, annotation_mapvalue.value  from image
 inner join imageannotationlink on image.id =imageannotationlink.parent
 inner join annotation_mapvalue on
 annotation_mapvalue.annotation_id=imageannotationlink.child
 left join datasetimagelink on datasetimagelink.child=image.id
 left join dataset on datasetimagelink.parent=dataset.id
 left join projectdatasetlink on dataset.id=projectdatasetlink.child
 left join project on project.id=projectdatasetlink.parent
 left join wellsample on wellsample.image=image.id
 left join well on wellsample.well= well.id
 left join plate on well.plate=plate.id
 left join screenplatelink on plate.id=screenplatelink.child
 left join screen on screen.id=screenplatelink.parent
 where annotation_mapvalue.value  like '% ' $condition
 group by project_name, screen_name,image.id, annotation_mapvalue.name,
 annotation_mapvalue.value
"""
)

duplicated_keyvalue_pairs_query = Template(
    """
Select  image.id as image_id, project.name as project_name, screen.name as screen_name,
 annotation_mapvalue.name,  annotation_mapvalue.value, count (*) from image
 left join datasetimagelink on datasetimagelink.child=image.id
 left join dataset on datasetimagelink.parent=dataset.id
 left join projectdatasetlink on dataset.id=projectdatasetlink.child
 left join project on project.id=projectdatasetlink.parent
 left join wellsample on wellsample.image=image.id
 left join well on wellsample.well= well.id  left join plate on well.plate=plate.id
 left join screenplatelink on plate.id=screenplatelink.child
 left join screen on screen.id=screenplatelink.parent
 inner join imageannotationlink on image.id =imageannotationlink.parent
 inner join annotation_mapvalue on
 annotation_mapvalue.annotation_id=imageannotationlink.child
  $condition
 group by project_name, screen_name,image.id, annotation_mapvalue.name,
 annotation_mapvalue.value HAVING COUNT(*)>1
 """
)

project_key_values = Template(
    """
Select DISTINCT (annotation_mapvalue.value)  from image
left join imageannotationlink on image.id =imageannotationlink.parent
left join annotation_mapvalue on
annotation_mapvalue.annotation_id=imageannotationlink.child
inner join datasetimagelink on datasetimagelink.child=image.id
inner join dataset on datasetimagelink.parent=dataset.id
inner join projectdatasetlink on dataset.id=projectdatasetlink.child
inner join project on project.id=projectdatasetlink.parent
where project.id= $id and lower (annotation_mapvalue.name) =lower('$name');
"""
)

screen_key_values = Template(
    """
Select DISTINCT (annotation_mapvalue.value)  from image
left join imageannotationlink on image.id =imageannotationlink.parent
left join annotation_mapvalue on
annotation_mapvalue.annotation_id=imageannotationlink.child
inner join wellsample on wellsample.image=image.id
inner join well on wellsample.well= well.id
inner join plate on well.plate=plate.id
inner join screenplatelink on plate.id=screenplatelink.child
inner join screen on screen.id=screenplatelink.parent
where screen.id =$id and lower (annotation_mapvalue.name) =lower('$name');
   """
)

container_from_name = Template(
    """
select id from $container where name like '%$name%';
"""
)
