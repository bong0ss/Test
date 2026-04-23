import logging
import os
import shutil
import time

from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.urls import reverse
from django.utils.safestring import mark_safe
from openpyxl import load_workbook

from .alarms_TP_to_unified import (
    convert_fieldinfo,
    extract_alarm_parameters,
    norm,
    strip_index,
    to_int,
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
    wb = load_workbook(input_xlsx)
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
    os.makedirs(f"UserFiles/{str(user_id)}", exist_ok=True)
    shutil.move(output_xlsx, f"UserFiles/{str(user_id)}")
    return mark_safe(
        f'<a href="{reverse('download', args=[user_id, output_xlsx, og_output_xlsx])}">Pobierz plik</a>'
    )
