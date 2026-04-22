import re


def norm(s):
    return re.sub(r"\s+", " ", str(s).strip().lower())


def extract_alarm_parameter_1(fieldinfo):
    """
    Extracts Tag from <ref id = 0 ... Tag = XXX; ...>
    """
    if not isinstance(fieldinfo, str):
        return None

    m = re.search(
        r"id\s*=\s*0.*?Tag\s*=\s*([^;>\s]+)", fieldinfo, flags=re.IGNORECASE | re.DOTALL
    )
    if m:
        return m.group(1).strip()
    return None


def extract_alarm_parameters(fieldinfo):
    """
    Extracts all Tags from <ref ... Tag = XXX; ...> blocks,
    ordered by their id (0, 1, 2, ...).
    """
    if not isinstance(fieldinfo, str):
        return []

    refs = re.findall(
        r"<ref\b.*?>",
        fieldinfo,
        flags=re.IGNORECASE | re.DOTALL,
    )

    def get_id(ref):
        m = re.search(r"id\s*=\s*(\d+)", ref, flags=re.IGNORECASE)
        return int(m.group(1)) if m else None

    refs_with_id = sorted(
        ((get_id(ref), ref) for ref in refs),
        key=lambda x: x[0] if x[0] is not None else 9999,
    )

    tags = []
    for _, ref in refs_with_id:
        m = re.search(
            r"Tag\s*=\s*([^;>\s]+)",
            ref,
            flags=re.IGNORECASE,
        )
        if m:
            tags.append(m.group(1).strip())

    return tags


def to_int(v):
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, str) and re.fullmatch(r"-?\d+", v.strip()):
        return int(v.strip())
    return None


def strip_index(tag):
    return re.sub(r"\[\d+\]\s*$", "", tag.strip())


def convert_fieldinfo(fieldinfo):
    if not isinstance(fieldinfo, str):
        return fieldinfo

    # Counter used to assign sequential Parameter numbers (1, 2, 3, ...)
    # based on appearance order of <ref ...> blocks, independent of id.
    param_counter = {"n": 0}

    def repl(m):
        ref = m.group(0)

        is_common = "type = CommonTextList" in ref

        param_counter["n"] += 1
        param_no = param_counter["n"]

        if ("type = AlarmTag" in ref) or is_common:
            ref = re.sub(
                r"type\s*=\s*(AlarmTag|CommonTextList)",
                f"type = AlarmParameterWithOrWithoutCommonTextList; "
                f"Parameter = Parameter {param_no}",
                ref,
                flags=re.IGNORECASE,
            )
        else:
            return ref

        extras = [
            "Precision = 0",
            "Alignment = Right",
            "ZeroPadding = False",
        ]

        if is_common and "DisplayType" not in ref:
            # Insert DisplayType = Textlist before Length if possible,
            # otherwise just append at the end together with other extras.
            if "Length" in ref:
                ref = re.sub(
                    r"(Length\s*=\s*[^;>]+;?)",
                    r"DisplayType = Textlist; \1",
                    ref,
                    flags=re.IGNORECASE,
                )
            else:
                extras.append("DisplayType = Textlist")

        for ex in extras:
            if ex not in ref:
                ref = ref.rstrip(">;") + f"; {ex};>"

        return ref

    return re.sub(r"<ref\b.*?>", repl, fieldinfo, flags=re.DOTALL)
