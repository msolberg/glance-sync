#!/usr/bin/env python

# Copyright 2018 Michael Solberg <msolberg@redhat.com>
# All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import openstack
import hashlib
import mmap

BLACKLIST=['EvmSnapshot']

def copy_image(src_image, src, dest, workdir, dryrun):
    if src_image in BLACKLIST:
        print "Skipping image %s" % (src_image)
        return

    print "Copying image %s" % (src_image)
    
    image = src.image.find_image(src_image)
    if image is None:
        raise Exception("Couldn't find source image: %s" % (src_image,))
    
    if dryrun:
        return

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
parser.add_argument('-n', dest='dryrun', action='store_true', default=False)
args = parser.parse_args()

print "Copying images from %s to %s."%(args.src, args.dest)
if args.dryrun:
    print "Dry run"

src = openstack.connect(cloud=args.src)
dest = openstack.connect(cloud=args.dest)

src_images = src.list_images()
dest_images = dest.list_images()

for src_image in [x['name'] for x in src_images]:
    if src_image not in [y['name'] for y in dest_images]:
        copy_image(src_image, src, dest, args.workdir, args.dryrun)
    else:
        print "Image %s exists on destination" %(src_image)
