# NFS

This section of the Help contains information on using the NFS namespace access protocol.

## Using NFS

NFS is one of the industry-standard protocols HCP supports for namespace access. To access a namespace through NFS, you can write applications that use any standard NFS client library, or you can use the command line in an NFS client to access the namespace directly.

Using the NFS protocol, you can store, view, retrieve, and delete objects. You can also change certain system metadata for existing objects.

For you to access a namespace through NFS, this protocol must be enabled in the namespace configuration. If you cannot use NFS to access the namespace, contact your tenant administrator.

This chapter explains how to use NFS for namespace access.

### Namespace access with NFS

You access the namespace through NFS by mounting a namespace directory on an NFS client. You can mount the namespace as a whole, either root directory (data or metadata), or any specific data directory or metadirectory. Additionally, you can have multiple directories mounted at the same time.

Once mounted, the namespace appears to be part of the local file system, and you can perform any of the operations HCP supports for NFS.

When mounting a namespace, you can use either the domain name of the HCP system or the IP address of a node in the system. Here’s the format for each method:

```
mount-otcp,vers=3,timeo=600,hard,intr
-t nfsnfs.hcp-domain-name:/fs/tenant-name/namespace-name
[/(data|metadata)[/directory-path]] mount-point-path

mount-otcp,vers=3,timeo=600,hard,intr
-t nfsnode-ip-address:/fs/tenant-name/namespace-name
[/(data|metadata)[/directory-path]] mount-point-path
```

The parameters shown are recommended but not required.

All parts of the path following the domain name or IP address are case sensitive.

Examples:

```
mount -o tcp,vers=3,timeo=600,hard,intr -t nfs
  nfs.hcp.example.com:/fs/europe/finance HCP-finance

mount -o tcp,vers=3,timeo=600,hard,intr -t nfs
  nfs.hcp.example.com:/fs/europe/finance/data datamount

mount -o tcp,vers=3,timeo=600,hard,intr -t nfs
  192.168.210.16:/fs/europe/finance/data/presentations/images HCP-images

mount -o tcp,vers=3,timeo=600,hard,intr -t nfs
  nfs.hcp.example.com:/fs/europe/finance/metadata metadatamount
```

Note: When mounting the namespace, do not specify the `rsize` and `wsize` options. Omitting these options allows HCP to use the optimal values based on system configuration.


### NFS return codes

The list below describes the possible return codes for NFS requests against a namespace.

EACCES

The requested operation is not allowed. Reasons for this return code include attempts to:


- Rename an object
- Rename a directory that contains one or more objects
- Overwrite an object
- Modify the content of an object
- Add a file (other than a file containing custom metadata), directory, or symbolic link anywhere in the metadata structure
- Delete a metafile or metadirectory

EAGAIN
HCP tried to read the requested object from another system in the replication topology, and the data either could not be read or was not yet available.
EIO

The requested operation is not allowed. This code is returned in response to attempts to:


- Shorten the retention period of an object
- Create a hard link

ENOTEMPTY

For an rm request to delete a directory, the specified directory cannot be deleted because it is not empty.
EROFS

For an rm request to delete an object, the specified object cannot be deleted because it is under retention.


## NFS examples

The following sections show examples of using NFS to access a namespace. Each example shows both a Unix command and Python code that implements the same command.

These examples assume that the data directory is mounted at datamount and the metadata metadirectory is mounted at metadatamount.

### Example: Storing an object

This example stores an object named wind.jpg in the existing images directory by copying a file of the same name from the local file system.

## Unix command

```
cp wind.jpg /datamount/images/wind.jpg
```

## Python code

```
import shutil
shutil.copy("wind.jpg", "/datamount/images/wind.jpg")
```

### Example: Changing a retention setting

This example extends the retention period for the wind.jpg object by one year. If this object is still open due to lazy close, changing the retention setting closes it.

## Unix command

```
echo +1y > /metadatamount/images/wind.jpg/retention.txt
```

## Python code

```
retention_value = "+1y"
retention_fh = file("/datamount/images/wind.jpg/retention.txt")
try:
retention_fh.write(retention_value)
finally:
retention_fh.close()
```

### Example: Using atime to set retention

This example changes the value of the POSIX atime attribute for the wind.jpg object. If the namespace is configured to synchronize `atime` values with retention settings and the object has a retention setting that specifies a date or time in the future, this also changes the retention setting for the object.

## Unix command

```
touch -a -t 201505171200 /datamount/images/wind.jpg
```

## Python code

```
import os
mTime = os.path.getmtime("/datamount/images/wind.jpg")
aTime = 1431878400 #12:00 May 17th 2015
os.utime("/datamount/images/wind.jpg", (aTime, mTime))
```

### Example: Creating a symbolic link

This example creates a symbolic link named `big_dipper` that references an object named ursa\_major.jpg.

## Unix command

```
ln -s /datamount/images/constellations/ursa_major.jpg
/datamount/constellations/common_names/big_dipper
```

## Python code

```
import os
os.symlink("/datamount/images/constellations/ursa_major.jpg",
"/datamount/constellations/common_names/big_dipper"
```

### Example Retrieving an object

This example retrieves the object named wind.jpg from a namespace and stores the resulting file in the retrieved\_files directory.

