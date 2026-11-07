#!/bin/sh
cat > /tmp/s3.json <<EOF
{"identities":[{"name":"lake","credentials":[{"accessKey":"${S3_ACCESS_KEY}","secretKey":"${S3_SECRET_KEY}"}],"actions":["Admin","Read","Write","List","Tagging"]}]}
EOF
exec weed server -dir=/data -master.volumeSizeLimitMB=512 -volume.max=50 -filer -s3 -s3.port=8333 -s3.config=/tmp/s3.json
