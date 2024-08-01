import json
import os
import sys
import logging
import pandas as pd

from omero_search_engine.api.v1.resources.resource_analyser import (
    get_resource_attributes,
)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

"""
this script read the log file and get the search terms
it analyses the file and produces reports
 e.g. csv files contain the search terms
"""


def get_search_terms(folder_name, max_top_values, return_file_content=False):
    logging.info("checking the available keys for each resource")
    res_av_keys_ = get_resource_attributes("all")
    logging.info("prepare keys to validate the search terms")
    res_av_keys = {}
    for res, values_ in res_av_keys_.items():
        values = []
        res_av_keys[res] = values
        for val in values_:
            values.append(val.lower().strip())

    logging.info("checking files inside: %s" % folder_name)
    resourses = {}
    for root, dirs, files in os.walk(folder_name):
        logging.info("0....%s,%s,%s" % (root, dirs, files))
        for file_name in files:
            logging.info("1..... checking %s" % file_name)
            if file_name.endswith("engine_gunilog.log"):
                file_name = os.path.join(root, file_name)
                logging.info("2..... checking %s" % file_name)
                analyse_log_file(file_name, resourses, res_av_keys)
    logging.info("Write the reports")
    contents = write_reports(
        resourses,
        return_file_content,
        os.path.join(folder_name, "report.csv"),
        max_top_values,
    )
    if return_file_content:
        return contents


def analyse_log_file(file_name, resourses, res_av_keys):
    # file_name="/mnt/d/logs/engine_gunilog.log"
    logging.info("Analyse: %s" % file_name)
    f = open(file_name, "r")
    contents = f.read()
    logs = contents.split(
        "INFO in query_handler: -------------------------------------------------"
    )
    f.close()

    failes = 0
    suc = 0
    co = 0
    filters = []
    for i in range(0, len(logs), 2):
        cont = logs[i].split(("\n"))
        lo = cont[1].split("in query_handler:")
        ss = "{'and_filters':" + lo[-1].split("{'and_filters':")[-1]
        if "[20]" in ss:
            continue
        co += 1
        ss = ss.replace("'", '"').replace("False", "false").replace("None", '"None"')
        try:
            filters.append(json.loads(ss, strict=False))
            suc = suc + 1
        except Exception as e:
            logging.info(str(e))
            failes = failes + 1

    for filter in filters:
        check_filters(filter.get("and_filters"), resourses, res_av_keys)
        for or_f in filter.get("or_filters"):
            check_filters(or_f, resourses, res_av_keys)
    print("################################################")
    print("Dalied is %s" % failes)
    print("################################################")


def check_filters(conds, resourses, res_av_keys):
    for cond in conds:
        if cond.get("resource") in resourses:
            names_values = resourses[cond.get("resource")]
        else:
            names_values = {}
            resourses[cond.get("resource")] = names_values
        name = cond.get("name")
        # check if the key exists
        # add it only of the key in the available resource's keys
        if not name.strip().lower() in res_av_keys[cond.get("resource")]:
            continue
        value = cond.get("value")
        if name in names_values:
            names_values[name].append(value)
        else:
            names_values[name] = [value]


def write_reports(resourses, return_file_content, file_name, max_top_values=5):
    columns = [
        "Keys \n (Shows no. of attempted searches)",
        "total hits \n(No. of KVP searches)",
        "unique hits \n(No. of unique KVPs searched for)",
    ]
    if max_top_values != 0:
        if max_top_values == "all":
            columns.append("All searched values")
        elif max_top_values > 1:
            columns.append("Top %s searched values" % max_top_values)
        else:
            columns.append("Top searched value")

    import io

    out_io = io.BytesIO()
    writer = pd.ExcelWriter(out_io, engine="xlsxwriter")
    # writer.book.formats[0].set_text_wrap()
    containers_lines = {}
    containers = ["project", "screen"]
    for res, terms in resourses.items():
        res_ = res
        lines = []
        if res in containers:
            if res in containers_lines:
                lines = containers_lines[res]
            else:
                containers_lines[res] = lines

        for name, values in terms.items():
            line = [name]
            lines.append(line)
            vv_ = {}
            for val in values:
                if val not in vv_:
                    vv_[val] = 1
                else:
                    vv_[val] = vv_[val] + 1
            vv = sorted(vv_.items(), key=lambda kv: kv[1])
            top_searchvalues = ""
            if max_top_values == "all":
                max_top_values = len(vv)

            for i in range(max_top_values):
                index = len(vv) - 1 - i
                if index < 0:
                    break
                if top_searchvalues:
                    top_searchvalues = top_searchvalues + ", %s:%s" % (
                        vv[index][0],
                        vv[index][1],
                    )
                else:
                    top_searchvalues = "%s:%s" % (vv[index][0], vv[index][1])
            line.insert(1, len(values))
            line.insert(2, len(vv))
            if max_top_values != 0:
                line.insert(3, "{%s}" % top_searchvalues)

        if res in containers:
            if len(containers_lines) > 1:
                lines = adjust_containers(containers_lines)
                res_ = "container"
            else:
                continue
        df = pd.DataFrame(lines, columns=columns)
        df2 = df.sort_values(by=[columns[1], columns[2]], ascending=[False, False])
        df2.to_excel(
            writer,
            index=False,
            sheet_name=res_,
        )
        adjust_colunms_width(writer.sheets[res_], columns, df2)
        insert_chart(writer, res_, df2, len(lines))

    writer.save()
    if return_file_content:
        return out_io
    with open(file_name, "wb") as out:
        out.write(out_io.getvalue())


def adjust_colunms_width(worksheet, columns, df2):
    for idx, col in enumerate(df2.columns):
        if idx == 3:
            worksheet.set_column(idx, idx, 30 + 1)
            continue
        series = df2[col]
        max_width = len(columns[idx])
        max_width_ = [len(str(s)) for s in series if len(str(s)) > max_width]
        if len(max_width_) > 0:
            max_width = max(max_width_)
        worksheet.set_column(idx, idx, max_width + 1)


def insert_chart(writer, sheet, df, no_points):
    workbook = writer.book
    sheet_obj = writer.sheets[sheet]
    chart = workbook.add_chart({"type": "pie"})
    (max_row, max_col) = df.shape
    chart.add_series({"values": [sheet, 1, 1, max_row, 1]})
    chart.add_series(
        {
            "categories": "=%s!A2:A%s" % (sheet, no_points),
            "values": "=%s!B2:B%s" % (sheet, no_points),
        }
    )
    sheet_obj.insert_chart(2, 5, chart)


def adjust_containers(containers_lines):
    lines = []
    added_keys = []
    for res, lines_ in containers_lines.items():
        for line in lines_:
            if not line[0].strip().lower() in added_keys:
                lines.append(line)
                added_keys.append(line[0].lower().strip())
    return lines
