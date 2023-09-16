#
# Helper for memory calc
#
import logging as log

MEM_DIMS = ["Mb", "Gb"]


def parse_mem_str(value):

    v, dim = value[:-2], value[-2:]
    if dim not in MEM_DIMS:
        raise Exception(
            'Unsupported dimension {}/ avaliable [Mb, Gb]'.format(dim))
    return v, dim


def mem_str_to_bytes(mem_str):

    amount, unit = parse_mem_str(mem_str)
    log.debug("%s amount %s unit", amount, unit)
    if unit == MEM_DIMS[0]:
        return int(amount) * 1024 * 1024
    if unit == MEM_DIMS[1]:
        return int(amount) * 1024 * 1024 * 1024

    raise Exception(f"Unit {unit} not defined")


def mem_str_to_kilobytes(mem_str):

    amount, unit = parse_mem_str(mem_str)
    log.debug("%s amount %s unit", amount, unit)
    if unit == MEM_DIMS[0]:
        return int(amount) * 1024
    if unit == MEM_DIMS[1]:
        return int(amount) * 1024 * 1024

    raise Exception(f"Unit {unit} not defined")
