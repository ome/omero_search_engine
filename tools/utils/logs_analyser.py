import json
import os
import sys
import logging
import pandas as pd

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

"""
this script read the log file and get the search terms
it analyses the file and produces reports
 e.g. csv files contain the search terms
"""


def get_search_terms(folder_name, return_file_content=False):
    logging.info("checking files inside: %s" % folder_name)
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
            logging.info(str(e))
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


def write_reports(resourses, return_file_content, file_name):
    columns = ["key", "total hits", "unique hits"]
    import io

    out_io = io.BytesIO()
    writer = pd.ExcelWriter(out_io, engine="xlsxwriter")
    for res, terms in resourses.items():
        lines = []
        for name, values in terms.items():
            line = [name]
            lines.append(line)
            vv = []
            for val in values:
                if val not in vv:
                    vv.append(val)
            line.insert(1, len(values))
            line.insert(2, len(vv))

        df = pd.DataFrame(lines, columns=columns)
        df2 = df.sort_values(by=["total hits", "unique hits"], ascending=[False, False])
        df2.to_excel(writer, index=False, sheet_name=res)
        adjust_colunms_width(writer.sheets[res], columns, df2)
        insert_chart(writer, res, df2, len(lines))

    writer.save()
    writer.close()
    if return_file_content:
        return out_io
    with open(file_name, "wb") as out:
        out.write(out_io.getvalue())


def adjust_colunms_width(worksheet, columns, df2):
    for idx, col in enumerate(df2.columns):
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
