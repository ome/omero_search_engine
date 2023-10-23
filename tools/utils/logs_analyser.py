import json
import os
import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

"""
this script read the log file and get the search terms
it analyses the file and produces reports
 e.g. csv files contain the search terms
"""


def get_search_terms(folder_name, resource=None, return_file_content=False):
    logging.info("checking files inisde: %s" % folder_name)
    resourses = {}
    for root, dirs, files in os.walk(folder_name):
        logging.info("0....%s,%s,%s" % (root, dirs, files))
        for file_name in files:
            logging.info("1..... checking %s" % file_name)
            if file_name.endswith("engine_gunilog.log"):
                file_name = os.path.join(root, file_name)
                logging.info("2..... checking %s" % file_name)
                analyse_log_file(file_name, resourses)
    logging.info("Write the reports")
    contents = write_reports(
        resourses,
        resource,
        return_file_content,
        os.path.join(folder_name, "report.csv"),
    )
    if return_file_content:
        return contents


def analyse_log_file(file_name, resourses):
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
            print(str(e))
            failes = failes + 1

    for filter in filters:
        check_filters(filter.get("and_filters"), resourses)
        for or_f in filter.get("or_filters"):
            check_filters(or_f, resourses)


def check_filters(conds, resourses):
    for cond in conds:
        if cond.get("resource") in resourses:
            names_values = resourses[cond.get("resource")]
        else:
            names_values = {}
            resourses[cond.get("resource")] = names_values
        name = cond.get("name")
        value = cond.get("value")
        if name in names_values:
            names_values[name].append(value)
        else:
            names_values[name] = [value]


def write_reports(resourses, resource, return_file_content, file_name):
    for res, itms in resourses.items():
        lines = ["key,total hits,unique hits"]
        for name, values in itms.items():
            line = [name]
            vv = []
            for val in values:
                if val not in vv:
                    vv.append(val)
            line.insert(1, str(len(values)))
            line.insert(2, str(len(vv)))
            lines.append(",".join(line))
        contents = "\n".join(lines)
        if return_file_content:
            if res == resource:
                print("================================")
                print(resource, return_file_content)
                print("================================")
                return contents
        else:
            f = open(file_name.replace(".csv", "_%s.csv" % res), "w")
            f.write(contents)
            f.close()
