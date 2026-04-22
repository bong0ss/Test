START_DBW = 14
START_LS = 3004


def dbw_to_ls(dbw: int) -> int:
    """Convert PLC DBW address to Pro-face LS word."""
    if (dbw - START_DBW) % 2 != 0:
        raise ValueError("DBW address must be word-aligned.")
    if dbw < START_DBW:
        raise ValueError("DBW address is before mapping start.")
    return START_LS + ((dbw - START_DBW) // 2)


def ls_to_dbw(ls_word: int) -> int:
    """Convert Pro-face LS word back to PLC DBW."""
    if ls_word < START_LS:
        raise ValueError("LS address is before mapping start.")
    return START_DBW + ((ls_word - START_LS) * 2)


def dbx_to_ls(byte_addr: int, bit: int) -> str:
    """
    Convert PLC DBX byte.bit to Pro-face LSword.bit format.

    Confirmed mapping:
    - even PLC byte -> LSxxxx.08 ... .15
    - odd PLC byte  -> LSxxxx.00 ... .07
    """
    if byte_addr < START_DBW:
        raise ValueError("Byte address is before mapping start.")
    if not (0 <= bit <= 7):
        raise ValueError("Bit must be in range 0..7")

    ls_word = START_LS + ((byte_addr - START_DBW) // 2)

    if byte_addr % 2 == 0:
        ls_bit = 8 + bit
    else:
        ls_bit = bit

    return f"LS{ls_word}{ls_bit:02d}"


def dbx_to_ls_compact(byte_addr: int, bit: int) -> str:
    """
    Same as dbx_to_ls, but in compact Pro-face style:
    LS3327.08 -> LS332708
    """
    human = dbx_to_ls(byte_addr, bit)
    word, bitpart = human.split(".")
    return f"{word}{bitpart}"


def dbb_to_ls_word(byte_addr: int) -> int:
    """
    Map a PLC byte address to the LS word that contains that byte.

    Examples:
    DBB660 -> LS3327
    DBB661 -> LS3327
    DBB662 -> LS3328
    """
    if byte_addr < START_DBW:
        raise ValueError("Byte address is before mapping start.")
    return START_LS + ((byte_addr - START_DBW) // 2)


def ls_bit_to_dbx(ls_word: int, ls_bit: int) -> str:
    """
    Convert Pro-face LSword.bit back to PLC DBX byte.bit.

    Confirmed reverse mapping:
    - LSxxxx.00 ... .07 -> odd PLC byte, bits 0..7
    - LSxxxx.08 ... .15 -> even PLC byte, bits 0..7
    """
    if ls_word < START_LS:
        raise ValueError("LS address is before mapping start.")
    if not (0 <= ls_bit <= 15):
        raise ValueError("LS bit must be in range 0..15")

    base_byte = START_DBW + ((ls_word - START_LS) * 2)

    if 0 <= ls_bit <= 7:
        byte_addr = base_byte + 1  # odd byte
        bit = ls_bit
    else:
        byte_addr = base_byte  # even byte
        bit = ls_bit - 8

    return f"DBX{byte_addr}.{bit}"


def ls_compact_to_dbx(ls_compact: int | str) -> str:
    """
    Convert compact Pro-face bit format like 332708 or 'LS332708'
    to PLC DBX byte.bit.

    Example:
    LS332708 -> DBX660.0
    """
    text = str(ls_compact).upper().replace("LS", "").strip()

    if len(text) < 3:
        raise ValueError("Compact LS bit address is too short.")

    ls_word = int(text[:-2])
    ls_bit = int(text[-2:])
    return ls_bit_to_dbx(ls_word, ls_bit)


def ls_to_dbb_bytes(ls_word: int) -> tuple[int, int]:
    """
    Convert an LS word into the two PLC byte addresses it contains.

    Returns:
        (even_byte, odd_byte)

    Example:
    LS3327 -> (660, 661)
    """
    if ls_word < START_LS:
        raise ValueError("LS address is before mapping start.")
    even_byte = START_DBW + ((ls_word - START_LS) * 2)
    odd_byte = even_byte + 1
    return even_byte, odd_byte


def memcpy_count_for_end(start_dbw: int, end_dbw: int) -> int:
    """Calculate memcpy word count to reach end_dbw inclusive."""
    if end_dbw < start_dbw:
        raise ValueError("end_dbw must be >= start_dbw")
    if (end_dbw - start_dbw) % 2 != 0:
        raise ValueError("Start and end must be word-aligned DBW addresses")
    return ((end_dbw - start_dbw) // 2) + 1


def memcpy_end_from_count(start_dbw: int, count: int) -> int:
    """Calculate ending DBW from start DBW and memcpy count."""
    if count < 1:
        raise ValueError("count must be >= 1")
    return start_dbw + (count - 1) * 2


if __name__ == "__main__":
    print("=== PLC -> Pro-face ===")
    print("DBX660.0 ->", dbx_to_ls(660, 0))  # LS332708
    print("DBB662   -> LS", dbb_to_ls_word(662))  # LS3328

    print("\n=== Pro-face -> PLC ===")
    print("LS332708 ->", ls_bit_to_dbx(3327, 8))  # DBX660.0
    print("LS3328    -> DBB", ls_to_dbb_bytes(3328))  # (662, 663)
