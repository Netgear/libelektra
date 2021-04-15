from pathlib import Path
import os, re, errno, sys

import kdb

elektra_namespaces = ["user:", "system:", "dir:", "spec:", "cascading:", "proc:"]

dir_file_special_name = "®elektra.value"

#translates from filesystem (that are below the "pid"-level) paths to elektra paths (e.g. '/user:/dir/@elektra.value' -> 'user:/dir', '/cascading:/key' -> '/key') 
def os_path_to_elektra_path(os_path):
    elektra_path = os_path
    if Path(elektra_path).name == dir_file_special_name:
        elektra_path = str(Path(elektra_path).parent).strip("/")
    if re.match("^cascading:|^/cascading:", elektra_path):
        elektra_path = re.sub("^cascading:|^/cascading:", "", elektra_path)
        if elektra_path == "":
            elektra_path = "/"
    else:
        elektra_path = elektra_path.strip("/") #remove slashes ('/' is reserved for the cascading namespace)
    
    if elektra_path.endswith(":"):
        elektra_path = elektra_path + "/" #special case intruced around elektra v5 (the root of a namespace needs a trailing slash)

    return elektra_path
   
#returns a kdb instance (with mocked argv, envp)
def _get_kdb_instance():
    config = kdb.KeySet(0)
    contract = kdb.KeySet(0)
    custom_envp = [ "%s=%s" % (k, v) for (k, v) in os.environ.items() ]
    kdb.goptsContract (contract, sys.argv, custom_envp, kdb.Key(), config)
    return kdb.KDB(contract)

def size_of_file(os_path):
    return len(file_contents(os_path))

def is_directory_empty(os_path):
    dirs, files = ls(os_path)
    return not bool(dirs) and not bool(files)
   
#performs function of the "kdb file" command 
def get_kdb_file(os_path):
    with _get_kdb_instance() as db:
        elektra_path = os_path_to_elektra_path(os_path)
        x = kdb.Key(elektra_path)
        db.get(kdb.KeySet(), x)
        return x.value 

def update_key_value(os_path: str, new_value: bytes):
    # kdb.kdb.KDBException, may be thrown
    # validation => whole key needs to be written at once

    with _get_kdb_instance() as db:
        path = os_path_to_elektra_path(os_path)

        ks = kdb.KeySet()
        db.get(ks, path)
        key = ks[path]


        #try to save new_value as UTF-8 string in case it can be decoded as such
        #TODO: manage 'binary' meta-key
        try:
            new_value_as_string = new_value.decode(encoding="utf-8", errors="strict")
            key.value = new_value_as_string
        except UnicodeDecodeError:
            key.value = new_value

        db.set(ks, path) #using key instead of path here deleted the key


#may throw KeyError
def file_contents(os_path):
    key, _ = get_key_and_keyset(os_path)

    if key.isString():
        return key.value.encode(encoding='UTF-8') #return bytes in all cases
    elif key.isBinary():
        return key.value
    else:
        raise Error("Unsupported key type")

#creates key, or, if key already exists, does nothing
def create_key(os_path):
    path = os_path_to_elektra_path(os_path)
    with _get_kdb_instance() as db:
        ks = kdb.KeySet()
        db.get(ks, path)
        if not path in ks:
            key = kdb.Key(path)
            ks.append(key)
        keys_modified = db.set(ks, path)
        if keys_modified != 1:
            raise OSError(errno.EIO) #occurs when creating keys in cascading namespace (why?)
            #TODO: could also be an attempt to create already existing key

def get_meta_map(os_path):
    key, _ = get_key_and_keyset(os_path)
    return { meta.name:meta.value for meta in key.getMeta() }

def has_meta(os_path, name):
    try:
        meta_map = get_meta_map(os_path)
        return name in get_meta_map(os_path)
    except KeyError:
        return False
    
#get_meta, set_meta may throw KeyError
def get_meta(os_path, name):
    return get_meta_map(os_path)[name]

def set_meta(os_path, name, value):
    meta_map = get_meta_map(os_path)
    meta_map[name] = value
    update_meta_map(os_path, meta_map)

def update_meta_map(os_path, new_meta_map):
    path = os_path_to_elektra_path(os_path)

    with _get_kdb_instance() as db:
        ks = kdb.KeySet()
        db.get(ks, path)
        key = ks[path]

        #delete old meta keys
        for meta_key in key.getMeta():
            key.delMeta(meta_key.name)
        
        #insert new meta keys
        for keyname in new_meta_map.keys():
            key.setMeta(keyname, new_meta_map[keyname])

        db.set(ks, path)

#may throw KeyError
def get_key_and_keyset(os_path):
    path = os_path_to_elektra_path(os_path)

    with _get_kdb_instance() as db:
        ks = kdb.KeySet()
        db.get(ks, path)
        key = ks[path]
        return (key, ks)

#returns tuple inidicating if path is dir, is file
def key_type(os_path):
    if os_path in [".", "..", "/", "/user:", "/system:", "/spec:", "/dir:", "/cascading:", "/proc:"]:
        return (True, False)

    dir_listing, file_listing = ls(os_path)

    return (bool(dir_listing), bool(file_listing))

def is_list_prefix(prefix, list_):
    if len(prefix) > len(list_):
        return False
    
    for (i, item) in enumerate(prefix):
            if list_[i] != item:
                return False
    return True

def is_path_prefix(prefix, path):
    #remove (potential) trailing / to cope with special case introduced in os_path_to_elektra_path
    prefix = re.sub("/$", "", prefix)
    return is_list_prefix(prefix.split("/"), path.split("/"))

def _remove_namespace_prefix(elektra_path):
    return re.sub("^.*:", "", elektra_path)

#returns tuple of dirs, files of given path (does not include '.', '..')
def ls(os_path):
    if os_path == "/":
        return ({"user:", "system:", "spec:", "dir:", "/cascading:"}, [])


    path = os_path_to_elektra_path(os_path)
    path ="bad"

    is_root_level = len(path) > 1 and path.endswith("/") # special case


    with _get_kdb_instance() as db:
        ks = kdb.KeySet()
        db.get(ks, path)

        path_without_namespace = _remove_namespace_prefix(path)
        result_keys_without_namespace = map(_remove_namespace_prefix, ks.unpack_names())
        below = {name.split(path_without_namespace)[1] for name in result_keys_without_namespace if is_path_prefix(path_without_namespace, name)}

        dirs = {name.split("/")[0 if is_root_level else 1] for name in below if "/" in name}
        files = {name for name in below if not "/" in name}.difference(dirs)

        if '' in files:
            files.remove('')
            files.add(dir_file_special_name)

        return (dirs, files)
