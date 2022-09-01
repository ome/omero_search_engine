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

from omero_search_engine import search_omero_app
import pandas as pd
import os
from string import Template


image_sql = Template(
    """
select image.id, image.description, image.owner_id, image.experiment, image.group_id,
image.name as name, annotation_mapvalue.name as mapvalue_name,
annotation_mapvalue.value as mapvalue_value,
annotation_mapvalue.index as mapvalue_index,
project.name as project_name, project.id as project_id,
dataset.name as dataset_name, dataset.id as dataset_id,
screen.id as screen_id, screen.name as screen_name,
plate.id as plate_id, plate.name as plate_name,
well.id as well_id,wellsample.id as wellsample_id
from image
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
$whereclause
GROUP BY image.id, annotation_mapvalue.index,
annotation_mapvalue.name, annotation_mapvalue.value,
annotation_mapvalue.index, project.name, project.id,
dataset.name, dataset.id, screen.id, screen.name,
plate.id, plate.name, well.id,wellsample.id"""
)

images_sql_to_csv = (
    """copy ({image_sql}) TO 'images_sorted_ids.csv'  WITH CSV HEADER""".format(
        image_sql=image_sql.substitute(whereclause="")
    )
)  # noqa


plate_sql = Template(
    """
select plate.id, plate.owner_id, plate.group_id,plate.description,
plate.name as name, annotation_mapvalue.name as mapvalue_name,
annotation_mapvalue.value as mapvalue_value,
annotation_mapvalue.index as mapvalue_index from plate
inner join plateannotationlink on plate.id=plateannotationlink.parent
inner join annotation_mapvalue on
annotation_mapvalue.annotation_id=plateannotationlink.child
$whereclause
GROUP BY plate.id, annotation_mapvalue.index,
annotation_mapvalue.name, annotation_mapvalue.value"""
)

plate_sql_to_csv = (
    """copy ({plate_sql}) TO 'plates_sorted_ids.csv' WITH CSV HEADER""".format(
        plate_sql=plate_sql.substitute(whereclause="")
    )
)  # noqa

project_sql = Template(
    """
select project.id, project.owner_id, project.group_id, project.description,
project.name as name, annotation_mapvalue.name as mapvalue_name,
annotation_mapvalue.value as mapvalue_value,
annotation_mapvalue.index as mapvalue_index
from project
inner join projectannotationlink on project.id =projectannotationlink.parent
inner join annotation_mapvalue on
annotation_mapvalue.annotation_id=projectannotationlink.child
$whereclause
GROUP BY project.id, annotation_mapvalue.index,
annotation_mapvalue.name, annotation_mapvalue.value"""
)

project_sql_to_csv = """
copy ({project_sql}) TO 'projects_sorted_projects_screen_ids.csv'
WITH CSV HEADER""".format(
    project_sql=project_sql.substitute(whereclause="")
)


screen_sql = Template(
    """
select screen.id, screen.owner_id, screen.group_id,
screen.name as name,screen.description,
annotation_mapvalue.name as mapvalue_name,
annotation_mapvalue.value as mapvalue_value,
annotation_mapvalue.index as mapvalue_index from screen
inner join screenannotationlink on screen.id =screenannotationlink.parent
inner join annotation_mapvalue on
annotation_mapvalue.annotation_id=screenannotationlink.child
$whereclause
GROUP BY screen.id, annotation_mapvalue.index,
annotation_mapvalue.name, annotation_mapvalue.value"""
)

screen_sql_to_csv = """
copy ({screen_sql}) TO 'screens_sorted_projects_screen_ids.csv'
WITH CSV HEADER""".format(
    screen_sql=screen_sql.substitute(whereclause="")
)


