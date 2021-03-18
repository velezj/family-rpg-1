#!/usr/bin/env fish

set BASE ../../../march-2021/

rm -rf content
mkdir -p content
cp -r $BASE content/

for i in (find content/ -iname "*.md")
    echo "relinking '$i'"
    awk -i inplace -e '{ print gensub(/\(([^/]\S+)\.md\)/,"(../\\\\1)","g",$0); }' "$i"
end

