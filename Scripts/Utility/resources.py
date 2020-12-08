from psutil import virtual_memory


# check if there is enough free memory, limit set to 2GB
def is_there_free_memory(limit: object = 2 * 1000 * 1000 * 1000) -> object:
    return virtual_memory().free > limit
