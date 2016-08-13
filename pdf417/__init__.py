from pdf417.encoders import DataEncoder
from pdf417.util import chunks
from pdf417.error_correction import compute_error_correction_code_words
from pdf417.codes import map_code_word

START_CHARACTER = 0x1fea8
STOP_CHARACTER = 0x3fa29
PADDING_CODE_WORD = 900


def encode_low(data, columns=6, security_level=2):
    if columns < 1 or columns > 30:
        raise ValueError("'columns' must be between 1 and 30. Given: %r" % columns)

    if security_level < 1 or security_level > 8:
        raise ValueError("'security_level' must be between 1 and 8. Given: %r" % security_level)

    num_cols = columns  # Nomenclature

    # Convert data to code words and split into rows
    code_words = encode_high(data, num_cols, security_level)
    rows = list(chunks(code_words, num_cols))

    return encode_rows(rows, num_cols, security_level)


def encode_rows(rows, num_cols, security_level):
    num_rows = len(rows)

    for row_no, row_data in enumerate(rows):
        left = get_left_code_word(row_no, num_rows, num_cols, security_level)
        right = get_right_code_word(row_no, num_rows, num_cols, security_level)

        yield encode_row(row_no, row_data, left, right)


def encode_row(row_no, row_words, left, right):
    table_idx = row_no % 3

    # Convert high level code words to low level code words
    left_low = map_code_word(table_idx, left)
    right_low = map_code_word(table_idx, right)
    row_words_low = [map_code_word(table_idx, word) for word in row_words]

    return [START_CHARACTER, left_low] + row_words_low + [right_low, STOP_CHARACTER]


def encode_high(data, columns, security_level):
    """Converts the input string to high level code words.

    Including the length indicator and the error correction words, but without
    padding.
    """

    # Encode data to code words
    data_words = list(DataEncoder().encode(data))
    data_count = len(data_words)

    # Get the padding to align data to column count
    ec_count = 2 ** (security_level + 1)
    padding_words = get_padding(data_count, ec_count, columns)
    padding_count = len(padding_words)

    # Length includes the data CWs, padding CWs and the specifier itself
    length = data_count + padding_count + 1

    # Join encoded data with the length specifier and padding
    extendend_words = [length] + data_words + padding_words

    # Calculate error correction words
    ec_words = compute_error_correction_code_words(extendend_words, security_level)

    return extendend_words + ec_words


def get_left_code_word(row_no, num_rows, num_cols, security_level):
    table_id = row_no % 3

    if table_id == 0:
        x = (num_rows - 1) // 3
    elif table_id == 1:
        x = security_level * 3 + (num_rows - 1) % 3
    elif table_id == 2:
        x = num_cols - 1

    return 30 * (row_no // 3) + x


def get_right_code_word(row_no, num_rows, num_cols, security_level):
    table_id = row_no % 3

    if table_id == 0:
        x = num_cols - 1
    elif table_id == 1:
        x = (num_rows - 1) // 3
    elif table_id == 2:
        x = security_level * 3 + (num_rows - 1) % 3

    return 30 * (row_no // 3) + x


def get_padding(data_count, ec_count, num_cols):
    # Total number of data words and error correction words, additionally
    # reserve 1 code word for the length descriptor
    total_count = data_count + ec_count + 1
    mod = total_count % num_cols

    return [PADDING_CODE_WORD] * (num_cols - mod) if mod > 0 else []