## Unix command

```
cp /datamount/images/wind.jpg retrieved_files/wind.jpg
```

## Python code

```
import shutil
shutil.copy("/datamount/images/wind.jpg", "retrieved_files/ \
wind.jpg")
```

## NFS usage considerations

This chapter presents considerations that affect the use of the NFS protocol for namespace access.

Note:HCP is an object store with multiple gateways that support various protocols. The NFS protocol exists on HCP to support legacy applications that do not have modern HTTP REST/S3 support. The NFS protocol on HCP is not designed to support direct end-user access.


### NFS lazy close

When writing a file to the namespace, NFS can cause a flush at any time and never issue a close. After each flush or write, HCP waits a short amount of time for the next one. If no write occurs within that time, HCP considers the resulting object to be complete and automatically closes it. This event is called lazy close.

If you set retention on an object during the lazy close period, HCP closes the object immediately. The object becomes WORM, and retention applies, even if the object contains no data. However, if the directory that contains the object and its corresponding metadirectory are mounted on two different nodes in the HCP system, setting retention during the lazy close period does not close the object.

### Using NFS with objects open for write

These considerations apply to objects that are open for write through any protocol:

- While an object is open for write through one IP address, you cannot open it for write through any other IP address.
- You can read an object that is open for write from any IP address, even though the object data may be incomplete. A read against the node hosting the write may return more data than a read against any other node.
- While an object is open for write, you cannot delete it.

Note: Depending on the timing, the delete request may result in a busy error. In that case, wait one or two seconds and then try the request again.


- While an object that’s open for write has no data:
  - It is not WORM
  - It may or may not have a cryptographic hash value
  - It is not subject to retention
  - It cannot have custom metadata
  - It is not indexed
  - It is not replicated

Note: If you observe multiple stale NFS file handle errors on an NFS client, you might resolve the issue by disabling client-side caching. To do this, add the mount option `lookupcache=none` to the command. The complete set of options will be:


```
-o tcp,vers=3,timeo=600,hard,intr,lookupcache=none
```

Setting this option will enhance the consistency of client access and may assist in mitigating the issue. However, it's important to note that it may also result in a significant degradation of performance.

### Failed NFS write operations

An NFS write operation is considered to have failed if the target node failed while the object was open for write. Also, in some circumstances, a write operation is considered to have failed if another node or other hardware failed while the object was open for write.

An NFS write operation is not considered to have failed if the TCP connection broke. This is because HCP doesn’t see the failure. In this case, lazy close applies, and the object is considered complete.

Objects left by failed NFS write operations:

- May have none, some, or all of their data
- If partially written, may or may not have a cryptographic hash value
- If the failure was on the HCP side, remain open and:

  - Are not WORM
  - Cannot have annotations
  - Are not indexed
  - Are not replicated
- If the failure was on the client side, are WORM after the lazy close

If a write operation fails, delete the object and try the write operation again.

Note: If the object is WORM, any retention setting applies. In this case, you may not be able to delete the object.


### Storing zero-sized files with NFS

When you store a zero-sized file with NFS, the resulting object has no data. After lazy close occurs, the object becomes WORM and is treated like any other object in the namespace.

### Out-of-order writes with NFS

NFS can write the data for an object out of order. If HCP receives an out-of-order write for a large file (200,000 bytes or larger), it discards the cryptographic hash value it already calculated. The object then has no hash value until either of these occurs:

- HCP returns to the object at a later time and calculates the hash value for it.
- A user or application opens or downloads the hash.txt metafile for the object, which causes HCP to calculate the hash value. However, because HCP calculates this value asynchronously, the value may not be immediately available. This is particularly true for large objects.

### NFS reads of large objects

While HCP is reading very large objects (thousands of megabytes or more) through NFS, system performance decreases.

### Walking large directory trees

HCP occasionally reuses inode numbers. Normally, this has no impact. However, it can affect programs that walk the directory tree, like the Unix du command. If you run such a program against a very large directory tree, it may not go down certain subdirectory paths.

One way to prevent this problem is to work on directory segments, instead of the entire directory tree. For example, when you use the du command you can run the command against smaller segments of the directory hierarchy; then add the returned values together to get the total.

### NFS delete operations

While an object is open for write through NFS on a given node, it cannot be deleted through NFS on other nodes.

### NFS mounts on a failed node

If an HCP node fails, NFS mounts that target the failed node lose their connections to the namespace. To recover from a node failure, unmount the namespace at the current mount point. Then take one of these actions:

- Mount the namespace on a different node. You can do this by specifying either the domain name of the HCP system or a different node IP address in the mount command. If you specify a domain name, HCP automatically selects a node from among the healthy ones.
- When the failed node becomes available again, remount the namespace on that node.

### Multithreading with NFS

HCP lets multiple threads access a namespace simultaneously. Using multiple threads can enhance performance, especially when accessing many small objects across multiple directories.

With NFS, multiple concurrent threads can write to the same object, but only if they are working against the same node. Multiple concurrent threads can read the same object on the same or different nodes.

With a single mount point, concurrent threads are always working against the same node.

HCP doesn’t limit the number of concurrent NFS threads per node but does limit the total number of outstanding requests using all protocols to 500 per node.

Note: CIFS and NFS share the same thread pool.