import json
import logging
import os
import shutil
import time

import openpyxl
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.urls import reverse
from django.utils.safestring import mark_safe

from .alarms_TP_to_unified import (
    convert_fieldinfo,
    extract_alarm_parameters,
    norm,
    strip_index,
    to_int,
)
from .proface_adress_translator import (
    change_start_val,
    dbb_to_ls_word,
    dbx_to_ls,
    ls_bit_to_dbx,
    ls_to_dbb_bytes,
)
from .utility import custom_data

logger = logging.getLogger(__name__)


@shared_task
def add(x, y, user_id=None):
    return x + y


@shared_task
def sub(x, y, user_id=None):
    return x - y


@shared_task
def mult(x, y, user_id=None):
    return x * y


@shared_task(name="members.tasks.timer", bind=True)
def timer(self, time_left, user_id=None):
    progress = ProgressRecorder(self)
    custom_data(
        data=f"Action started at {time.ctime()}, await {time_left} seconds! Predicted to finish at {time.ctime(time.time() + time_left)}"
    )
    for i in range(time_left):
        time.sleep(1)
        progress.set_progress(i + 1, time_left, description="Processing...")
    custom_data(data=f"Action finished at {time.ctime()}")
    return "Finished!"


@shared_task(bind=True)
def alarms_tp_uni(self, input_xlsx, output_xlsx, input_txt, user_id):
    wb = openpyxl.load_workbook(input_xlsx)
    ws = wb["DiscreteAlarms"]
    og_output_xlsx = output_xlsx
    output_xlsx = str(user_id) + "_" + str(int(time.time())) + "_" + output_xlsx
    # Map headers
    headers = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(1, c).value
        if v:
            headers[norm(v)] = c
    tag_col = headers["trigger tag"]
    bit_col = headers["trigger bit"]
    fieldinfo_col = headers["fieldinfo [alarm text]"]

    # ---- Rename headers ----
    ws.cell(1, 3).value = "Alarm text [en-US], Alarm text 1"
    ws.cell(1, 4).value = "FieldInfo [Alarm text 1]"

    # ---- Add "Alarm parameter" columns ----
    ws.insert_cols(ws.max_column + 1)
    param1_col = ws.max_column
    ws.cell(1, param1_col).value = "Alarm parameter 1"
    param2_col = param1_col + 1
    param3_col = param1_col + 2
    param4_col = param1_col + 3
    ws.cell(1, param2_col).value = "Alarm parameter 2"
    ws.cell(1, param3_col).value = "Alarm parameter 3"
    ws.cell(1, param4_col).value = "Alarm parameter 4"
    # ---- Process rows ----
    for r in range(2, ws.max_row + 1):
        # Trigger fix
        tag = ws.cell(r, tag_col).value
        bit = to_int(ws.cell(r, bit_col).value)

        if isinstance(tag, str) and bit is not None:
            base = strip_index(tag)
            if base in input_txt:
                elem = bit // 16
                within = bit % 16
                fixed_bit = within ^ 8

                ws.cell(r, tag_col).value = f"{base}[{elem}]"
                ws.cell(r, bit_col).value = fixed_bit

        # FieldInfo conversion
        fi = ws.cell(r, fieldinfo_col).value
        ws.cell(r, fieldinfo_col).value = convert_fieldinfo(fi)

        # ---- Alarm parameter extraction ----
        fi = ws.cell(r, fieldinfo_col).value
        params = extract_alarm_parameters(fi)
        # Default values when parameter is missing
        ws.cell(r, param1_col).value = params[0] if len(params) >= 1 else "<No value>"
        ws.cell(r, param2_col).value = params[1] if len(params) >= 2 else "<No value>"
        ws.cell(r, param3_col).value = params[2] if len(params) >= 3 else "<No value>"
        ws.cell(r, param4_col).value = params[3] if len(params) >= 4 else "<No value>"
    if os.path.exists(input_xlsx):
        os.remove(input_xlsx)
    wb.save(output_xlsx)
    os.makedirs(f"UserFiles/{str(user_id)}/alarmsTPuni", exist_ok=True)
    shutil.move(output_xlsx, f"UserFiles/{str(user_id)}/alarmsTPuni")
    return mark_safe(
        f'<a href="{reverse("download", args=[user_id, output_xlsx, og_output_xlsx, "alarmsTPuni"])}">Download</a>'
    )


@shared_task(bind=True)
def proface_adress_translate(self, data, user_id=None):
    change_start_val(int(data.get("startdbw")), int(data.get("startls")))
    int_data = data.get("intData", {})
    results = []
    results_json = {}
    for i in int_data["plc"]:
        if len(int_data["plc"][i]) > 1:
            results.append(
                dbx_to_ls(
                    int(int_data["plc"][i][0].get("word")),
                    int(int_data["plc"][i][1].get("bit")),
                )
            )
        else:
            results.append(dbb_to_ls_word(int(int_data["plc"][i][0].get("word"))))
    for i in int_data["proface"]:
        if len(int_data["proface"][i]) > 1:
            results.append(
                ls_bit_to_dbx(
                    int(int_data["proface"][i][0].get("word")),
                    int(int_data["proface"][i][1].get("bit")),
                )
            )
        else:
            results.append(ls_to_dbb_bytes(int(int_data["proface"][i][0].get("word"))))

    for i, value in enumerate(results):
        results_json[i] = value
    return json.dumps(results_json)


@shared_task(bind=True)
def merge_xlsx(
    self,
    og_xlsx,
    og_names,
    og_values,
    fix_xlsx,
    fix_names,
    fix_values,
    output_xlsx,
    user_id=None,
):
    og_output_xlsx = output_xlsx
    output_xlsx = str(user_id) + "_" + str(int(time.time())) + "_" + output_xlsx
    wb = openpyxl.load_workbook(og_xlsx)
    og_wb = wb.active
    fix_wb = openpyxl.load_workbook(fix_xlsx).active

    og_values = ord(og_values.upper()) - 64
    fix_values = ord(fix_values.upper()) - 64

    for cell in fix_wb[fix_names]:
        for newcell in og_wb[og_names]:
            if cell.value is not None and cell.value == newcell.value:
                if (
                    og_wb.cell(newcell.row, og_values).value
                    != fix_wb.cell(cell.row, fix_values).value
                ):
                    og_wb.cell(newcell.row, og_values).value = fix_wb.cell(
                        cell.row, fix_values
                    ).value

    wb.save(output_xlsx)
    os.makedirs(f"UserFiles/{str(user_id)}/FixedXLSX", exist_ok=True)
    shutil.move(output_xlsx, f"UserFiles/{str(user_id)}/FixedXLSX")
    if os.path.exists(og_xlsx):
        os.remove(og_xlsx)
    if os.path.exists(fix_xlsx):
        os.remove(fix_xlsx)
    return mark_safe(
        f'<a href="{reverse("download", args=[user_id, output_xlsx, og_output_xlsx, "FixedXLSX"])}">Download</a>'
    )