well_sql = Template(
    """
select well.id, well.owner_id, well.group_id,
annotation_mapvalue.name as mapvalue_name,
annotation_mapvalue.value as mapvalue_value,
annotation_mapvalue.index as mapvalue_index from well
inner join wellannotationlink on well.id =wellannotationlink.parent
inner join annotation_mapvalue on
annotation_mapvalue.annotation_id=wellannotationlink.child
$whereclause
GROUP BY well.id,  annotation_mapvalue.index,
annotation_mapvalue.name, annotation_mapvalue.value"""
)

well_sql_to_csv = """
copy ({well_sql}) TO 'wells_sorted_ids.csv'  WITH CSV HEADER""".format(
    well_sql=well_sql.substitute(whereclause="")
)

images_projects_datasets = """
copy (select project.name as project_name,project.id as project_id,
dataset.name as dataset_name, dataset.id as dataset_id,
datasetimagelink.child as image_id from projectdatasetlink
inner join dataset on dataset.id=projectdatasetlink.child
inner join project on project.id=projectdatasetlink.parent
inner join  datasetimagelink on datasetimagelink.parent=dataset.id
where project.id is not null and dataset.id is not null) TO
'images_project_dataset.csv'  WITH CSV HEADER"""

images_plates_weel = """
copy (select wellsample.image as image_id, screenplatelink.parent
as screen_id, screen.name as screen_name , plate.name as plate_name,
plate.id as plate_id from plate
inner join screenplatelink on screenplatelink.child=plate.id
inner join  well on well.plate=plate.id
inner join wellsample on wellsample.well=well.id
inner join screen on screen.id=screenplatelink.parent
) TO 'images_plate_well.csv'  WITH CSV HEADER"""


def get_images_dataset_project(ids):
    sql = "select project.name as project_name,project.id as project_id,\
         dataset.name as dataset_name, dataset.id as dataset_id,\
         datasetimagelink.child as image_id from projectdatasetlink\
         inner join dataset on dataset.id=projectdatasetlink.child\
         inner join project on project.id=projectdatasetlink.parent\
         inner join datasetimagelink on datasetimagelink.parent=dataset.id\
         where project.id is not null and dataset.id is not null and\
         datasetimagelink.child in ({ids})".format(
        ids=ids
    )
    results = search_omero_app.config["database_connector"].execute_query(sql)
    return results


def get_images_plates_screens(ids):
    sql = "select wellsample.image as image_id, screenplatelink.parent\
           as screen_id, screen.name as screen_name ,\
           plate.name as plate_name,\
           plate.id as plate_id from plate\
           inner join screenplatelink on\
           screenplatelink.child=plate.id\
           inner join well on well.plate=plate.id\
           inner join wellsample on wellsample.well=well.id\
           inner join screen on screen.id=screenplatelink.parent\
           where wellsample.image in ({ids})".format(
        ids=ids
    )
    results = search_omero_app.config["database_connector"].execute_query(sql)
    screens = []
    plates = []
    for res in results:
        if res.get("screen_id") not in screens:
            screens.append(res.get("screen_id"))
        if res.get("plate_id") not in plates:
            plates.append(res.get("plate_id"))
    return results


def create_csv_for_images(folder):
    """
    Query database to get the image data then save them to multiple CSV files
    """
    conn = search_omero_app.config["database_connector"]
    image_data = conn.execute_query(image_sql)
    total_records = len(image_data)
    file_size = 2200000

    no_files = total_records / file_size
    print("Total reecords: ", total_records, ", no of files: ", no_files)
    data = pd.DataFrame(image_data)
    # data.to_csv(os.path(f'total_image_data.csv',folder),index=False)
    for i in range(no_files):
        print("Processing file no: {i}".format(i=i))
        df = data[file_size * i : file_size * (i + 1)]
        df.to_csv(os.path.join(f"image_data{i + 1}.csv", folder), index=False)


def create_csv_for_non_images(resource, csv_file):
    pass


sqls_resources = {
    "image": image_sql,
    "project": project_sql,
    "well": well_sql,
    "plate": plate_sql,
    "screen": screen_sql,
}
