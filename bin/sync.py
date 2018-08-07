#!/usr/bin/env python

# Copyright 2018 Michael Solberg <msolberg@redhat.com>
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import argparse
import openstack
import hashlib
import mmap

BLACKLIST=['EvmSnapshot']

def copy_image(src_image, src, dest, workdir):
    if src_image in BLACKLIST:
        print "Skipping image %s" % (src_image)
        return

    print "Copying image %s" % (src_image)
    
    image = src.image.find_image(src_image)
    if image is None:
        raise Exception("Couldn't find source image: %s" % (src_image,))
    
    md5 = hashlib.md5()

    tmpfile = open("%s/%s.qcow2" % (workdir, src_image), 'wb')
    response = src.image.download_image(image, stream=True)
        
    for chunk in response.iter_content(chunk_size=128):
        md5.update(chunk)
        tmpfile.write(chunk)
        
    if response.headers['Content-MD5'] != md5.hexdigest():
        raise Exception("Checksum mismatch in downloaded content.")

    tmpfile.close()
    
    tmpfile = open("%s/%s.qcow2" % (workdir, src_image), 'rb')

    #TODO: We should use mmap if the files are exceptionally large
    #data = mmap.mmap(tmpfile.fileno(), 0)
    data = tmpfile.read()
    tmpfile.close()
    
    image_attrs = {
        'name': src_image,
        'data': data,
        'disk_format': image.disk_format,
        'container_format': image.container_format,
        'min_disk': image.min_disk,
        'min_ram': image.min_ram,
        'architecture': image.architecture,
        'visibility': 'public',
    }
    dest.image.upload_image(**image_attrs)
    
    #TODO: We should use mmap if the files are exceptionally large
    #data.close()


parser = argparse.ArgumentParser()
parser.add_argument('-s', '--src')
parser.add_argument('-d', '--dest')
parser.add_argument('-w', '--workdir', default='/tmp')
args = parser.parse_args()

print "Copying images from %s to %s."%(args.src, args.dest)

src = openstack.connect(cloud=args.src)
dest = openstack.connect(cloud=args.dest)

src_images = src.list_images()
dest_images = dest.list_images()

for src_image in [x['name'] for x in src_images]:
    if src_image not in [y['name'] for y in dest_images]:
        copy_image(src_image, src, dest, args.workdir)
    else:
        print "Image %s exists on destination" %(src_image)
